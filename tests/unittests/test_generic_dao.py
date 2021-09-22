from abc import ABC
from dataclasses import dataclass
from typing import List

from pytest import raises, mark

from nova_api.entity import Entity
from nova_api.dao import GenericDAO
from nova_api.exceptions import DuplicateEntityException, NotEntityException


@dataclass
class TestEntity(Entity):
    name: str = ""


class MyDAO(GenericDAO):
    def __init__(self, **kwargs):
        super().__init__(return_class=TestEntity, **kwargs)

    def get(self, id_):
        super(MyDAO, self).get(id_)

    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        super(MyDAO, self).get_all(length, offset, filters)

    def remove(self, entity: Entity) -> None:
        super(MyDAO, self).remove(entity)

    def create(self, entity: Entity) -> str:
        return super(MyDAO, self).create(entity)

    def update(self, entity: Entity) -> str:
        super(MyDAO, self).update(entity)

    @classmethod
    def predict_db_type(cls, cls_to_predict):
        super(MyDAO, cls).predict_db_type(cls_to_predict)

    def close(self):
        super(MyDAO, self).close()


class MySecondDAO(GenericDAO):
    pass


class TestGenericDAO:
    def test_init(self):
        with raises(TypeError):
            GenericDAO()

    def test_subclass_no_implementation(self):
        with raises(TypeError):
            MySecondDAO()

    def test_get(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.get("test_id")

    def test_get_all(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.get_all()

    def test_remove(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.remove(None)

    @staticmethod
    @mark.parametrize("arg", [
        "",
        1,
        True,
        1.0
    ])
    def test_should_raise_NotEntityException_if_create_not_entity(arg):
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

    def test_update(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.update(None)

    def test_close(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.close()
