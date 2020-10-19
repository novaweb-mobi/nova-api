from User import User

from nova_api.dao.generic_sql_dao import GenericSQLDAO


class UserDAO(GenericSQLDAO):
    table = 'usuarios'

    def __init__(self, database_type=None, **kwargs):
        super(UserDAO, self).__init__(database_type=database_type,
                                      table=UserDAO.table,
                                      return_class=User,
                                      **kwargs)
