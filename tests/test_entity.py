from dataclasses import dataclass
from datetime import datetime

from pytest import fixture, raises

import nova_api
from nova_api.Entity import Entity


@dataclass
class EntityForTest(Entity):
    test_field: int = 0


class TestEntity:

    @fixture
    def entity(self):
        return EntityForTest()

    def test_auto_generate_id(self, entity):
        assert len(entity.id_) == 32

    def test_datetime_generation(self, entity):
        assert type(entity.creation_datetime) == datetime\
                and type(entity.last_modified_datetime) == datetime

    def test_not_implemented(self):
        with raises(NotImplementedError):
            Entity()
