from dataclasses import dataclass, field
from typing import List

from nova_api.entity import Entity


class Phone:
    pass


@dataclass
class Contact(Entity):
    first_name: str = field(default=None, metadata={"type": "VARCHAR(45)"})
    last_name: str = ''
    phone_numbers: List[Phone] = field(default_factory=list,
                                       metadata={"database": False})


@dataclass
class Phone(Entity):
    name: str = field(default='', metadata={"type": "VARCHAR(45)"})
    number: str = field(default='', metadata={"type": "VARCHAR(15)"})
    contact: Contact = field(default=None, metadata={"primary_key": True})
