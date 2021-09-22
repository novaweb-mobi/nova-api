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

    def get(self, id_: str) -> Optional[Entity]:
        pass

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        pass

    def remove(self, entity: Entity) -> None:
        pass

    @staticmethod
    def custom_serializer(field_):
        if isinstance(field_, datetime) or isinstance(field_, date):
            return field_
        return Entity._serialize_field(field_)

    def create(self, entity: Entity) -> str:
        super().create(entity)

        ent_values = entity.get_db_values(MongoDAO.custom_serializer)
        db_doc = {key: value
                  for key, value in zip(self.fields.values(), ent_values)}
        self.database[self.collection].insert_one(db_doc)



    def update(self, entity: Entity) -> str:
        pass

    def close(self):
        pass
