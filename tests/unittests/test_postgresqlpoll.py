from mock import call
from pytest import fixture

from nova_api.persistence.postgresql_pool import PostgreSQLPool


class TestPostgreSQLPoll:

    @fixture
    def pooling_mock(self, mocker):
        return mocker.patch('nova_api.persistence.postgresql_pool.pool')

    def test_get_instance_not_exist(self, pooling_mock):
        mock = pooling_mock.SimpleConnectionPool
        PostgreSQLPool.get_instance(host="test_host", user="test_user",
                                    password="test_passwd", database="test_db")
        assert mock.mock_calls == [call(
            maxconn=5,
            minconn=5,
            host='test_host',
            database='test_db',
            user='test_user',
            password='test_passwd')]

    def test_get_instance_wrong_chars(self, pooling_mock):
        PostgreSQLPool.get_instance(host="test_host",
                                    user="test_user@test_host",
                                    password="test_passwd", database="test_db")
        assert pooling_mock.mock_calls == [call.SimpleConnectionPool(
            maxconn=5,
            minconn=5,
            host='test_host',
            database='test_db',
            user='test_user@test_host',
            password='test_passwd')]

    def test_get_instance_too_loong(self, pooling_mock):
        PostgreSQLPool.get_instance(
            host="test_hosthosthosthosthosthosthosthosthos"
                 "thosthosthosthosthosthosthost",
            user="test_user@test_host",
            password="test_passwd", database="test_db")
        assert pooling_mock.mock_calls == [call.SimpleConnectionPool(
            maxconn=5,
            minconn=5,
            host="test_hosthosthosthosthosthosthosthosthos"
                 "thosthosthosthosthosthosthost",
            database='test_db',
            user='test_user@test_host',
            password='test_passwd')]

    def test_get_instance_exist_extra_args(self, pooling_mock):
        PostgreSQLPool.get_instance(host="test_host", user="test_user",
                                    password="test_passwd", database="test_db",
                                    database_args={"ssl_ca": "file"})
        assert pooling_mock.mock_calls == []

    def test_get_instance_not_exist_extra_args(self, pooling_mock):
        PostgreSQLPool.get_instance(host="test_host2", user="test_user",
                                    password="test_passwd", database="test_db",
                                    database_args={"ssl_ca": "file"})
        assert pooling_mock.mock_calls == [call.SimpleConnectionPool(
            maxconn=5,
            minconn=5,
            host='test_host2',
            database='test_db',
            user='test_user',
            password='test_passwd',
            ssl_ca='file')]

    def test_get_instance_exist(self, pooling_mock):
        inst_1 = PostgreSQLPool.get_instance(host="test_host",
                                             user="test_user",
                                             password="test_passwd",
                                             database="test_db")
        inst_2 = PostgreSQLPool.get_instance(host="test_host",
                                             user="test_user",
                                             password="test_passwd",
                                             database="test_db")
        assert inst_1 is not None
        assert inst_1 == inst_2

    def test_get_instance_different(self, pooling_mock):
        inst_1 = PostgreSQLPool.get_instance(host="test_host",
                                             user="test_user",
                                             password="test_passwd",
                                             database="test_db")
        inst_2 = PostgreSQLPool.get_instance(host="test_host",
                                             user="test_user",
                                             password="test_passwd",
                                             database="test_db2")
        assert inst_1 is not None and inst_2 is not None
        assert inst_1 != inst_2
