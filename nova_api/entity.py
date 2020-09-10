import logging
from dataclasses import dataclass, field, fields
from datetime import date, datetime
from uuid import uuid4


def generate_id():
    return uuid4().hex


def get_time():
    datetime_no_microseconds = datetime.now().replace(microsecond=0)
    return datetime_no_microseconds


@dataclass
class Entity:
    id_: str = field(default_factory=generate_id,
                     metadata={"type": "CHAR(32)",
                               "primary_key": True,
                               "default": "NOT NULL"})
    creation_datetime: datetime = field(init=True,
                                        default_factory=get_time,
                                        compare=False,
                                        metadata={"type": "DATETIME"})
    last_modified_datetime: datetime = field(init=True,
                                             default_factory=get_time,
                                             compare=False,
                                             metadata={"type": "DATETIME"})

    def __post_init__(self):
        logger = logging.getLogger(__name__)
        for field_ in fields(self.__class__):
            try:
                if issubclass(field_.type, Entity) \
                        and \
                        not isinstance(self.__getattribute__(field_.name),
                                       field_.type):
                    # pylint: disable=W0511
                    # TODO call dao.get
                    logger.debug("Received %s field as %s. Converting.",
                                 type(self.__getattribute__(field_.name)),
                                 field_.type)
                    self.__setattr__(field_.name, field_.type(
                        self.__getattribute__(field_.name)
                    ))
                if issubclass(field_.type, datetime) \
                        and \
                        not isinstance(self.__getattribute__(field_.name),
                                       field_.type):
                    logger.debug("Received %s field as %s. Converting.",
                                 type(self.__getattribute__(field_.name)),
                                 field_.type)
                    self.__setattr__(
                        field_.name,
                        datetime.strptime(
                            self.__getattribute__(field_.name),
                            field_.metadata.get("datetime_format",
                                                "%Y-%m-%d "
                                                "%H:%M:%S")
                        ))
                if issubclass(field_.type, date) \
                        and \
                        not isinstance(self.__getattribute__(field_.name),
                                       field_.type):
                    logger.debug("Received %s field as %s. Converting.",
                                 type(self.__getattribute__(field_.name)),
                                 field_.type)
                    self.__setattr__(
                        field_.name,
                        datetime.strptime(
                            self.__getattribute__(field_.name),
                            field_.metadata.get("date_format",
                                                "%Y-%m-%d")
                        ).date())
            except TypeError:
                logger.warning("Unable to check field %s type",
                               field_.name, exc_info=True)
            finally:
                logger.debug("Processed field %s", field_.name)
        if self.__class__ == Entity:
            logger.error("Trying to instantiate Entity!")
            raise NotImplementedError("Abstract class can't be instantiated")

    def __iter__(self):
        for key in self.__dict__:
            if issubclass(self.__dict__[key].__class__, Entity):
                yield key + '_id_', Entity._serialize_field(self.__dict__[key])
            else:
                yield key, Entity._serialize_field(self.__dict__[key])

    @staticmethod
    def _serialize_field(field_):
        if issubclass(field_.__class__, Entity):
            return field_.id_
        if isinstance(field_, datetime):
            return field_.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(field_, date):
            return field_.strftime("%Y-%m-%d")
        return field_

    def get_db_values(self):
        return [Entity._serialize_field(self.__getattribute__(field_.name))
                for field_ in fields(self)
                if field_.metadata.get("database", True)]
