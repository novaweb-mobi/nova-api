from dataclasses import dataclass, field
from datetime import date
from time import sleep

from pytest import fixture, mark, raises

from nova_api.dao.generic_sql_dao import GenericSQLDAO
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


class UserDAO(GenericSQLDAO):
    table = 'usuarios'

    def __init__(self, pooled=False, **kwargs):
        super(UserDAO, self).__init__(table=UserDAO.table,
                                      return_class=User, prefix='',
                                      pooled=pooled, **kwargs)


@dataclass
class Payment(Entity):
    value: int = 0
    payer: User = None
    receiver: User = None


class PaymentDAO(GenericSQLDAO):
    table = 'payments'

    def __init__(self, pooled=False, **kwargs):
        super(PaymentDAO, self).__init__(table=PaymentDAO.table,
                                         return_class=Payment, prefix='',
                                         pooled=pooled, **kwargs)


@mark.parametrize("pool", [True, False])
class TestIntegrationMySQL:
    @fixture
    def user_dao(self, pool):
        user_dao = UserDAO(pooled=pool)
        user_dao.create_table_if_not_exists()

        return user_dao

    @fixture
    def payment_dao(self, pool):
        return PaymentDAO(pooled=pool)

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

    @mark.parametrize("dao", [
        UserDAO,
        PaymentDAO
    ])
    def test_create_table_not_exists(self, dao, pool):
        dao = dao(pooled=pool)
        try:
            dao.database.query("DROP TABLE {tbl}".format(tbl=dao.table))
        except Exception:
            pass
        dao.create_table_if_not_exists()
        dao.database.query("show tables;")
        table = dao.table
        results = [result[0] for result in dao.database.get_results()]
        dao.close()
        assert table in results

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
    def test_create_row(self, dao, ent, pool):
        dao = dao(pooled=pool)
        dao.create_table_if_not_exists()
        dao.create(ent)
        created_ent = dao.get(ent.id_)
        dao.database.query("DELETE FROM {table}".format(table=dao.table))
        dao.close()
        assert created_ent == ent

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
    def test_create_existent(self, dao, ent, pool):
        dao = dao(pooled=pool)
        dao.create_table_if_not_exists()
        try:
            dao.create(ent)
        except DuplicateEntityException:
            pass
        assert dao.get(ent.id_) == ent
        with raises(DuplicateEntityException):
            dao.create(ent)
        dao.close()

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
        user_dao.close()
        assert updated_user.birthday == date(1998, 12, 21)
        assert updated_user.last_modified_datetime > last_modified_old

    def test_update_payment(self, payment_dao, payment):
        payment_dao.create_table_if_not_exists()
        try:
            payment_dao.create(payment)
        except Exception:
            assert payment_dao.get(payment.id_) is not None
        last_modified_old = payment.last_modified_datetime
        sleep(1)
        payment.value = 5
        payment_dao.update(payment)
        updated_payment = payment_dao.get(payment.id_)
        payment_dao.close()
        assert updated_payment.value == 5
        assert updated_payment.last_modified_datetime > last_modified_old

    @mark.parametrize("dao, ent", [
        (UserDAO, User(id_="150596d218f14b0a8f6c8c12dd9eb23a")),
        (PaymentDAO, Payment(id_="77f3777929e1417c96c747c312f4325f")),
    ])
    def test_delete(self, dao, ent, pool):
        dao = dao(pooled=pool)
        dao.create_table_if_not_exists()
        try:
            dao.create(ent)
        except DuplicateEntityException:
            assert dao.get(ent.id_) is not None
        dao.remove(ent)
        assert dao.get(ent.id_) is None
        dao.close()

    def test_get_not_existent(self, user_dao):

        assert user_dao.get("4b918d8a2add4857ae2a5b29f58f32df") is None
        user_dao.close()

    def test_update_not_existent(self, user_dao):
        try:

            user = User(id_="4b918d8a2add4857ae2a5b29f58f32df")
            with raises(AssertionError):
                user_dao.update(user)
        finally:
            user_dao.close()

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

    def test_filter_date(self, user_dao):

        u1 = User(birthday=date(1998, 12, 21))
        u2 = User(birthday=date(2005, 11, 21), first_name="Jose")
        user_dao.create(u1)
        user_dao.create(u2)
        results = user_dao.get_all(
            filters={"birthday": ['>', "2005-1-1"]})[1]
        user_dao.remove(u1)
        user_dao.remove(u2)
        user_dao.close()
        assert len(results) == 1

    def test_filter_name(self, user_dao):

        u1 = User(birthday=date(1998, 12, 21))
        u2 = User(birthday=date(2005, 11, 21), first_name="Jose")
        user_dao.create(u1)
        user_dao.create(u2)
        results = user_dao.get_all(
            filters={"first_name": ["LIKE", "J%"]})[1]
        user_dao.remove(u1)
        user_dao.remove(u2)
        user_dao.close()
        assert len(results) == 1
