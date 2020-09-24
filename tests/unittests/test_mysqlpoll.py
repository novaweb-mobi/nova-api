from mock import call
from pytest import fixture

from nova_api.mysql_pool import MySQLPool


class TestMySQLPoll:

    @fixture
    def pooling_mock(self, mocker):
        return mocker.patch('nova_api.mysql_pool.pooling')

    def test_get_instance_not_exist(self, pooling_mock):
        mock = pooling_mock.MySQLConnectionPool
        MySQLPool.get_instance(host="test_host", user="test_user",
                               password="test_passwd", database="test_db")
        assert mock.mock_calls == [call(
            pool_name='test_user_test_host-test_db',
            pool_size=5,
            pool_reset_session=True,
            host='test_host',
            database='test_db',
            user='test_user',
            password='test_passwd')]

    def test_get_instance_wrong_chars(self, pooling_mock):
        MySQLPool.get_instance(host="test_host", user="test_user@test_host",
                               password="test_passwd", database="test_db")
        assert pooling_mock.mock_calls == [call.MySQLConnectionPool(
            pool_name='test_user_test_host_test_host-test_db',
            pool_size=5,
            pool_reset_session=True,
            host='test_host',
            database='test_db',
            user='test_user@test_host',
            password='test_passwd')]

    def test_get_instance_exist_extra_args(self, pooling_mock):
        MySQLPool.get_instance(host="test_host", user="test_user",
                               password="test_passwd", database="test_db",
                               database_args={"ssl_ca": "file"})
        assert pooling_mock.mock_calls == []

    def test_get_instance_not_exist_extra_args(self, pooling_mock):
        MySQLPool.get_instance(host="test_host2", user="test_user",
                               password="test_passwd", database="test_db",
                               database_args={"ssl_ca": "file"})
        assert pooling_mock.mock_calls == [call.MySQLConnectionPool(
            pool_name='test_user_test_host2-test_db',
            pool_size=5,
            pool_reset_session=True,
            host='test_host2',
            database='test_db',
            user='test_user',
            password='test_passwd',
            ssl_ca='file')]

    def test_get_instance_exist(self, pooling_mock):
        inst_1 = MySQLPool.get_instance(host="test_host", user="test_user",
                                        password="test_passwd",
                                        database="test_db")
        inst_2 = MySQLPool.get_instance(host="test_host", user="test_user",
                                        password="test_passwd",
                                        database="test_db")
        assert inst_1 is not None
        assert inst_1 == inst_2

    def test_get_instance_different(self, pooling_mock):
        inst_1 = MySQLPool.get_instance(host="test_host", user="test_user",
                                        password="test_passwd",
                                        database="test_db")
        inst_2 = MySQLPool.get_instance(host="test_host", user="test_user",
                                        password="test_passwd",
                                        database="test_db2")
        assert inst_1 is not None and inst_2 is not None
        assert inst_1 != inst_2


