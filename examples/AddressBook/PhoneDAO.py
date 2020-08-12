from Contact import Phone

from nova_api.generic_dao import GenericSQLDAO


class PhoneDAO(GenericSQLDAO):
    def __init__(self, database=None):
        super(PhoneDAO, self).__init__(database=database,
                                       return_class=Phone)
