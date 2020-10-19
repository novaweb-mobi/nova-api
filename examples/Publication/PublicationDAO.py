from Publication import Publication

from nova_api.dao.generic_sql_dao import GenericSQLDAO


class PublicationDAO(GenericSQLDAO):
    table = 'publicacao'

    def __init__(self, database_type=None, **kwargs):
        super(PublicationDAO, self).__init__(database_type=database_type,
                                             table=PublicationDAO.table,
                                             return_class=Publication,
                                             **kwargs)
