from dataclasses import dataclass

from Entity import Entity
from GenericSQLDAO import GenericSQLDAO


@dataclass
class User(Entity):
    first_name: str = None
    last_name: str = None
    email: str = None


class UserDAO(GenericSQLDAO):
    TABLE = 'usuarios'

    def __init__(self, db=None):
        super(UserDAO, self).__init__(db=db, table=UserDAO.TABLE,
                                      return_class=User, prefix='')
