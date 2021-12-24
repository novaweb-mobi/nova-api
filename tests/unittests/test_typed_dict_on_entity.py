from dataclasses import dataclass, field
from typing import TypedDict

from nova_api import Entity


class ATypedDict(TypedDict):
    test: str
    another: str


@dataclass
class MyTestEntity(Entity):
    fieldTyped: ATypedDict = field(default_factory=dict)


class TestTypedDict:
    @staticmethod
    def test_may_instantiate():
        MyTestEntity(fieldTyped={"test": "abc"})

    @staticmethod
    def test_may_iter():
        for a in MyTestEntity(fieldTyped={"another": "string"}):
            assert a

    @staticmethod
    def test_may_get_db_values():
        a = MyTestEntity(fieldTyped={"another": "string"})
        assert a.get_db_values() == [Entity.serialize_field(field_[1])
                for field_ in a]

