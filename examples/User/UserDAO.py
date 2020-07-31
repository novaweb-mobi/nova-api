from User import User

from nova_api.GenericSQLDAO import GenericSQLDAO


class UserDAO(GenericSQLDAO):
    TABLE = 'usuarios'

    def __init__(self, db=None):
        super(UserDAO, self).__init__(db=db, table=UserDAO.TABLE,
                                      return_class=User, prefix='')
