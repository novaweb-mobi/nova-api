from abc import ABC
from typing import List

from nova_api.entity import Entity
from pytest import raises

from nova_api.dao import GenericDAO


class MyDAO(GenericDAO):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def get(self, id_):
        super(MyDAO, self).get(id_)
    
    def get_all(self, length: int = 20, offset: int = 0,
                filters: dict = None) -> (int, List[Entity]):
        super(MyDAO, self).get_all(length, offset, filters)
        
    def remove(self, entity: Entity) -> None:
        super(MyDAO, self).remove(entity)
    
    def create(self, entity: Entity) -> str:
        super(MyDAO, self).create(entity)
        
    def update(self, entity: Entity) -> str:
        super(MyDAO, self).update(entity)
        
    def create_table_if_not_exists(self):
        super(MyDAO, self).create_table_if_not_exists()
        
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

    def test_create(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.create(None)

    def test_update(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.update(None)

    def test_create_table_if_not_exists(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.create_table_if_not_exists()

    def test_close(self):
        dao = MyDAO()
        with raises(NotImplementedError):
            dao.close()