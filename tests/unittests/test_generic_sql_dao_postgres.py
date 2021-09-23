from dataclasses import dataclass, field
from datetime import date, datetime
from time import sleep

from mock import call
from pytest import fixture, mark, raises

from nova_api.dao.generic_sql_dao import GenericSQLDAO
from nova_api.entity import Entity
from nova_api.exceptions import DuplicateEntityException, \
    InvalidIDException, InvalidIDTypeException, NoRowsAffectedException, \
    NotEntityException
# pylint: disable=R0201
from nova_api.persistence import postgresql_helper


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


class TestGenericSQLDAOPostgres:
    @fixture
    def postgres_mock(self, mocker):
        postgres_mock = mocker.patch.object(postgresql_helper,
                                            'PostgreSQLHelper')
        props = postgres_mock.return_value
        props.ALLOWED_COMPARATORS = ['=', '<=>', '<>', '!=',
                                                       '>', '>=', '<=', 'LIKE']
        props.CREATE_QUERY = "CREATE TABLE IF NOT EXISTS " \
                                               "{table} ({fields}, " \
                                               "PRIMARY KEY({primary_keys}));"
        props.COLUMN = "{field} {type} {default}"
        props.SELECT_QUERY = "SELECT {fields} FROM " \
                                               "{table} {filters} LIMIT %s" \
                                               " OFFSET %s;"
        props.FILTERS = "WHERE {filters}"
        props.FILTER = "{column} {comparator} %s"
        props.DELETE_QUERY = "DELETE FROM {table} {filters};"
        props.INSERT_QUERY = "INSERT INTO {table} " \
                                               "({fields}) VALUES ({values});"
        props.UPDATE_QUERY = "UPDATE {table} SET {fields} " \
                                               "WHERE {column} = %s;"
        props.QUERY_TOTAL_COLUMN = "SELECT count({column}" \
                                                     ") FROM {table};"

        def predict(cls):
            TYPE_MAPPING = {
                "bool": "TINYINT(1)",
                "datetime": "DATETIME",
                "str": "VARCHAR(100)",
                "int": "INT",
                "float": "DECIMAL",
                "date": "DATE"
            }
            return TYPE_MAPPING.get(cls.__name__)

        props.predict_db_type.side_effect = predict
        return postgres_mock

    @fixture
    def generic_dao(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            table="test_table",
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity)
        return generic_dao

    @fixture
    def generic_dao2(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            table="test_table",
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity2)
        return generic_dao

    @fixture
    def generic_dao_with_child(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            table="test_table",
            prefix='',
            return_class=TestEntityWithChild)
        return generic_dao

    @fixture
    def entity(self):
        return TestEntity(id_="a022f42cfd2b40338bbb54a2894cba9f")

    def test_create_table(self, generic_dao, postgres_mock):
        generic_dao.create_table_if_not_exists()
        assert postgres_mock.query.called_with(
            'CREATE table IF NOT EXISTS test_table ('
            'id CHAR(32) NOT NULL, '
            'creation_datetime TIMESTAMP NULL, '
            'last_modified_datetime TIMESTAMP NULL, '
            'name VARCHAR(100) NULL, '
            'birthday DATE NULL, '
            'PRIMARY KEY(id)'
            ');'
        )

    def test_create_table_with_primary_key_null(self, generic_dao2,
                                                postgres_mock):
        generic_dao2.create_table_if_not_exists()
        assert postgres_mock.query.called_with(
            'CREATE table IF NOT EXISTS test_table ('
            'id CHAR(32) NOT NULL, '
            'creation_datetime TIMESTAMP NULL, '
            'last_modified_datetime TIMESTAMP NULL, '
            'name VARCHAR(100) NOT NULL, '
            'birthday DATE NULL, '
            'PRIMARY KEY(id, name)'
            ');'
        )

    def test_create_table_with_child(self, postgres_mock):
        generic_dao = GenericSQLDAO(database_type=postgres_mock,
                                    return_class=TestEntityWithChild,
                                    prefix='')
        generic_dao.create_table_if_not_exists()
        assert postgres_mock.query.called_with(
            'CREATE table IF NOT EXISTS test_entity_with_childs ('
            'id_ CHAR(32) NOT NULL, '
            'creation_datetime TIMESTAMP NULL, '
            'last_modified_datetime TIMESTAMP NULL, '
            'name VARCHAR(100) NULL, '
            'birthday DATE NULL, '
            'child_id_ CHAR(32) NULL, '
            'PRIMARY KEY(id_)'
            ');'
        )

    def test_init(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity)
        assert postgres_mock.mock_calls == [call()]
        assert generic_dao.database == postgres_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_extra_params(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity,
            pooled=False, host="changed")
        assert postgres_mock.mock_calls == [call(host="changed", pooled=False)]
        assert generic_dao.database == postgres_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_pooled(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity, pooled=True)
        assert postgres_mock.mock_calls == [call(pooled=True)]
        assert generic_dao.database == postgres_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_pooled_database_args(self, postgres_mock):
        generic_dao = GenericSQLDAO(
            database_type=postgres_mock,
            fields={"id_": "id",
                    "creation_datetime": "creation_datetime",
                    "last_modified_datetime": "last_modified_datetime",
                    "name": "name",
                    "birthday": "birthday"},
            return_class=TestEntity, pooled=True,
            database_args={"ssl_ca": "file"})
        assert postgres_mock.mock_calls == [
            call(pooled=True, database_args={"ssl_ca": "file"})]
        assert generic_dao.database == postgres_mock.return_value
        assert generic_dao.table == "test_entitys"
        assert generic_dao.fields == {"id_": "id",
                                      "creation_datetime": "creation_datetime",
                                      "last_modified_datetime":
                                          "last_modified_datetime",
                                      "name": "name",
                                      "birthday": "birthday"}
        assert generic_dao.return_class == TestEntity

    def test_init_parameter_gen(self, postgres_mock):
        generic_dao = GenericSQLDAO(database_type=postgres_mock,
                                    table='test_table', prefix='test_',
                                    return_class=TestEntity)
        assert generic_dao.fields == {"id_": "test_id_",
                                      "creation_datetime":
                                          "test_creation_datetime",
                                      "last_modified_datetime":
                                          "test_last_modified_datetime",
                                      "name": "test_name",
                                      "birthday": "test_birthday"}

    def test_init_parameter_gen_no_prefix(self, postgres_mock):
        generic_dao = GenericSQLDAO(database_type=postgres_mock,
                                    table='test_table',
                                    return_class=TestEntity)
        assert generic_dao.fields == {"id_": "test_entity_id_",
                                      "creation_datetime":
                                          "test_entity_creation_datetime",
                                      "last_modified_datetime":
                                          "test_entity_last_modified_datetime",
                                      "name": "test_entity_name",
                                      "birthday": "test_entity_birthday"}

    def test_get(self, generic_dao, postgres_mock):
        id_ = "a022f42cfd2b40338bbb54a2894cba9f"

        db = postgres_mock.return_value
        db.get_results.return_value = [[id_,
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]

        entity = generic_dao.get(id_=id_)

        assert postgres_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE id = %s LIMIT %s OFFSET %s;",
            ['a022f42cfd2b40338bbb54a2894cba9f', 1, 0]
        )
        assert entity == TestEntity(id_,
                                    datetime(2020, 7, 26, 12, 00, 00),
                                    datetime(2020, 7, 26, 12, 00, 00))

    def test_get_child(self, postgres_mock):
        generic_dao = GenericSQLDAO(database_type=postgres_mock,
                                    return_class=TestEntityWithChild,
                                    prefix='')
        id_ = "a022f42cfd2b40338bbb54a2894cba9f"

        db = postgres_mock.return_value
        db.get_results.return_value = [[id_,
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None,
                                        id_]]

        entity = generic_dao.get(id_=id_)

        assert postgres_mock.mock_calls[1] == call().query(
            "SELECT id_, creation_datetime, last_modified_datetime,"
            " name, birthday, child_id_ "
            "FROM test_entity_with_childs WHERE id_ = %s "
            "LIMIT %s OFFSET %s;",
            ['a022f42cfd2b40338bbb54a2894cba9f', 1, 0]
        )
        assert entity == TestEntityWithChild(
            id_,
            datetime(2020, 7, 26, 12, 00, 00),
            datetime(2020, 7, 26, 12, 00, 00),
            child=TestEntity(id_))

    def test_get_no_results(self, generic_dao, postgres_mock):
        id_ = "a022f42cfd2b40338bbb54a2894cba9f"

        db = postgres_mock.return_value
        db.get_results.return_value = None

        entity = generic_dao.get(id_=id_)

        assert postgres_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE id = %s LIMIT %s OFFSET %s;",
            ['a022f42cfd2b40338bbb54a2894cba9f', 1, 0]
        )
        assert entity is None

    @mark.parametrize("id_, error_type", [
        ("123", InvalidIDException),
        (123, InvalidIDTypeException)
    ])
    def test_get_invalid_id(self, generic_dao, id_, error_type):
        with raises(error_type):
            generic_dao.get(id_=id_)

    def test_get_all(self, generic_dao, postgres_mock):
        db = postgres_mock.return_value
        db.get_results.return_value = [["a022f42cfd2b40338bbb54a2894cba9f",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None],
                                       ["a59d80c8c5694e08a25b625a745d24e0",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Testando",
                                        None]]

        total, res = generic_dao.get_all(filters={"creation_datetime":
                                                      ['>',
                                                       "2020-01-01 00:00:00"],
                                                  "id_": ['LIKE', "123%"],
                                                  "name": "Anom"})
        assert postgres_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE creation_datetime > %s "
            "AND id LIKE %s "
            "AND name = %s "
            "LIMIT %s OFFSET %s;",
            ["2020-01-01 00:00:00", '123%', 'Anom', 20, 0]
        )

        assert postgres_mock.mock_calls[3] == call().query(
            'SELECT count(id) FROM test_table;'
        )

        assert res == [TestEntity("a022f42cfd2b40338bbb54a2894cba9f",
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  "Anom",
                                  None),
                       TestEntity("a59d80c8c5694e08a25b625a745d24e0",
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  datetime(2020, 7, 26, 12, 00, 00),
                                  "Testando",
                                  None)]

    def test_get_all_no_results(self, generic_dao, postgres_mock):
        db = postgres_mock.return_value
        db.get_results.return_value = None

        total, res = generic_dao.get_all(filters={"creation_datetime":
                                                      ['>',
                                                       "2020-01-01 00:00:00"],
                                                  "id_": ['LIKE', "123%"],
                                                  "name": "Anom"})
        assert postgres_mock.mock_calls[1] == call().query(
            "SELECT id, creation_datetime, last_modified_datetime,"
            " name, birthday "
            "FROM test_table WHERE creation_datetime > %s "
            "AND id LIKE %s "
            "AND name = %s "
            "LIMIT %s OFFSET %s;",
            ["2020-01-01 00:00:00", '123%', 'Anom', 20, 0]
        )

        assert total == 0 and res == []

    def test_get_all_no_filter(self, generic_dao, postgres_mock):
        generic_dao.get_all()
        assert postgres_mock.mock_calls[1] == call().query(
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

    def test_remove(self, generic_dao, postgres_mock, entity):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 1, 0
            return None

        db = postgres_mock.return_value
        db.get_results.return_value = [["a022f42cfd2b40338bbb54a2894cba9f",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]
        db.query.side_effect = is_delete_query
        generic_dao.remove(entity)
        assert postgres_mock.query.called_with(
            'DELETE FROM test_table WHERE id = %s;',
            ['a022f42cfd2b40338bbb54a2894cba9f']
        )

    def test_remove_with_filters(self, generic_dao, postgres_mock, entity):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 1, 0
            return None

        db = postgres_mock.return_value
        db.get_results.return_value = [["a022f42cfd2b40338bbb54a2894cba9f",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]
        db.query.side_effect = is_delete_query
        generic_dao.remove(entity, filters={"name": ["LIKE", "M%"]})
        assert postgres_mock.query.called_with(
            'DELETE FROM test_table WHERE id = %s;',
            ["a022f42cfd2b40338bbb54a2894cba9f"]
        )

    def test_remove_only_filters(self, generic_dao, postgres_mock, entity):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 1, 0
            return None

        db = postgres_mock.return_value
        db.get_results.return_value = None
        db.query.side_effect = is_delete_query
        generic_dao.remove(filters={"name": ["LIKE", "M%"]})
        assert postgres_mock.query.called_with(
            'DELETE FROM test_table WHERE name LIKE %s;',
            ['M%'])

    def test_remove_filters_no_rows(self, generic_dao, postgres_mock, entity):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 0, 0
            return None

        db = postgres_mock.return_value
        db.get_results.return_value = None
        db.query.side_effect = is_delete_query
        with raises(NoRowsAffectedException):
            generic_dao.remove(filters={"name": ["LIKE", "M%"]})

    def test_remove_fail(self, generic_dao, postgres_mock, entity):
        def is_delete_query(*args):
            if "DELETE" in args[0]:
                return 0, 0
            return None


        db = postgres_mock.return_value
        db.get_results.return_value = [["a022f42cfd2b40338bbb54a2894cba9f",
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        datetime(2020, 7, 26, 12, 00, 00),
                                        "Anom",
                                        None]]
        db.query.side_effect = is_delete_query
        with raises(NoRowsAffectedException):
            generic_dao.remove(entity)

    def test_remove_not_exist(self, generic_dao, postgres_mock, entity):
        db = postgres_mock.return_value
        db.get_results.return_value = None
        with raises(AssertionError):
            generic_dao.remove(entity)

    def test_remove_not_entity(self, generic_dao, postgres_mock):
        with raises(RuntimeError):
            generic_dao.remove("a022f42cfd2b40338bbb54a2894cba9f")

    @mark.parametrize("param", [12, '123', (123,), [123,], object()])
    def test_remove_filters_not_dict(self, generic_dao, param):
        with raises(RuntimeError):
            generic_dao.remove(filters=param)

    def test_create(self, generic_dao, postgres_mock, entity):
        def is_insert_query(*args):
            if "INSERT" in args[0]:
                return 1, 0
            return None

        db = postgres_mock.return_value
        db.get_results.return_value = None

        db.query.side_effect = is_insert_query

        id_ = generic_dao.create(entity)

        assert postgres_mock.mock_calls[3] == call().query(
            'INSERT INTO test_table (id, creation_datetime,'
            ' last_modified_datetime, name, birthday) '
            'VALUES (%s, %s, %s, %s, %s);', list(dict(entity).values()))
        assert id_ == entity.id_

    def test_create_with_child(self, generic_dao_with_child,
                               postgres_mock):
        def is_insert_query(*args):
            if "INSERT" in args[0]:
                return 1, 0
            return None

        entity = TestEntityWithChild()

        db = postgres_mock.return_value
        db.get_results.return_value = None

        db.query.side_effect = is_insert_query

        id_ = generic_dao_with_child.create(entity)

        assert postgres_mock.mock_calls[3] == call().query(
            'INSERT INTO test_table (id_, creation_datetime,'
            ' last_modified_datetime, name, birthday, child_id_) '
            'VALUES (%s, %s, %s, %s, %s, %s);', entity.get_db_values())
        assert id_ == entity.id_

    def test_create_exist(self, generic_dao, postgres_mock, entity):
        db = postgres_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        with raises(DuplicateEntityException):
            generic_dao.create(entity)

    def test_create_not_entity(self, generic_dao, postgres_mock):
        with raises(NotEntityException):
            generic_dao.create("a022f42cfd2b40338bbb54a2894cba9f")

    def test_create_no_rows_affected(self, generic_dao, postgres_mock, entity):
        db = postgres_mock.return_value
        db.query.return_value = 0, 0
        with raises(NoRowsAffectedException):
            generic_dao.create(entity)

    def test_update_not_entity(self, generic_dao, postgres_mock):
        with raises(TypeError):
            generic_dao.update("a022f42cfd2b40338bbb54a2894cba9f")

    def test_update_entity_not_exists(self, generic_dao, postgres_mock, entity):
        db = postgres_mock.return_value
        db.get_results.return_value = None
        with raises(AssertionError):
            generic_dao.update(entity)

    def test_update(self, generic_dao, postgres_mock, entity):
        db = postgres_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        db.query.return_value = 1, 0
        entity.birthday = date(1998, 12, 21)
        entity.name = "MyTestName"
        sleep(1)
        generic_dao.update(entity)
        assert postgres_mock.mock_calls[5] == call().query(
            'UPDATE test_table SET id=%s, creation_datetime=%s, '
            'last_modified_datetime=%s, name=%s, birthday=%s '
            'WHERE id = %s;', list(dict(entity).values()) + [entity.id_]
        )
        assert entity.creation_datetime < entity.last_modified_datetime

    def test_update_with_child(self, generic_dao_with_child,
                               postgres_mock):
        entity = TestEntityWithChild()
        db = postgres_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        db.query.return_value = 1, 0
        entity.birthday = date(1998, 12, 21)
        entity.name = "MyTestName"
        sleep(1)
        generic_dao_with_child.update(entity)
        assert postgres_mock.mock_calls[5] == call().query(
            'UPDATE test_table SET id_=%s, creation_datetime=%s, '
            'last_modified_datetime=%s, name=%s, birthday=%s, child_id_=%s '
            'WHERE id_ = %s;', entity.get_db_values() + [entity.id_]
        )
        assert entity.creation_datetime < entity.last_modified_datetime

    def test_update_no_rows_affected(self, generic_dao, postgres_mock, entity):
        db = postgres_mock.return_value
        db.get_results.return_value = [list(entity.__dict__.values())]
        db.query.return_value = 0, 0
        with raises(NoRowsAffectedException):
            generic_dao.update(entity)

    def test_close(self, generic_dao, postgres_mock):
        db = postgres_mock.return_value
        generic_dao.close()
        assert db.mock_calls == [call.close()]

    def test_generate_filters(self, generic_dao):
        filters = generic_dao.generate_filters(filters={
            "id_": "a022f42cfd2b40338bbb54a2894cba9f",
            "creation_datetime": [">", "2020-1-1"]})
        assert filters == ("WHERE id = %s AND creation_datetime > %s",
                           ["a022f42cfd2b40338bbb54a2894cba9f", "2020-1-1"])

    def test_generate_filter(self, generic_dao):
        filters = generic_dao.generate_filters(filters={
            "id_": "a022f42cfd2b40338bbb54a2894cba9f"})
        assert filters == ("WHERE id = %s",
                           ["a022f42cfd2b40338bbb54a2894cba9f"])

    def test_generate_filters_none(self, generic_dao):
        with raises(ValueError):
            generic_dao.generate_filters(None)

    @mark.parametrize("param", [1, "test", 1.0, [1, 'test'], (1, 2)])
    def test_generate_filters_not_dict(self, generic_dao, param):
        with raises(TypeError):
            generic_dao.generate_filters(param)
