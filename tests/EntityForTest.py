from dataclasses import dataclass, field

from nova_api.entity import Entity


@dataclass
class EntityForTest(Entity):
    test_field: int = 0
    not_to_add_field: str = field(default="", metadata={"database": False})
