from User import User

from nova_api.dao.generic_sql_dao import GenericSQLDAO


class UserDAO(GenericSQLDAO):
    table = 'usuarios'

    def __init__(self, database=None):
        super(UserDAO, self).__init__(database=database, table=UserDAO.table,
                                      return_class=User)
