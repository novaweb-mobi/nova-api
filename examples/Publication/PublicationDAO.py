from Publication import Publication

from nova_api.dao.generic_sql_dao import GenericSQLDAO


class PublicationDAO(GenericSQLDAO):
    table = 'publicacao'

    def __init__(self, database=None):
        super(PublicationDAO, self).__init__(database=database,
                                             table=PublicationDAO.table,
                                             return_class=Publication)
