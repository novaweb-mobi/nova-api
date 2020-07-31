import getopt
import os
import sys
from dataclasses import fields
from functools import wraps

from flask import helpers, jsonify, make_response

import nova_api.BaseAPI as BaseAPI


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


def generate_api():
    entity = ''
    version = ''
    dao_class = ''
    usage = 'Usage: %s generate_api -e entity ' \
            '[-d entity_dao -v api_version]'
    try:
        options, args = getopt.getopt(sys.argv[1:], "e:d:v:")
        for option, value in options:
            if option == '-e':
                entity = value
            elif option == '-d':
                dao_class = value
            elif option == '-v':
                version = value
    except getopt.GetoptError as er:
        print(er.msg)
        print(usage % (sys.argv[0]))
    if entity == '':
        print(usage % (sys.argv[0]))
        sys.exit(1)
    try:
        sys.path.insert(0, '')
        mod = __import__(entity, fromlist=[entity])
        ent = getattr(mod, entity)
        if dao_class == '':
            dao_class = entity + 'DAO'
        __import__(dao_class, fromlist=[dao_class])
    except ModuleNotFoundError as e:
        print("You should run the script in the same folder as your entity and"
              " it's DAO class. You must inform the entity name with -e and "
              "the DAO name with -d. You may inform the version with -v.")
        print(e)
        sys.exit(1)

    entity_lower = entity.lower()

    if os.path.isfile(
            "{entity_lower}_api.py".format(entity_lower=entity_lower)):
        print("API already exists. Skipping generation...")
    with open("{entity_lower}_api.py".format(entity_lower=entity_lower),
              'w+') as f:
        f.write(BaseAPI.base_api.format(DAO_CLASS=dao_class, ENTITY=entity,
                                        ENTITY_LOWER=entity_lower))

    if version == '':
        version = '1'
    parameters = list()
    for f in fields(ent):
        parameters.append(
            BaseAPI.parameter.format(parameter_name=f.name,
                                     parameter_location='query',
                                     parameter_type='string'))

    parameters = '\n'.join(parameters)

    if os.path.isfile(
            "{entity_lower}_api.yml".format(entity_lower=entity_lower)):
        print("API documentation already exists. Skipping generation...")
    with open("{entity_lower}_api.yml".format(entity_lower=entity_lower),
              'w+') as f:
        f.write(BaseAPI.api_swagger.format(ENTITY=entity,
                                           ENTITY_LOWER=entity_lower,
                                           VERSION=version,
                                           PARAMETERS=parameters))
