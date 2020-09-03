from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List

from pytest import fixture, raises

from nova_api.entity import Entity
# pylint: disable=R0201
@dataclass
class SampleEntity(Entity):
    pass


@dataclass
class EntityForTest(Entity):
    test_field: int = 0
    my_date: date = field(default=date(2020, 1, 1))
    child: SampleEntity = None

@dataclass
class EntityForTestWithTypeError(Entity):
    childs: List[SampleEntity] = None


class TestEntity:

    @fixture
    def entity(self):
        return EntityForTest("12345678901234567890123456789012",
                             datetime(2020, 1, 1, 0, 0, 0),
                             datetime(2020, 1, 1, 0, 0, 0),
                             0, child=SampleEntity(
                                 "12345678901234567890123456789012"))

    def test_auto_generate_id(self, entity):
        assert len(entity.id_) == 32

    def test_datetime_generation(self, entity):
        assert isinstance(entity.creation_datetime, datetime) \
                and isinstance(entity.last_modified_datetime, datetime)

    def test_to_dict(self, entity):
        entity_dict = dict(entity)
        assert entity_dict == {"id_": "12345678901234567890123456789012",
                               "creation_datetime": "2020-01-01 00:00:00",
                               "last_modified_datetime": "2020-01-01 00:00:00",
                               "test_field": 0,
                               "my_date": "2020-01-01",
                               "child_id_": "12345678901234567890123456789012"}

    def test_not_implemented(self):
        with raises(NotImplementedError):
            Entity()

    def test_field_type_error(self):
        ent = EntityForTestWithTypeError()
        assert isinstance(ent, EntityForTestWithTypeError)
