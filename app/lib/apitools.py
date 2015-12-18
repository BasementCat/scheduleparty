import math
import logging
import functools


logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, *args):
        # Code, message, data, headers
        defaults = [500, 'Error', {}, {}]
        args = list(args)
        for i in range(len(defaults)):
            try:
                args[i]
                assert args[i]
            except IndexError:
                args.append(defaults[i])
            except AssertionError:
                args[i] = defaults[i]
        super(ApiError, self).__init__(*args)


class ApiPlugin(object):
    name = 'api'
    api = 2

    def apply(self, callback, route):
        @functools.wraps(callback)
        def _api_plugin_impl(*args, **kwargs):
            try:
                out = callback(*args, **kwargs)
                if isinstance(out, tuple):
                    out = [a or b for a, b in zip(list(out), [None, 200, {}])]
                else:
                    out = [out, 200, {}]
                response, code, headers = out
                logger.warning("TODO: handle code and headers")
                if 'result' not in response:
                    response = {'result': response}
                return response
            except Exception as e:
                logger.error("%s", str(error), exc_info=True)
                if isinstance(error, ApiError):
                    response_code, result, error_data, headers = error
                elif isinstance(error, HTTPException):
                    result = str(error)
                    response_code = error.code
                    error_data = {}
                    headers = {}
                else:
                    result = 'Internal Server Error'
                    response_code = 500
                    error_data = {}
                    headers = {}

                logger.warning("TODO: handle code and headers")
                return {'error': {'code': response_code, 'message': result, 'data': error_data}}
        return _api_plugin_impl
