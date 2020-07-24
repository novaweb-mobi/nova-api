from functools import wraps

from flask import helpers, jsonify, make_response


def default_response(success: bool, status_code: int,
                     message: str, data: dict) -> helpers:
    return make_response(
        jsonify({"success": success,
                 "message": message,
                 "data": data}),
        status_code,
        {"Content-type": "application/json"})


def error_response(status_code: int = 500, message: str = "Error",
                   data: dict = None) -> helpers:
    if data is None:
        data = dict()
    return default_response(success=False, status_code=status_code,
                            message=message, data=data)


def success_response(status_code: int = 200, message: str = "OK",
                     data: dict = None) -> helpers:
    if data is None:
        data = dict()
    return default_response(success=True, status_code=status_code,
                            message=message, data=data)


def use_dao(dao_class: type, error_message: str = "Erro"):
    def make_call(function):

        @wraps(function)
        def wrapper(*args, **kwargs):
            dao = None
            try:
                dao = dao_class()
                return function(dao=dao, *args, **kwargs)
            except Exception as e:
                return error_response(message=error_message,
                                      data={"error": str(e)})
            finally:
                if dao:
                    dao.close()

        return wrapper

    return make_call
