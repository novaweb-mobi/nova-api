from os import environ
from typing import List, Optional, Type
from urllib.parse import quote_plus

from pymongo import MongoClient

from dao import camel_to_snake
from entity import Entity
from nova_api.exceptions import NotEntityException
from nova_api import GenericDAO


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

    def create(self, entity: Entity) -> str:
        super().create(entity)

    def update(self, entity: Entity) -> str:
        pass

    def close(self):
        pass
