from dataclasses import dataclass
from datetime import date, datetime

import mysql.connector
from mock import call
from mysql.connector import InterfaceError, DatabaseError, Error
from pytest import fixture, mark, raises

from nova_api.persistence.mysql_helper import MySQLHelper
from nova_api.entity import Entity


@dataclass
class TestEntity(Entity):
    pass


class TestMySQLHelper:
    @fixture
    def mysql_mock(self, mocker):
        return mocker.patch('nova_api.persistence'
                            '.mysql_helper.mysql.connector')

    @fixture
    def raise_exception(self):
        def side_effect_func(*args, **kwargs):
            raise mysql.connector.Error(errno=1146, sqlstate='42S02',
                                        msg="Table 'test.spam' doesn't exist")

        return side_effect_func

    @fixture
    def db_(self, mysql_mock):
        return MySQLHelper(pooled=False)

    @fixture
    def cursor_mock(self, mysql_mock):
        cursor_mock = mysql_mock.connect.return_value.cursor.return_value
        cursor_mock.rowcount = 1
        cursor_mock.lastrowid = 1
        return cursor_mock

    def test_init(self, mysql_mock):
        MySQLHelper(host='127.0.0.1', user='test',
                    password='12345', database='test_db', pooled=False)
        assert mysql_mock.mock_calls == [
            call.connect(host='127.0.0.1', user='test',
                         password='12345', database='test_db'),
            call.connect().cursor()
        ]

    def test_init_extra_args_no_pool(self, mysql_mock):
        MySQLHelper(host='127.0.0.1', user='test',
                    password='12345', database='test_db', pooled=False,
                    database_args={"ssl_ca": "file"})
        assert mysql_mock.mock_calls == [
            call.connect(host='127.0.0.1', user='test',
                         password='12345', database='test_db', ssl_ca="file"),
            call.connect().cursor()
        ]

    def test_init_pooled(self, mocker):
        pool_mock = mocker.patch("nova_api.persistence.mysql_helper.MySQLPool")
        MySQLHelper(host='127.0.0.1', user='test',
                    password='12345', database='test_db', pooled=True)
        assert pool_mock.mock_calls == [
            call.get_instance(host='127.0.0.1', user='test',
                              password='12345', database='test_db',
                              database_args={}),
            call.get_instance().get_connection(),
            call.get_instance().get_connection().cursor()
        ]

    def test_init_pooled_extra_args(self, mocker):
        pool_mock = mocker.patch("nova_api.persistence.mysql_helper.MySQLPool")
        MySQLHelper(host='127.0.0.1', user='test',
                    password='12345', database='test_db', pooled=True,
                    database_args={"ssl_ca": "file"})
        assert pool_mock.mock_calls == [
            call.get_instance(host='127.0.0.1', user='test',
                              password='12345', database='test_db',
                              database_args={"ssl_ca": "file"}),
            call.get_instance().get_connection(),
            call.get_instance().get_connection().cursor()
        ]

    def test_init_none(self, mysql_mock):
        MySQLHelper(host=None, user='test',
                    password='12345', database='test_db', pooled=False)
        assert mysql_mock.mock_calls == [
            call.connect(host='localhost', user='test',
                         password='12345', database='test_db'),
            call.connect().cursor()
        ]

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
    def test_query(self, mysql_mock, cursor_mock, query, params, calls, db_):
        row_count, last_id = db_.query(query, params)
        assert ([call_ for call_ in calls
                 if call_ in mysql_mock.mock_calls] == calls
                and row_count == 1 and last_id == 1)

    @mark.parametrize("results, returned", [
        ([], None),
        ([[1, 2, 3]], [[1, 2, 3]])
    ])
    def test_get_results(self, mysql_mock, cursor_mock,
                         results, returned, db_):
        cursor_mock.fetchall.return_value = results
        assert db_.get_results() == returned

    def test_close(self, mysql_mock, db_, cursor_mock):
        db_.close()
        calls = [
            call.connect(host='localhost', user='root',
                         password='root', database='TEST'),
            call.connect().cursor(),
            call.connect().cursor().close(),
            call.connect().close()
        ]
        assert mysql_mock.mock_calls == calls

    @mark.parametrize("exception_type", [ValueError,
                                         InterfaceError])
    def test_fail_init(self, mysql_mock, exception_type):
        def raise_exception(*args, **kwargs):
            raise exception_type()

        mysql_mock.connect.side_effect = raise_exception

        with raises(ConnectionError):
            db_ = MySQLHelper(pooled=False)

    @mark.parametrize("exception_type", [InterfaceError,
                                         DatabaseError,
                                         Error])
    def test_fail_query(self, mysql_mock, db_, exception_type):
        def raise_exception(*args, **kwargs):
            raise exception_type()

        cursor_mock = mysql_mock.connect.return_value.cursor.return_value
        cursor_mock.execute.side_effect = raise_exception

        with raises(RuntimeError):
            db_.query("SELECT * FROM table")

    @mark.parametrize("exception_type", [InterfaceError,
                                         DatabaseError,
                                         Error])
    def test_fail_get_results(self, mysql_mock, db_, exception_type):
        def raise_exception(*args, **kwargs):
            raise exception_type()

        cursor_mock = mysql_mock.connect.return_value.cursor.return_value
        cursor_mock.fetchall.side_effect = raise_exception

        with raises(RuntimeError):
            db_.get_results()

    @mark.parametrize("cls, type_", [
        (bool, "TINYINT(1)"),
        (datetime, "DATETIME"),
        (str, "VARCHAR(100)"),
        (int, "INT"),
        (float, "DECIMAL"),
        (date, "DATE"),
        (TestEntity, "CHAR(32)")
    ])
    def test_predict_db_type(self, cls, type_, mysql_mock):
        helper = MySQLHelper(pooled=False)
        assert helper.predict_db_type(cls) == type_
