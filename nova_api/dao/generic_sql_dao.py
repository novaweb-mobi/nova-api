import dataclasses
from datetime import datetime
from typing import List, Optional, Type

from nova_api.dao import GenericDAO, camel_to_snake
from nova_api.entity import Entity
from nova_api.exceptions import NoRowsAffectedException
from nova_api.persistence import PersistenceHelper
from nova_api.persistence.mysql_helper import MySQLHelper


class GenericSQLDAO(GenericDAO):
    # pylint: disable=R0913
    def __init__(self, database_type: Type[PersistenceHelper] = None,
                 database_instance=None,
                 table: str = None,
                 fields: dict = None,
                 return_class: Type[Entity] = Entity,
                 prefix: str = None, **kwargs) -> None:
        super().__init__(fields, return_class, prefix)

        self.database_type = database_type

        if database_type is None and database_instance is None:
            self.database_type = MySQLHelper

        self.logger.debug("Started %s with database type as %s, table as %s, "
                          "fields as %s, return_class as %s and prefix as %s",
                          self.__class__.__name__, str(database_type),
                          table,
                          fields,
                          return_class.__name__,
                          prefix)

        self.database = database_instance

        if self.database is None:
            self.logger.debug("Database connection starting. Extra args: %s. ",
                              str(kwargs))
            self.database = self.database_type(**kwargs)
            self.logger.debug("Connected to database.")

        self.table = table or camel_to_snake(return_class.__name__) + 's'

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
        _, results = self.get_all(1, 0, {"id_": id_})

        if len(results) == 0:
            self.logger.info("No entries with id %s found. Returning None",
                             id_)
            return None

        self.logger.debug("Found instance with id %s. Result: %s",
                          id_,
                          str(results[0]))
        return results[0]

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        """
        Recovers all instances that match the given filters up to the length \
        specified starting from the offset given.

        The filters should be given as a dictionary, available keys are the \
        `return_class` attributes. The values may be only the desired value \
        or a list with the comparator in the first position and the value in \
        the second.

        Example:
            >>> dao.get_all(length=50, offset=0,
            ...             filters={"birthday":[">", "1/1/1998"],
            ...                      "name":"John"})
            (2, [ent1, ent2])

        :param length:
        :param offset:
        :param filters:
        :return:
        """
        self.logger.debug("Getting all with filters %s limit %s and offset %s",
                          str(filters), length, offset)

        filters_, query_params = ('', []) \
            if not filters \
            else self.generate_filters(filters)

        query = self.database.SELECT_QUERY.format(
            fields=', '.join(self.fields.values()),
            table=self.table,
            filters=filters_
        )

        self.logger.debug("Running query in database %s with params %s",
                          query,
                          str([*query_params, length, offset]))
        self.database.query(query, [*query_params, length, offset])
        results = self.database.get_results()

        if results is None:
            self.logger.info("No results found for query %s, %s in get_all. "
                             "Returning none", query, str([*query_params,
                                                           length, offset]))
            return 0, []

        return_list = [self.return_class(*result) for result in results]

        query_total = self.database.QUERY_TOTAL_COLUMN.format(
            table=self.table,
            column=self.fields['id_'])

        self.database.query(query_total)
        total = self.database.get_results()[0][0]
        self.logger.debug("Results are %s and the total in the database is %s",
                          str(return_list),
                          total)

        return total, return_list

    def remove(self, entity: Entity = None,
               filters: dict = None) -> int:
        """
        Removes entities from database. May be called either with an instance
        of return_class or a dict of filters. *If both are passed, the instance
        will be removed and the filters won't be considered.*

        :raises RuntimeError: If `entity` is not a `return_class` instance \
        and filters are None or if filters is not None and is not a dict.
        :raises AssertionError: If the entity is not found in the database.
        :raises NoRowsAffectedException: If no rows are affected by the \
        delete query.

        :param entity: `return_class` instance to delete.
        :param filters: Filters to apply to delete query in dict format as
        specified by `generate_filters`
        :return: Number of affected rows.
        """
        super().remove(entity, filters)

        filters_ = None
        query_params = None

        if filters is not None:
            filters_, query_params = self.generate_filters(filters)
        elif entity is not None:
            filters_, query_params = self.generate_filters({"id_": entity.id_})

        query = self.database.DELETE_QUERY.format(
            table=self.table,
            column=self.fields['id_'],
            filters=filters_)

        self.logger.debug("Running remove query in database: %s and params %s",
                          query,
                          query_params)
        row_count, _ = self.database.query(query, query_params)
        if row_count == 0:
            self.logger.error("No rows were affected in database during "
                              "remove!")
            raise NoRowsAffectedException()

        self.logger.info("{row_count} entities removed from database.",
                         row_count=row_count)

        return row_count

    def create(self, entity: Entity) -> str:
        """
        Creates a new row in the databse with data from `entity`.

        :param entity: The instance to save in the database.
        :return: The entity uuid.
        :raise NotEntityException: Raised if the entity argument
        is not of the return_class of this DAO
        :raise DuplicateEntityException: Raised if an entity with
        the same ID exists in the database already.
        """

        super().create(entity)

        ent_values = entity.get_db_values()

        query = self.database.INSERT_QUERY.format(
            table=self.table,
            fields=', '.join(self.fields.values()),
            values=', '.join(['%s'] * len(ent_values)))

        self.logger.debug("Running query in database: %s and params %s",
                          query,
                          ent_values)
        row_count, _ = self.database.query(query, ent_values)

        if row_count == 0:
            self.logger.error("No rows were affected in database during "
                              "create!")
            raise NoRowsAffectedException()

        self.logger.info("Entity created as %s", entity)

        return entity.id_

    def update(self, entity: Entity) -> str:
        """
        Updates an entity on the database.

        :param entity: The entity with updated values to update on \
        the database.
        :return: The id_ of the updated entity.
        """
        if not isinstance(entity, self.return_class):
            self.logger.error("Entity was not passed as an instance to update."
                              " Value received: %s", entity)
            raise TypeError(
                f"Entity must be a {self.return_class} object!"
            )

        if self.get(entity.id_) is None:
            self.logger.error("Entity was not found in database to update."
                              " Value received: %s", entity)
            raise AssertionError("Entity uuid doesn't exists in database!")

        entity.last_modified_datetime = datetime.now()

        ent_values = entity.get_db_values()

        query = self.database.UPDATE_QUERY.format(
            table=self.table,
            fields=', '.join(
                [field + '=%s' for field in
                 self.fields.values()]),
            column=self.fields['id_']
        )

        self.logger.debug("Running query in database: %s and params %s",
                          query,
                          ent_values + [entity.id_])
        row_count, _ = self.database.query(query,
                                           ent_values + [entity.id_])

        if row_count == 0:
            self.logger.error("No rows were affected in database during "
                              "update!")
            raise NoRowsAffectedException()

        self.logger.info("Entity updated to %s", entity)
        return entity.id_

    def create_table_if_not_exists(self) -> None:
        """
        Creates the table in the database based on the `return_class` \
        attributes. The types used in the database will be inferred through \
        `predict_db_types` or through the field metadata in the "type" key.

        :return: None
        """
        fields_ = []
        primary_keys = []

        self.logger.info("Starting create table processing.")
        for field in dataclasses.fields(self.return_class):
            self.logger.debug("Processing field %s", field)
            if field.metadata.get("database") is False:
                self.logger.debug("Field '%s' not included in database table, "
                                  "skipping.", field.name)
                continue

            type_ = field.metadata.get('type') \
                    or self.database.predict_db_type(field.type)
            self.logger.debug("'%s' type defined as '%s'", field.name, type_)

            default = field.metadata.get('default') or "NULL"

            field_name = self.fields.get(field.name)
            self.logger.debug("'%s' name defined as '%s'",
                              field.name, field_name)

            if field.metadata.get("primary_key"):
                self.logger.debug("'%s' added as primary key", field_name)
                primary_keys.append(str(field_name))
                if default == "NULL":
                    self.logger.warning("Had to change '%s' default because "
                                        "it is primary key and set to NULL.",
                                        field_name)
                    default = "NOT NULL"

            fields_.append(self.database.COLUMN.format(field=field_name,
                                                       type=type_,
                                                       default=default))
        fields_ = ', '.join(fields_)
        primary_keys = ', '.join(primary_keys)
        query = self.database.CREATE_QUERY.format(table=self.table,
                                                  fields=fields_,
                                                  primary_keys=primary_keys)
        self.logger.info("Creating table with query: %s", query)
        self.database.query(query)
        self.logger.info("Table created")

    def generate_filters(self, filters: dict) -> (str, List[str]):
        """
        Converts a dict of filters to apply to a query to a SQL query format.

        Example:
            >>> dao.generate_filters(
            ...     filters={"id_": "12345678901234567890123456789012",
            ...              "creation_datetime": [">", "2020-1-1"]})
            ("WHERE id_ = %s AND creation_datetime > %s", \
            ["12345678901234567890123456789012", "2020-1-1"])

        :raises ValueError: If filters is None.
        :raises TypeError: If filters is not a dict

        :param filters: dictionary of filters to apply. The key must be a \
        property of `return_class` and the value may be only the values, \
        if equality is expected or a list with the comparator and the value.
        :return: a tupĺe with the where statement and the list of params to use
        """
        if filters is None:
            raise ValueError("No filters where passed! Filters must be a dict "
                             "with param names, expected values and "
                             "comparators in this form: "
                             "{'param':['comparator', 'value']} "
                             "or {'param': 'value'} for equality.")

        if not isinstance(filters, dict):
            raise TypeError("Filters where passed not as dict!"
                            " Filters must be a dict "
                            "with param names, expected values and "
                            "comparators in this form: "
                            "{'param':['comparator', 'value']} "
                            "or {'param': 'value'} for equality.")

        query_params = [item[1] if isinstance(item, list) else item
                        for item in filters.values()]

        field_keys = self.fields.keys()
        for property_, value in filters.items():
            if property_ not in field_keys:
                self.logger.error("Property %s not available in %s for "
                                  "get_all.",
                                  property_,
                                  self.return_class.__name__)
                raise ValueError(
                    f"Property {property_} not available "
                    f"in {self.return_class.__name__}."
                )
            if isinstance(value, list) \
                    and value[0] not in self.database.ALLOWED_COMPARATORS:
                self.logger.error("Comparator %s not available in %s for "
                                  "get_all.",
                                  value[0],
                                  self.return_class.__name__)
                raise ValueError(
                    f"Comparator {value[0]} not allowed "
                    f"for {self.return_class.__name__}"
                )

        filters_for_query = [
            self.database.FILTER.format(
                column=self.fields[filter_],
                comparator=(filters[filter_][0]
                            if isinstance(filters[filter_], list)
                            else '='))
            for filter_ in filters.keys()
        ]
        filters_ = self.database.FILTERS.format(
            filters=' AND '.join(filters_for_query))

        return filters_, query_params

    def close(self) -> None:
        """
        Closes the connection to the database

        :return: None
        """
        self.logger.debug("Closing connection to database.")
        self.database.close()
