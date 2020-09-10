from jose import jwt
from werkzeug.exceptions import Unauthorized
from pytest import mark, raises

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

    @mark.parametrize("claim_name, claim_value, valid", [
        ("iss", "novaweb.teste", True),
        ("sub", "tester@novaweb", False),
        ("custom_claim", "testing", True)
    ])
    def test_validate_claims(self, claim_name, claim_value, valid):
        token_info = {"iss": "novaweb.teste",
                      "sub": "tester2@novaweb",
                      "custom_claim": "testing"}
        kwargs = {claim_name: claim_value}

        @auth.validate_jwt_claims(token_info=token_info, **kwargs)
        def test_function(keyword=None):
            return keyword == 1234

        if not valid:
            with raises(Unauthorized):
                test_function()
        else:
            assert test_function(keyword=1234)

    def test_unauthorize(self):
        with raises(Unauthorized):
            auth.unauthorize()
