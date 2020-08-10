from dataclasses import dataclass, field
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
                                        metadata={"type": "DATETIME"})
    last_modified_datetime: datetime = field(init=True,
                                             default_factory=get_time,
                                             compare=False,
                                             metadata={"type": "DATETIME"})

    def __post_init__(self):
        if self.__class__ == Entity:
            raise NotImplementedError("Abstract class can't be instantiated")

    def __iter__(self):
        for key in self.__dict__:
            if issubclass(self.__dict__[key].__class__, Entity):
                yield key + '_id_', self.__dict__[key].id_
            elif isinstance(self.__dict__[key], datetime):
                yield key, self.__dict__[key].strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(self.__dict__[key], date):
                yield key, self.__dict__[key].strftime("%Y-%m-%d")
            else:
                yield key, self.__dict__[key]
