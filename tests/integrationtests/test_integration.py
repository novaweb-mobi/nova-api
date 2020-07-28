from dataclasses import dataclass, field
from datetime import date

from pytest import fixture, mark

from Entity import Entity
from GenericSQLDAO import GenericSQLDAO


@dataclass
class User(Entity):
    first_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    last_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    email: str = field(default=None, metadata={"type": "CHAR(255)"})
    active: bool = True
    birthday: date = None


class UserDAO(GenericSQLDAO):
    TABLE = 'usuarios'

    def __init__(self, db=None):
        super(UserDAO, self).__init__(db=db, table=UserDAO.TABLE,
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
        user_dao.db.query("show tables;")
        assert user_dao.db.get_results() is None
        user_dao.create_table_if_not_exists()
        user_dao.db.query("show tables;")
        results = user_dao.db.get_results()[0]
        assert user_dao.TABLE in results

    @mark.order2
    def test_create_row(self, user_dao, user):
        user_dao.create(user)
        assert user_dao.get(user.id_) == user

    @mark.order3
    def test_update(self, user_dao, user):
        user.birthday = date(1998, 12, 21)
        user_dao.update(user)
        assert user_dao.get(user.id_).birthday == date(1998, 12, 21)

    @mark.order4
    def test_delete(self, user_dao, user):
        user_dao.remove(user)
        assert user_dao.get(user.id_) is None
