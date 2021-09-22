from dataclasses import dataclass, field
from datetime import date

from pytest import fixture, mark

from dao.mongo_dao import MongoDAO
from entity import Entity


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
    def test_create_row(self, dao, ent):
        dao = dao(host="localhost", user="root", password="root",
                  database="default")
        dao.create(ent)
        created_ent = dao.get(ent.id_)
        # dao.database.query("DELETE FROM {table}".format(table=dao.table))
        dao.close()
        assert created_ent == ent

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