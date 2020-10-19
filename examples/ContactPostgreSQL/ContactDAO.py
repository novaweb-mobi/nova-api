from nova_api.dao.generic_sql_dao import GenericSQLDAO
from nova_api.persistence.postgresql_helper import PostgreSQLHelper

from Contact import Contact


class ContactDAO(GenericSQLDAO):
    def __init__(self, database_type=PostgreSQLHelper, **kwargs):
        super(ContactDAO, self).__init__(database_type=database_type,
                                         return_class=Contact, **kwargs)
