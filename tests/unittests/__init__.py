from dataclasses import dataclass, field
from datetime import date

from nova_api.entity import Entity

TEST_DATE = "2020-01-01 00:00:00"


@dataclass
class TestEntity(Entity):
    name: str = "Anom"
    birthday: date = date(1, 1, 1)


@dataclass
class TestEntity2(Entity):
    name: str = field(default=None, metadata={"default": "NULL",
                                              "primary_key": True})
    birthday: date = date(1, 1, 1)


@dataclass
class TestEntityWithChild(Entity):
    name: str = "Anom"
    birthday: date = date(1, 1, 1)
    child: TestEntity = field(default_factory=TestEntity)
    not_to_database: str = field(default='', metadata={"database": False})
