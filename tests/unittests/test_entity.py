import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from functools import partial
from typing import List

from pytest import fixture, raises

from nova_api.validations import *
from nova_api.entity import Entity
from nova_api.exceptions import InvalidAttributeException


# pylint: disable=R0201
@dataclass
class SampleEntity(Entity):
    pass


@dataclass
class EntityForTest(Entity):
    test_field: int = 0
    my_date: date = field(default=date(2020, 1, 1))
    child: SampleEntity = None


@dataclass
class EntityForTestWithDateFormat(Entity):
    my_date: date = field(default=None, metadata={
        "date_format": "%d/%m/%Y",
    })
    my_datetime: datetime = field(default=None, metadata={
        "datetime_format": "%d/%m/%Y %H:%M",
    })


@dataclass
class EntityForTestWithDatetime(Entity):
    my_date: datetime = field(default=datetime(year=2020, month=1, day=12))


@dataclass
class EntityForTestWithTypeError(Entity):
    childs: List[SampleEntity] = None


@dataclass
class EntityForTestWithString(Entity):
    name: str = None


class SimpleEnum(Enum):
    name1 = 0
    name2 = 1


@dataclass
class EntityForTestWithEnum(Entity):
    simple_enum: SimpleEnum = None


class TestEnum(Enum):
    VALUE1 = 1
    VALUE2 = 2


@dataclass
class EntityForTestWithEnum2(Entity):
    name: str = None
    value: TestEnum = TestEnum.VALUE1


def is_valid_json(value) -> bool:
    try:
        return isinstance(json.loads(value), dict)
    except ValueError:
        return False


@dataclass
class EntityForTestWithValidation(Entity):
    my_json: str = field(default='',
                         metadata={'validation': is_valid_json})


class MyCustomException(Exception):
    ...


def validate_with_custom_exception(value):
    if value != 'valid':
        raise MyCustomException
    return True


@dataclass
class EntityForTestWithDefaultValidations(Entity):
    name: str = field(default='', metadata={'validation': has_max_length})
    password: str = field(default='some really good password',
                          metadata={'validation': partial(has_min_length,
                                                          min_length=8)})
    age: int = field(default=10, metadata={'validation': is_greater_than})
    birth: datetime = field(
        default=datetime.today() - timedelta(weeks=10),
        metadata={'validation': partial(is_less_than,
                                        upper_bound=datetime.now())}
    )
    status: str = field(default='valid',
                        metadata={'validation': validate_with_custom_exception})


class TestEntity:

    @fixture
    def entity(self):
        return EntityForTest("12345678901234567890123456789012",
                             datetime(2020, 1, 1, 0, 0, 0),
                             datetime(2020, 1, 1, 0, 0, 0),
                             0, child=SampleEntity(
                "12345678901234567890123456789012"))

    def test_auto_generate_id(self, entity):
        assert len(entity.id_) == 32

    def test_datetime_generation(self, entity):
        assert isinstance(entity.creation_datetime, datetime) \
               and isinstance(entity.last_modified_datetime, datetime)

    def test_received_datetime_should_turn_date(self):
        ent = EntityForTestWithDateFormat(my_date=datetime(1, 1, 1, 12, 1))
        assert not isinstance(ent.my_date, datetime)
        assert ent.my_date == date(1, 1, 1)

    def test_to_dict(self, entity):
        entity_dict = dict(entity)
        assert entity_dict == {"id_": "12345678901234567890123456789012",
                               "creation_datetime": "2020-01-01 00:00:00",
                               "last_modified_datetime": "2020-01-01 00:00:00",
                               "test_field": 0,
                               "my_date": "2020-01-01",
                               "child_id_": "12345678901234567890123456789012"}

    def test_to_dict_with_enum(self):
        entity_dict = dict(
            EntityForTestWithEnum2("12345678901234567890123456789012",
                                   datetime(2020, 1, 1, 0, 0, 0),
                                   datetime(2020, 1, 1, 0, 0, 0)))

        assert entity_dict == {"id_": "12345678901234567890123456789012",
                               "creation_datetime": "2020-01-01 00:00:00",
                               "last_modified_datetime": "2020-01-01 00:00:00",
                               "name": None,
                               "value": 1}

    def test_not_implemented(self):
        with raises(NotImplementedError):
            Entity()

    def test_field_type_error(self):
        ent = EntityForTestWithTypeError()
        assert isinstance(ent, EntityForTestWithTypeError)

    def test_date_parsing(self):
        ent1 = EntityForTest(my_date="2020-1-1")
        ent2 = EntityForTest(id_=ent1.id_)
        assert ent1 == ent2

    def test_datetime_parsing(self):
        ent1 = EntityForTestWithDatetime(my_date="2020-1-12 00:00:00")
        ent2 = EntityForTestWithDatetime(id_=ent1.id_)
        assert ent1 == ent2

    def test_str_stripping(self):
        ent1 = EntityForTestWithString(name=" John ")
        ent2 = EntityForTestWithString(id_=ent1.id_, name="John")
        assert ent1 == ent2

    def test_format_date(self):
        ent1 = EntityForTestWithDateFormat(my_date="13/8/2020",
                                           my_datetime="14/09/2021 19:07")
        ent2 = EntityForTestWithDateFormat(id_=ent1.id_,
                                           my_date=date(day=13,
                                                        month=8, year=2020),
                                           my_datetime=datetime(day=14,
                                                                month=9,
                                                                year=2021,
                                                                hour=19,
                                                                minute=7))
        assert ent1 == ent2

    def test_enum_parsing(self):
        ent = EntityForTestWithEnum('0' * 32,
                                    datetime(day=21,
                                             month=9,
                                             year=2021,
                                             hour=0,
                                             minute=0),
                                    datetime(day=21,
                                             month=9,
                                             year=2021,
                                             hour=0,
                                             minute=0),
                                    simple_enum=0)

        assert isinstance(ent.simple_enum, Enum)
        assert ent.get_db_values() == ['0' * 32,
                                       *['2021-09-21 00:00:00'] * 2,
                                       0]

    def test_fields_are_parsed_when_setting_attribute(self):
        ent = EntityForTestWithDatetime()

        ent.my_date = '2020-1-12 00:00:00'

        assert isinstance(ent.my_date, datetime)

    def test_set_attribute_fail_validation(self):
        with raises(InvalidAttributeException):
            EntityForTestWithValidation()

    def test_set_attribute_pass_validation(self):
        ent = EntityForTestWithValidation(my_json='{"name": "value"}')

        assert ent.my_json == '{"name": "value"}'

    def test_set_attribute_that_doesnt_exists_raise_attribute_error(self):
        ent = EntityForTest()

        with raises(AttributeError):
            ent.not_here = True

    def test_set_attribute_with_default_validations(self):
        ent = EntityForTestWithDefaultValidations()
        with raises(InvalidAttributeException):
            ent.name = 'some loooong name'

        with raises(InvalidAttributeException):
            ent.age = -1

        with raises(InvalidAttributeException):
            ent.birth = datetime.now() + timedelta(1)

        with raises(InvalidAttributeException):
            ent.password = 'pass'

        with raises(MyCustomException):
            EntityForTestWithDefaultValidations(status='invalid')
