Creating your Entity
********************

To read the full documentation on the entity module, refer to
:doc:`entity`.

Quick Start
===========

The first step on creating your entity is modeling it. You may do
that however you prefer, e.g. UML.

After modeling it, you may start implementing it with NovaAPI. First,
create a file in camel case with the first letter in capital case.

In our example, this will be `Contact.py`.

Next, start with the necessary imports on the file: ::

    from dataclasses import dataclass, field

    from nova_api.entity import Entity

The dataclasses module allows us to declare the attributes of our
entity in a simpler way and also creates some methods for us like
`__init__`, `compare` and `__repr__`. The Entity module from NovaAPI
allows us to easily serialize and deserialize our entity when sending
an API response or dealing with the database.

Next, we may start creating our class, which inherits from Entity and
is decorated with the `@dataclass` decorator. ::

    @dataclass
    class Contact(Entity):

The class should have the same name as the file, this ensures that it
will be easily found by the cli tools and consistency.

Now we can start adding the attributes to our class. The easiest way is
just adding the field with a type hint and the default value: ::

    @dataclass
    class Contact(Entity):
        name: str = 'Anom'

The type hint and the default value must be included as the Entity inserts
the `id_`, `creation_datetime` and `last_modified_datetime` attributes with
default values, which would cause the program to fail if your class doesn't
include one.

Defining Mutable Default Values
===============================

It's a fact that in Python you shouldn't use mutable default values like `list()` and
`datetime.now()` as they're evaluated at the start of your program. However, the
dataclasses module solves this issue using a default_factory, which is called when
`__init__` is executing. This function must accept 0 arguments. ::

    @dataclass
    class Contact(Entity):
        name: str = 'Anom'
        birthday: datetime = field(default_factory=datetime.now)

Customizing Fields
==================

The field function for dataclasses that was used to define mutable values may
also be used to achieve a higher level of customization in NovaAPI using the
metadata value. This argument receives a dictionary which may be used to define
the database type, the default value in the database, add constraints, etc. ::

    @dataclass
    class Contact(Entity):
        name: str = 'Anom'
        birthday: datetime = field(default_factory=datetime.now)
        age: int = field(default=0, compare=False, metadata={"database": False})

Metadata Supported Options
--------------------------

database
^^^^^^^^
May be used to exclude a field from the database serialization. If you would
like to exclude a field from the database, add `{"database": False}` to metadata.
Defaults to True.

primary_key
^^^^^^^^^^^
Defines the attribute as a primary key in the database. This should be used with
`{"default": "NOT NULL"}`, which will be added to the field if not specified. To
apply, add `{"primary_key": True}` to metadata. Defaults to False.

type
^^^^
May be used to alter the default NovaAPI predicted database type. To change the field
type, just add `{"type": "<the_type>"}` to the metadata, e.g. `{"type": "VARCHAR(15)"}`.

default
^^^^^^^
Used to define the default database value of the field. Usually it assumes either NULL
or NOT NULL, when it's not acceptable to have null values on the database. Although it
is not directly this options intention, you may add constraints through it, like UNIQUE.
If you would like to restrict NULL values, add `{"default": "NOT NULL"}` to the metadata,
to use UNIQUE, you could add {"default": "NOT NULL UNIQUE"}.
Defaults to NULL.

datetime_format
^^^^^^^^^^^^^^^
This may be used to determine how the entity accepts datetime values in its `__init__` method.
Considering that most times we receive data through http and parse it to an entity, being able
to initialize datetime fields with string may help you a lot. This property should be set
according to the `strptime` function in the datetime module. For example:
`{"datetime_format":"%Y-%m-%d %H:%M:%S"}`, which is the default format.

date_format
^^^^^^^^^^^
This may be used to determine how the entity accepts date values in its `__init__` method.
This works like the datetime_format. This property should be set according to the `strptime`
function in the datetime module. For example: `{"datetime_format":"%Y-%m-%d"}`, which is
the default format.

validation
^^^^^^^^^^
This may be used to validate the attribute values in the `__setattr__` method.
It expects a callable object that receives an argument, the attribute's value,
and returns a boolean value indicating whether the value is valid or not. It's
very important to return an object that evaluates to True if the value is valid,
otherwise the `__setattr__` method will raise an InvalidAttributeException. If
you would like to return a custom exception when the value is invalid you could do
this in the validation function. Generic validation functions that expect more
than one argument could be converted to `functools.partial <https://docs.python.org/pt-br/3/library/functools.html#functools.partial>`_
object so it acts as a function that expects a single argument. ::

    def is_between(value, min_value, max_value) -> bool:
        return min_value <= value <= max_value

    def is_valid_name(value) -> bool:
        if len(value) < 3:
            raise MyCustomException
        return True

    @dataclass
    class Contact(Entity):
        name: str = field(default='Anom',
                          metadata={'validation': is_valid_name})
        birthday: datetime = field(default_factory=datetime.now)
        age: int = field(default=0, compare=False,
                         metadata={"database": False,
                                   "validation": partial(is_between,
                                                         min_value=0,
                                                         max_value=122)})
        height: float = field(default=0, compare=False,
                              metadata={"database": False,
                                        "validation": partial(is_between,
                                                              min_value=0.5464,
                                                              max_value=2.52)})

Next Steps
==========

Next, you should create your DAO class. For more information on this topic, refer to :doc:`create_dao`