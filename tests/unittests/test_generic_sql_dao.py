from dataclasses import dataclass, field
from datetime import date, datetime
from time import sleep

from mock import call
from pytest import fixture, mark, raises

from nova_api.entity import Entity
from nova_api.generic_dao import GenericSQLDAO
from nova_api.exceptions import NoRowsAffectedException
# pylint: disable=R0201

@dataclass
class TestEntity(Entity):
    name: str = "Anom"
    birthday: date = None

@dataclass
class TestEntity2(Entity):
    name: str = field(default=None, metadata={"default": "NULL",
                                              "primary_key": True})
    birthday: date = None


@dataclass
class TestEntityWithChild(Entity):
    name: str = "Anom"
    birthday: date = None
    child: TestEntity = None
    not_to_database: str = field(default='', metadata={"database": False})


class TestGenericSQLDAO:
    @fixture
    def mysql_mock(self, mocker):
        return mocker.patch('nova_api.generic_dao.MySQLHelper')

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

    @fixture
    def generic_dao2(self, mysql_mock):
        generic_dao = GenericSQLDAO(
            table="test_table",
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity2)
        return generic_dao

    @fixture
    def generic_dao_with_child(self, mysql_mock):
        generic_dao = GenericSQLDAO(
            table="test_table",
            prefix='',
            return_class=TestEntityWithChild)
        return generic_dao

    @fixture
    def entity(self):
        return TestEntity(id_="12345678901234567890123456789012")

    def test_create_table(self, generic_dao, mysql_mock):
        generic_dao.create_table_if_not_exists()
        assert mysql_mock.mock_calls[1] == call().query(
            'CREATE table IF NOT EXISTS test_table ('
            '`id` CHAR(32) NOT NULL, '
            '`creation_datetime` DATETIME NULL, '
            '`last_modified_datetime` DATETIME NULL, '
            '`name` VARCHAR(100) NULL, '
            '`birthday` DATE NULL, '
            'PRIMARY KEY(`id`)'
            ') '
            'ENGINE = InnoDB;'
        )

    def test_create_table_with_primary_key_null(self, generic_dao2,
                                                mysql_mock):
        generic_dao2.create_table_if_not_exists()
        assert mysql_mock.mock_calls[1] == call().query(
            'CREATE table IF NOT EXISTS test_table ('
            '`id` CHAR(32) NOT NULL, '
            '`creation_datetime` DATETIME NULL, '
            '`last_modified_datetime` DATETIME NULL, '
            '`name` VARCHAR(100) NOT NULL, '
            '`birthday` DATE NULL, '
            'PRIMARY KEY(`id`, `name`)'
            ') '
            'ENGINE = InnoDB;'
        )

    def test_create_table_with_child(self, mysql_mock):
        generic_dao = GenericSQLDAO(return_class=TestEntityWithChild,
                                    prefix='')
        generic_dao.create_table_if_not_exists()
        print(mysql_mock.mock_calls)
        assert mysql_mock.mock_calls[1] == call().query(
            'CREATE table IF NOT EXISTS test_entity_with_childs ('
            '`id_` CHAR(32) NOT NULL, '
            '`creation_datetime` DATETIME NULL, '
            '`last_modified_datetime` DATETIME NULL, '
            '`name` VARCHAR(100) NULL, '
            '`birthday` DATE NULL, '
            '`child_id_` CHAR(32) NULL, '
            'PRIMARY KEY(`id_`)'
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
            return_class=TestEntity,
            pooled=False)
        assert mysql_mock.mock_calls == [call(pooled=False, database_args={})]
        assert generic_dao.database == mysql_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_pooled(self, mysql_mock):
        generic_dao = GenericSQLDAO(
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity, pooled=True)
        assert mysql_mock.mock_calls == [call(pooled=True, database_args={})]
        assert generic_dao.database == mysql_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_pooled_database_args(self, mysql_mock):
        generic_dao = GenericSQLDAO(
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity, pooled=True,
            database_args={"ssl_ca": "file"})
        assert mysql_mock.mock_calls == [call(pooled=True, database_args={"ssl_ca": "file"})]
        assert generic_dao.database == mysql_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_parameter_gen(self, mysql_mock):
        generic_dao = GenericSQLDAO(table='test_table', prefix='test_',
                                    return_class=TestEntity)
        assert generic_dao.fields == {"id_": "test_id_",
                                      "creation_datetime":
                                          "test_creation_datetime",
                                      "last_modified_datetime":
                                          "test_last_modified_datetime",
                                      "name": "test_name",
                                      "birthday": "test_birthday"}

    def test_init_parameter_gen_no_prefix(self, mysql_mock):
        generic_dao = GenericSQLDAO(table='test_table',
                                    return_class=TestEntity)
        assert generic_dao.fields == {"id_": "test_entity_id_",
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

    def test_get_child(self, mysql_mock):
        generic_dao = GenericSQLDAO(return_class=TestEntityWithChild,
                                    prefix='')
        id_ = "12345678901234567890123456789012"

        db = mysql_mock.return_value
        db.get_results.return_value = [[id_,
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None,
                                        id_]]

        entity = generic_dao.get(id_=id_)

        assert mysql_mock.mock_calls[1] == call().query(
            "SELECT id_, creation_datetime, last_modified_datetime,"
            " name, birthday, child_id_ "
            "FROM test_entity_with_childs WHERE id_ = %s "
            "LIMIT %s OFFSET %s;",
            ['12345678901234567890123456789012', 1, 0]
        )
        assert entity == TestEntityWithChild(
            id_,
            datetime(2020, 7, 26, 12, 00, 00),
            datetime(2020, 7, 26, 12, 00, 00),
            child=TestEntity(id_))

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

    def test_remove(self, generic_dao, mysql_mock, entity):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 1, 0
            return None

        db = mysql_mock.return_value
        db.get_results.return_value = [["12345678901234567890123456789012",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]
        db.query.side_effect = is_delete_query
        generic_dao.remove(entity)
        assert mysql_mock.mock_calls[5] == call().query(
            'DELETE FROM test_table WHERE id = %s;',
            ['12345678901234567890123456789012']
        )

    def test_remove_fail(self, generic_dao, mysql_mock, entity):
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
            generic_dao.remove(entity)

    def test_remove_not_exist(self, generic_dao, mysql_mock, entity):
        db = mysql_mock.return_value
        db.get_results.return_value = None
        with raises(AssertionError):
            generic_dao.remove(entity)

    def test_remove_not_entity(self, generic_dao, mysql_mock):
        with raises(TypeError):
            generic_dao.remove("12345678901234567890123456789012")

    def test_create(self, generic_dao, mysql_mock, entity):
        def is_insert_query(*args):
            if "INSERT" in args[0]:
                return 1, 0
            return None

        db = mysql_mock.return_value
        db.get_results.return_value = None

        db.query.side_effect = is_insert_query

        id_ = generic_dao.create(entity)

        assert mysql_mock.mock_calls[3] == call().query(
            'INSERT INTO test_table (id, creation_datetime,'
            ' last_modified_datetime, name, birthday) '
            'VALUES (%s, %s, %s, %s, %s);', list(dict(entity).values()))
        assert id_ == entity.id_

    def test_create_with_child(self, generic_dao_with_child,
                               mysql_mock):
        def is_insert_query(*args):
            if "INSERT" in args[0]:
                return 1, 0
            return None

        entity = TestEntityWithChild()

        db = mysql_mock.return_value
        db.get_results.return_value = None

        db.query.side_effect = is_insert_query

        id_ = generic_dao_with_child.create(entity)

        assert mysql_mock.mock_calls[3] == call().query(
            'INSERT INTO test_table (id_, creation_datetime,'
            ' last_modified_datetime, name, birthday, child_id_) '
            'VALUES (%s, %s, %s, %s, %s, %s);', entity.get_db_values())
        assert id_ == entity.id_

    def test_create_exist(self, generic_dao, mysql_mock, entity):
        db = mysql_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        with raises(AssertionError):
            generic_dao.create(entity)

    def test_create_not_entity(self, generic_dao, mysql_mock):
        with raises(TypeError):
            generic_dao.create("12345678901234567890123456789012")

    def test_create_no_rows_affected(self, generic_dao, mysql_mock, entity):
        db = mysql_mock.return_value
        db.query.return_value = 0, 0
        with raises(NoRowsAffectedException):
            generic_dao.create(entity)

    def test_update_not_entity(self, generic_dao, mysql_mock):
        with raises(TypeError):
            generic_dao.update("12345678901234567890123456789012")

    def test_update_entity_not_exists(self, generic_dao, mysql_mock, entity):
        db = mysql_mock.return_value
        db.get_results.return_value = None
        with raises(AssertionError):
            generic_dao.update(entity)

    def test_update(self, generic_dao, mysql_mock, entity):
        db = mysql_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        db.query.return_value = 1, 0
        entity.birthday = date(1998, 12, 21)
        entity.name = "MyTestName"
        sleep(1)
        generic_dao.update(entity)
        assert mysql_mock.mock_calls[5] == call().query(
            'UPDATE test_table SET id=%s, creation_datetime=%s, '
            'last_modified_datetime=%s, name=%s, birthday=%s '
            'WHERE id = %s;', list(dict(entity).values()) + [entity.id_]
        )
        assert entity.creation_datetime < entity.last_modified_datetime

    def test_update_with_child(self, generic_dao_with_child,
                               mysql_mock):
        entity = TestEntityWithChild()
        db = mysql_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        db.query.return_value = 1, 0
        entity.birthday = date(1998, 12, 21)
        entity.name = "MyTestName"
        sleep(1)
        generic_dao_with_child.update(entity)
        assert mysql_mock.mock_calls[5] == call().query(
            'UPDATE test_table SET id_=%s, creation_datetime=%s, '
            'last_modified_datetime=%s, name=%s, birthday=%s, child_id_=%s '
            'WHERE id_ = %s;', entity.get_db_values() + [entity.id_]
        )
        assert entity.creation_datetime < entity.last_modified_datetime

    def test_update_no_rows_affected(self, generic_dao, mysql_mock, entity):
        db = mysql_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        db.query.return_value = 0, 0
        with raises(NoRowsAffectedException):
            generic_dao.update(entity)

    def test_close(self, generic_dao, mysql_mock):
        db = mysql_mock.return_value
        generic_dao.close()
        assert db.mock_calls == [call.close()]

    @mark.parametrize("cls, type_", [
        (bool, "TINYINT(1)"),
        (datetime, "DATETIME"),
        (str, "VARCHAR(100)"),
        (int, "INT"),
        (float, "DECIMAL"),
        (date, "DATE")
    ])
    def test_predict_db_type(self, cls, type_):
        assert GenericSQLDAO.predict_db_type(cls) == type_
