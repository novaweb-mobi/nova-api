Error reporting module
===================================

Quick Start
***********

In NovaAPI it's possible to use custom exceptions to generate error responses with custom status codes,
messages, and data objects. It's actually quite simple to do it and you may subclass the NovaAPIException
class or use it as is. Below are two examples, one with each approach: ::

    @use_dao(MyEntityDAO, "Default error message")
    def read(id_: str):
        if len(id_) < 5: # Some arbitrary requirement
            raise NovaAPIException(status_code=400, message="Id is not valid!",
                error_code=3, debug=f"{id_} is less than 5 chars long.")

Now, an example with the custom class could look like: ::

    @dataclass
    class InvalidIDException(NovaAPIException):
        status_code: int = field(default=400, init=False)
        message: str = field(default="ID is invalid!", init=False)
        error_code: int = field(default=1, init=False)
        debug: str = "ID not valid"

    ...
    @use_dao(MyEntityDAO, "Default error message")
    def read(id_: str):
        if len(id_) < 5:
            raise InvalidIDException(f"{id_} received")


Module Documentation
********************

.. automodule:: nova_api.exceptions
    :members:
