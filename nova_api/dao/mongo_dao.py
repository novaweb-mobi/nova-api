from datetime import date, datetime
from os import environ
from typing import List, Optional, Type
from urllib.parse import quote_plus

from pymongo import MongoClient

from nova_api import GenericDAO
from nova_api.dao import camel_to_snake
from nova_api.entity import Entity


class MongoDAO(GenericDAO):
    def __init__(self, database=environ.get('DB_NAME', 'default'),
                 fields: dict = None,
                 collection: str = None,
                 return_class: Type[Entity] = Entity,
                 prefix: str = None,
                 host: str = environ.get('DB_URL', 'localhost'),
                 user: str = environ.get('DB_USER', 'root'),
                 password: str = environ.get('DB_PASSWORD', 'root'),
                 database_instance=None, **kwargs) -> None:
        super().__init__(fields, return_class, prefix)

        self.client = database_instance
        if user:
            self.uri = "mongodb://%s:%s@%s" % (
                quote_plus(user), quote_plus(password), host)
        else:
            self.uri = host

        if self.client is None:
            self.client = MongoClient(host=self.uri)

        self.database = self.client[database]

        self.collection = collection \
                          or camel_to_snake(return_class.__name__) + 's'
        self.cursor = self.database[self.collection]

    def get(self, id_: str) -> Optional[Entity]:
        super().get(id_)

        self.logger.debug("Get called with valid id %s", id_)
        result = self.cursor.find_one({self.fields['id_']: id_})
        result_object = self.create_entity_from_result(result)

        self.logger.debug("Found instance with id %s. Result: %s",
                          id_,
                          str(result_object))

        return result_object

    def get_all(self, length: int = 20, offset: int = 0,
                filters=None) -> (int, List[Entity]):
        if filters is None:
            filters = {}
        self.logger.debug("Getting all with filters %s limit %s and offset %s",
                          filters, length, offset)

        result_cur = self.cursor.find(self.prepare_filters(filters),
                                      limit=length, skip=offset)

        results = []
        for result in result_cur:
            results.append(self.create_entity_from_result(result))

        if not results:
            self.logger.info("No results found in get_all. Returning none")
            return 0, []

        amount = self.cursor.count_documents({})

        return amount, results

    def prepare_filters(self, filters: dict) -> dict:
        prepared_filters = {}

        for key, value in filters.items():
            if key in self.fields:
                prepared_filters[self.fields[key]] = value

        return prepared_filters

    def create_entity_from_result(self, result):
        if not result:
            return None

        entity = {}
        for prop, field in self.fields.items():
            entity[prop] = result.pop(field, None)

        return self.return_class(**entity)

    def remove(self, entity: Entity = None, filters: dict = None) -> int:
        super().remove(entity, filters)

        if filters is not None:
            return self.cursor.delete_many(
                self.prepare_filters(filters)
            ).deleted_count
        elif entity is not None:
            self.cursor.delete_one({self.fields["id_"]: entity.id_})
            return 1

    def create(self, entity: Entity) -> str:
        super().create(entity)

        self.cursor.insert_one(
            self.prepare_db_dict(entity)
        )

        return entity.id_

    def prepare_db_dict(self, entity):
        values = entity.get_db_values(MongoDAO.custom_serializer)
        return {key: value
                for key, value in zip(self.fields.values(), values)}

    @staticmethod
    def custom_serializer(field_):
        if isinstance(field_, datetime) or isinstance(field_, date):
            return field_
        return Entity.serialize_field(field_)

    def update(self, entity: Entity) -> str:
        pass

    def close(self):
        self.client.close()
