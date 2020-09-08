from jose import jwt
from werkzeug.exceptions import Unauthorized
from pytest import raises

import nova_api
from nova_api import auth

class TestAuth:
    def test_decode_token(self):
        token_info = {"name": "test", "id": 123}
        token = jwt.encode(token_info,
                           nova_api.JWT_SECRET)
        assert auth.decode_jwt_token(token) == token_info

    def test_fail_decode(self):
        token_info = {"name": "test", "id": 123}
        token = jwt.encode(token_info,
                           "ab23")
        with raises(Unauthorized):
            auth.decode_jwt_token(token)

    def test_decode_expired(self):
        token_info = {"name": "test", "id": 123, "exp": "914241600"}
        token = jwt.encode(token_info,
                           nova_api.JWT_SECRET)
        with raises(Unauthorized):
            auth.decode_jwt_token(token)
