from datetime import date, datetime, time
from os import environ
from typing import Any, List, Optional, Type
from urllib.parse import quote_plus

from pymongo import MongoClient

from nova_api import GenericDAO
from nova_api.dao import camel_to_snake
from nova_api.entity import Entity


class MongoDAO(GenericDAO):
    """Mongo implementation for the GenericDAO interface
    """
    # pylint: disable=R0913
    def __init__(self, database=environ.get('DB_NAME', 'default'),
                 fields: dict = None,
                 collection: str = None,
                 return_class: Type[Entity] = Entity,
                 prefix: str = None,
                 host: str = environ.get('DB_URL', 'localhost'),
                 user: str = environ.get('DB_USER', 'root'),
                 password: str = environ.get('DB_PASSWORD', 'root'),
                 database_instance=None) -> None:
        super().__init__(fields, return_class, prefix)

        self.client = database_instance
        if user:
            self.uri = \
                f"mongodb://{quote_plus(user)}:{quote_plus(password)}@{host}"
        else:
            self.uri = host

        if self.client is None:
            self.client = MongoClient(host=self.uri)

        self.database = self.client[database]

        self.collection = collection \
                          or camel_to_snake(return_class.__name__) + 's'
        self.cursor = self.database[self.collection]

    def get(self, id_: str) -> Optional[Entity]:
        """
        Recovers and entity with `id_` from the database. The id_ must be the \
        nova_api generated id_ which is a 32-char uuid v4.

        :raises InvalidIDTypeException: If the UUID is not a string
        :raises InvalidIDException: If the UUID is not a valid UUID v4 \
        without '-'.

        :param id_: The UUID of the instance to recover
        :return: None if no instance is found or a `return_class` instance \
        if found
        """
        super().get(id_)

        self.logger.debug("Get called with valid id %s", id_)
        result = self.cursor.find_one({self.fields['id_']: id_})
        result_object = self._create_entity_from_result(result)

        self.logger.debug("Found instance with id %s. Result: %s",
                          id_,
                          str(result_object))

        return result_object

    def _create_entity_from_result(self, result: dict) -> Optional[Entity]:
        """
        Instantiates a `return_class` instance from the dict returned \
        from Mongo. Returns None if no dict

        :param result: Dictionary returned from Mongo
        :return: A `return_class` instance
        """
        if not result:
            return None

        entity = {}
        for prop, field in self.fields.items():
            entity[prop] = result.pop(field, None)

        return self.return_class(**entity)

    def get_all(self, length: int = 20, offset: int = 0,
                filters=None) -> (int, List[Entity]):
        """
                Recovers all instances that match the given filters up to
                the length \
                specified starting from the offset given.

                The filters should be given as a dictionary, available keys
                are the \
                `return_class` attributes. The values may be only the
                desired value \
                or a list with the comparator in the first position and the
                value in \
                the second.

                Example:
                    >>> dao.get_all(length=50, offset=0,
                    ...             filters={"birthday":[">", "1/1/1998"],
                    ...                      "name":"John"})
                    (2, [ent1, ent2])

        :param length: The number of items to select
        :param offset: The number of items to skip before starting to select
        :param filters: A dict with the filters to use. The key must be a \
        valid attribute in the entity and the value may either be an specific \
        value or a list with two elements: an operator and a value,
        respectively.
        :return: A tuple with the totol number of entities in the database \
        and a list of the matched results.
        """
        if filters is None:
            filters = {}
        self.logger.debug("Getting all with filters %s limit %s and offset %s",
                          filters, length, offset)

        result_cur = self.cursor.find(self._generate_filters(filters),
                                      limit=length, skip=offset)

        results = []
        for result in result_cur:
            results.append(self._create_entity_from_result(result))

        if not results:
            self.logger.info("No results found in get_all. Returning none")
            return 0, []

        amount = self.cursor.count_documents({})

        return amount, results

    def _generate_filters(self, filters: dict) -> dict:
        """
        Converts the filters dict to the database field notation \
        and removes unknown fields included in filters.

        :param filters: The filters dict from get_all
        :return: The filters dict to use when querying MongoDB
        """
        prepared_filters = {}

        for key, value in filters.items():
            if key in self.fields:
                prepared_filters[self.fields[key]] = value

        return prepared_filters

    def remove(self, entity: Entity = None, filters: dict = None) -> int:
        """
        Removes entities from database. May be called either with an instance
        of return_class or a dict of filters. *If both are passed, the instance
        will be removed and the filters won't be considered.*Invalid filters \
        won't be considered.

        :raises NotEntityException: If `entity` is not a `return_class` \
        instance and filters are None.
        :raises EntityNotFoundException: If the entity is not found in the \
        database.
        :raises InvalidFiltersException: If filters is not None and is not \
        a dict.

        :raises NoRowsAffectedException: If no rows are affected by the \
        delete query.

        :param entity: `return_class` instance to delete.
        :param filters: Filters to apply to delete query in dict format as
        specified by `_generate_filters`
        :return: Number of affected rows.
        """
        super().remove(entity, filters)

        count = 0
        if entity is not None:
            self.cursor.delete_one({self.fields["id_"]: entity.id_})
            count = 1
        elif filters is not None:
            count = self.cursor.delete_many(
                self._generate_filters(filters)
            ).deleted_count

        return count

    def create(self, entity: Entity) -> str:
        """
        Creates a new row in the database with data from `entity`.

        :raises NotEntityException: Raised if the entity argument
        is not of the return_class of this DAO
        :raises DuplicateEntityException: Raised if an entity with
        the same ID exists in the database already.

        :param entity: The instance to save in the database.
        :return: The entity uuid.
        """
        super().create(entity)

        self.cursor.insert_one(
            self._prepare_db_dict(entity)
        )

        return entity.id_

    def _prepare_db_dict(self, entity: Entity) -> dict:
        """
        Return the entity as a document(dict) to be inserted
        in MongoDB

        :param entity: `return_class instance to serialize`
        :return: The entity as a document(dict)
        """
        values = entity.get_db_values(MongoDAO._custom_serializer)
        return dict(zip(self.fields.values(), values))

    @staticmethod
    def _custom_serializer(field_: Any) -> Any:
        """
        Serializes field for MongoDB insertion. This is used to \
        override the default serialization for datetime/data fields \
        in Entity.

        :param field_: The field to be serialized
        :return: The serialized field
        """
        if isinstance(field_, datetime):
            return field_
        if isinstance(field_, date):
            return datetime.combine(field_, time())
        return Entity.serialize_field(field_)

    def update(self, entity: Entity) -> str:
        """
        Updates an entity on the database.

        :raises NotEntityException: If `entity` is not a `return_class` \
        instance.
        :raises EntityNotFoundException: If the entity is not found in the \
        database.

        :param entity: The entity with updated values to update on \
        the database.
        :return: The id_ of the updated entity.
        """
        super().update(entity)
        old_ent = self.get(entity.id_)
        entity.last_modified_datetime = datetime.now()

        old_entity = self._prepare_db_dict(old_ent)
        new_entity = self._prepare_db_dict(entity)

        query = {}
        for field in self.fields.values():
            if old_entity.get(field, None) != new_entity.get(field, None):
                query.update({field: new_entity.get(field, None)})

        self.cursor.update_one({self.fields["id_"]: entity.id_},
                               {"$set": query})

        return entity.id_

    def close(self):
        """
        Closes the connection to the database

        :return: None
        """
        self.client.close()
