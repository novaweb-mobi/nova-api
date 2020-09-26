from Contact import Contact

from nova_api.dao.generic_sql_dao import GenericSQLDAO


class ContactDAO(GenericSQLDAO):
    def __init__(self, database=None):
        super(ContactDAO, self).__init__(database=database,
                                         return_class=Contact)
