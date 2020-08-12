from dataclasses import dataclass, field

from nova_api.entity import Entity


@dataclass
class Phone(Entity):
   name: str = field(default='', metadata={"type": "VARCHAR(45)"})
   number: str = field(default='', metadata={"type": "VARCHAR(15)"})
   contact: Entity = field(default=None, metadata={"primary_key": True})
