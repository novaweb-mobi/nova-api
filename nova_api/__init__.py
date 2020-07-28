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


api_base = """
swagger: "2.0"
info:
  description: {entity} API
  version: "1.0.0"
  title: {entity} API
consumes:
  - "application/json"
produces:
  - "application/json"

basePath: "/v{version}"

paths:
  /health:
    get:
      operationId: {entity_api}.probe
      tags:
        - "{entity}"
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

  /{entity_lower}:
    get:
      operationId: {entity_api}.read
      tags:
        - "{entity}"
      parameters:
        - name: length
          in: query
          type: integer
          required: false
          description: "Amount of {entity_lowe} to select"
        - name: offset
          in: query
          type: integer
          required: false
          description: "Amount of {entity_lower} to skip"
        - name: filters
          in: body
          type: object
          required: false
      summary: "Lists all {entity} available"
      description: |
        "Lists all {entity} in the database. May be filtered by all fields."
      responses:
        200:
          description: "Available {entity}"
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
                    items:
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
      operationId: {entity_api}.create
      tags:
        - "{entity}"
      parameters:
        - name: entity
          in: body
          type: object
          required: true
          description: "{entity} to add"
      summary: "Create a new {entity}."
      description: |
        "Creates a new {entity} in the database"
      responses:
        201:
          description: "{entity} created"
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
  
  /{entity_lower}/{id_}:
    get:
      operationId: {entity_api}.read_one
      tags:
        - "{entity}"
      parameters:
        - name: id_
          in: path
          type: string
          required: true
          description: "Id of {entity_lower} to select"
      summary: "Recover {entity_lower}"
      description: |
        "Select {entity_lower} by Id"
      responses:
        201:
          description: "{entity}"
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
      operationId: {entity_api}.update
      tags:
        - "{entity}"
      parameters:
        - name: id_
          in: path
          type: string
          required: true
          description: "Id of {entity_lower} to select"
        - name: entity
          in: body
          type: object
          required: true
          description: "{entity} data"
      summary: "Update {entity}"
      description: |
        "Update {entity} in database."
      responses:
        200:
          description: "{entity}"
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
      operationId: {entity_api}.delete
      tags:
        - "{entity}"
      parameters:
        - name: id_
          in: path
          type: string
          required: true
          description: "Id of {entity_lower} to select"
      summary: "Delete {entity}"
      description: |
        "Delete {entity} in database."
      responses:
        200:
          description: "{entity}"
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

parameter = \
    """        - name: {parameter_name}
          in: {parameter_location}
          type: {parameter_type}
          required: false"""
