from dataclasses import dataclass, field
from datetime import date
from time import sleep

from pytest import fixture, mark, raises

from nova_api.entity import Entity
from nova_api.dao.generic_sql_dao import GenericSQLDAO


@dataclass
class User(Entity):
    first_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    last_name: str = field(default=None, metadata={"type": "CHAR(45)"})
    email: str = field(default=None, metadata={"type": "CHAR(255)"})
    active: bool = True
    birthday: date = None


class UserDAO(GenericSQLDAO):
    table = 'usuarios'

    def __init__(self, database=None, pooled=False):
        super(UserDAO, self).__init__(database=database, table=UserDAO.table,
                                      return_class=User, prefix='',
                                      pooled=pooled)


@dataclass
class Payment(Entity):
    value: int = 0
    payer: User = None
    receiver: User = None


class PaymentDAO(GenericSQLDAO):
    table = 'payments'

    def __init__(self, database=None, pooled=False):
        super(PaymentDAO, self).__init__(database=database,
                                         table=PaymentDAO.table,
                                         return_class=Payment, prefix='',
                                         pooled=pooled)


@mark.parametrize("pool", [True, False])
class TestIntegration:
    @fixture
    def user_dao(self, pool):
        return UserDAO(pooled=pool)

    @fixture
    def payment_dao(self, pool):
        return PaymentDAO(pooled=pool)

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
            id_="12345678901234567890123456789012",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )),
        (PaymentDAO, Payment(
            id_="00000000000000000000000000000000",
            value=10,
            payer=User(id_="12345678901234567890123456789012"),
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
            id_="12345678901234567890123456789012",
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com"
        )),
        (PaymentDAO, Payment(
            id_="00000000000000000000000000000000",
            value=10,
            payer=User(id_="12345678901234567890123456789012"),
            receiver=User(id_="12345678901234567890123456789013")
        )),
    ])
    def test_create_existent(self, dao, ent, pool):
        dao = dao(pooled=pool)
        dao.create_table_if_not_exists()
        try:
            dao.create(ent)
        except AssertionError:
            pass
        assert dao.get(ent.id_) == ent
        with raises(AssertionError):
            dao.create(ent)
        dao.close()

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
        (UserDAO, User(id_="12345678901234567890123456789012")),
        (PaymentDAO, Payment(id_="00000000000000000000000000000000")),
    ])
    def test_delete(self, dao, ent, pool):
        dao = dao(pooled=pool)
        dao.create_table_if_not_exists()
        try:
            dao.create(ent)
        except Exception:
            assert dao.get(ent.id_) is not None
        dao.remove(ent)
        res_ent = dao.get(ent.id_)
        dao.close()
        assert res_ent is None

    def test_get_not_existent(self, user_dao):
        user_dao.create_table_if_not_exists()
        res = user_dao.get("12345678901234567890123456789023")
        user_dao.close()
        assert res is None

    def test_update_not_existent(self, user_dao):
        try:
            user_dao.create_table_if_not_exists()
            user = User(id_="12345678901234567890123456789023")
            with raises(AssertionError):
                user_dao.update(user)
        finally:
            user_dao.close()

    def test_delete_not_existent(self, user_dao):
        try:
            user_dao.create_table_if_not_exists()
            user = User(id_="12345678901234567890123456789023")
            with raises(AssertionError):
                user_dao.remove(user)
        finally:
            user_dao.close()

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
        user_dao.close()
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
        user_dao.close()
        assert len(results) == 1
