import functools

from werkzeug.exceptions import HTTPException

from flask import (
    Response,
    jsonify,
    )


class ApiError(Exception):
    def __init__(self, *args):
        defaults = [500, 'Error', {}]
        args = list(args)
        for i in range(len(defaults)):
            try:
                args[i]
            except IndexError:
                args.append(defaults[i])
        super(ApiError, self).__init__(*args)


def json_error_handler(error):
    if isinstance(error, ApiError):
        response_code, result, error_data = error
    elif isinstance(error, HTTPException):
        result = str(error)
        response_code = error.code
        error_data = {}
    else:
        result = 'Internal Server Error'
        response_code = 500
        error_data = {}

    response = jsonify({'error': {'code': response_code, 'message': result, 'data': error_data}})
    response.status_code = int(response_code)
    return response


class JSONResponse(Response):
    def __init__(self, result, *args, **kwargs):
        result = {'result': result}
        kwargs['response'] = result
        super(Response, self).__init__(*args, **kwargs)


def json_response(callback):
    @functools.wraps(callback)
    def _json_response(*args, **kwargs):
        result = None
        response_code = None
        response_headers = {}

        raw_result = callback(*args, **kwargs)
        if isinstance(raw_result, tuple):
            if len(raw_result) > 2:
                result, response_code, response_headers = raw_result[:2]
            elif len(raw_result > 1):
                result, response_code = raw_result[:1]
            else:
                result = raw_result[0]
        else:
            result = raw_result

        response_code = response_code or 200

        result = {'result': result}

        return result, response_code, response_headers
    return _json_response
