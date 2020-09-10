import getopt
import logging
import os
import sys
from dataclasses import fields
from functools import wraps

from flask import helpers, jsonify, make_response

from nova_api import baseapi

# Authorization schemas
JWT = 0

possible_level = {"DEBUG": logging.DEBUG,
                  "INFO": logging.INFO,
                  "WARNING": logging.WARNING,
                  "ERROR": logging.ERROR,
                  "CRITICAL": logging.CRITICAL}

FORMAT = os.environ.get("LOG_FORMAT", '%(asctime)-15s -> (%(filename)s '
                                      '%(funcName)s) [%(levelname)s]: '
                                      '%(message)s')

LOG_FILE = os.environ.get("LOG_FILE") \
    if os.environ.get("LOG_FILE") is not None \
    else "novaapi.log"

LEVEL = os.environ.get("LOG_LEVEL") or "DEBUG"

logging.basicConfig(filename=LOG_FILE,
                    format=FORMAT,
                    level=possible_level.get(LEVEL))
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', "1234567890a")


def default_response(success: bool, status_code: int,
                     message: str, data: dict) -> helpers:
    json_content = jsonify({"success": success,
                            "message": message,
                            "data": data})
    logger.info("Sending message: %s with status code %s and success %s",
                str(json_content),
                str(status_code),
                success)
    return make_response(
        json_content,
        status_code,
        {"Content-type": "application/json"}
    )


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
                logger.info(
                    "API call to %s with dao %s and args: %s, kwargs: %s",
                    function,
                    dao_class,
                    args,
                    kwargs
                )
                dao = dao_class()
                return function(dao=dao, *args, **kwargs)
            # pylint: disable=W0703
            except Exception as exception:
                logger.error(
                    "Unable to generate api response due to an error.",
                    exc_info=True)
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
    except getopt.GetoptError:
        logger.error("Error while reading options passed to generate_api. "
                     "Options received: %s", sys.argv,
                     exc_info=True)
        print(usage % (sys.argv[0]))
        sys.exit(1)
    if entity == '':
        logger.critical("Entity not passed in the arguments! Call: %s",
                        sys.argv)
        print(usage % (sys.argv[0]))
        sys.exit(2)
    try:
        sys.path.insert(0, '')
        mod = __import__(entity, fromlist=[entity])
        ent = getattr(mod, entity)
        logger.debug("Entity found and successfully imported. Entity: %s", ent)
        if dao_class == '':
            dao_class = entity + 'DAO'
            logger.debug("DAO class name not passed, infering as %s",
                         dao_class)
        mod = __import__(dao_class, fromlist=[dao_class])
        dao = getattr(mod, dao_class)
        logger.debug("DAO class found and successfully imported. DAO: %s",
                     dao_class)
    except ModuleNotFoundError:
        print("You should run the script in the same folder as your entity and"
              " it's DAO class. You must inform the entity name with -e and "
              "the DAO name with -d. You may inform the version with -v.")
        logger.critical("Not able to import entity and dao class.",
                        exc_info=True)
        sys.exit(3)

    create_api_files(ent, dao, version)


def get_auth_schema_yml(schema: int = None):
    if schema is None:
        return None
    return baseapi.SECURITY_DEFINITIONS[schema]


def create_api_files(entity, dao_class, version,
                     overwrite=False, auth_schema=None):
    entity_lower = entity.__name__.lower()

    if os.path.isfile(
            "{entity_lower}_api.py".format(entity_lower=entity_lower)) \
            and not overwrite:
        logger.debug("API already exists. Skipping generation...")
    else:
        with open("{entity_lower}_api.py".format(entity_lower=entity_lower),
                  'w+') as api_implementation:
            logger.info("Writing api implementation for entity %s...",
                        entity_lower)
            api_implementation.write(baseapi.BASE_API.format(
                DAO_CLASS=dao_class.__name__,
                ENTITY=entity.__name__,
                ENTITY_LOWER=entity_lower))
            logger.info("Done writing api for entity %s.", entity_lower)

    if version == '':
        version = '1'
    logger.info("Version for api is %s", version)
    parameters = list()
    for field in fields(entity):
        if not field.metadata.get("database", True):
            continue
        parameters.append(
            baseapi.PARAMETER.format(parameter_name=field.name,
                                     parameter_location='query',
                                     parameter_type='string'))

    parameters = '\n'.join(parameters)

    if os.path.isfile(
            "{entity_lower}_api.yml".format(entity_lower=entity_lower))\
            and not overwrite:
        logger.debug(
            "API documentation already exists. Skipping generation...")
    else:
        with open("{entity_lower}_api.yml".format(entity_lower=entity_lower),
                  'w+') as api_documentation:
            logger.info("Writing api documentation for entity %s...",
                        entity_lower)
            api_documentation.write(baseapi.API_SWAGGER.format(
                ENTITY=entity.__name__,
                ENTITY_LOWER=entity_lower,
                VERSION=version,
                PARAMETERS=parameters,
                SECURITY=baseapi.SECURITY_PARAMETERS[auth_schema]
                if auth_schema is not None
                else ""))
            if auth_schema is not None:
                api_documentation.write(get_auth_schema_yml(auth_schema))
            logger.info("Done writing api documentation for entity %s.",
                        entity_lower)
