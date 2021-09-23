import datetime
from dataclasses import dataclass
from datetime import date
from unittest.mock import call

from pytest import fixture, mark

from dao.mongo_dao import MongoDAO
from entity import Entity


@dataclass
class TestEntity(Entity):
    name: str = "Anom"
    birthday: date = None


class TestMongoDAO:
    @staticmethod
    def test_should_set_database_as_mongo_client_database(mongo_mock):
        dao = MongoDAO()
        assert dao.client == mongo_mock.return_value
        assert dao.database == mongo_mock.return_value["TEST"]

    @staticmethod
    def test_shouldnt_create_new_database_instance_if_received(mongo_mock):
        class TestDatabase:
            def __getitem__(self, item):
                return {"entitys": None}

        database = TestDatabase()
        dao = MongoDAO(database_instance=database)
        assert dao.client == database
        mongo_mock.assert_not_called()

    @staticmethod
    def test_should_use_default_values(mongo_mock):
        dao = MongoDAO()
        mongo_mock.assert_called_with(host='localhost')
        assert dao.client == mongo_mock.return_value

    @staticmethod
    def test_should_use_host(mongo_mock):
        dao = MongoDAO(host="test.url")
        mongo_mock.assert_called_with(host='test.url')
        assert dao.client == mongo_mock.return_value

    @staticmethod
    def test_should_use_user_and_password(mongo_mock):
        dao = MongoDAO(user="test", password="23")
        mongo_mock.assert_called_with(host='mongodb://test:23@localhost')
        assert dao.client == mongo_mock.return_value

    @staticmethod
    def test_should_scape_special_chars(mongo_mock):
        dao = MongoDAO(user="test", password="23:\+@0")
        mongo_mock.assert_called_with(
            host='mongodb://test:23%3A%5C%2B%400@localhost')
        assert dao.client == mongo_mock.return_value

    @staticmethod
    def test_should_set_return_class(dao):
        assert dao.return_class == TestEntity

    @staticmethod
    def test_should_set_collection_based_on_return_class(dao):
        assert dao.collection == "test_entitys"

    @staticmethod
    def test_should_use_collection(mongo_mock):
        dao = MongoDAO(return_class=TestEntity, collection="test")
        assert dao.collection == "test"

    @staticmethod
    def test_should_set_prefix_based_on_return_class(dao):
        assert dao.prefix == "test_entity_"

    @staticmethod
    def test_should_use_prefix(mongo_mock):
        dao = MongoDAO(return_class=TestEntity, prefix="test")
        assert dao.prefix == "test"

    @staticmethod
    def test_should_use_empty_prefix(mongo_mock):
        dao = MongoDAO(return_class=TestEntity, prefix="")
        assert dao.prefix == ""

    @staticmethod
    def test_should_set_fields_from_return_class(dao):
        assert dao.fields == {
            "id_": "_id",
            "creation_datetime": "test_entity_creation_datetime",
            "last_modified_datetime": "test_entity_last_modified_datetime",
            "name": "test_entity_name",
            "birthday": "test_entity_birthday"
        }

    @staticmethod
    def test_should_call_insert_one_if_create_valid(dao, test_entity):
        dao.create(test_entity)
        print(dao.database["test_entitys"].insert_one.mock_calls)
        dao.database["test_entitys"].insert_one.assert_has_calls(
            [call({
                '_id': '12345678901234567890123456789012',
                'test_entity_creation_datetime': test_entity.creation_datetime,
                'test_entity_last_modified_datetime':
                    test_entity.last_modified_datetime,
                'test_entity_name': 'Test',
                'test_entity_birthday': test_entity.birthday})],
            any_order=True)

    @staticmethod
    def test_get_all_should_call_find(dao):
        dao.get_all()
        dao.cursor.find.assert_called()

    @staticmethod
    @mark.parametrize("length, offset", [
        (10, 2),
        (20, 0)
    ])
    def test_get_all_should_use_limit_and_skip_and_empty_filters(dao,
                                                                 length,
                                                                 offset):
        dao.get_all(length=length, offset=offset)
        dao.cursor.find.assert_called_with({}, limit=length, skip=offset)

    @staticmethod
    @mark.parametrize("length, offset", [
        (10, 2),
        (20, 0)
    ])
    def test_get_all_should_use_limit_and_skip_and_empty_filters(dao,
                                                                 length,
                                                                 offset):
        dao.get_all(length=length, offset=offset)
        dao.cursor.find.assert_called_with({}, limit=length, skip=offset)

    @staticmethod
    def test_get_all_no_result_should_return_empty(dao):
        dao.cursor.count_documents.return_value = 0

        res = dao.get_all()
        dao.cursor.find.assert_called_with({}, limit=20, skip=0)
        dao.cursor.count_documents.assert_not_called()
        assert res == (0, [])

    @staticmethod
    def test_get_all_with_result_should_return_elements(dao, test_entity):
        dao.cursor.find.return_value = Cursor([
            dao.prepare_db_dict(test_entity)])
        dao.cursor.count_documents.return_value = 1

        res = dao.get_all()
        dao.cursor.find.assert_called_with({}, limit=20, skip=0)
        dao.cursor.count_documents.assert_called_with({})

        assert res == (1, [
            test_entity])

    @staticmethod
    def test_get_all_with_filter_should_use_filter(dao, test_entity):
        dao.cursor.find.return_value = Cursor([
            dao.prepare_db_dict(test_entity)])
        dao.cursor.count_documents.return_value = 1

        res = dao.get_all(filters={"name": "Test"})
        dao.cursor.find.assert_called_with({"name": "Test"}, limit=20, skip=0)
        dao.cursor.count_documents.assert_called_with({})

        assert res == (1, [
            test_entity])

    @staticmethod
    @fixture
    def dao(mongo_mock):
        return MongoDAO(return_class=TestEntity)

    @staticmethod
    @fixture
    def mongo_mock(mocker):
        mock = mocker.patch("dao.mongo_dao.MongoClient")
        return mock

    @staticmethod
    @fixture
    def test_entity():
        return TestEntity(id_="12345678901234567890123456789012",
                          creation_datetime=datetime.datetime(1, 1, 1),
                          last_modified_datetime=datetime.datetime(1, 1, 1),
                          name="Test",
                          birthday=datetime.datetime(2, 2, 2))


class Cursor:
    def __init__(self, data: list):
        self.data = data

    def __iter__(self):
        yield self.data.pop()
