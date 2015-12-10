import logging
import functools

from werkzeug.exceptions import HTTPException

from flask import (
    Response,
    jsonify,
    )


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


def json_error_handler(error):
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

    response = jsonify(error={'code': response_code, 'message': result, 'data': error_data})
    response.status_code = int(response_code)
    for k, v in headers.items():
        response.headers[k] = v
    # response.headers.update(headers)
    return response


def json_response(result, *args, **kwargs):
    resp = jsonify(result=result)
    resp.mimetype = 'application/json'
    return resp

def returns_json(callback):
    @functools.wraps(callback)
    def _returns_json_impl(*args, **kwargs):
        return json_response(callback(*args, **kwargs))
    return _returns_json_impl
