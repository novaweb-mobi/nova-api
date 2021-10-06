"""Module for Data Access Objects implementation"""

import dataclasses
import logging
from abc import ABC, abstractmethod
# pylint: disable=W0622
from re import I, compile, sub
from typing import List, Optional, Type

from nova_api.entity import Entity
from nova_api.exceptions import DuplicateEntityException, \
    EntityNotFoundException, InvalidFiltersException, InvalidIDException, \
    InvalidIDTypeException, \
    NotEntityException


def camel_to_snake(name: str):
    """Converts a camel case name to snake case.

    :param name: String in camel case to be converted
    :return: String in snake case
    """
    assert isinstance(name, str)
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


uuidv4regex = compile(
    r'^[a-f0-9]{8}[a-f0-9]{4}4[a-f0-9]{3}[89ab][a-f0-9]{3}[a-f0-9]{12}'
    r'\Z', I)


def is_valid_uuidv4(id_: str) -> bool:
    """
    Checks that the id_ is indeed a UUIDv4 valid string without dashes.

    :param id_: The ID to validate.
    :return: True if id_ is an UUIDv4, False otherwise.
    """
    return uuidv4regex.match(id_)


class GenericDAO(ABC):
    """ Interface class for the implementation of Data Access Objects.
    """

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

    def _generate_field_database_name(self, arg: dataclasses.Field) -> str:
        """
        Generates the database field_name from the prefix, the field name \
        and a suffix, if necessary. The suffix is added if the field is \
        an entity and only the id_ should be saved.

        :param arg: The Field to generate the database name for.
        :return: The field database name.
        """
        return self.prefix \
               + arg.name \
               + ('' if not issubclass(arg.type, Entity) else "_id_")

    @abstractmethod
    def get(self, id_: str) -> Optional[Entity]:
        """
        Recovers and entity with `id_` from the database. The id_ must be the \
        nova_api generated id_ which is a 32-char uuid v4.

        :raises InvalidIDTypeException: If the UUID is not a string
        :raises InvalidIDException: If the UUID is not a valid UUID v4 \
        without '-'.

        :param id_: The UUID of the instance to recover
        :return: None if no instance is found or a `return_class` instance \
        if found
        """
        if not isinstance(id_, str):
            self.logger.error("ID was not passed as a str to get. "
                              "Value received: %s", str(id_))
            raise InvalidIDTypeException(debug=f"Received ID was {id_}")
        if not is_valid_uuidv4(id_):
            self.logger.error("ID is not a valid str in get. "
                              "Should be a valid uuid4."
                              "Value received: %s", str(id_))
            raise InvalidIDException(debug=f"Received ID was {id_}")

    @abstractmethod
    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        """
        Recovers all instances that match the given filters up to the length \
        specified starting from the offset given.

        The filters should be given as a dictionary, available keys are the \
        `return_class` attributes. The values may be only the desired value \
        or a list with the comparator in the first position and the value in \
        the second.

        Example:
            >>> dao.get_all(length=50, offset=0,
            ...             filters={"birthday":[">", "1/1/1998"],
            ...                      "name":"John"})
            (2, [ent1, ent2])

        :param length: The number of items to select
        :param offset: The number of items to skip before starting to select
        :param filters: A dict with the filters to use. The key must be a \
        valid attribute in the entity and the value may either be an specific \
        value or a list with two elements: an operator and a value,
        respectively.
        :return: A tuple with the totol number of entities in the database \
        and a list of the matched results.
        """
        raise NotImplementedError()

    @abstractmethod
    def remove(self, entity: Entity = None, filters: dict = None) -> int:
        """
        Removes entities from database. May be called either with an instance
        of return_class or a dict of filters. *If both are passed, the instance
        will be removed and the filters won't be considered.*Invalid filters \
        won't be considered.

        :raises NotEntityException: If `entity` is not a `return_class` \
        instance and filters are None.
        :raises EntityNotFoundException: If the entity is not found in the \
        database.
        :raises InvalidFiltersException: If filters is not None and is not \
        a dict.

        :raises NoRowsAffectedException: If no rows are affected by the \
        delete query.

        :param entity: `return_class` instance to delete.
        :param filters: Filters to apply to delete query in dict format as
        specified by `_generate_filters`
        :return: Number of affected rows.
        """
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
        Creates a new row in the database with data from `entity`.

        :raises NotEntityException: Raised if the entity argument
        is not of the return_class of this DAO
        :raises DuplicateEntityException: Raised if an entity with
        the same ID exists in the database already.

        :param entity: The instance to save in the database.
        :return: The entity uuid.
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
        """
        Updates an entity on the database.

        :raises NotEntityException: If `entity` is not a `return_class` \
        instance.
        :raises EntityNotFoundException: If the entity is not found in the \
        database.

        :param entity: The entity with updated values to update on \
        the database.
        :return: The id_ of the updated entity.
        """
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
        """
        Closes the connection to the database

        :return: None
        """
        raise NotImplementedError()
