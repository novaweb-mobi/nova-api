from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


def generate_id():
    return uuid4().hex


@dataclass
class Entity(object):
    id_: str = field(default_factory=generate_id)
    creation_datetime: datetime = field(init=True,
                                        default_factory=datetime.now)
    last_modified_datetime: datetime = field(init=True,
                                             default_factory=datetime.now)

    def __post_init__(self):
        if self.__class__ == Entity:
            raise NotImplementedError("Abstract class can't be instantiated")

    def __iter__(self):
        for key in self.__dict__:
            if issubclass(type(self.__dict__[key]), Entity):
                yield key + '_id_', self.__dict__[key].id_
            elif type(self.__dict__[key]) == datetime:
                yield key, self.__dict__[key].strftime("%Y-%m-%d %H:%M:%S")
            else:
                yield key, self.__dict__[key]
