from GenericSQLDAO import GenericSQLDAO
from User import User


class UserDAO(GenericSQLDAO):
    TABLE = 'usuarios'

    def __init__(self, db=None):
        super(UserDAO, self).__init__(db=db, table=UserDAO.TABLE,
                                      return_class=User, prefix='')
