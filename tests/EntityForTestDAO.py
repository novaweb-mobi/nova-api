from nova_api.generic_dao import GenericSQLDAO
from EntityForTest import EntityForTest


class EntityForTestDAO(GenericSQLDAO):
    table = 'entities'

    def __init__(self, database=None):
        super(EntityForTestDAO, self).__init__(database=database,
                                               table=EntityForTestDAO.TABLE,
                                               return_class=EntityForTest)
