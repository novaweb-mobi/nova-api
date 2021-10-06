import logging
from inspect import Parameter, Signature, signature

from flask import abort
from jose import JWTError, jwt
from makefun import add_signature_parameters, wraps
from werkzeug.exceptions import HTTPException

from nova_api import JWT_SECRET

logger = logging.getLogger(__name__)


# pylint: disable=R1710
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
        logger.info("Decoding Token %s", token)
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


def validate_jwt_claims(add_token_info: bool = False, claims=None):
    """Decorator to authenticate and authorize access to API endpoint

    Checks if the received claims are present in token_info and if they match \
    the necessary values. If the decorated function doesn't have a keyword \
    argument `token_info`, it will be added by the decorator.

    Example:
        In the following example, if the `token_info` doesn't have the iss \
        claim with value "novaweb", `my_endpoint` won't be called. ::

            @validate_jwt_claims(claims = {"iss":"novaweb"})
            def my_endpoint():
                ...

    :param claims: Dictionary with the necessary claims to authorize the use\
    of the endpoint

    :param add_token_info: If set to true, token_info will be passed to \
    decorated function as `token_info` keyword argument.

    :return: Decorated function if token contains correct claims or \
    unauthorize.
    """
    if claims is None:
        claims = {}

    def make_call(function):
        new_func_sig = _check_and_update_signature(signature(function))

        @wraps(function, new_sig=new_func_sig)
        def wrapper(*args, **kwargs):
            token_info = kwargs.get('token_info', None)

            if not _check_claims(token_info, claims):
                return unauthorize()

            logger.info("Validated claims on call to %s "
                        "with token %s and claims: %s",
                        function, token_info, kwargs)
            if not add_token_info:
                kwargs.pop("token_info")

            return function(*args, **kwargs)

        return wrapper

    return make_call


def _check_and_update_signature(func_sig: Signature):
    """
    Checks that the function signature includes token_info parameter \
    and includes it if not.

    :param func_sig: Original signature of the function.
    :return: Signature of the function with the token_info parameter.
    """
    new_sig = func_sig
    if not func_sig.parameters.get('token_info', None):
        token_info_param = Parameter('token_info',
                                     kind=Parameter.KEYWORD_ONLY,
                                     default=None)
        new_sig = add_signature_parameters(func_sig,
                                           last=[token_info_param])
    return new_sig


def _check_claims(token_info: dict, claims: dict) -> bool:
    """
    Checks that token_info is a dict of claims and that contains the \
    claims in the claims dict.
    :param token_info: Claims of the received token.
    :param claims: Claims to check on the received token.
    :return: True if claims are valid and False otherwise.
    """
    if not token_info or not isinstance(token_info, dict):
        logger.error("Token info not received in validate_jwt_claims!")
        return False

    for claim_name, claim_value in claims.items():
        if token_info.get(claim_name, None) != claim_value:
            logger.error("Token claim %s wih value "
                         "%s doesn't match expected "
                         "value %s!",
                         claim_name,
                         token_info.get(claim_name, None),
                         claim_value)
            return False
    return True
