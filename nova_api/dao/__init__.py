import dataclasses
import logging
from abc import ABC, abstractmethod
from re import I, compile, sub
from typing import List, Optional, Type

from nova_api.entity import Entity
from nova_api.exceptions import DuplicateEntityException, \
    EntityNotFoundException, InvalidFiltersException, InvalidIDException, \
    InvalidIDTypeException, \
    NotEntityException


def camel_to_snake(name):
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


uuidv4regex = compile(
    r'^[a-f0-9]{8}[a-f0-9]{4}4[a-f0-9]{3}[89ab][a-f0-9]{3}[a-f0-9]{12}'
    r'\Z', I)


def is_valid_uuidv4(id_):
    return uuidv4regex.match(id_)


class GenericDAO(ABC):
    @abstractmethod
    def __init__(self,
                 fields: dict = None,
                 return_class: Type[Entity] = Entity,
                 prefix: str = None) -> None:
        self.logger = logging.getLogger("nova_api")
        self.return_class = return_class

        if prefix == '':
            self.prefix = ''
        else:
            self.prefix = prefix or camel_to_snake(return_class.__name__) + "_"

        self.fields = fields
        if not self.fields:
            class_args = dataclasses.fields(return_class)
            self.logger.debug("Field passed to %s are %s.",
                              self.__class__.__name__,
                              str(class_args))

            self.fields = {arg.name: self._generate_field_database_name(arg)
                           for arg in class_args
                           if arg.metadata.get("database", True)}

            self.logger.debug("Processed fields for %s are %s.",
                              self.__class__.__name__,
                              str(self.fields))

    def _generate_field_database_name(self, arg: dataclasses.Field):
        return self.prefix \
               + arg.name \
               + ('' if not issubclass(arg.type, Entity) else "_id_")

    @abstractmethod
    def get(self, id_: str) -> Optional[Entity]:
        if not isinstance(id_, str):
            self.logger.error("ID was not passed as a str to get. "
                              "Value received: %s", str(id_))
            raise InvalidIDTypeException(debug=f"Received ID was {id_}")
        if not is_valid_uuidv4(id_):
            self.logger.error("ID is not a valid str in get. "
                              "Should be a valid uuid4."
                              "Value received: %s", str(id_))
            raise InvalidIDException(debug=f"Received ID was {id_}")
        return None

    @abstractmethod
    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        raise NotImplementedError()

    @abstractmethod
    def remove(self, entity: Entity = None, filters: dict = None) -> int:
        if not isinstance(entity, self.return_class) and filters is None:
            self.logger.info(
                "Entity was not passed as an instance to remove"
                " and no filters where specified! "
                "Value received: %s", str(entity))
            raise NotEntityException(
                debug=f"Entity must be a {self.return_class.__name__} object "
                      f"or filters must be specified!"
            )

        if filters is not None and not isinstance(filters, dict):
            self.logger.error(
                "Filters were not passed as an dict to remove!"
                " Value received: %s", str(filters))
            raise InvalidFiltersException(
                debug=f"Filters were {str(filters)}")

        if entity is not None and self.get(entity.id_) is None:
            self.logger.error("Entity was not found in database to remove."
                              " Value received: %s", str(entity))
            raise EntityNotFoundException(debug=f"Entity id_ is {entity.id_}")

        return 0

    @abstractmethod
    def create(self, entity: Entity) -> str:
        """
            Creates a new entry in the databse with data from `entity`.

            :param entity: The instance to save in the database.
            :return: The entity uuid.
            :raise NotEntityException: Raised if the entity argument
            is not of the return_class of this DAO
            :raise DuplicateEntityException: Raised if an entity with
            the same ID exists in the database already.
        """
        if not isinstance(entity, self.return_class):
            self.logger.error("Entity was not passed as an instance to create."
                              " Value received: %s", str(entity))
            raise NotEntityException(
                debug=f"Entity must be a {self.return_class.__name__} object! "
                      f"Entity was a {entity.__class__.__name__} object."
            )

        if self.get(entity.id_) is not None:
            self.logger.error("Entity was found in database before create."
                              " Value received: %s", str(entity))
            raise DuplicateEntityException(
                debug=f"{self.return_class.__name__} uuid {entity.id_} "
                      f"already exists in database!"
            )

        return entity.id_

    @abstractmethod
    def update(self, entity: Entity) -> str:
        if not isinstance(entity, self.return_class):
            self.logger.error("Entity was not passed as an instance to update."
                              " Value received: %s", str(entity))
            raise NotEntityException(
                debug=f"Entity must be a {self.return_class.__name__} object! "
                      f"Entity was a {entity.__class__.__name__} object."
            )

        if self.get(entity.id_) is None:
            self.logger.error("Entity was not found in database to update."
                              " Value received: %s", str(entity))
            raise EntityNotFoundException(debug=f"Entity id_ is {entity.id_}")

        return ""

    @abstractmethod
    def close(self):
        raise NotImplementedError()
