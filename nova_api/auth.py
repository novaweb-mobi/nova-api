import logging
from functools import wraps

from flask import abort
from jose import jwt, JWTError

from nova_api import JWT_SECRET

logger = logging.getLogger(__name__)


def decode_jwt_token(token):
    try:
        return jwt.decode(
            token, JWT_SECRET, algorithms=['HS256'],
            options={'verify_aud': False, 'verify_iss': False,
                     'verify_sub': False, 'verify_jti': False,
                     'verify_at_hash': False})
    except JWTError:
        unauthorize()


# pylint: disable=W0613
def unauthorize(*args, **kwargs):
    return abort(401, "Unauthorized")


def validate_jwt_claims(token_info: dict = None, add_token_info=True,
                        **kwargs):
    def make_call(function):
        for claim_name, claim_value in kwargs.items():
            if token_info.get(claim_name, None) != claim_value:
                return unauthorize

        @wraps(function)
        def wrapper(*args, **kwargs):
            logger.info(
                "Validating claims on call to %s with token %s and claims: %s",
                function, token_info, kwargs)
            if add_token_info:
                kwargs.update(("token_info", token_info))
            return function(*args, **kwargs)

        return wrapper

    return make_call
