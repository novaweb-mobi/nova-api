import mysql.connector
from mock import call
from pytest import fixture, mark

from nova_api.MySQLHelper import MySQLHelper


class TestMySQLHelper:
    @fixture
    def mysql_mock(self, mocker):
        return mocker.patch('nova_api.MySQLHelper.mysql.connector')

    @fixture
    def raise_exception(self):
        def side_effect_func(*args, **kwargs):
            raise mysql.connector.Error(errno=1146, sqlstate='42S02',
                                        msg="Table 'test.spam' doesn't exist")

        return side_effect_func

    @fixture
    def db_(self, mysql_mock):
        return MySQLHelper()

    @fixture
    def cursor_mock(self, mysql_mock):
        cursor_mock = mysql_mock.connect.return_value.cursor.return_value
        cursor_mock.rowcount = 1
        cursor_mock.lastrowid = 1
        return cursor_mock

    def test_init(self, mysql_mock):
        MySQLHelper(host='127.0.0.1', user='test',
                    password='12345', database='test_db')
        assert mysql_mock.mock_calls == [
            call.connect(host='127.0.0.1', user='test',
                         passwd='12345', database='test_db'),
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
                         passwd='root', database='default'),
            call.connect().cursor(),
            call.connect().cursor().close(),
            call.connect().close()
        ]
        assert mysql_mock.mock_calls == calls
