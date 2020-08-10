import getopt
import os
import sys
from dataclasses import fields
from functools import wraps

from flask import helpers, jsonify, make_response

from nova_api import baseapi


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
            # pylint: disable=W0703
            except Exception as exception:
                return error_response(message=error_message,
                                      data={"error": str(exception)})
            finally:
                if dao:
                    dao.close()

        return wrapper

    return make_call


def generate_api():
    entity = ''
    version = ''
    dao_class = ''
    usage = 'Usage: %s generate_api -e entity ' \
            '[-d entity_dao -v api_version]'
    try:
        options, _ = getopt.getopt(sys.argv[1:], "e:d:v:")
        for option, value in options:
            if option == '-e':
                entity = value
            elif option == '-d':
                dao_class = value
            elif option == '-v':
                version = value
    except getopt.GetoptError as getopt_error:
        print(getopt_error.msg)
        print(usage % (sys.argv[0]))
        sys.exit(1)
    if entity == '':
        print(usage % (sys.argv[0]))
        sys.exit(2)
    try:
        sys.path.insert(0, '')
        mod = __import__(entity, fromlist=[entity])
        ent = getattr(mod, entity)
        print("<", dao_class, ">", " is '': ", dao_class == '')
        if dao_class == '':
            dao_class = entity + 'DAO'
        mod = __import__(dao_class, fromlist=[dao_class])
        dao = getattr(mod, dao_class)
    except ModuleNotFoundError as exception:
        print("You should run the script in the same folder as your entity and"
              " it's DAO class. You must inform the entity name with -e and "
              "the DAO name with -d. You may inform the version with -v.")
        print(exception)
        sys.exit(3)

    create_api_files(ent, dao, version)


def create_api_files(entity, dao_class, version):
    entity_lower = entity.__name__.lower()

    if os.path.isfile(
            "{entity_lower}_api.py".format(entity_lower=entity_lower)):
        print("API already exists. Skipping generation...")
    else:
        print("WILL CREATE FILE")
        with open("{entity_lower}_api.py".format(entity_lower=entity_lower),
                  'w+') as api_implementation:
            api_implementation.write(baseapi.BASE_API.format(
                DAO_CLASS=dao_class.__name__,
                ENTITY=entity.__name__,
                ENTITY_LOWER=entity_lower))

    if version == '':
        version = '1'
    parameters = list()
    for field in fields(entity):
        parameters.append(
            baseapi.PARAMETER.format(parameter_name=field.name,
                                     parameter_location='query',
                                     parameter_type='string'))

    parameters = '\n'.join(parameters)

    if os.path.isfile(
            "{entity_lower}_api.yml".format(entity_lower=entity_lower)):
        print("API documentation already exists. Skipping generation...")
    else:
        print("WILL CREATE FILE")
        with open("{entity_lower}_api.yml".format(entity_lower=entity_lower),
                  'w+') as api_documentation:
            api_documentation.write(baseapi.API_SWAGGER.format(
                ENTITY=entity.__name__,
                ENTITY_LOWER=entity_lower,
                VERSION=version,
                PARAMETERS=parameters))
