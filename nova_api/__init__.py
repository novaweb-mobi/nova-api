"""A package to accelerate REST API development"""
import getopt
import logging
import os
import sys
import time
from dataclasses import Field, fields
from functools import wraps
from typing import Type

from flask import jsonify, make_response
from flask.wrappers import Response

from nova_api import baseapi
from nova_api.dao import GenericDAO
from nova_api.exceptions import NovaAPIException

# Authorization schemas
JWT = 0

AUTHENTICATION_SCHEMAS = {"JWT": 0}

possible_level = {"DEBUG": logging.DEBUG,
                  "INFO": logging.INFO,
                  "WARNING": logging.WARNING,
                  "ERROR": logging.ERROR,
                  "CRITICAL": logging.CRITICAL}

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', "1234567890a")
DEBUG = bool(os.environ.get('NOVAAPI_DEBUG', False))


def close_if_still_open(dao: GenericDAO) -> None:
    """Closes a DAO connection if it's still open.

    :param dao: DAO instance to be closed
    :return:
    """
    if dao:
        dao.close()


def default_response(success: bool, status_code: int,
                     message: str, data: dict) -> Response:
    """ Send a flask response with json payload in a default format

    Example:
        JSON response ::

            {
                "sucess": True,
                "message": "API call OK",
                "data": {
                    "num": "123"
                }
            }

    :param success: bool that represents if the request was successfully \
    processed.
    :param status_code: integer that represents the http status code of the \
    response.
    :param message: summary string for the response.
    :param data: dictionary (json valid) with data to be sent in the response
    :return: a flask response with headers and status codes set
    """
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
                   data: dict = None) -> Response:
    """Wrapper of default_response for error responses.

    Calls default_response with status_code=500, message=Error
    and success=false passing data. Other status code and messages
    may be passed.

    :param status_code: Integer that represents the http status code of the \
    response.
    :param message: Summary string for the response.
    :param data: Dictionary (json valid) with data to be sent in the response
    :return: Default response with success=false
    """
    if data is None:
        data = dict()
    return default_response(success=False, status_code=status_code,
                            message=message, data=data)


def success_response(status_code: int = 200, message: str = "OK",
                     data: dict = None) -> Response:
    """Wrapper of default_response for success responses.

        Calls default_response with status_code=200, message=OK
        and success=true passing data. Other status code and messages
        may be passed.

        :param status_code: Integer that represents the http status code of \
        the response.
        :param message: Summary string for the response.
        :param data: Dictionary (json valid) with data to be sent in the \
        response
        :return: Default response with success=true
        """
    if data is None:
        data = dict()
    return default_response(success=True, status_code=status_code,
                            message=message, data=data)


def use_dao(dao_class: GenericDAO,
            error_message: str = "Erro",
            dao_parameters: dict = None,
            retry_delay: float = float(os.environ.get("NOVAAPI_RETRY_DELAY",
                                                      "1.0")),
            retries: int = int(os.environ.get("NOVAAPI_RETRIES", "3")), ):
    """Decorator to handle database access in an API call

    This decorator instantiates the DAO specified in `dao_class` within a try \
    except block. If a exception is raised during the API call or database \
    access, it generates an `error_response` with `message=error_message` and \
    with the exception description in data. The DAO instance is passed to the \
    decorated function as a keyword argument `dao`.

    :param dao_class: DAO to instantiate and pass to the decorated function
    :param error_message: Default error message to send in the error_response \
    if an exception is thrown
    :param dao_parameters: Parameters to add to the call to the DAO \
    constructor. They'll be added to the call with the expansion \
    `**dao_parameters`.
    :param retries: Number of times to retry connection with database. \
    Defaults to 3. May be set through the env variable NOVAAPI_RETRIES
    :param retry_delay: Seconds to wait before retrying to connect to \
    database. Defaults to 1.0. May be set through the env variable \
    NOVAAPI_RETRY_DELAY.

    :return: The decorated function
    """

    if dao_parameters is None:
        dao_parameters = dict()

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

                attempted_retries = retries
                while attempted_retries:
                    try:
                        dao = dao_class(**dao_parameters)
                        break
                    except ConnectionError as con_error:
                        print("Connection failed, will retry "
                              "%s times" % attempted_retries)
                        time.sleep(retry_delay)
                        if attempted_retries == 1:
                            raise con_error
                    finally:
                        attempted_retries -= 1

                return function(dao=dao, *args, **kwargs)
            except NovaAPIException as nova_api_exception:
                response_data = {"error_code": nova_api_exception.error_code}
                if DEBUG:
                    response_data["debug"]=nova_api_exception.debug
                return error_response(
                    status_code=nova_api_exception.status_code,
                    message=nova_api_exception.message,
                    data=response_data)
            except Exception as exception: # pylint: disable=W0703
                logger.error(
                    "Unable to generate api response due to an error.",
                    exc_info=True)

                error_description = str(exception) \
                    if DEBUG \
                    else "Something went wrong... Please try again later."

                return error_response(message=error_message,
                                      data={"error": error_description})
            finally:
                close_if_still_open(dao)

        return wrapper

    return make_call


