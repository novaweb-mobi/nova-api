from datetime import datetime
from typing import List, Optional, Dict

from MySQLHelper import MySQLHelper
from Entity import Entity


class GenericMySQLDAO(object):
    def __init__(self, db=None, table: str = '', fields: dict = None,
                 return_class: type = Entity) -> None:
        self.db = db
        if db is None:
            self.db = MySQLHelper()
        self.TABLE = table
        self.FIELDS = fields
        self.RETURN_CLASS = return_class

    def get(self, id_: str, fields: List[str] = None,
            filters: Dict[str, str] = None) -> Optional[Entity]:
        if type(id_) != str:
            raise TypeError("UUID must be a 32-char string!")
        if len(id_) != 32:
            raise ValueError("UUID must be a 32-char string!")

        if not fields:
            fields_ = '*'
        else:
            fields_ = ', '.join(self.FIELDS[field] for field in fields)

        query = "SELECT {fields} FROM {table} WHERE {column} = %s;".format(
            fields=fields_,
            table=self.TABLE,
            column=self.FIELDS['id_'], )
        try:
            self.db.query(query, [id_])
            results = self.db.get_results()
        except Exception as e:
            raise e

        if results is None:
            return None

        result = results[0]
        result_dict = dict()

        for index, result_column in enumerate(self.FIELDS.keys()):
            result_dict[result_column] = result[index]

        return_object = self.RETURN_CLASS(**result_dict)

        return return_object

    def get_all(self, length: int = 20, offset: int = 0) \
            -> (int, List[Entity]):
        query = "SELECT * FROM {table} LIMIT %s OFFSET %s;".format(
            table=self.TABLE)
        query_total = "SELECT count({column}) FROM {table};".format(
            table=self.TABLE,
            column=self.FIELDS['id_'])
        try:
            self.db.query(query, [length, offset])
            results = self.db.get_results()
        except Exception as e:
            raise e

        if results is None:
            return 0, []

        return_list = list()
        for result in results:
            result_dict = dict()

            for index, result_column in enumerate(self.FIELDS.keys()):
                result_dict[result_column] = result[index]

            return_object = self.RETURN_CLASS(**result_dict)
            return_list.append(return_object)

        try:
            self.db.query(query_total)
            total = self.db.get_results()[0][0]
        except Exception as e:
            raise e

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
        try:
            row_count, last_row = self.db.query(query, [entity.id_])
        except Exception as e:
            raise e

        if row_count == 0:
            raise IOError("No rows affected!")

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
        try:
            ent_values = entity.__dict__.copy()
            for key in ent_values.keys():
                value = ent_values[key]
                if type(value) == datetime:
                    ent_values[key] = value.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            row_count, last_row = self.db.query(query,
                                                list(ent_values.values()))
        except Exception as e:
            raise e

        if row_count == 0:
            raise IOError("No rows affected!")

        return entity.id_

    def update(self, entity: Entity) -> str:
        if type(entity) != self.RETURN_CLASS:
            raise TypeError("monitor must be a Monitor object!")

        if self.get(entity.id_) is None:
            raise AssertionError("monitor uuid doesn't exists in database!")

        query = "UPDATE {table} SET {fields} WHERE {column} = %s;".format(
            table=self.TABLE,
            fields=', '.join(
                [field + '=%s' for field in
                 self.FIELDS.values()]),
            column=self.FIELDS['id_']
        )
        try:
            row_count, last_row = self.db.query(query,
                                                list(entity.__dict__.values())
                                                + [entity.id_])
        except Exception as e:
            raise e

        if row_count == 0:
            raise IOError("No rows affected!")

        return entity.id_

    def close(self):
        self.db.close()
