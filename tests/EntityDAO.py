from nova_api.GenericSQLDAO import GenericSQLDAO
from EntityForTest import EntityForTest


class EntityDAO(GenericSQLDAO):
    TABLE = 'entities'

    def __init__(self, db=None):
        super(EntityDAO, self).__init__(db=db, table=EntityDAO.TABLE,
                                        return_class=EntityForTest)
