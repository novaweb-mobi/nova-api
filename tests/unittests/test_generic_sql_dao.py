from dataclasses import dataclass
from datetime import date, datetime

from mock import call
from pytest import fixture, mark, raises

from Entity import Entity
from GenericSQLDAO import GenericSQLDAO


@dataclass
class TestEntity(Entity):
    name: str = "Anom"
    birthday: date = None


class TestGenericSQLDAO:
    @fixture
    def mysql_mock(self, mocker):
        return mocker.patch('GenericSQLDAO.MySQLHelper')

    @fixture
    def generic_dao(self, mysql_mock):
        generic_dao = GenericSQLDAO(
            table="test_table",
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity)
        return generic_dao

    def test_create_table(self, generic_dao, mysql_mock):
        generic_dao.create_table_if_not_exists()
        print(mysql_mock.mock_calls)
        assert mysql_mock.mock_calls[1] == call().query(
            'CREATE TABLE IF NOT EXISTS test_table ('
            '`id` CHAR(32) NOT NULL, '
            '`creation_datetime` DATETIME NULL, '
            '`last_modified_datetime` DATETIME NULL, '
            '`name` VARCHAR(100) NULL, '
            '`birthday` DATE NULL, '
            'PRIMARY KEY(`id`)'
            ') '
            'ENGINE = InnoDB;'
        )

    def test_init(self, mysql_mock, generic_dao):
        assert generic_dao.db == mysql_mock.return_value
        assert generic_dao.TABLE == "test_table"
        assert generic_dao.FIELDS == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.RETURN_CLASS == TestEntity

    def test_init_parameter_gen(self, mysql_mock):
        generic_dao = GenericSQLDAO(table='test_table', prefix='test_',
                                    return_class=TestEntity)
        assert generic_dao.FIELDS == {"id_": "test_id_",
                                      "creation_datetime":
                                          "test_creation_datetime",
                                      "last_modified_datetime":
                                          "test_last_modified_datetime",
                                      "name": "test_name",
                                      "birthday": "test_birthday"}

    def test_init_parameter_gen_no_prefix(self, mysql_mock):
        generic_dao = GenericSQLDAO(table='test_table',
                                    return_class=TestEntity)
        assert generic_dao.FIELDS == {"id_": "testentity_id_",
                                      "creation_datetime":
                                          "testentity_creation_datetime",
                                      "last_modified_datetime":
                                          "testentity_last_modified_datetime",
                                      "name": "testentity_name",
                                      "birthday": "testentity_birthday"}

    def test_get(self, generic_dao, mysql_mock):
        id_ = "12345678901234567890123456789012"
        generic_dao.get(id_=id_)
        db = mysql_mock.return_value
        db.query.return_value = [id_,
                                 datetime(2020, 7, 26, 12, 00, 00),
                                 datetime(2020, 7, 26, 12, 00, 00)]
        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE id = %s LIMIT %s OFFSET %s;",
            ['12345678901234567890123456789012', 1, 0]
        )

    @mark.parametrize("id_, error_type", [
        ("123", ValueError),
        (123, TypeError)
    ])
    def test_get_invalid_id(self, generic_dao, id_, error_type):
        with raises(error_type):
            generic_dao.get(id_=id_)

    def test_get_all(self, generic_dao, mysql_mock):
        generic_dao.get_all(filters={"creation_datetime":
                                         ['>', "2020-01-01 00:00:00"],
                                     "id_": ['LIKE', "123"],
                                     "name": "Anom"})
        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE creation_datetime > %s "
            "AND id LIKE %s "
            "AND name = %s "
            "LIMIT %s OFFSET %s;",
            ["2020-01-01 00:00:00", '123', 'Anom', 20, 0]
        )

    def test_get_all_no_filter(self, generic_dao, mysql_mock):
        generic_dao.get_all()
        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table  "
            "LIMIT %s OFFSET %s;",
            [20, 0]
        )

    def test_get_all_unallowed_operator(self, generic_dao):
        with raises(ValueError):
            generic_dao.get_all(filters={"creation_datetime": ['>>', 'abc']})

    def test_get_all_unknown_property(self, generic_dao):
        with raises(ValueError):
            generic_dao.get_all(filters={"test": 1})
