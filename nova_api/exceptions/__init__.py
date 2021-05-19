from dataclasses import dataclass


@dataclass
class NovaAPIException(Exception):
    status_code: int
    message: str
    error_code: int
    debug: str


class NoRowsAffectedException(IOError):
    pass
