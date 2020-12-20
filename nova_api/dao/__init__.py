"""Module for Data Access Objects implementation"""
from abc import ABC, abstractmethod
from re import sub
from typing import List, Optional, Type

from nova_api.entity import Entity


def camel_to_snake(name: str):
    """Converts a camel case name to snake case.

    :param name: String in camel case to be converted
    :return: String in snake case
    """
    assert isinstance(name, str)
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class GenericDAO(ABC):
    """ Interface class for the implementation of Data Access Objects.
    """
    @abstractmethod
    def __init__(self, table: str = None, fields: dict = None,
                 return_class: Type[Entity] = Entity,
                 prefix: str = None, **kwargs) -> None:
        pass

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
    def create_table_if_not_exists(self):
        raise NotImplementedError()

    @abstractmethod
    def close(self):
        raise NotImplementedError()
