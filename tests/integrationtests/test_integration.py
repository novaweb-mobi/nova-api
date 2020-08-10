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
        super(UserDAO, self).__init__(database=database, table=UserDAO.table,
                                      return_class=User, prefix='')


@dataclass
class Payment(Entity):
    value: int = 0
    payer: User = None
    receiver: User = None


class PaymentDAO(GenericSQLDAO):
    table = 'payments'

    def __init__(self, database=None):
        super(PaymentDAO, self).__init__(database=database,
                                         table=PaymentDAO.table,
                                         return_class=Payment, prefix='')


class TestIntegration:
    @fixture
    def user_dao(self):
        return UserDAO()

    @fixture
    def payment_dao(self):
        return PaymentDAO()

    @fixture
    def user(self):
        return User(
            id_="12345678901234567890123456789012",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )

    @fixture
    def payment(self):
        return Payment(
            id_="00000000000000000000000000000000",
            value=10,
            payer=User(id_="12345678901234567890123456789012"),
            receiver=User(id_="12345678901234567890123456789013")
        )

    @mark.parametrize("dao", [
        UserDAO(),
        PaymentDAO()
    ])
    def test_create_table_not_exists(self, dao):
        try:
            dao.database.query("DROP TABLE {tbl}".format(tbl=dao.table))
        except Exception:
            pass
        dao.create_table_if_not_exists()
        dao.database.query("show tables;")
        results = [result[0] for result in dao.database.get_results()]
        assert dao.table in results

    @mark.parametrize("dao, ent", [
        (UserDAO(), User(
            id_="12345678901234567890123456789012",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )),
        (PaymentDAO(), Payment(
            id_="00000000000000000000000000000000",
            value=10,
            payer=User(id_="12345678901234567890123456789012"),
            receiver=User(id_="12345678901234567890123456789013")
        )),
    ])
    def test_create_row(self, dao, ent):
        dao.create_table_if_not_exists()
        dao.create(ent)
        created_ent = dao.get(ent.id_)
        dao.database.query("DELETE FROM {table}".format(table=dao.table))
        assert created_ent == ent

    @mark.parametrize("dao, ent", [
        (UserDAO(), User(
            id_="12345678901234567890123456789012",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )),
        (PaymentDAO(), Payment(
            id_="00000000000000000000000000000000",
            value=10,
            payer=User(id_="12345678901234567890123456789012"),
            receiver=User(id_="12345678901234567890123456789013")
        )),
    ])
    def test_create_existent(self, dao, ent):
        dao.create_table_if_not_exists()
        dao.create(ent)
        assert dao.get(ent.id_) == ent
        with raises(AssertionError):
            dao.create(ent)

    def test_update_user(self, user_dao, user):
        user_dao.create_table_if_not_exists()
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
        assert updated_payment.value == 5
        assert updated_payment.last_modified_datetime > last_modified_old

    @mark.parametrize("dao, ent", [
        (UserDAO(), User(id_="12345678901234567890123456789012")),
        (PaymentDAO(), Payment(id_="00000000000000000000000000000000")),
    ])
    def test_delete(self, dao, ent):
        dao.create_table_if_not_exists()
        try:
            dao.create(ent)
        except Exception:
            assert dao.get(ent.id_) is not None
        dao.remove(ent)
        assert dao.get(ent.id_) is None

    def test_get_not_existent(self, user_dao):
        user_dao.create_table_if_not_exists()
        assert user_dao.get("12345678901234567890123456789023") is None

    def test_update_not_existent(self, user_dao):
        user_dao.create_table_if_not_exists()
        user = User(id_="12345678901234567890123456789023")
        with raises(AssertionError):
            user_dao.update(user)

    def test_delete_not_existent(self, user_dao):
        user_dao.create_table_if_not_exists()
        user = User(id_="12345678901234567890123456789023")
        with raises(AssertionError):
            user_dao.remove(user)

    def test_filter_date(self, user_dao):
        user_dao.create_table_if_not_exists()
        u1 = User(birthday=date(1998, 12, 21))
        u2 = User(birthday=date(2005, 11, 21), first_name="Jose")
        user_dao.create(u1)
        user_dao.create(u2)
        results = user_dao.get_all(
            filters={"birthday": ['>', "2005-1-1"]})[1]
        user_dao.remove(u1)
        user_dao.remove(u2)
        assert len(results) == 1

    def test_filter_name(self, user_dao):
        user_dao.create_table_if_not_exists()
        u1 = User(birthday=date(1998, 12, 21))
        u2 = User(birthday=date(2005, 11, 21), first_name="Jose")
        user_dao.create(u1)
        user_dao.create(u2)
        results = user_dao.get_all(
            filters={"first_name": ["LIKE", "J%"]})[1]
        user_dao.remove(u1)
        user_dao.remove(u2)
        assert len(results) == 1
