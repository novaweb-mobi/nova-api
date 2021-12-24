from dataclasses import dataclass
from datetime import date, datetime
from typing import TypedDict

import psycopg2
from mock import Mock, call
from psycopg2 import DatabaseError, Error, InterfaceError
from pytest import fixture, mark, raises

from nova_api.entity import Entity
from nova_api.persistence.postgresql_helper import PostgreSQLHelper


class MyTestTypedDict(TypedDict):
    test: str
    another: str


@dataclass
class TestEntity(Entity):
    test: str = None


class TestPostgreSQLHelper:
    @fixture
    def postgresql_mock(self, mocker):
        return mocker.patch('nova_api.persistence'
                            '.postgresql_helper.psycopg2')

    @fixture
    def pool_mock(self, mocker):
        return mocker.patch("nova_api.persistence.postgresql_helper"
                            ".PostgreSQLPool")

    @fixture
    def raise_exception(self):
        def side_effect_func(*args, **kwargs):
            raise psycopg2.Error(errno=1146, sqlstate='42S02',
                                 msg="Table 'test.spam' doesn't exist")

        return side_effect_func

    @fixture
    def db_(self, postgresql_mock):
        return PostgreSQLHelper(pooled=False)

    @fixture
    def db_pooled(self, postgresql_mock, pool_mock):
        return PostgreSQLHelper(pooled=True)

    @fixture
    def cursor_mock(self, postgresql_mock):
        cursor_mock = postgresql_mock.connect.return_value.cursor.return_value
        cursor_mock.rowcount = 1
        cursor_mock.lastrowid = 1
        return cursor_mock

    def test_init_pghelper(self, postgresql_mock):
        PostgreSQLHelper(host='127.0.0.1', user='test',
                         password='12345', database='test_db', pooled=False)
        assert postgresql_mock.mock_calls == [
            call.connect(host='127.0.0.1', user='test',
                         password='12345', database='test_db'),
            call.connect().cursor()
        ]

    def test_init_extra_args_no_pool_pghelper(self, postgresql_mock):
        PostgreSQLHelper(host='127.0.0.1', user='test',
                         password='12345', database='test_db', pooled=False,
                         database_args={"ssl_ca": "file"})
        assert postgresql_mock.mock_calls == [
            call.connect(host='127.0.0.1', user='test',
                         password='12345', database='test_db', ssl_ca="file"),
            call.connect().cursor()
        ]

    def test_init_pooled_pghelper(self, pool_mock):
        help = PostgreSQLHelper(host='127.0.0.1', user='test',
                                password='12345', database='test_db',
                                pooled=True)
        assert pool_mock.mock_calls == [
            call.get_instance(host='127.0.0.1', user='test',
                              password='12345', database='test_db',
                              database_args={}),
            call.get_instance().getconn(key=id(help)),
            call.get_instance().getconn().cursor()
        ]

    def test_init_pooled_extra_args_pghelper(self, pool_mock):
        helper = PostgreSQLHelper(host='127.0.0.1', user='test',
                                  password='12345', database='test_db',
                                  pooled=True,
                                  database_args={"ssl_ca": "file"})
        assert pool_mock.mock_calls == [
            call.get_instance(host='127.0.0.1', user='test',
                              password='12345', database='test_db',
                              database_args={"ssl_ca": "file"}),
            call.get_instance().getconn(key=id(helper)),
            call.get_instance().getconn().cursor()
        ]

    def test_init_none_pghelper(self, postgresql_mock):
        PostgreSQLHelper(host=None, user='test',
                         password='12345', database='test_db', pooled=False)
        assert postgresql_mock.mock_calls == [
            call.connect(host='localhost', user='test',
                         password='12345', database='test_db'),
            call.connect().cursor()
        ]

    @mark.parametrize("cls, type_", [
        (bool, "BOOLEAN"),
        (datetime, "TIMESTAMP"),
        (str, "VARCHAR(100)"),
        (int, "INT"),
        (float, "DECIMAL"),
        (date, "DATE"),
        (TestEntity, "CHAR(32)"),
        (MyTestTypedDict, "jsonb")
    ])
    def test_predict_db_type_pghelper(self, cls, type_, postgresql_mock):
        helper = PostgreSQLHelper(pooled=False)
        assert helper.predict_db_type(cls) == type_

    @mark.parametrize("query, params, calls", [
        ("SELECT * FROM teste;", None,
         [call.connect().cursor().execute("SELECT * FROM teste;")]),
        ("SELECT * FROM teste WHERE id=%s;", [1],
         [call.connect().cursor().execute("SELECT * FROM teste WHERE id=%s;",
                                          [1])]),
        ("INSERT INTO t (a) VALUES (%s);", [1], [
            call.connect().cursor().execute("INSERT INTO t (a) VALUES (%s);",
                                            [1]),
            call.connect().commit()
        ]),
        ("DELETE FROM t;", [1], [
            call.connect().cursor().execute("DELETE FROM t;", [1]),
            call.connect().commit()
        ]),
        ("UPDATE t SET a=%s;", [1], [
            call.connect().cursor().execute("UPDATE t SET a=%s;", [1]),
            call.connect().commit()
        ])
    ])
    def test_query(self, postgresql_mock, cursor_mock, query, params, calls,
                   db_):
        row_count, last_id = db_.query(query, params)
        assert ([call_ for call_ in calls
                 if call_ in postgresql_mock.mock_calls] == calls
                and row_count == 1 and last_id == 1)

    @mark.parametrize("results, returned", [
        ([], None),
        ([[1, 2, 3]], [[1, 2, 3]])
    ])
    def test_get_results(self, postgresql_mock: Mock, cursor_mock,
                         results, returned, db_):
        cursor_mock.fetchall.return_value = results
        assert db_.get_results() == returned

    def test_close(self, postgresql_mock: Mock, db_, cursor_mock):
        db_.close()
        calls = [
            call.connect(host='localhost', user='root',
                         password='root', database='TEST'),
            call.connect().cursor(),
            call.connect().cursor().close(),
            call.connect().close()
        ]
        postgresql_mock.assert_has_calls(calls, any_order=False)

    def test_close_pooled(self, pool_mock, db_pooled, cursor_mock):
        db_pooled.close()
        my_conn = Mock()
        pool_mock.get_instance.return_value.getconn.return_value = my_conn

        assert call.get_instance().getconn().cursor().close() \
               in pool_mock.mock_calls
        assert pool_mock.get_instance.return_value.putconn.called_with(my_conn)

    @mark.parametrize("exception_type", [ValueError,
                                         InterfaceError])
    def test_fail_init(self, postgresql_mock, exception_type):
        def raise_exception(*args, **kwargs):
            raise exception_type()

        postgresql_mock.connect.side_effect = raise_exception

        with raises(ConnectionError):
            db_ = PostgreSQLHelper(pooled=False)

    @mark.parametrize("exception_type", [InterfaceError,
                                         DatabaseError,
                                         Error])
    def test_fail_query(self, postgresql_mock, db_, exception_type):
        def raise_exception(*args, **kwargs):
            raise exception_type()

        cursor_mock = postgresql_mock.connect.return_value.cursor.return_value
        cursor_mock.execute.side_effect = raise_exception

        with raises(RuntimeError):
            db_.query("SELECT * FROM table")

    @mark.parametrize("exception_type", [InterfaceError,
                                         DatabaseError,
                                         Error])
    def test_fail_get_results(self, postgresql_mock, db_, exception_type):
        def raise_exception(*args, **kwargs):
            raise exception_type()

        cursor_mock = postgresql_mock.connect.return_value.cursor.return_value
        cursor_mock.fetchall.side_effect = raise_exception

        with raises(RuntimeError):
            db_.get_results()

    def test_custom_serializer_json(self, postgresql_mock, db_):
        test_dict = {"test": "test"}
        assert db_.custom_serializer(test_dict) == '{"test": "test"}'

        class MyTypedDict(TypedDict):
            test: str

        a = MyTypedDict("test")
        assert db_.custom_serializer(a) == '{"test": "test"}'