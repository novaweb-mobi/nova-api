import os
from dataclasses import dataclass
from datetime import date
from unittest import mock
from unittest.mock import Mock

from pytest import fixture

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
                pass

            pass

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
    def test_should_set_return_class(mongo_mock):
        dao = MongoDAO(return_class=TestEntity)
        assert dao.return_class == TestEntity

    @staticmethod
    def test_should_set_collection_based_on_return_class(mongo_mock):
        dao = MongoDAO(return_class=TestEntity)
        assert dao.collection == "test_entitys"

    @staticmethod
    def test_should_use_collection(mongo_mock):
        dao = MongoDAO(return_class=TestEntity, collection="test")
        assert dao.collection == "test"

    @staticmethod
    def test_should_set_prefix_based_on_return_class(mongo_mock):
        dao = MongoDAO(return_class=TestEntity)
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
    def test_should_set_fields_from_return_class(mongo_mock):
        dao = MongoDAO(return_class=TestEntity)
        assert dao.fields == {
            "id_": "test_entity_id_",
            "creation_datetime": "test_entity_creation_datetime",
            "last_modified_datetime": "test_entity_last_modified_datetime",
            "name": "test_entity_name",
            "birthday": "test_entity_birthday"
        }

    @staticmethod
    @fixture
    def mongo_mock(mocker):
        mock = mocker.patch("dao.mongo_dao.MongoClient")
        return mock
