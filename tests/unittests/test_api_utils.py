from json import dumps

from mock import Mock, call
from pytest import mark

import nova_api


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
    def test_success_response(self, mocker, data):
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
