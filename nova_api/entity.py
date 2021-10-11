"""Base entity for modeling of API's entities"""
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
        (but only with `id_` set). Datetime formats also will be cast if
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
                if issubclass(field_.type, (Entity, Enum)) \
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
                elif field_.type == date \
                        and \
                        isinstance(field_value, datetime):
                    logger.debug(received_log,
                                 type(field_value),
                                 field_.type)
                    self.__setattr__(
                        field_.name,
                        field_value.date())
                elif issubclass(field_.type, str) \
                        and field_value is not None:
                    logger.debug("Stripping string field")
                    self.__setattr__(
                        field_.name,
                        str(field_value).strip())
            except TypeError:
                logger.debug("Unable to check field %s type",
                             field_.name, exc_info=True)
            finally:
                logger.debug("Processed field %s", field_.name)
        if self.__class__ == Entity:
            logger.error("Trying to instantiate Entity!")
            raise NotImplementedError("Abstract class can't be instantiated")

    def __iter__(self):
        """Iteration through the Entity receiving the tuple
        (field_name, field_value_serialized)

        Iterates through the fields in the entity and yields a tuple with the
        field_name and the serialized field_value. For fields that are
        instances of Entities, the key will have `_id_` appended and the value
        will be the `id_`, as stated in `_serialize_field`.

        :return key, value: The tuple with the field_name and field_value
        """
        for key, value in self.__dict__.items():
            if isinstance(value, Entity):
                yield key + '_id_', Entity.serialize_field(value)
            else:
                yield key, Entity.serialize_field(value)

    @staticmethod
    def serialize_field(field_value):
        """Returns the value of a field formatted to be saved in the database.

        For fields that are subclasses of Entity, returns only the id_ to save
        in the database. For datetime and date fields, values are transformed
        into strings with strftime function from datetime.

        :param field_value: Value of the field in the entity being serialized.
        :return: The serialized value of the field for database insertion.
        """
        serialized_value = field_value
        if issubclass(field_value.__class__, Entity):
            serialized_value = field_value.id_
        elif isinstance(field_value, datetime):
            serialized_value = field_value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(field_value, date):
            serialized_value = field_value.strftime("%Y-%m-%d")
        elif isinstance(field_value, Enum):
            serialized_value = field_value.value
        return serialized_value

    def get_db_values(self, field_serializer=None) -> list:
        """Returns all attributes to save in database with formatted values.

        Goes through the fields in the entity and converts them to the
        expected value to save in the database. For example: datetime
        values are converted to string with the specific sql format.

        Also verifies if a field contains in metadata `database=False` and
        excludes it from the list if so. Default for `database` is True.

        :param field_serializer: Custom function to define serialization of
        fields
        :return: Serialized values to save in database
        """
        field_serializer = field_serializer or Entity.serialize_field
        return [field_serializer(self.__getattribute__(field_.name))
                for field_ in fields(self)
                if field_.metadata.get("database", True)]
