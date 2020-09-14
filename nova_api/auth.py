import logging
from functools import wraps

from flask import abort
from jose import jwt, JWTError
from werkzeug.exceptions import HTTPException

from nova_api import JWT_SECRET

logger = logging.getLogger(__name__)


def decode_jwt_token(token: str) -> dict:
    """Function to decode JWT token.

    Decodes JWT Token using JWT_SECRET environment variable as key. During \
    decoding the JWS(signature) is validated along with exp(expiry timestamp),\
    iat(issued at timestamp) and nbf(not before) claims. No other claims are \
    validated and they should be validated with the validate_jwt_claims \
    decorator.

    :param token: JWT token base64 encoded and signed
    :return: Dictionary of token claims if JWT is valid or raises \
    unauthorized if invalid
    """
    try:
        return jwt.decode(
            token, JWT_SECRET, algorithms=['HS256'],
            options={'verify_aud': False, 'verify_iss': False,
                     'verify_sub': False, 'verify_jti': False,
                     'verify_at_hash': False})
    except JWTError:
        logger.error("Unauthorized request!", exc_info=True)
        unauthorize()


# pylint: disable=W0613
def unauthorize(*args, **kwargs) -> HTTPException:
    """Aborts API call with status code 401 and message "Unauthorized"

    This functions takes any argument as it is used by the auth decorators.

    :return: HTTPException with status code 401
    """
    return abort(401, "Unauthorized")


def validate_jwt_claims(add_token_info: bool = False, claims={}):
    """Decorator to authenticate and authorize access to API endpoint

    Checks if the received claims are present in token_info and if they match \
    the necessary values.

    Example:
        In the following example, if the `token_info` doesn't have the iss \
        claim with value "novaweb", `my_endpoint` won't be called. ::

            @validate_jwt_claims(claims = {iss="novaweb"})
            def my_endpoint():
                ...

    :param claims: Dictionary with the necessary claims to authorize the use\
    of the endpoint

    :param add_token_info: If set to true, token_info will be passed to \
    decorated function as `token_info` keyword argument.

    :return: Decorated function if token contains correct claims or \
    unauthorize.
    """
    def make_call(function):

        @wraps(function)
        def wrapper(*args, **kwargs):
            token_info = kwargs.get('token_info', None)
            print(token_info)

            if not token_info:
                logger.error("Token info not received in validate_jwt_claims!")
                return unauthorize()

            for claim_name, claim_value in claims.items():
                if token_info.get(claim_name, None) != claim_value:
                    logger.error(f"Token claim {claim_name} wih value "
                                 f"{claim_value} doesn't match expected "
                                 f"value!")
                    return unauthorize()

            logger.info(
                "Validating claims on call to %s with token %s and claims: %s",
                function, token_info, kwargs)
            if not add_token_info:
                kwargs.pop("token_info")
            return function(*args, **kwargs)

        return wrapper

    return make_call
