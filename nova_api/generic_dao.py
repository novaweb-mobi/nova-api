import dataclasses
import logging
from datetime import datetime
from re import sub
from typing import List, Optional

from nova_api.entity import Entity
from nova_api.exceptions import NoRowsAffectedException
from nova_api.mysql_helper import MySQLHelper


def camel_to_snake(name):
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class GenericSQLDAO:
    ALLOWED_COMPARATORS = ['=', '<=>', '<>', '!=', '>', '>=', '<=', 'LIKE']
    TYPE_MAPPING = {
        "bool": "TINYINT(1)",
        "datetime": "DATETIME",
        "str": "VARCHAR(100)",
        "int": "INT",
        "float": "DECIMAL",
        "date": "DATE"
    }
    CREATE_QUERY = "CREATE table IF NOT EXISTS {table} ({fields}, " \
                   "PRIMARY KEY({primary_keys})) ENGINE = InnoDB;"
    COLUMN = "`{field}` {type} {default}"
    SELECT_QUERY = "SELECT {fields} FROM {table} {filters} LIMIT %s OFFSET %s;"
    FILTERS = "WHERE {filters}"
    FILTER = "{column} {comparator} %s"

    # pylint: disable=R0913
    def __init__(self, database=None, table: str = None, fields: dict = None,
                 return_class: dataclasses.dataclass = Entity,
                 prefix: str = None) -> None:

        self.logger = logging.getLogger(__name__)

        self.logger.debug("Started %s with database as %s, table as %s, "
                          "fields as %s, return_class as %s and prefix as %s",
                          self.__class__.__name__, database, table, fields,
                          return_class, prefix)

        self.database = database
        if database is None:
            self.database = MySQLHelper()

        self.return_class = return_class

        self.table = table or camel_to_snake(return_class.__name__) + 's'

        self.prefix = prefix or camel_to_snake(return_class.__name__) + "_"

        if prefix == '':
            self.prefix = ''

        self.fields = fields
        if not self.fields:
            class_args = dataclasses.fields(return_class)
            self.logger.debug("Field passed to %s are %s.", self, class_args)
            self.fields = {arg.name:
                               self.prefix
                               + arg.name
                               + (''
                                  if not issubclass(arg.type,
                                                    Entity)
                                  else "_id_")
                           for arg in class_args
                           if arg.metadata.get("database", True)}
            self.logger.debug("Processed fields for %s are %s.",
                              self,
                              self.fields)

    def get(self, id_: str) -> Optional[Entity]:
        if not isinstance(id_, str):
            self.logger.error("ID was not passed as a str to get. "
                              "Value received: %s", id_)
            raise TypeError("UUID must be a 32-char string!")
        if len(id_) != 32:
            self.logger.error("ID is not a valid str in get. "
                              "Should be an uuid."
                              "Value received: %s", id_)
            raise ValueError("UUID must be a 32-char string!")

        self.logger.debug("Get called with valid id %s", id_)
        _, results = self.get_all(1, 0, {"id_": id_})

        if len(results) == 0:
            self.logger.info("No entries with id %s found. Returning None",
                             id_)
            return None

        self.logger.debug("Found instance with id %s. Result: %s",
                          id_,
                          results[0])
        return results[0]

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        query_params = list()
        self.logger.debug("Getting all with filters %s limit %s and offset %s",
                          filters, length, offset)
        filters_ = ''
        if filters:
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
                        "Property {prop} not available in {entity}.".format(
                            prop=property_,
                            entity=self.return_class.__name__
                        )
                    )
                if isinstance(value, list) \
                        and value[0] not in self.ALLOWED_COMPARATORS:
                    self.logger.error("Comparator %s not available in %s for "
                                      "get_all.",
                                      value[0],
                                      self.return_class.__name__)
                    raise ValueError(
                        "Comparator {comparator} not allowed for {entity}"
                        .format(comparator=value[0],
                                entity=self.return_class.__name__
                                )
                    )

            filters_for_query = [
                GenericSQLDAO.FILTER.format(
                    column=self.fields[filter_],
                    comparator=(filters[filter_][0]
                                if isinstance(filters[filter_], list)
                                else '='))
                for filter_ in filters.keys()
            ]
            filters_ = GenericSQLDAO.FILTERS.format(
                filters=' AND '.join(filters_for_query))

        query = GenericSQLDAO.SELECT_QUERY.format(
            fields=', '.join(self.fields.values()),
            table=self.table,
            filters=filters_
        )

        self.logger.debug("Running query in database %s with params %s",
                          query,
                          [*query_params, length, offset])
        self.database.query(query, [*query_params, length, offset])
        results = self.database.get_results()

        if results is None:
            self.logger.info("No results found for query %s, %s in get_all. "
                             "Returning none", query, [*query_params,
                                                       length, offset])
            return 0, []

        return_list = [self.return_class(*result) for result in results]

        query_total = "SELECT count({column}) FROM {table};".format(
            table=self.table,
            column=self.fields['id_'])

        self.database.query(query_total)
        total = self.database.get_results()[0][0]
        self.logger.debug("Results are %s and the total in the database is %s",
                          return_list,
                          total)

        return total, return_list

    def remove(self, entity: Entity) -> None:
        if not isinstance(entity, self.return_class):
            self.logger.error("Entity was not passed as an instance to remove."
                              " Value received: %s", entity)
            raise TypeError("Entity must be a {type} object!".format(
                type=self.return_class.__name__))

        if self.get(entity.id_) is None:
            self.logger.error("Entity was not found in database to remove."
                              " Value received: %s", entity)
            raise AssertionError(
                "{entity} uuid doesn't exists in database!".format(
                    entity=self.return_class.__name__
                )
            )

        query = 'DELETE FROM {table} WHERE {column} = %s;'.format(
            table=self.table,
            column=self.fields['id_'])

        self.logger.debug("Running remove query in database: %s and params %s",
                          query,
                          entity.id_)
        row_count, _ = self.database.query(query, [entity.id_])

        if row_count == 0:
            self.logger.error("No rows were affected in database during "
                              "remove!")
            raise NoRowsAffectedException()

        self.logger.info("Entity %s removed from database.", entity)

    def create(self, entity: Entity) -> str:
        if not isinstance(entity, self.return_class):
            self.logger.error("Entity was not passed as an instance to create."
                              " Value received: %s", entity)
            raise TypeError(
                "Entity must be a {entity} object!".format(
                    entity=self.return_class.__name__
                )
            )

        if self.get(entity.id_) is not None:
            self.logger.error("Entity was found in database before create."
                              " Value received: %s", entity)
            raise AssertionError(
                "{entity} uuid already exists in database!".format(
                    entity=self.return_class.__name__
                )
            )

        ent_values = entity.get_db_values()

        query = 'INSERT INTO {table} ({fields}) VALUES ({values});'.format(
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
        if not isinstance(entity, self.return_class):
            self.logger.error("Entity was not passed as an instance to update."
                              " Value received: %s", entity)
            raise TypeError(
                "Entity must be a {return_class} object!".format(
                    return_class=self.return_class
                )
            )

        if self.get(entity.id_) is None:
            self.logger.error("Entity was not found in database to update."
                              " Value received: %s", entity)
            raise AssertionError("Entity uuid doesn't exists in database!")

        entity.last_modified_datetime = datetime.now()

        ent_values = entity.get_db_values()

        query = "UPDATE {table} SET {fields} WHERE {column} = %s;".format(
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
            raise NoRowsAffectedException

        self.logger.info("Entity updated to %s", entity)
        return entity.id_

    def create_table_if_not_exists(self):
        fields_ = list()
        primary_keys = list()

        self.logger.info("Starting create table processing.")
        for field in dataclasses.fields(self.return_class):
            self.logger.debug("Processing field %s", field)
            if field.metadata.get("database") is False:
                self.logger.debug("Field '%s' not included in database table, "
                                  "skipping.", field.name)
                continue

            type_ = field.metadata.get('type') \
                    or GenericSQLDAO.predict_db_type(field.type)
            self.logger.debug("'%s' type defined as '%s'", field.name, type_)

            default = field.metadata.get('default') or "NULL"

            field_name = self.fields.get(field.name)
            self.logger.debug("'%s' name defined as '%s'",
                              field.name, field_name)

            if field.metadata.get("primary_key"):
                self.logger.debug("'%s' added as primary key", field_name)
                primary_keys.append('`{key}`'.format(key=field_name))
                if default == "NULL":
                    self.logger.warning("Had to change '%s' default because "
                                        "it is primary key and set to NULL.",
                                        field_name)
                    default = "NOT NULL"

            fields_.append(GenericSQLDAO.COLUMN.format(field=field_name,
                                                       type=type_,
                                                       default=default))
        fields_ = ', '.join(fields_)
        primary_keys = ', '.join(primary_keys)
        query = GenericSQLDAO.CREATE_QUERY.format(table=self.table,
                                                  fields=fields_,
                                                  primary_keys=primary_keys)
        self.logger.info("Creating table with query: %s", query)
        self.database.query(query)
        self.logger.info("Table created")

    @classmethod
    def predict_db_type(cls, cls_to_predict):
        if issubclass(cls_to_predict, Entity):
            return "CHAR(32)"
        return GenericSQLDAO.TYPE_MAPPING.get(cls_to_predict.__name__) \
               or "CHAR(100)"

    def close(self):
        self.logger.debug("Closing connection to database.")
        self.database.close()
