from dataclasses import fields
from datetime import datetime
from inspect import getfullargspec
from typing import List, Optional

from Entity import Entity
from MySQLHelper import MySQLHelper
from exceptions import NoRowsAffectedException


class GenericSQLDAO(object):
    ALLOWED_COMPARATORS = ['=', '<=>', '<>', '!=', '>', '>=', '<=', 'LIKE']
    TYPE_MAPPING = {
        "bool": "TINYINT(1)",
        "datetime": "DATETIME",
        "str": "VARCHAR(100)",
        "int": "INT",
        "float": "DECIMAL",
        "date": "DATE"
    }
    CREATE_QUERY = "CREATE TABLE IF NOT EXISTS {table} ({fields}, " \
                   "PRIMARY KEY({primary_keys})) ENGINE = InnoDB;"
    COLUMN = "`{field}` {type} {default}"
    SELECT_QUERY = "SELECT {fields} FROM {table} {filters} LIMIT %s OFFSET %s;"
    FILTERS = "WHERE {filters}"
    FILTER = "{column} {comparator} %s"

    def __init__(self, db=None, table: str = '', fields: dict = None,
                 return_class: type = Entity, prefix: str = None) -> None:
        self.db = db
        if db is None:
            self.db = MySQLHelper()
        self.TABLE = table
        if self.TABLE == '':
            raise ValueError("Table must have a name")
        self.PREFIX = prefix or return_class.__name__.lower() + "_"
        self.FIELDS = fields
        if not self.FIELDS:
            class_args = getfullargspec(return_class.__init__).args
            class_args.pop(class_args.index('self'))
            self.FIELDS = {arg: self.PREFIX + arg for arg in class_args}
        self.RETURN_CLASS = return_class

    def get(self, id_: str) -> Optional[Entity]:
        if type(id_) != str:
            raise TypeError("UUID must be a 32-char string!")
        if len(id_) != 32:
            raise ValueError("UUID must be a 32-char string!")

        query = GenericSQLDAO.SELECT_QUERY.format(
            fields=', '.join(self.FIELDS.values()),
            table=self.TABLE,
            filters=GenericSQLDAO.FILTERS.format(
                filters=GenericSQLDAO.FILTER.format(
                    column=self.FIELDS['id_'],
                    comparator="="
                )
            )
        )

        self.db.query(query, [id_, 1, 0])
        results = self.db.get_results()

        if results is None:
            return None

        result = results[0]
        result_dict = dict()

        for index, result_column in enumerate(self.FIELDS.keys()):
            result_dict[result_column] = result[index]

        return_object = self.RETURN_CLASS(**result_dict)

        return return_object

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        filters_for_query = list()
        query_params = list()
        filters_ = ''
        if filters:
            print("received filters")
            query_params = [item[1] if type(item) == list else item
                            for item in filters.values()]

            field_keys = self.FIELDS.keys()
            for property_, value in filters.items():
                if property_ not in field_keys:
                    raise ValueError(
                        "Property {prop} not available in {entity}.".format(
                            prop=property_,
                            entity=self.RETURN_CLASS.__name__
                        )
                    )
                if type(value) == list \
                        and value[0] not in self.ALLOWED_COMPARATORS:
                    raise ValueError(
                        "Comparator {comparator} not allowed for {entity}"
                            .format(comparator=value[0],
                                    entity=self.RETURN_CLASS.__name__
                                    )
                    )

            filters_for_query = [
                GenericSQLDAO.FILTER.format(
                    column=self.FIELDS[filter_],
                    comparator=(filters[filter_][0]
                                if type(filters[filter_]) == list
                                else '='))
                for filter_ in filters.keys()
            ]
            filters_ = GenericSQLDAO.FILTERS.format(
                filters=' AND '.join(filters_for_query))

        query = GenericSQLDAO.SELECT_QUERY.format(
            fields=', '.join(self.FIELDS.values()),
            table=self.TABLE,
            filters=filters_
        )

        query_total = "SELECT count({column}) FROM {table};".format(
            table=self.TABLE,
            column=self.FIELDS['id_'])

        self.db.query(query, [*query_params, length, offset])
        results = self.db.get_results()

        if results is None:
            return 0, []

        return_list = list()
        for result in results:
            result_dict = dict()

            for index, result_column in enumerate(self.FIELDS.keys()):
                result_dict[result_column] = result[index]

            return_object = self.RETURN_CLASS(**result_dict)
            return_list.append(return_object)

        self.db.query(query_total)
        total = self.db.get_results()[0][0]

        return total, return_list

    def remove(self, entity: Entity) -> None:
        if type(entity) != self.RETURN_CLASS:
            raise TypeError("Entity must be a {type} object!".format(
                type=self.RETURN_CLASS.__name__))

        if self.get(entity.id_) is None:
            raise AssertionError("monitor uuid doesn't exists in database!")

        query = 'DELETE FROM {table} WHERE {column} = %s;'.format(
            table=self.TABLE,
            column=self.FIELDS['id_'])

        row_count, last_row = self.db.query(query, [entity.id_])

        if row_count == 0:
            raise NoRowsAffectedException()

    def create(self, entity: Entity) -> str:
        if type(entity) != self.RETURN_CLASS:
            raise TypeError(
                "Entity must be a {entity} object!".format(
                    entity=self.RETURN_CLASS.__name__
                )
            )

        if self.get(entity.id_) is not None:
            raise AssertionError("Entity uuid already exists in database!")
        query = 'INSERT INTO {table} ({fields}) VALUES ({values});'.format(
            table=self.TABLE,
            fields=', '.join(self.FIELDS.values()),
            values=', '.join(['%s'] * len(
                self.FIELDS.values())))

        ent_values = dict(entity).copy()
        row_count, last_row = self.db.query(query,
                                            list(ent_values.values()))

        if row_count == 0:
            raise NoRowsAffectedException()

        return entity.id_

    def update(self, entity: Entity) -> str:
        if type(entity) != self.RETURN_CLASS:
            raise TypeError(
                "Entity must be a {return_class} object!".format(
                    return_class=self.RETURN_CLASS
                )
            )

        if self.get(entity.id_) is None:
            raise AssertionError("Entity uuid doesn't exists in database!")

        entity.last_modified_datetime = datetime.now()

        query = "UPDATE {table} SET {fields} WHERE {column} = %s;".format(
            table=self.TABLE,
            fields=', '.join(
                [field + '=%s' for field in
                 self.FIELDS.values()]),
            column=self.FIELDS['id_']
        )

        row_count, last_row = self.db.query(query,
                                            list(dict(entity).values())
                                            + [entity.id_])

        if row_count == 0:
            raise NoRowsAffectedException

        return entity.id_

    def create_table_if_not_exists(self):
        fields_ = list()
        primary_keys = list()

        for f in fields(self.RETURN_CLASS):
            type_ = f.metadata.get('type') \
                    or GenericSQLDAO.predict_db_type(f.type)
            default = f.metadata.get('default') or "NULL"
            field_name = self.FIELDS[f.name]

            if f.metadata.get("primary_key") is True:
                primary_keys.append('`{key}`'.format(key=field_name))

            fields_.append(GenericSQLDAO.COLUMN.format(field=field_name,
                                                       type=type_,
                                                       default=default))
        fields_ = ', '.join(fields_)
        primary_keys = ', '.join(primary_keys)
        query = GenericSQLDAO.CREATE_QUERY.format(table=self.TABLE,
                                                  fields=fields_,
                                                  primary_keys=primary_keys)
        self.db.query(query)

    @classmethod
    def predict_db_type(cls, cls_to_predict):
        return GenericSQLDAO.TYPE_MAPPING.get(cls_to_predict.__name__) \
               or "CHAR(100)"

    def close(self):
        self.db.close()
