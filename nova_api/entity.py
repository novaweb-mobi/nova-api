"""Base entity for modeling of API's"""
import logging
from abc import ABC
from dataclasses import dataclass, field, fields
from datetime import date, datetime
from enum import Enum
from uuid import uuid4


def generate_id() -> str:
    """Generates an uuid v4.

    :return: Hexadecimal string representation of the uuid.
    """
    return uuid4().hex


def get_time() -> datetime:
    """Get current time without microseconds

    :return: Current datetime with no microseconds.
    """
    datetime_no_microseconds = datetime.now().replace(microsecond=0)
    return datetime_no_microseconds


@dataclass
class Entity(ABC):
    """Base Entity implementation

    This class is the base implementation of the entity for modeling
    API resources. The fields included in this class will be inherited for
    all subclasses.

    Examples:
         ::

            @dataclass
            class Person(Entity):
                name: str = None
                age: int = None
                birthday: date = None
    """
    id_: str = field(default_factory=generate_id,
                     metadata={"type": "CHAR(32)",
                               "primary_key": True,
                               "default": "NOT NULL"})
    creation_datetime: datetime = field(init=True,
                                        default_factory=get_time,
                                        compare=False,
                                        metadata={"type": "TIMESTAMP"})
    last_modified_datetime: datetime = field(init=True,
                                             default_factory=get_time,
                                             compare=False,
                                             metadata={"type": "TIMESTAMP"})

    def __post_init__(self):
        """Post processing of fields

        Post init goes through the parameters passed to init and makes some
        validations. Fields that are subclasses of Entity will be instantiated
        (but only with id_ set). Datetime formats also will be cast if
        received as strings. Strings will have trailing and leading white
        spaces removed.

        __post_init__ may be overridden to include validations required by
        any use case. In such case, it's important to include a super call
        to maintain the aforementioned functionalities.

        :return: None
        """
        logger = logging.getLogger(__name__)
        received_log = "Received %s field as %s. Converting."
        for field_ in fields(self):
            try:
                field_value = self.__getattribute__(field_.name)
                if issubclass(field_.type, Entity) \
                        and \
                        not isinstance(field_value, field_.type):
                    # pylint: disable=W0511
                    # TODO call dao.get
                    logger.debug(received_log,
                                 type(field_value),
                                 field_.type)
                    self.__setattr__(field_.name, field_.type(field_value))
                elif issubclass(field_.type, datetime) \
                        and \
                        not isinstance(field_value, field_.type):
                    logger.debug(received_log,
                                 type(field_value), field_.type)
                    self.__setattr__(
                        field_.name,
                        datetime.strptime(
                            field_value,
                            field_.metadata.get("datetime_format",
                                                "%Y-%m-%d %H:%M:%S")
                        ))
                elif issubclass(field_.type, date) \
                        and \
                        not isinstance(field_value,
                                       field_.type):
                    logger.debug(received_log,
                                 type(field_value),
                                 field_.type)
                    self.__setattr__(
                        field_.name,
                        datetime.strptime(
                            field_value,
                            field_.metadata.get("date_format",
                                                "%Y-%m-%d")
                        ).date())
                elif issubclass(field_.type, str) \
                        and field_value is not None:
                    logger.debug("Stripping string field")
                    self.__setattr__(
                        field_.name,
                        str(field_value).strip())
                elif issubclass(field_.type, Enum) \
                        and \
                        not isinstance(field_value, field_.type):
                    logger.debug(received_log,
                                 type(field_value),
                                 field_.type)
                    self.__setattr__(field_.name,
                                     field_.type(field_value))
            except TypeError:
                logger.debug("Unable to check field %s type",
                             field_.name, exc_info=True)
            finally:
                logger.debug("Processed field %s", field_.name)
        if self.__class__ == Entity:
            logger.error("Trying to instantiate Entity!")
            raise NotImplementedError("Abstract class can't be instantiated")

    def __iter__(self):
        """

        :return:
        """
        for key in self.__dict__:
            if issubclass(self.__dict__[key].__class__, Entity):
                yield key + '_id_', Entity._serialize_field(self.__dict__[key])
            else:
                yield key, Entity._serialize_field(self.__dict__[key])

    @staticmethod
    def _serialize_field(field_value):
        """

        :param field_value: Value of the field to be serialized
        :return: Serialized value
        """
        if issubclass(field_value.__class__, Entity):
            return field_value.id_
        if isinstance(field_value, datetime):
            return field_value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(field_value, date):
            return field_value.strftime("%Y-%m-%d")
        if isinstance(field_value, Enum):
            return field_value.value
        return field_value

    def get_db_values(self) -> list:
        """Returns all attributes to save in database with formatted values.

        Goes through the fields in the entity and converts them to the
        expected value to save in the database. For example: datetime
        values are converted to string with the specific sql format.

        Also verifies if a field contains in metadata `database=False` and
        excludes it from the list if so. Default for `database` is True.

        :return: Serialized values to save in database
        """
        return [Entity._serialize_field(self.__getattribute__(field_.name))
                for field_ in fields(self)
                if field_.metadata.get("database", True)]
