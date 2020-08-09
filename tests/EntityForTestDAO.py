from nova_api.GenericSQLDAO import GenericSQLDAO
from EntityForTest import EntityForTest


class EntityForTestDAO(GenericSQLDAO):
    TABLE = 'entities'

    def __init__(self, db=None):
        super(EntityForTestDAO, self).__init__(db=db,
                                               table=EntityForTestDAO.TABLE,
                                               return_class=EntityForTest)
