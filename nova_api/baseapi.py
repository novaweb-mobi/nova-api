BASE_API = """from dataclasses import fields

from nova_api.dao.generic_sql_dao import GenericSQLDAO
from nova_api import error_response, success_response, use_dao

from {DAO_CLASS} import {DAO_CLASS}
from {ENTITY} import {ENTITY}


@use_dao({DAO_CLASS}, "API Unavailable")
def probe(dao: GenericSQLDAO = None):
    total, _ = dao.get_all(length=1, offset=0, filters=None)
    return success_response(message="API Ready",
                            data={{"available": total}})


@use_dao({DAO_CLASS}, "Unable to list {ENTITY_LOWER}")
def read(length: int = 20, offset: int = 0,
         dao: GenericSQLDAO = None, **kwargs):
    filters = dict()

    entity_attributes = [field.name for field in fields({ENTITY})]

    for key, value in kwargs.items():
        if key not in entity_attributes:
            continue

        filters[key] = value.split(',') \\
                       if len(str(value).split(',')) > 1 \\
                       else value

    total, results = dao.get_all(length=length, offset=offset,
                                 filters=filters if filters else None)
    return success_response(message="List of {ENTITY_LOWER}",
                            data={{"total": total, "results": [dict(result)
                                                              for result
                                                              in results]}})


@use_dao({DAO_CLASS}, "Unable to retrieve {ENTITY_LOWER}")
def read_one(id_: str, dao: GenericSQLDAO = None):
    result = dao.get(id_=id_)

    if not result:
        return success_response(status_code=404,
                                message="{ENTITY} not found in database",
                                data={{"id_": id_}})

    return success_response(message="{ENTITY} retrieved",
                            data={{"{ENTITY}": dict(result)}})


@use_dao({DAO_CLASS}, "Unable to create {ENTITY_LOWER}")
def create(entity: dict, dao: GenericSQLDAO = None):
    entity_to_create = {ENTITY}(**entity)

    dao.create(entity=entity_to_create)

    return success_response(message="{ENTITY} created",
                            data={{"{ENTITY}": dict(entity_to_create)}})


@use_dao({DAO_CLASS}, "Unable to update {ENTITY_LOWER}")
def update(id_: str, entity: dict, dao: GenericSQLDAO = None):
    entity_to_update = dao.get(id_)

    if not entity_to_update:
        return error_response(status_code=404,
                              message="{ENTITY} not found",
                              data={{"id_": id_}})

    entity_fields = dao.fields.keys()

    for key, value in entity.items():
        if key not in entity_fields:
            raise KeyError("{{key}} not in {{entity}}"
                           .format(key=key,
                                   entity=dao.return_class))

        entity_to_update.__dict__[key] = value

    dao.update(entity_to_update)

    return success_response(message="{ENTITY} updated",
                            data={{"{ENTITY}": dict(entity_to_update)}})


@use_dao({DAO_CLASS}, "Unable to delete {ENTITY_LOWER}")
def delete(id_: str, dao: GenericSQLDAO):
    entity = dao.get(id_=id_)

    if not entity:
        return error_response(status_code=404,
                              message="{ENTITY} not found",
                              data={{"id_": id_}})

    dao.remove(entity)

    return success_response(message="{ENTITY} deleted",
                            data={{"{ENTITY}": dict(entity)}})
"""

API_SWAGGER = """swagger: "2.0"
info:
  description: {ENTITY} API
  version: "1.0.0"
  title: {ENTITY} API
consumes:
  - "application/json"
produces:
  - "application/json"

basePath: "/v{VERSION}/{ENTITY_LOWER}"

paths:
  /health:
    get:
      operationId: {ENTITY_LOWER}_api.probe
      tags:
        - "{ENTITY}"
      summary: "Status check"
      description: "Verifies if the API is ready."
      responses:
        200:
          description: "API ready"
          schema:
            type: object
            properties:
              message:
                type: string
              data:
                type: object
                properties:
                  available:
                    type: integer
        500:
          description: "API not ready"

  /:
    get:
      operationId: {ENTITY_LOWER}_api.read{SECURITY}
      tags:
        - "{ENTITY}"
      parameters:
        - name: length
          in: query
          type: integer
          required: false
          description: "Amount of {ENTITY_LOWER} to select"
        - name: offset
          in: query
          type: integer
          required: false
          description: "Amount of {ENTITY_LOWER} to skip"
{PARAMETERS}
      summary: "Lists all {ENTITY} available"
      description: |
        "Lists all {ENTITY} in the database. May be filtered by all fields."
      responses:
        200:
          description: "Available {ENTITY}"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  total:
                    type: integer
                  results:
                    type: array
                    properties:
                      entities:
                        type: object
        500:
          description: "An error ocurred"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  error:
                    type: string
    post:
      operationId: {ENTITY_LOWER}_api.create{SECURITY}
      tags:
        - "{ENTITY}"
      parameters:
        - name: entity
          in: body
          schema:
            type: object
          required: true
          description: "{ENTITY} to add"
      summary: "Create a new {ENTITY}."
      description: |
        "Creates a new {ENTITY} in the database"
      responses:
        201:
          description: "{ENTITY} created"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  entity:
                    type: object
        500:
          description: "An error ocurred"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  error:
                    type: string

  /{{id_}}:
    get:
      operationId: {ENTITY_LOWER}_api.read_one{SECURITY}
      tags:
        - "{ENTITY}"
      parameters:
        - name: id_
          in: path
          type: string
          required: true
          description: "Id of {ENTITY_LOWER} to select"
      summary: "Recover {ENTITY_LOWER}"
      description: |
        "Select {ENTITY_LOWER} by Id"
      responses:
        201:
          description: "{ENTITY}"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  entity:
                    type: object
        500:
          description: "An error ocurred"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  error:
                    type: string
    put:
      operationId: {ENTITY_LOWER}_api.update{SECURITY}
      tags:
        - "{ENTITY}"
      parameters:
        - name: id_
          in: path
          type: string
          required: true
          description: "Id of {ENTITY_LOWER} to select"
        - name: entity
          in: body
          schema:
            type: object
          required: true
          description: "{ENTITY} to add"
      summary: "Update {ENTITY}"
      description: |
        "Update {ENTITY} in database."
      responses:
        200:
          description: "{ENTITY}"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  entity:
                    type: object
        500:
          description: "An error ocurred"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  error:
                    type: string
    delete:
      operationId: {ENTITY_LOWER}_api.delete{SECURITY}
      tags:
        - "{ENTITY}"
      parameters:
        - name: id_
          in: path
          type: string
          required: true
          description: "Id of {ENTITY_LOWER} to select"
      summary: "Delete {ENTITY}"
      description: |
        "Delete {ENTITY} in database."
      responses:
        200:
          description: "{ENTITY}"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  entity:
                    type: object
        500:
          description: "An error ocurred"
          schema:
            type: object
            properties:
              success:
                type: boolean
              message:
                type: string
              data:
                type: object
                properties:
                  error:
                    type: string
"""

PARAMETER_FORMAT = \
    """        - name: {parameter_name}
          in: {parameter_location}
          type: {parameter_type}
          required: false"""

SECURITY_PARAMETERS = ["""
      security:
        - jwt: ['secret']
"""]

SECURITY_DEFINITIONS = ["""
securityDefinitions:
  jwt:
    type: apiKey
    name: Authorization
    in: header
    x-authentication-scheme: Bearer
    x-bearerInfoFunc: nova_api.auth.decode_jwt_token
"""]
