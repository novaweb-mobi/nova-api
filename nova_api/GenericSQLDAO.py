from datetime import datetime
from inspect import getfullargspec
from typing import List, Optional

from Entity import Entity
from MySQLHelper import MySQLHelper
from exceptions import NoRowsAffectedException

SELECT_QUERY = "SELECT {fields} FROM {table} {filters} LIMIT %s OFFSET %s;"
FILTERS = "WHERE {filters}"
FILTER = "{column} {comparator} %s"


class GenericSQLDAO(object):
    ALLOWED_COMPARATORS = ['=', '<=>', '<>', '!=', '>', '>=', '<=', 'LIKE']

    def __init__(self, db=None, table: str = '', fields: dict = None,
                 return_class: type = Entity, prefix: str = None) -> None:
        self.db = db
        if db is None:
            self.db = MySQLHelper()
        self.TABLE = table
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

        query = SELECT_QUERY.format(
            fields=', '.join(self.FIELDS.values()),
            table=self.TABLE,
            filters=FILTERS.format(
                filters=FILTER.format(
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
        field_keys = self.FIELDS.keys()
        for property_ in filters.keys():
            if property_ not in field_keys:
                raise ValueError(
                    "Property {prop} not available in {entity}.".format(
                        prop=property_,
                        entity=self.RETURN_CLASS.__name__
                    )
                )
            if type(filters[property_]) == list \
                    and filters[property_][0] not in self.ALLOWED_COMPARATORS:
                raise ValueError(
                    "Comparator {comparator} not allowed for {entity}".format(
                        comparator=filters[property_][0],
                        entity=self.RETURN_CLASS.__name__
                    )
                )

        query = SELECT_QUERY.format(
            fields=', '.join(self.FIELDS.values()),
            table=self.TABLE,
            filters=FILTERS.format(
                filters=' AND '.join(
                    [FILTER.format(
                        column=self.FIELDS[filter_],
                        comparator=(filters[filter_][0]
                                    if type(filters[filter_]) == list
                                    else '='),
                    ) for filter_ in filters.keys()]
                )
            )
        )

        query_total = "SELECT count({column}) FROM {table};".format(
            table=self.TABLE,
            column=self.FIELDS['id_'])

        query_params = [item[1] if type(item) == list else item
                        for item in filters.values()]

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

        ent_values = entity.__dict__.copy()
        for key in ent_values.keys():
            value = ent_values[key]
            if type(value) == datetime:
                ent_values[key] = value.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
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
                                            list(entity.__dict__.values())
                                            + [entity.id_])

        if row_count == 0:
            raise NoRowsAffectedException

        return entity.id_

    def close(self):
        self.db.close()
