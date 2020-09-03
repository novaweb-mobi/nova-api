import os

from flask import abort
from jose import jwt, JWTError

from nova_api import JWT_SECRET


def decode_jwt_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except JWTError as e:
        return abort(401, "Unauthorized")
