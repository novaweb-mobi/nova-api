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


class NoRowsAffectedException(IOError):
    pass
