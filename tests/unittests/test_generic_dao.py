from dataclasses import dataclass
from typing import List

from pytest import mark, raises

from nova_api.dao import GenericDAO
from nova_api.entity import Entity
from nova_api.exceptions import DuplicateEntityException, \
    EntityNotFoundException, InvalidFiltersException, InvalidIDException, \
    InvalidIDTypeException, \
    NotEntityException


@dataclass
class TestEntity(Entity):
    name: str = ""


@dataclass
class TestEntity2(Entity):
    first_name: str = ""


class MyDAO(GenericDAO):
    def __init__(self, **kwargs):
        super().__init__(return_class=TestEntity, **kwargs)

    def get(self, id_):
        super().get(id_)

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        super().get_all(length, offset, filters)

    def remove(self, entity: Entity = None, filters: dict = None) -> int:
        return super().remove(entity, filters)

    def create(self, entity: Entity) -> str:
        return super().create(entity)

    def update(self, entity: Entity) -> str:
        super().update(entity)

    @classmethod
    def predict_db_type(cls, cls_to_predict):
        super().predict_db_type(cls_to_predict)

    def close(self):
        super().close()


class MyDAOWithEntries(GenericDAO):
    def __init__(self, **kwargs):
        super().__init__(return_class=TestEntity, **kwargs)

    def get(self, id_):
        super().get(id_)
        return TestEntity(id_=id_)

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        super().get_all(length, offset, filters)
        return 1, [TestEntity()]

    def remove(self, entity: Entity = None, filters: dict = None) -> int:
        return super().remove(entity, filters)

    def create(self, entity: Entity) -> str:
        return super().create(entity)

    def update(self, entity: Entity) -> str:
        return super().update(entity)

    @classmethod
    def predict_db_type(cls, cls_to_predict):
        super().predict_db_type(cls_to_predict)

    def close(self):
        super().close()


class MySecondDAO(GenericDAO):
    pass


class TestGenericDAO:
    def test_init(self):
        with raises(TypeError):
            GenericDAO()

    def test_subclass_no_implementation(self):
        with raises(TypeError):
            MySecondDAO()

    @mark.parametrize("id_", [
        1,
        True,
        [],
        {},
        1.0
    ])
    def test_get_should_raise_invalid_type(self, id_):
        dao = MyDAO()
        with raises(InvalidIDTypeException):
            dao.get(id_)

    @mark.parametrize("id_", [
        "12345678901234567890123456789012",
        'a0fa7c92-1c73-11ec-b226-24ee9a65a1ee',
        "ID",
        "44444444444444444444444444444444",
        '671b63e1-64a7-4c50-8788-a3bb34da87f3'  # We expect UUID's without -
    ])
    def test_get_should_raise_invalid_uuid(self, id_):
        dao = MyDAO()
        with raises(InvalidIDException):
            dao.get(id_)

    def test_get_all(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.get_all()

    @mark.parametrize("arg", [
        1,
        None,
        TestEntity2(),
        1.0,
        True
    ])
    def test_remove_raise_not_ent_if_not_ent(self, arg):
        dao = MyDAO()
        with raises(NotEntityException):
            dao.remove(arg)

    def test_remove_not_found_should_raise_ent_not_found(self):
        dao = MyDAO()
        with raises(EntityNotFoundException):
            dao.remove(TestEntity())

    def test_remove_should_return_0(self):
        dao = MyDAOWithEntries()
        assert dao.remove(TestEntity()) == 0

    def test_remove_should_return_0_with_filters(self):
        dao = MyDAOWithEntries()
        assert dao.remove(filters={"name": "ToRemove"}) == 0

    @staticmethod
    @mark.parametrize("filters", [
        "",
        1,
        True,
        1.0,
        []
    ])
    def test_remove_filters_not_dict(filters):
        dao = MyDAO()
        with raises(InvalidFiltersException):
            dao.remove(filters=filters)

    @staticmethod
    @mark.parametrize("arg", [
        "",
        1,
        True,
        1.0,
        TestEntity2()
    ])
    def test_should_raise_not_ent_exc_if_create_not_entity(arg):
        dao = MyDAO()
        with raises(NotEntityException):
            dao.create(arg)

    @staticmethod
    def test_should_raise_if_entity_already_exists(mocker):
        existing_ent = TestEntity(id_="00000000000000000000000000000000")
        mocker.patch.object(MyDAO, 'get', return_value=existing_ent)
        dao = MyDAO()
        with raises(DuplicateEntityException):
            dao.create(existing_ent)

    @staticmethod
    def test_should_return_id_if_ok(mocker):
        existing_ent = TestEntity(id_="00000000000000000000000000000000")
        mocker.patch.object(MyDAO, 'get', return_value=None)
        dao = MyDAO()
        assert dao.create(existing_ent) == existing_ent.id_

    @mark.parametrize("arg", [
        1,
        None,
        TestEntity2(),
        1.0,
        True
    ])
    def test_update_not_entity_should_raise_not_ent(self, arg):
        dao = MyDAO()
        with raises(NotEntityException):
            dao.update(arg)

    def test_update_not_found_should_raise_ent_not_found(self):
        dao = MyDAO()
        with raises(EntityNotFoundException):
            dao.update(TestEntity())

    def test_update_should_return_empty(self):
        dao = MyDAOWithEntries()
        assert dao.update(TestEntity()) == ""

    def test_close(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.close()
