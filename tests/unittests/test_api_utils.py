import os
from os.path import isfile as is_file
import sys
from dataclasses import dataclass
from json import dumps

from connexion.spec import Specification
from mock import Mock, call
from pytest import mark, raises

import nova_api
from EntityDAO import EntityDAO
from EntityForTest import EntityForTest
from EntityForTestDAO import EntityForTestDAO


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

    def test_use_dao(self, mocker):
        my_mock = Mock()

        @nova_api.use_dao(dao_class=my_mock)
        def test(**kwargs):
            return kwargs.get('dao') == my_mock.return_value

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()] and ret

    def test_use_dao_exception(self, mocker):
        my_mock = Mock()
        mocker.patch("nova_api.error_response",
                     return_value="NOT OK")

        @nova_api.use_dao(dao_class=my_mock)
        def test(**kwargs):
            if kwargs.get('dao') == my_mock.return_value:
                raise Exception()

        ret = test()
        assert my_mock.mock_calls == [call(), call().close()]
        assert ret == "NOT OK"

    def test_generate_valid_api_yml(self):
        nova_api.create_api_files(EntityForTest, EntityDAO, '1')
        gen_spec = Specification.load('entityfortest_api.yml')
        base_spec = Specification.load(
            'unittests/entityfortest_api_result.yml'
        )
        assert gen_spec == base_spec
        os.remove('entityfortest_api.yml')
        os.remove('entityfortest_api.py')

    def test_generate_api_py(self):
        nova_api.create_api_files(EntityForTest, EntityDAO, '1')
        gen_spec = ''
        with open('entityfortest_api.py', 'r') as f:
            gen_spec = f.read()
        with open('unittests/entityfortest_api_result.py') as f:
            base_spec = f.read()
            assert gen_spec == base_spec
        os.remove('entityfortest_api.yml')
        os.remove('entityfortest_api.py')

    def test_not_overwrite_file(self, mocker):
        mock = mocker.patch.object(nova_api.os.path,
                            "isfile",
                            return_value=True)
        nova_api.create_api_files(EntityForTest, EntityDAO, '')
        assert not is_file('entityfortest_api.yml')
        assert not is_file('entityfortest_api.py')

    @mark.parametrize("call_, argv", [
        (
                call(EntityForTest, EntityDAO, '2'),
                ["python",
                 "-e", "EntityForTest",
                 "-d", "EntityDAO",
                 "-v", "2"]
        ),
        (
                call(EntityForTest, EntityDAO, ''),
                ["python",
                 "-e", "EntityForTest",
                 "-d", "EntityDAO"]
        ),
        (
                call(EntityForTest, EntityForTestDAO, ''),
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
        assert pytest_wrapped_e.value.code == 1

    @mark.parametrize("argv, status_code", [
        (
                ["python", "-e", "EntityFail"],
                3
        ),
        (
                ["python", "-e", "EntityForTest", "-d", "MyDAO"],
                3
        ),
        (
                ["python"],
                2
        ),
        (
                ["python", "-v", "2"],
                2
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
