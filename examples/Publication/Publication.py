from dataclasses import dataclass, field

from nova_api.entity import Entity

from User import User


def anom_user():
    return User(id_="00000000000000000000000000000000", first_name="Anom")


@dataclass
class Publication(Entity):
    text: str = field(default='', metadata={"type": "LONGTEXT"})
    publisher: User = field(default_factory=anom_user,
                            metadata={"primary_key": True})
