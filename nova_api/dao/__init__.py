import dataclasses
import logging
from abc import ABC, abstractmethod
from re import sub
from typing import List, Optional, Type

from nova_api.entity import Entity


def camel_to_snake(name):
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class GenericDAO(ABC):
    @abstractmethod
    def __init__(self,
                 fields: dict = None,
                 return_class: Type[Entity] = Entity,
                 prefix: str = None) -> None:
        self.logger = logging.getLogger("nova_api_logger")
        self.return_class = return_class

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

    @abstractmethod
    def get(self, id_: str) -> Optional[Entity]:
        raise NotImplementedError()

    @abstractmethod
    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        raise NotImplementedError()

    @abstractmethod
    def remove(self, entity: Entity) -> None:
        raise NotImplementedError()

    @abstractmethod
    def create(self, entity: Entity) -> str:
        raise NotImplementedError()

    @abstractmethod
    def update(self, entity: Entity) -> str:
        raise NotImplementedError()

    @abstractmethod
    def close(self):
        raise NotImplementedError()
