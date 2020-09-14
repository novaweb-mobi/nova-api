Authentication/Authorization module
===================================

Quick Start
***********

As of this version, NovaAPI supports authentication and authorization with JWT tokens. To use JWT tokens, it
is necessary necessary to set the environment variable `JWT_SECRET` with the key used to validate the JWS
signature.

If you are using the file generation functionalities, you may call it with `auth_schema=nova_api.JWT` to
automatically add the JWT validation to all endpoints except health check. This
default configuration will only validate exp(expiry timestamp), iat(issued at) and
nbf(not before).

If you are not using the file generation, you may add the following security definition to the end of your
api configuration file (for swagger 2.0). ::

    securityDefinitions:
        jwt:
            type: apiKey
            name: Authorization
            in: header
            x-authentication-scheme: Bearer
            x-bearerInfoFunc: nova_api.auth.decode_jwt_token



The `x-bearerInfoFunc` indicates the function which will validate the token. After adding the definition,
you may apply it to an endpoint as follows: ::

    /:
      get:
        operationId: my_api.read
        security:
          - jwt: ['secret']
        tags:
         - "my_tag"
        parameters:
         ...
        summary: "Lists all things available"
        description: "Lists all things in the database. May be filtered by all fields."
        responses:
          200:
      ...

After adding the security option, the JWT decoding will occur before the call to operationId.
If you need to validate claims other than those related to emission date and expiration, you may
use the `validate_jwt_claims` decorator. In the next example, we validate if the issuer was `novaweb`
using the `iss` claim. As of this moment, there is no support for lists of possible values in claims. ::

    from nova_api.auth import validade_jwt_claims

    @validate_jwt_claims(iss="novaweb")
    def read():
        ...

If you need to check a claim which needs to be changed dynamically, the best option is to not use
the `validate_jwt_claims` decorator and add the `token_info` keyword argument to the operation.
Remember that it is still necessary to add the security definitions to the yaml file as shown above. ::

    def read(token_info: dict = None):
        # Now we can check claims here
        if token_info.get("my_claim") == "my_value":
            do_something
        ...

If you have a combination of dynamic and static claims, you may use the `add_token_info` parameter of the
`validate_jwt_claims` decorator to forward the token info for your operation. You have to add token_info as
a keyword argument or `**kwargs` ::

    from nova_api.auth import validade_jwt_claims

    @validate_jwt_claims(iss="novaweb", add_token_info=True)
    def read(token_info: dict = None):
        # Now we can check other claims here
        if token_info.get("my_claim") == "my_value":
            do_something
        ...

Module Documentation
********************

.. automodule:: nova_api.auth
    :members: