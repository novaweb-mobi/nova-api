import dataclasses
from datetime import datetime
from inspect import getfullargspec
from re import sub
from typing import List, Optional

from nova_api.entity import Entity
from nova_api.mysql_helper import MySQLHelper
from nova_api.exceptions import NoRowsAffectedException


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
        self.database = database
        if database is None:
            self.database = MySQLHelper()

        self.return_class = return_class

        self.table = table or camel_to_snake(return_class.__name__) + 's'

        self.prefix = prefix or camel_to_snake(return_class.__name__) + "_"

        self.fields = fields
        if not self.fields:
            class_args = getfullargspec(return_class.__init__).args
            class_args.pop(class_args.index('self'))
            self.fields = {arg: self.prefix + arg for arg in class_args}

    def get(self, id_: str) -> Optional[Entity]:
        if not isinstance(id_, str):
            raise TypeError("UUID must be a 32-char string!")
        if len(id_) != 32:
            raise ValueError("UUID must be a 32-char string!")

        _, results = self.get_all(1, 0, {"id_": id_})

        if len(results) == 0:
            return None

        return results[0]

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        query_params = list()
        filters_ = ''
        if filters:
            query_params = [item[1] if isinstance(item, list) else item
                            for item in filters.values()]

            field_keys = self.fields.keys()
            for property_, value in filters.items():
                if property_ not in field_keys:
                    raise ValueError(
                        "Property {prop} not available in {entity}.".format(
                            prop=property_,
                            entity=self.return_class.__name__
                        )
                    )
                if isinstance(value, list) \
                        and value[0] not in self.ALLOWED_COMPARATORS:
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

        self.database.query(query, [*query_params, length, offset])
        results = self.database.get_results()

        if results is None:
            return 0, []

        return_list = [self.return_class(*result) for result in results]

        query_total = "SELECT count({column}) FROM {table};".format(
            table=self.table,
            column=self.fields['id_'])

        self.database.query(query_total)
        total = self.database.get_results()[0][0]

        return total, return_list

    def remove(self, entity: Entity) -> None:
        if not isinstance(entity, self.return_class):
            raise TypeError("Entity must be a {type} object!".format(
                type=self.return_class.__name__))

        if self.get(entity.id_) is None:
            raise AssertionError(
                "{entity} uuid doesn't exists in database!".format(
                    entity=self.return_class.__name__
                )
            )

        query = 'DELETE FROM {table} WHERE {column} = %s;'.format(
            table=self.table,
            column=self.fields['id_'])

        row_count, _ = self.database.query(query, [entity.id_])

        if row_count == 0:
            raise NoRowsAffectedException()

    def create(self, entity: Entity) -> str:
        if not isinstance(entity, self.return_class):
            raise TypeError(
                "Entity must be a {entity} object!".format(
                    entity=self.return_class.__name__
                )
            )

        if self.get(entity.id_) is not None:
            raise AssertionError(
                "{entity} uuid already exists in database!".format(
                    entity=self.return_class.__name__
                )
            )

        query = 'INSERT INTO {table} ({fields}) VALUES ({values});'.format(
            table=self.table,
            fields=', '.join(self.fields.values()),
            values=', '.join(['%s'] * len(
                self.fields.values())))

        ent_values = dict(entity).copy()
        row_count, _ = self.database.query(query,
                                           list(ent_values.values()))

        if row_count == 0:
            raise NoRowsAffectedException()

        return entity.id_

    def update(self, entity: Entity) -> str:
        if not isinstance(entity, self.return_class):
            raise TypeError(
                "Entity must be a {return_class} object!".format(
                    return_class=self.return_class
                )
            )

        if self.get(entity.id_) is None:
            raise AssertionError("Entity uuid doesn't exists in database!")

        entity.last_modified_datetime = datetime.now()
        print(entity.last_modified_datetime)

        query = "UPDATE {table} SET {fields} WHERE {column} = %s;".format(
            table=self.table,
            fields=', '.join(
                [field + '=%s' for field in
                 self.fields.values()]),
            column=self.fields['id_']
        )

        row_count, _ = self.database.query(query,
                                           list(dict(entity).values())
                                           + [entity.id_])

        if row_count == 0:
            raise NoRowsAffectedException

        return entity.id_

    def create_table_if_not_exists(self):
        fields_ = list()
        primary_keys = list()

        for fields in dataclasses.fields(self.return_class):
            type_ = fields.metadata.get('type') \
                    or GenericSQLDAO.predict_db_type(fields.type)
            default = fields.metadata.get('default') or "NULL"
            field_name = self.fields[fields.name]

            if fields.metadata.get("primary_key") is True:
                primary_keys.append('`{key}`'.format(key=field_name))

            fields_.append(GenericSQLDAO.COLUMN.format(field=field_name,
                                                       type=type_,
                                                       default=default))
        fields_ = ', '.join(fields_)
        primary_keys = ', '.join(primary_keys)
        query = GenericSQLDAO.CREATE_QUERY.format(table=self.table,
                                                  fields=fields_,
                                                  primary_keys=primary_keys)
        self.database.query(query)

    @classmethod
    def predict_db_type(cls, cls_to_predict):
        return GenericSQLDAO.TYPE_MAPPING.get(cls_to_predict.__name__) \
               or "CHAR(100)"

    def close(self):
        self.database.close()
