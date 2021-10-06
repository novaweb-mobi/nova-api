import datetime
from unittest.mock import call

from bson.objectid import ObjectId
from pytest import fixture, mark, raises

from dao.mongo_dao import MongoDAO
from nova_api.exceptions import DuplicateEntityException, \
    EntityNotFoundException, InvalidFiltersException, NotEntityException
from tests.unittests import TestEntity, TestEntity2


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
        mongo_mock.assert_called_with(host='mongodb://root:root@localhost')
        assert dao.client == mongo_mock.return_value

    @staticmethod
    def test_should_use_host(mongo_mock):
        dao = MongoDAO(host="test.url")
        mongo_mock.assert_called_with(host='mongodb://root:root@test.url')
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
            "id_": "test_entity_id_",
            "creation_datetime": "test_entity_creation_datetime",
            "last_modified_datetime": "test_entity_last_modified_datetime",
            "name": "test_entity_name",
            "birthday": "test_entity_birthday"
        }

    @staticmethod
    def test_should_call_insert_one_if_create_valid(dao, test_entity):
        dao.cursor.find_one.return_value = None
        dao.create(test_entity)
        print(dao.database["test_entitys"].insert_one.mock_calls)
        dao.database["test_entitys"].insert_one.assert_has_calls(
            [call({
                'test_entity_id_': '671b63e164a74c508788a3bb34da87f3',
                'test_entity_creation_datetime': test_entity.creation_datetime,
                'test_entity_last_modified_datetime':
                    test_entity.last_modified_datetime,
                'test_entity_name': 'Test',
                'test_entity_birthday': datetime.datetime.combine(test_entity.birthday,
                                                         datetime.time())})],
            any_order=True)

    @staticmethod
    def test_should_return_id_if_ok(test_entity, dao):
        dao.cursor.find_one.return_value = None
        assert dao.create(test_entity) == test_entity.id_

    @staticmethod
    def test_should_raise_duplicate_if_entity_exists(dao, test_entity):
        dao.cursor.find_one.return_value = {
            "_id": ObjectId(),
            'test_entity_id_': '671b63e164a74c508788a3bb34da87f3',
            'test_entity_creation_datetime': test_entity.creation_datetime,
            'test_entity_last_modified_datetime':
                test_entity.last_modified_datetime,
            'test_entity_name': 'Another Ent',
            'test_entity_birthday': test_entity.birthday}
        with raises(DuplicateEntityException):
            dao.create(test_entity)
        dao.database["test_entitys"].insert_one.assert_not_called()

    @staticmethod
    @mark.parametrize("ent", [
        datetime.datetime(1, 1, 1),
        1,
        1.0,
        True,
        [],
        {},
        TestEntity2
    ])
    def test_should_raise_not_ent_if_not_entity(dao, ent):
        with raises(NotEntityException):
            dao.create(ent)
        dao.database["test_entitys"].insert_one.assert_not_called()

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
        db_dict = dao._prepare_db_dict(test_entity)
        db_dict.update({"_id": ObjectId()})
        dao.cursor.find.return_value = Cursor([db_dict])
        dao.cursor.count_documents.return_value = 1

        res = dao.get_all()
        dao.cursor.find.assert_called_with({}, limit=20, skip=0)
        dao.cursor.count_documents.assert_called_with({})

        assert res == (1, [
            test_entity])

    @staticmethod
    def test_get_all_with_filter_should_use_filter(dao, test_entity):
        db_dict = dao._prepare_db_dict(test_entity)
        db_dict.update({"_id": ObjectId()})
        dao.cursor.find.return_value = Cursor([db_dict])
        dao.cursor.count_documents.return_value = 1

        res = dao.get_all(filters={"name": "Test"})
        dao.cursor.find.assert_called_with({"test_entity_name": "Test"},
                                           limit=20, skip=0)
        dao.cursor.count_documents.assert_called_with({})

        assert res == (1, [
            test_entity])

    @staticmethod
    def test_get_should_call_find_one_with_id_filter(dao):
        dao.cursor.find_one.return_value = None
        res = dao.get('671b63e164a74c508788a3bb34da87f3')

        dao.cursor.find_one.assert_called_with(
            {"test_entity_id_": "671b63e164a74c508788a3bb34da87f3"})
        assert res is None

    @staticmethod
    def test_get_should_return_entity(dao, test_entity):
        dao.cursor.find_one.return_value = {
            "_id": ObjectId(),
            'test_entity_id_': '671b63e164a74c508788a3bb34da87f3',
            'test_entity_creation_datetime': test_entity.creation_datetime,
            'test_entity_last_modified_datetime':
                test_entity.last_modified_datetime,
            'test_entity_name': 'Test',
            'test_entity_birthday': test_entity.birthday}

        res = dao.get('671b63e164a74c508788a3bb34da87f3')

        dao.cursor.find_one.assert_called_with(
            {"test_entity_id_": "671b63e164a74c508788a3bb34da87f3"})
        assert res == test_entity

    @staticmethod
    def test_close(dao, mongo_mock):
        dao.close()
        mongo_mock.return_value.close.assert_called()

    @staticmethod
    def test_delete_with_no_arguments_should_raise_no_ent(dao, mongo_mock):
        with raises(NotEntityException):
            dao.remove(None)
        dao.cursor.delete_one.assert_not_called()

    @staticmethod
    def test_delete_with_invalid_filters_should_raise(dao, mongo_mock):
        with raises(InvalidFiltersException):
            dao.remove(filters=[])
        dao.cursor.delete_one.assert_not_called()

    @staticmethod
    def test_delete_entity_not_in_database_should_raise(dao, mongo_mock,
                                                        test_entity):
        dao.cursor.find_one.return_value = None
        with raises(EntityNotFoundException):
            dao.remove(test_entity)
        dao.cursor.delete_one.assert_not_called()

    @staticmethod
    def test_delete_entity_should_delete(dao, mongo_mock,
                                         test_entity):
        dao.cursor.find_one.return_value = {
            "_id": ObjectId(),
            'test_entity_id_': '671b63e164a74c508788a3bb34da87f3',
            'test_entity_creation_datetime': test_entity.creation_datetime,
            'test_entity_last_modified_datetime':
                test_entity.last_modified_datetime,
            'test_entity_name': 'Test',
            'test_entity_birthday': test_entity.birthday
        }

        assert dao.remove(test_entity) == 1

        dao.cursor.delete_one.assert_called_with(
            {"test_entity_id_": test_entity.id_}
        )

    @staticmethod
    def test_delete_filters_should_delete(dao, mongo_mock,
                                          test_entity):
        dao.cursor.delete_many.return_value.deleted_count = 3
        assert dao.remove(filters={"name": "Test"}) == 3

        dao.cursor.delete_many.assert_called_with(
            {"test_entity_name": "Test"}
        )

    @staticmethod
    @mark.parametrize("ent", [
        datetime.datetime(1, 1, 1),
        1,
        1.0,
        True,
        [],
        {},
        TestEntity2
    ])
    def test_should_raise_not_ent_if_not_entity_update(dao, ent):
        with raises(NotEntityException):
            dao.update(ent)
        dao.database["test_entitys"].update_one.assert_not_called()

    @staticmethod
    def test_update_entity_not_in_database_should_raise(dao, mongo_mock,
                                                        test_entity):
        dao.cursor.find_one.return_value = None
        with raises(EntityNotFoundException):
            dao.update(test_entity)
        dao.cursor.update_one.assert_not_called()

    @staticmethod
    def test_update_entity_should_update(dao, mongo_mock,
                                         test_entity):
        dao.cursor.find_one.side_effect = [{
            "_id": ObjectId(),
            'test_entity_id_': '671b63e164a74c508788a3bb34da87f3',
            'test_entity_creation_datetime': test_entity.creation_datetime,
            'test_entity_last_modified_datetime':
                test_entity.last_modified_datetime,
            'test_entity_name': 'Test',
            'test_entity_birthday': test_entity.birthday
        }, {
            "_id": ObjectId(),
            'test_entity_id_': '671b63e164a74c508788a3bb34da87f3',
            'test_entity_creation_datetime': test_entity.creation_datetime,
            'test_entity_last_modified_datetime':
                test_entity.last_modified_datetime,
            'test_entity_name': 'Test',
            'test_entity_birthday': test_entity.birthday
        }]
        old_last_modified = test_entity.last_modified_datetime

        test_entity.name = "Update test"

        assert dao.update(test_entity) == test_entity.id_
        assert test_entity.last_modified_datetime != old_last_modified

        dao.cursor.update_one.assert_called_with(
            {'test_entity_id_': '671b63e164a74c508788a3bb34da87f3'},
            {"$set": {"test_entity_name": "Update test",
                      "test_entity_last_modified_datetime":
                          test_entity.last_modified_datetime
                      }}
        )

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
        return TestEntity(id_="671b63e164a74c508788a3bb34da87f3",
                          creation_datetime=datetime.datetime(1, 1, 1),
                          last_modified_datetime=datetime.datetime(1, 1, 1),
                          name="Test",
                          birthday=datetime.datetime(2, 2, 2))


class Cursor:
    def __init__(self, data: list):
        self.data = data

    def __iter__(self):
        yield self.data.pop()
