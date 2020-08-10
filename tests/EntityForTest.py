from dataclasses import dataclass

from nova_api.entity import Entity


@dataclass
class EntityForTest(Entity):
    test_field: int = 0