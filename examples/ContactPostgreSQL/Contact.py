from dataclasses import dataclass, field

from nova_api.entity import Entity

@dataclass
class Contact(Entity):
    first_name: str = field(default=None, metadata={"type":"VARCHAR(45)"})
    last_name: str = ''
    telephone_number: str = field(default=None, metadata={"type":"VARCHAR(15)"})
    email: str = field(default=None, metadata={"type":"VARCHAR(255)"})
