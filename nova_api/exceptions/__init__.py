"""
Custom exceptions for NovaAPI
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NovaAPIException(Exception):
    """Base class for API error reporting

        This class allows for an easier error handling on API's. \
        When use_dao captures one error that subclasses this class, \
        it reads through the fields to fill the error response to be \
        returned to the user. It is also possible to add a debug \
        message which is only sent if DEBUG is set to True.


        :param status_code: The integer HTTP status code to send in the \
        response. Defaults to 500.
        :param message: The message to send in the message field of the \
        response. Defaults to Error.
        :param error_code: The error code to send in the data object. This \
        may be used to help debugging in production environments. Defaults \
        to the status code.
        :param debug: The debug message to send in the data object if \
        DEBUG is True. Defaults to "No debug information".
        """
    status_code: int = 500
    message: str = "Error"
    error_code: Optional[int] = None
    debug: str = "No debug information"

    def __post_init__(self):
        if self.error_code is None:
            self.error_code = self.status_code


@dataclass
class NotEntityException(NovaAPIException):
    status_code: int = field(default=400, init=False)
    message: str = field(default="Argument is not an Entity", init=False)


@dataclass
class InvalidFiltersException(NovaAPIException):
    status_code: int = field(default=400, init=False)
    message: str = field(default="Filters are not valid", init=False)


@dataclass
class InvalidIDTypeException(NovaAPIException):
    status_code: int = field(default=400, init=False)
    message: str = field(default="ID type is not string", init=False)


@dataclass
class InvalidIDException(NovaAPIException):
    status_code: int = field(default=400, init=False)
    message: str = field(default="ID is not a valid UUID v4", init=False)


@dataclass
class DuplicateEntityException(NovaAPIException):
    status_code: int = field(default=409, init=False)
    message: str = field(default="Entity already exists in database",
                         init=False)


@dataclass
class EntityNotFoundException(NovaAPIException):
    status_code: int = field(default=404, init=False)
    message: str = field(default="The requested entity was not "
                                 "found in database", init=False)


@dataclass
class NoRowsAffectedException(NovaAPIException):
    status_code: int = field(default=304, init=False)
    message: str = field(default="No rows were affected by the "
                                 "desired operation", init=False)
    error_code: int = field(default=304, init=False)
