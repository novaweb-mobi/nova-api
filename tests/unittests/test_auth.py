import os
from inspect import signature
from unittest.mock import patch

from jose import jwt
from pytest import mark, raises
from werkzeug.exceptions import Unauthorized

import nova_api
from nova_api import auth


class TestAuth:
    def test_decode_token(self):
        token_info = {"name": "test", "id": 123}
        token = jwt.encode(token_info,
                           nova_api.auth.JWT_SECRET)
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
                           nova_api.auth.JWT_SECRET)
        with raises(Unauthorized):
            auth.decode_jwt_token(token)

    @mark.parametrize("claim_name, claim_value", [
        ("iss", "novaweb"),
        ("sub", "novaweb"),
        ("jti", "123456"),
        ("aud", "novaweb"),
        ("at_hash", "1234rdg")
    ])
    def test_decode_with_reserved_claims(self, claim_name, claim_value):
        token_info = {"name": "test", "id": 123, claim_name: claim_value}
        token = jwt.encode(token_info,
                           nova_api.auth.JWT_SECRET)
        assert auth.decode_jwt_token(token) == token_info

    @staticmethod
    def test_decode_should_use_algorithms(mocker):
        mock = mocker.patch("nova_api.auth.jwt").decode
        mock.return_value = "OK"
        token = "SimpleToken"
        res = auth.decode_jwt_token(token)
        assert res == "OK"
        mock.assert_called_with(token, nova_api.auth.JWT_SECRET,
                                algorithms=nova_api.auth.JWT_ALGORITHMS,
                                options={'verify_aud': False,
                                         'verify_iss': False,
                                         'verify_sub': False,
                                         'verify_jti': False,
                                         'verify_at_hash': False})

    @staticmethod
    @patch.dict(os.environ, {"JWT_ALGORITHMS": "HS256"})
    def test_read_decode_algorithm_should_generate_algorithm_list_with_one():
        assert auth.read_decode_algorithms() == ["HS256"]

    @staticmethod
    @patch.dict(os.environ, {"JWT_ALGORITHMS": "HS256,RS256"})
    def test_read_decode_algorithm_should_generate_algorithm_list():
        assert auth.read_decode_algorithms() == ["HS256", "RS256"]

    @staticmethod
    @patch.dict(os.environ, {"JWT_ALGORITHMS": "HS256, RS256"})
    def test_read_decode_algorithm_should_tolerate_spaces():
        assert auth.read_decode_algorithms() == ["HS256", "RS256"]

    @staticmethod
    @patch.dict(os.environ, {"JWT_ALGORITHMS": "HS256, HS384, HS512  ,RS256,"
                                               "RS384, RS512,  ES256, ES384,"
                                               " ES512, TEST_ALG"})
    def test_read_decode_algorithm_should_ignore_unknown_algs():
        assert auth.read_decode_algorithms() == ["HS256", "HS384", "HS512",
                                                 "RS256", "RS384", "RS512",
                                                 "ES256", "ES384", "ES512"]

    @mark.parametrize("claim_name, claim_value, valid", [
        ("iss", "novaweb.teste", True),
        ("sub", "tester@novaweb", False),
        ("custom_claim", "testing", True)
    ])
    def test_validate_claims(self, claim_name, claim_value, valid):
        token_info = {"iss": "novaweb.teste",
                      "sub": "tester2@novaweb",
                      "custom_claim": "testing"}
        claims = {claim_name: claim_value}

        @auth.validate_jwt_claims(claims=claims)
        def test_function(keyword=None, token_info=token_info, **kwargs):
            return "token_info" in kwargs.keys()

        if not valid:
            with raises(Unauthorized):
                test_function(keyword=1234)
        else:
            assert test_function(keyword=1234)

    def test_validate_claims(self):
        token_info = {"iss": "novaweb.teste",
                      "sub": "tester2@novaweb",
                      "custom_claim": "testing"}

        @auth.validate_jwt_claims(add_token_info=False,
                                  claims=token_info)
        def test_function():
            return True

        assert test_function(token_info=token_info)

    def test_validate_claims_no_token(self):
        token_info = {"iss": "novaweb.teste",
                      "sub": "tester2@novaweb",
                      "custom_claim": "testing"}

        @auth.validate_jwt_claims(add_token_info=False,
                                  claims=token_info)
        def test_function():
            return True

        with raises(Unauthorized):
            test_function()

    def test_validate_claims_invalid(self):
        token_info = {"iss": "novaweb.teste",
                      "sub": "tester2@novaweb",
                      "custom_claim": "testing"}

        @auth.validate_jwt_claims(add_token_info=False,
                                  claims=token_info.copy())
        def test_function():
            return True

        token_info.update({"iss": "errado"})
        with raises(Unauthorized):
            test_function(token_info=token_info)

    def test_ok_if_claims_empty(self):
        token_info = {"iss": "novaweb.teste",
                      "sub": "tester2@novaweb",
                      "custom_claim": "testing"}

        @auth.validate_jwt_claims(add_token_info=False)
        def test_function():
            return True

        assert test_function(token_info=token_info)

    def test_unauthorize(self):
        with raises(Unauthorized):
            auth.unauthorize()

    def test_add_token_info_param(self):
        @auth.validate_jwt_claims(add_token_info=False,
                                  claims={})
        def test_function():
            return True

        assert signature(test_function).parameters.get('token_info')
