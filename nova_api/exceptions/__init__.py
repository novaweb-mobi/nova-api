from dataclasses import dataclass


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
    error_code: int = None
    debug: str = "No debug information"

    def __post_init__(self):
        if self.error_code is None:
            self.error_code = self.status_code


class NotEntityException(NovaAPIException):
    status_code = 400
    message = "Argument is not an Entity"


class InvalidFiltersException(NovaAPIException):
    status_code = 400
    message = "Filters are not valid"


class InvalidIDTypeException(NovaAPIException):
    status_code = 400
    message = "ID type is not string"


class InvalidIDException(NovaAPIException):
    status_code = 400
    message = "ID is not a valid UUID v4"


class DuplicateEntityException(NovaAPIException):
    status_code = 409
    message = "Entity already exists in database"


class EntityNotFoundException(NovaAPIException):
    status_code = 404
    message = "The requested entity was not found in database"

class NoRowsAffectedException(IOError):
    pass
