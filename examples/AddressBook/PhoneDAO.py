from Contact import Phone

from nova_api.dao.generic_sql_dao import GenericSQLDAO


class PhoneDAO(GenericSQLDAO):
    def __init__(self, database_type=None, **kwargs):
        super(PhoneDAO, self).__init__(database_type=database_type,
                                       return_class=Phone, **kwargs)
