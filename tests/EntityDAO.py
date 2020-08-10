from nova_api.generic_dao import GenericSQLDAO
from EntityForTest import EntityForTest


class EntityDAO(GenericSQLDAO):
    table = 'entities'

    def __init__(self, database=None):
        super(EntityDAO, self).__init__(database=database, table=EntityDAO.TABLE,
                                        return_class=EntityForTest)
