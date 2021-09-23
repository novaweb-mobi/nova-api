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
                 host: str = environ.get('DB_URL', ''),
                 user: str = environ.get('DB_USER', ''),
                 password: str = environ.get('DB_PASSWORD', ''),
                 database_instance=None, **kwargs) -> None:
        super().__init__(fields, return_class, prefix)
        self.fields["id_"] = "_id"

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
        pass

    def get_all(self, length: int = 20, offset: int = 0,
                filters=None) -> (int, List[Entity]):
        if filters is None:
            filters = {}
        self.logger.debug("Getting all with filters %s limit %s and offset %s",
                          filters, length, offset)

        result_cur = self.cursor.find(filters, limit=length, skip=offset)

        results = []
        for result in result_cur:
            for prop, field in self.fields.items():
                result[prop] = result.pop(field)
            results.append(self.return_class(**result))

        if not results:
            self.logger.info("No results found in get_all. Returning none")
            return 0, []

        amount = self.cursor.count_documents({})

        return amount, results

    def remove(self, entity: Entity) -> None:
        pass

    def create(self, entity: Entity) -> str:
        super().create(entity)

        db_values = self.prepare_db_dict(entity)
        print(db_values)
        self.cursor.insert_one(db_values)

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
        pass
