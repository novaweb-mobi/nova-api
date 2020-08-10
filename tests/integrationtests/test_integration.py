from dataclasses import dataclass, field
from datetime import date
from time import sleep

from pytest import fixture, mark, raises

from nova_api.entity import Entity
from nova_api.generic_dao import GenericSQLDAO


@dataclass
class User(Entity):
    first_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    last_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    email: str = field(default=None, metadata={"type": "CHAR(255)"})
    active: bool = True
    birthday: date = None


class UserDAO(GenericSQLDAO):
    table = 'usuarios'

    def __init__(self, database=None):
        super(UserDAO, self).__init__(database=database, table=UserDAO.TABLE,
                                      return_class=User, prefix='')


class TestIntegration:
    @fixture
    def user_dao(self):
        return UserDAO()

    @fixture
    def user(self):
        return User(
            id_="12345678901234567890123456789012",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )

    @mark.order1
    def test_create_table_not_exists(self, user_dao):
        user_dao.database.query("show tables;")
        assert user_dao.database.get_results() is None
        user_dao.create_table_if_not_exists()
        user_dao.database.query("show tables;")
        results = user_dao.database.get_results()[0]
        assert user_dao.TABLE in results

    @mark.order2
    def test_create_row(self, user_dao, user):
        user_dao.create(user)
        assert user_dao.get(user.id_) == user

    @mark.order3
    def test_create_existent(self, user_dao, user):
        with raises(AssertionError):
            user_dao.create(user)

    @mark.order4
    def test_update(self, user_dao, user):
        last_modified_old = user.last_modified_datetime
        sleep(1)
        user.birthday = date(1998, 12, 21)
        assert user_dao.get(user.id_).birthday != date(1998, 12, 21)
        user_dao.update(user)
        updated_user = user_dao.get(user.id_)
        assert updated_user.birthday == date(1998, 12, 21)
        assert updated_user.last_modified_datetime > last_modified_old

    @mark.order5
    def test_delete(self, user_dao, user):
        user_dao.remove(user)
        assert user_dao.get(user.id_) is None

    def test_get_not_existent(self, user_dao):
        assert user_dao.get("12345678901234567890123456789023") is None

    def test_update_not_existent(self, user_dao):
        user = User(id_="12345678901234567890123456789023")
        with raises(AssertionError):
            user_dao.update(user)

    def test_delete_not_existent(self, user_dao):
        user = User(id_="12345678901234567890123456789023")
        with raises(AssertionError):
            user_dao.remove(user)

    @mark.order6
    def test_filter_date(self, user_dao):
        u1 = User(birthday=date(1998, 12, 21))
        u2 = User(birthday=date(2005, 11, 21), first_name="Jose")
        user_dao.create(u1)
        user_dao.create(u2)
        results = user_dao.get_all(
            filters={"birthday": ['>', "2005-1-1"]})[1]
        user_dao.remove(u1)
        user_dao.remove(u2)
        assert len(results) == 1

    @mark.order7
    def test_filter_name(self, user_dao):
        u1 = User(birthday=date(1998, 12, 21))
        u2 = User(birthday=date(2005, 11, 21), first_name="Jose")
        user_dao.create(u1)
        user_dao.create(u2)
        results = user_dao.get_all(
            filters={"first_name": ["LIKE", "J%"]})[1]
        user_dao.remove(u1)
        user_dao.remove(u2)
        assert len(results) == 1

    @mark.last
    def test_drop_table(self, user_dao):
        user_dao.database.query("DROP table usuarios;")
        with raises(Exception):
            user_dao.get("12345678901234567890123456789012")