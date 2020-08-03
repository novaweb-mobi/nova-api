from dataclasses import dataclass
from datetime import date, datetime

from mock import call
from pytest import fixture, mark, raises

from Entity import Entity
from GenericSQLDAO import GenericSQLDAO
from nova_api.exceptions import NoRowsAffectedException


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

    def test_init(self, mysql_mock):
        generic_dao = GenericSQLDAO(
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity)
        assert generic_dao.db == mysql_mock.return_value
        assert generic_dao.TABLE == "test_entitys"
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
        assert generic_dao.FIELDS == {"id_": "test_entity_id_",
                                      "creation_datetime":
                                          "test_entity_creation_datetime",
                                      "last_modified_datetime":
                                          "test_entity_last_modified_datetime",
                                      "name": "test_entity_name",
                                      "birthday": "test_entity_birthday"}

    def test_get(self, generic_dao, mysql_mock):
        id_ = "12345678901234567890123456789012"

        db = mysql_mock.return_value
        db.get_results.return_value = [[id_,
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]

        entity = generic_dao.get(id_=id_)

        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE id = %s LIMIT %s OFFSET %s;",
            ['12345678901234567890123456789012', 1, 0]
        )
        assert entity == TestEntity(id_,
                                    datetime(2020, 7, 26, 12, 00, 00),
                                    datetime(2020, 7, 26, 12, 00, 00))

    def test_get_no_results(self, generic_dao, mysql_mock):
        id_ = "12345678901234567890123456789012"

        db = mysql_mock.return_value
        db.get_results.return_value = None

        entity = generic_dao.get(id_=id_)

        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE id = %s LIMIT %s OFFSET %s;",
            ['12345678901234567890123456789012', 1, 0]
        )
        assert entity is None

    @mark.parametrize("id_, error_type", [
        ("123", ValueError),
        (123, TypeError)
    ])
    def test_get_invalid_id(self, generic_dao, id_, error_type):
        with raises(error_type):
            generic_dao.get(id_=id_)

    def test_get_all(self, generic_dao, mysql_mock):
        db = mysql_mock.return_value
        db.get_results.return_value = [["12345678901234567890123456789012",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None],
                                       ["12345678901234567890123456789010",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Testando",
                                        None]]

        total, res = generic_dao.get_all(filters={"creation_datetime":
                                                      ['>',
                                                       "2020-01-01 00:00:00"],
                                                  "id_": ['LIKE', "123%"],
                                                  "name": "Anom"})
        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE creation_datetime > %s "
            "AND id LIKE %s "
            "AND name = %s "
            "LIMIT %s OFFSET %s;",
            ["2020-01-01 00:00:00", '123%', 'Anom', 20, 0]
        )

        assert mysql_mock.mock_calls[3] == call().query(
            'SELECT count(id) FROM test_table;'
        )

        assert res == [TestEntity("12345678901234567890123456789012",
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  "Anom",
                                  None),
                       TestEntity("12345678901234567890123456789010",
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  "Testando",
                                  None)]

    def test_get_all_no_results(self, generic_dao, mysql_mock):
        db = mysql_mock.return_value
        db.get_results.return_value = None

        total, res = generic_dao.get_all(filters={"creation_datetime":
                                                      ['>',
                                                       "2020-01-01 00:00:00"],
                                                  "id_": ['LIKE', "123%"],
                                                  "name": "Anom"})
        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE creation_datetime > %s "
            "AND id LIKE %s "
            "AND name = %s "
            "LIMIT %s OFFSET %s;",
            ["2020-01-01 00:00:00", '123%', 'Anom', 20, 0]
        )

        assert total == 0 and res == []

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

    def test_remove(self, generic_dao, mysql_mock):
        def isDeleteQuery(*args):
            if "DELETE" in args[0]:
                return 1, 0
            return None

        db = mysql_mock.return_value
        db.get_results.return_value = [["12345678901234567890123456789012",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]
        db.query.side_effect = isDeleteQuery
        generic_dao.remove(TestEntity(id_="12345678901234567890123456789012"))
        assert mysql_mock.mock_calls[5] == call().query(
            'DELETE FROM test_table WHERE id = %s;',
            ['12345678901234567890123456789012']
        )

    def test_remove_fail(self, generic_dao, mysql_mock):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 0, 0
            return None

        db = mysql_mock.return_value
        db.get_results.return_value = [["12345678901234567890123456789012",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]
        db.query.side_effect = is_delete_query
        with raises(NoRowsAffectedException):
            generic_dao.remove(
                TestEntity(id_="12345678901234567890123456789012")
            )

    def test_remove_not_exist(self, generic_dao, mysql_mock):
        db = mysql_mock.return_value
        db.get_results.return_value = None
        with raises(AssertionError):
            generic_dao.remove(TestEntity(
                id_="12345678901234567890123456789012"))

    def test_remove_not_entity(self, generic_dao, mysql_mock):
        with raises(TypeError):
            generic_dao.remove("12345678901234567890123456789012")

    def test_create(self, generic_dao, mysql_mock):
        def is_insert_query(*args):
            if "INSERT" in args[0]:
                return 1, 0
            return None

        entity = TestEntity(id_="12345678901234567890123456789012")

        db = mysql_mock.return_value
        db.get_results.return_value = None

        db.query.side_effect = is_insert_query

        id_ = generic_dao.create(entity)

        assert mysql_mock.mock_calls[3] == call().query(
            'INSERT INTO test_table (id, creation_datetime,'
            ' last_modified_datetime, name, birthday) '
            'VALUES (%s, %s, %s, %s, %s);', list(dict(entity).values()))
        assert id_ == entity.id_

    def test_create_exist(self, generic_dao, mysql_mock):
        entity = TestEntity(id_="12345678901234567890123456789012")
        db = mysql_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        with raises(AssertionError):
            generic_dao.create(entity)

    def test_create_not_entity(self, generic_dao, mysql_mock):
        with raises(TypeError):
            generic_dao.create("12345678901234567890123456789012")
