from dataclasses import dataclass, field
from datetime import date
from time import sleep

from pytest import fixture, mark, raises

from dao.mongo_dao import MongoDAO
from nova_api.entity import Entity
from nova_api.exceptions import DuplicateEntityException, \
    EntityNotFoundException


@dataclass
class User(Entity):
    first_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    last_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    email: str = field(default=None, metadata={"type": "CHAR(255)"})
    active: bool = True
    birthday: date = None


class UserDAO(MongoDAO):
    def __init__(self, **kwargs):
        super(UserDAO, self).__init__(return_class=User, prefix='',
                                      **kwargs)


@dataclass
class Payment(Entity):
    value: int = 0
    payer: User = None
    receiver: User = None


class PaymentDAO(MongoDAO):
    def __init__(self, **kwargs):
        super(PaymentDAO, self).__init__(return_class=Payment, prefix='',
                                         **kwargs)


class TestIntegrationMongo:
    @mark.parametrize("dao, ent", [
        (UserDAO, User(
            id_="150596d218f14b0a8f6c8c12dd9eb23a",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )),
        (PaymentDAO, Payment(
            id_="77f3777929e1417c96c747c312f4325f",
            value=10,
            payer=User(id_="150596d218f14b0a8f6c8c12dd9eb23a"),
            receiver=User(id_="12345678901234567890123456789013")
        )),
    ])
    def test_create_row(self, dao, ent):
        dao = dao()
        dao.create(ent)
        _, created_ents = dao.get_all()
        dao.remove(ent)
        dao.close()
        assert created_ents[0] == ent
        assert dao.get_all()[0] == 0

    @mark.parametrize("dao, ent", [
        (UserDAO, User(
            id_="150596d218f14b0a8f6c8c12dd9eb23a",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )),
        (PaymentDAO, Payment(
            id_="77f3777929e1417c96c747c312f4325f",
            value=10,
            payer=User(id_="150596d218f14b0a8f6c8c12dd9eb23a"),
            receiver=User(id_="12345678901234567890123456789013")
        )),
    ])
    def test_create_existent(self, dao, ent):
        dao = dao()
        try:
            dao.create(ent)
        except DuplicateEntityException:
            pass
        assert dao.get(ent.id_) == ent
        with raises(DuplicateEntityException):
            dao.create(ent)
        dao.close()

    @mark.parametrize("dao, ent", [
        (UserDAO, User(id_="150596d218f14b0a8f6c8c12dd9eb23a")),
        (PaymentDAO, Payment(id_="77f3777929e1417c96c747c312f4325f")),
    ])
    def test_delete(self, dao, ent):
        dao = dao()
        try:
            dao.create(ent)
        except DuplicateEntityException:
            assert dao.get(ent.id_) is not None
        dao.remove(ent)
        assert dao.get(ent.id_) is None
        dao.close()

    def test_delete_not_existent(self, user_dao):
        try:
            user = User(id_="4b918d8a2add4857ae2a5b29f58f32df")
            with raises(EntityNotFoundException):
                user_dao.remove(user)
        finally:
            user_dao.close()

    def test_delete_filters(self, user_dao):
        u1 = User(first_name="John", last_name="Doe")
        u2 = User(first_name="John", last_name="Jorge")

        user_dao.create(u1)
        user_dao.create(u2)

        assert user_dao.get_all()[0] == 2
        assert user_dao.remove(filters={"first_name": "John"}) == 2
        assert user_dao.get_all()[0] == 0
        user_dao.close()

    def test_get_not_existent(self, user_dao):
        assert user_dao.get("4b918d8a2add4857ae2a5b29f58f32df") is None
        user_dao.close()

    def test_update_user(self, user_dao, user):
        try:
            user_dao.create(user)
        except Exception:
            assert user_dao.get(user.id_) is not None
        last_modified_old = user.last_modified_datetime
        sleep(1)
        user.birthday = date(1998, 12, 21)
        user_dao.update(user)
        updated_user = user_dao.get(user.id_)
        assert updated_user.birthday == date(1998, 12, 21)
        assert updated_user.last_modified_datetime > last_modified_old
        user_dao.remove(user)
        user_dao.close()

    def test_update_payment(self, payment_dao, payment):
        try:
            payment_dao.create(payment)
        except Exception:
            assert payment_dao.get(payment.id_) is not None
        last_modified_old = payment.last_modified_datetime
        sleep(1)
        payment.value = 5
        payment_dao.update(payment)
        updated_payment = payment_dao.get(payment.id_)
        assert updated_payment.value == 5
        assert updated_payment.last_modified_datetime > last_modified_old
        payment_dao.remove(payment)
        payment_dao.close()

    def test_update_not_existent(self, user_dao):
        try:
            user = User(id_="4b918d8a2add4857ae2a5b29f58f32df")
            with raises(EntityNotFoundException):
                user_dao.update(user)
        finally:
            user_dao.close()

    @fixture
    def user_dao(self):
        return UserDAO()

    @fixture
    def payment_dao(self):
        return PaymentDAO()

    @fixture
    def user(self):
        return User(
            id_="150596d218f14b0a8f6c8c12dd9eb23a",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )

    @fixture
    def payment(self):
        return Payment(
            id_="77f3777929e1417c96c747c312f4325f",
            value=10,
            payer=User(id_="150596d218f14b0a8f6c8c12dd9eb23a"),
            receiver=User(id_="12345678901234567890123456789013")
        )