def generate_api():
    """CLI interface for generate_nova_api. Generates API files.

    Must be called at least with -e <Entity>. Generates the api files \
    with the arguments. Accepts the following arguments:
     * *-e*: Name of the Entity, which must be the same of the file that \
     contains it
     * *-d*: Name of the Entity DAO class, which must be the same of the \
     file that contains it. Only needs to be specified if it's not EntityDAO. \
     (Where Entity is the name of the entity passed to -e)
     * *-v*: API version string. Will be used in the base path before the \
     entity name
     * *-a*: Authentication Schema, type of authentication which will be \
     applied to endpoints in the generated API.

    :return: None.
    """
    entity = ''
    version = ''
    dao_class = ''
    auth = None
    overwrite = False
    usage = 'Usage: %s generate_api -e entity ' \
            '[-d entity_dao -v api_version -a auth_schema -o overwrite]'
    try:
        options, _ = getopt.getopt(sys.argv[1:], "e:d:v:a:o")
        for option, value in options:
            if option == '-e':
                entity = value
            elif option == '-d':
                dao_class = value
            elif option == '-v':
                version = value
            elif option == '-a':
                auth = value.strip()
            elif option == '-o':
                overwrite = True
    except getopt.GetoptError:
        logger.error("Error while reading options passed to generate_api. "
                     "Options received: %s", sys.argv,
                     exc_info=True)
        print(usage % (sys.argv[0]))
        sys.exit(os.EX_DATAERR)
    if entity == '':
        logger.critical("Entity not passed in the arguments! Call: %s",
                        sys.argv)
        print(usage % (sys.argv[0]))
        sys.exit(os.EX_USAGE)
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
        sys.exit(os.EX_IOERR)

    if auth and not is_valid_auth_schema(auth):
        print(("Schema %s not supported! The supported schemas "
               "are: " % auth) + ', '.join(
            AUTHENTICATION_SCHEMAS.keys()))
        sys.exit(os.EX_DATAERR)

    try:
        create_api_files(ent, dao, version, overwrite=overwrite,
                         auth_schema=AUTHENTICATION_SCHEMAS.get(auth, None))
    except (OSError, EOFError) as err:
        print("Something went wrong while creating the API files...", err)
        sys.exit(os.EX_CANTCREAT)


def is_valid_auth_schema(auth: str) -> bool:
    """Checks if the informed auth schema is valid.

    :param auth: The informed auth schema
    :return: True if the schema is in the valid schemas and False otherwise
    """
    return auth in AUTHENTICATION_SCHEMAS.keys()


def get_auth_schema_yml(schema: int = None):
    if schema is None:
        return None
    return baseapi.SECURITY_DEFINITIONS[schema]


def create_api_files(entity, dao_class, version,
                     overwrite=False, auth_schema=None):
    entity_lower = entity.__name__.lower()

    if python_api_exists(entity_lower) and not overwrite:
        logger.debug("API already exists. Skipping generation...")
    else:
        write_api_implementation(get_python_api_filename(entity_lower),
                                 dao_class, entity)

    if version == '':
        version = '1'
    logger.info("Version for api is %s", version)

    parameters = list()
    for field in fields(entity):
        if not field.metadata.get("database", True):
            continue
        parameters.append(format_parameter(field))

    parameters = '\n'.join(parameters)

    if os.path.isfile(
            "{entity_lower}_api.yml".format(entity_lower=entity_lower)) \
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


def format_parameter(field: Field) -> str:
    """Formats the field for the query parameters in get_all function.

    :param field: The field of the dataclass
    :return: The formatted param to the YAML Swagger file
    """
    parameter_format = get_parameter_format()
    return parameter_format.format(parameter_name=field.name,
                                   parameter_location='query',
                                   parameter_type='string')


def get_parameter_format() -> str:
    """Returns the base query parameter format for the YAML Swagger file.

    :return: The base format with the fields for the format function.
    """
    return baseapi.PARAMETER_FORMAT


def write_api_implementation(api_implementation_file: str,
                             dao_class: Type, entity: Type) -> None:
    """Writes the api implementation for the entity and dao_class in the
    api_implementation_file

    :param api_implementation_file: File name to write api implementation
    :param dao_class: The dao class for the entity
    :param entity: The entity class
    :return: None
    """
    entity_lower = entity.__name__.lower()

    with open(api_implementation_file,
              'w+') as api_implementation:
        logger.info("Writing api implementation for entity %s...",
                    entity_lower)

        api_implementation.write(
            generate_base_api_for_entity(dao_class, entity))

        logger.info("Done writing api for entity %s.", entity_lower)


def generate_base_api_for_entity(dao_class: Type, entity: Type) -> str:
    """Generates the base API implementation for the dao_class and the entity.

    :param dao_class: The dao class for the entity
    :param entity: The entity
    :return: The API implementation
    """
    return baseapi.BASE_API.format(
        DAO_CLASS=dao_class.__name__,
        ENTITY=entity.__name__,
        ENTITY_LOWER=entity.__name__.lower())


def get_python_api_filename(entity_lower: str) -> str:
    """Returns the default API filename.

    :param entity_lower: The entity name in lower case.
    :return:
    """
    return "{entity_lower}_api.py".format(entity_lower=entity_lower)


def python_api_exists(entity_lower: str) -> bool:
    """ Checks if the api implementation file exists with the default name.

    :param entity_lower: The entity name in lower case.
    :return: True if the file exists, false otherwise
    """
    return os.path.isfile(get_python_api_filename(entity_lower))
