import os
import time
from json import dumps
from os.path import isfile as is_file

from EntityDAO import EntityDAO
from EntityForTest import EntityForTest
from EntityForTestDAO import EntityForTestDAO
from connexion.spec import Specification
from mock import Mock, call
from pytest import mark, raises

import nova_api
from nova_api.exceptions import NovaAPIException

NOVA_API_ERROR_RESPONSE = "nova_api.error_response"
SAMPLE_ERROR_MESSAGE = "A error test"


class SimpleCustomException(NovaAPIException):
    pass


# pylint: disable=R0201
class TestAPIUtils:
    @mark.parametrize("status_code", [404, 400, 500, 200, 201])
    @mark.parametrize("success", [True, False])
    @mark.parametrize("message, data", [
        ("message1", {"test": "Not So Ok", "test2": True, "test3": 3}),
        ("message2", {"test": "OK", "test2": True, "test3": 3})
    ])
    def test_default_response(self, mocker, message, data,
                              success, status_code):
        make_response_patch = mocker.patch("nova_api.make_response",
                                           return_value=message)
        mocker.patch("nova_api.jsonify",
                     side_effect=lambda *args: dumps(*args))

        ret_val = nova_api.default_response(success,
                                            status_code,
                                            message,
                                            data)
        assert make_response_patch.mock_calls == [
            call(dumps({"success": success, "message": message, "data": data}),
                 status_code,
                 {'Content-type': 'application/json'})
        ]
        assert ret_val == message

    @mark.parametrize("data", [None, {"test": "mydata"}])
    def test_success_response(self, mocker, data):
        default_response_mock = mocker.patch("nova_api.default_response",
                                             return_value="OK")
        default_response_mock.return_value = 1
        ret_val = nova_api.success_response(data=data)
        assert (default_response_mock.mock_calls == [
            call(success=True,
                 status_code=200,
                 message="OK",
                 data={} if data is None else data)])
        assert ret_val == 1

    @mark.parametrize("data", [None, {"test": "mydata"}])
    def test_error_response(self, mocker, data):
        default_response_mock = mocker.patch("nova_api.default_response",
                                             return_value="OK")
        nova_api.error_response(data=data)
        assert (default_response_mock.mock_calls == [
            call(success=False,
                 status_code=500,
                 message="Error",
                 data={} if data is None else data)])

    def test_use_dao_should_open_and_close_dao(self, mocker):
        my_mock = Mock()

        @nova_api.use_dao(dao_class=my_mock, retries=1)
        def test_decorated_function(**kwargs):
            return kwargs.get('dao') == my_mock.return_value

        ret = test_decorated_function()
        assert my_mock.mock_calls == [call(), call().close()] and ret

    def test_use_dao_db_args(self, mocker):
        my_mock = Mock()

        @nova_api.use_dao(dao_class=my_mock,
                          dao_parameters={"pooled": False,
                                          "database_args": {"ssl_ca": "file"}},
                          retries=1)
        def test(**kwargs):
            return kwargs.get('dao') == my_mock.return_value

        ret = test()
        assert my_mock.mock_calls == [call(database_args={"ssl_ca": "file"},
                                           pooled=False),
                                      call().close()] and ret

    def test_use_dao_other_params(self, mocker):
        my_mock = Mock()

        @nova_api.use_dao(dao_class=my_mock,
                          dao_parameters={"pooled": False,
                                          "database_args": {"ssl_ca": "file"},
                                          "host": "localhost"},
                          retries=1)
        def test(**kwargs):
            return kwargs.get('dao') == my_mock.return_value

        ret = test()
        assert my_mock.mock_calls == [call(database_args={"ssl_ca": "file"},
                                           pooled=False,
                                           host="localhost"),
                                      call().close()] and ret

    def test_use_dao_pooled(self, mocker):
        my_mock = Mock()

        @nova_api.use_dao(dao_class=my_mock, dao_parameters={"pooled": True},
                          retries=1)
        def test(**kwargs):
            return kwargs.get('dao') == my_mock.return_value

        ret = test()
        assert my_mock.mock_calls == [call(pooled=True),
                                      call().close()] and ret

    def test_use_dao_retry(self, mocker):
        my_mock = Mock()
        mocker.patch(NOVA_API_ERROR_RESPONSE,
                     return_value="NOT OK")

        def raise_exception():
            raise ConnectionError("Teste")

        my_mock.side_effect = raise_exception

        @nova_api.use_dao(dao_class=my_mock, retries=3, retry_delay=1)
        def test(**kwargs):
            return kwargs.get('dao') == my_mock.return_value

        start = time.time()
        ret = test()
        end = time.time()

        assert my_mock.mock_calls == [call(), call(), call()]
        assert end - start > 3

    def test_use_dao_exception(self, mocker):
        my_mock = Mock()
        mocker.patch(NOVA_API_ERROR_RESPONSE,
                     return_value="NOT OK")

        @nova_api.use_dao(dao_class=my_mock, retries=1)
        def test(**kwargs):
            if kwargs.get('dao') == my_mock.return_value:
                raise Exception()

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()]
        assert ret == "NOT OK"

    def test_use_dao_custom_exception_debug(self, mocker):
        nova_api.DEBUG = True
        my_mock = Mock()
        mocker.patch(NOVA_API_ERROR_RESPONSE,
                     side_effect=lambda *args, **kwargs
                     : (args, kwargs))

        @nova_api.use_dao(dao_class=my_mock, retries=1)
        def test(**kwargs):
            raise SimpleCustomException(404, "something not found",
                                        1, "debug message")

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()]
        assert ret == ((), {"status_code": 404, "message": "something not found",
                        "data": {"error_code": 1, "debug": "debug message"}})

    def test_use_dao_custom_exception_no_debug(self, mocker):
        nova_api.DEBUG = False
        my_mock = Mock()
        mocker.patch(NOVA_API_ERROR_RESPONSE,
                     side_effect=lambda *args, **kwargs
                     : (args, kwargs))

        @nova_api.use_dao(dao_class=my_mock, retries=1)
        def test(**kwargs):
            raise SimpleCustomException(404, "something not found",
                                        1, "debug message")

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()]
        assert ret == ((), {"status_code": 404, "message": "something not found",
                        "data": {"error_code": 1}})

    @staticmethod
    def test_use_dao_exception_debug(mocker):
        nova_api.DEBUG = True
        my_mock = Mock()
        mocker.patch(NOVA_API_ERROR_RESPONSE,
                     side_effect=lambda **kwargs: kwargs)

        @nova_api.use_dao(dao_class=my_mock, retries=1)
        def test(**kwargs):
            if kwargs.get('dao') == my_mock.return_value:
                raise Exception(SAMPLE_ERROR_MESSAGE)

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()]
        assert ret == {"message": "Erro", "data": {"error": SAMPLE_ERROR_MESSAGE}}

    @staticmethod
    def test_use_dao_exception_no_debug(mocker):
        nova_api.DEBUG = False
        my_mock = Mock()
        mocker.patch(NOVA_API_ERROR_RESPONSE,
                     side_effect=lambda **kwargs: kwargs)

        @nova_api.use_dao(dao_class=my_mock, retries=1)
        def test(**kwargs):
            if kwargs.get('dao') == my_mock.return_value:
                raise Exception(SAMPLE_ERROR_MESSAGE)

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()]
        assert ret == {"message": "Erro", "data":
            {"error": "Something went wrong... Please try again later."}}

    def test_generate_valid_api_yml(self):
        nova_api.create_api_files(EntityForTest, EntityDAO, '1')
        gen_spec = Specification.load('entityfortest_api.yml')
        base_spec = Specification.load(
            'tests/unittests/entityfortest_api_result.yml'
        )
        assert gen_spec == base_spec
        os.remove('entityfortest_api.yml')
        os.remove('entityfortest_api.py')

    @mark.parametrize("schema_name, schema_text", [
        (nova_api.JWT, nova_api.baseapi.SECURITY_DEFINITIONS[0]),
        (None, None)
    ])
    def test_get_authorization_schema_yml(self, schema_name, schema_text):
        assert nova_api.get_auth_schema_yml(schema_name) == schema_text

    def test_generate_valid_api_yml_with_jwt(self):
        nova_api.create_api_files(EntityForTest, EntityDAO,
                                  '1', auth_schema=nova_api.JWT)
        gen_spec = Specification.load('entityfortest_api.yml')
        base_spec = Specification.load(
            'tests/unittests/entityfortest_api_jwt_result.yml'
        )
        with open('entityfortest_api.yml') as f:
            print(f.read())
        os.remove('entityfortest_api.yml')
        os.remove('entityfortest_api.py')
        assert gen_spec == base_spec

    def test_generate_api_py(self):
        nova_api.create_api_files(EntityForTest, EntityDAO, '1')
        gen_spec = ''
        with open('entityfortest_api.py', 'r') as f:
            gen_spec = f.read()
        with open('tests/unittests/entityfortest_api_result.py') as f:
            base_spec = f.read()
        os.remove('entityfortest_api.yml')
        os.remove('entityfortest_api.py')
        assert gen_spec == base_spec

    def test_not_overwrite_file(self, mocker):
        mock = mocker.patch.object(nova_api.os.path,
                                   "isfile",
                                   return_value=True)
        nova_api.create_api_files(EntityForTest, EntityDAO, '')
        assert not is_file('entityfortest_api.yml')
        assert not is_file('entityfortest_api.py')

    @mark.parametrize("call_, argv", [
        (
                call(EntityForTest, EntityDAO, '2',
                     overwrite=False, auth_schema=None),
                ["python",
                 "-e", "EntityForTest",
                 "-d", "EntityDAO",
                 "-v", "2"]
        ),
        (
                call(EntityForTest, EntityDAO, '2',
                     overwrite=False, auth_schema=0),
                ["python",
                 "-e", "EntityForTest",
                 "-d", "EntityDAO",
                 "-v", "2",
                 "-a", "JWT"]
        ),
        (
                call(EntityForTest, EntityDAO, '2',
                     overwrite=True, auth_schema=0),
                ["python",
                 "-e", "EntityForTest",
                 "-d", "EntityDAO",
                 "-v", "2",
                 "-a", "JWT",
                 "-o"]
        ),
        (
                call(EntityForTest, EntityDAO, '',
                     overwrite=False, auth_schema=None),
                ["python",
                 "-e", "EntityForTest",
                 "-d", "EntityDAO"]
        ),
        (
                call(EntityForTest, EntityForTestDAO, '',
                     overwrite=True, auth_schema=None),
                ["python",
                 "-e", "EntityForTest",
                 "-o"]
        ),
        (
                call(EntityForTest, EntityForTestDAO, '',
                     overwrite=False, auth_schema=None),
                ["python",
                 "-e", "EntityForTest"]
        )
    ])
    def test_generate_api_cli(self, mocker, call_, argv):
        nova_api.sys.argv = argv
        create_api_files_mock = mocker.patch.object(nova_api,
                                                    "create_api_files")
        nova_api.generate_api()
        assert create_api_files_mock.mock_calls == [call_]

    def test_generate_api_cli_get_opt_error(self, mocker):
        mocker.patch.object(nova_api,
                            "create_api_files")

        def raise_exception(*args, **kwargs):
            raise nova_api.getopt.GetoptError("Teste")

        mocker.patch.object(nova_api.getopt,
                            "getopt",
                            side_effect=raise_exception)

        with raises(SystemExit) as pytest_wrapped_e:
            nova_api.generate_api()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 65

    @mark.parametrize("argv, status_code", [
        (
                ["python", "-e", "EntityFail"],
                74
        ),
        (
                ["python", "-e", "EntityForTest", "-d", "MyDAO"],
                74
        ),
        (
                ["python"],
                64
        ),
        (
                ["python", "-v", "2"],
                64
        ),
        (
                ["python",
                 "-e", "EntityForTest",
                 "-a", "InvSchema"],
                65
        )
    ])
    def test_generate_api_cli_not_exists(self, mocker, argv, status_code):
        # We don't expect it to be called, but if no excpetions are thrown
        # and it is called it will generate api files if not mocked
        mocker.patch.object(nova_api,
                            "create_api_files")

        nova_api.sys.argv = argv
        with raises(SystemExit) as pytest_wrapped_e:
            nova_api.generate_api()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == status_code

    @mark.parametrize("exc_type", [
        IOError,
        FileExistsError,
        FileNotFoundError,
        OSError,
        EOFError,
        IsADirectoryError
    ])
    def test_generate_api_create_fail(self, mocker, exc_type):
        def raise_exception(*args, **kwargs):
            raise exc_type()

        mock = mocker.patch.object(nova_api,
                                   "create_api_files")
        mock.side_effect = raise_exception
        nova_api.sys.argv = ["python",
                             "-e", "EntityForTest"]
        with raises(SystemExit) as pytest_wrapped_e:
            nova_api.generate_api()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 73
