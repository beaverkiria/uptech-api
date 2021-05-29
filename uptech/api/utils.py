from typing import List, Optional, Union

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions, response
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler as drf_exception_handler


def _is_error_dict(d: Union[str, list, dict]) -> bool:
    if isinstance(d, dict):
        return len(d) == 2 and "message" in d and "code" in d
    return False


def _extract_errors(exc: Union[dict, list], path: list) -> List[dict]:
    errors = []
    if _is_error_dict(exc):
        errors.append(
            {
                "message": str(exc["message"]),
                "code": exc["code"],
                "field": ".".join(map(str, path)) or api_settings.NON_FIELD_ERRORS_KEY,
            }
        )
    elif isinstance(exc, dict):
        for k, item in exc.items():
            path.append(k)
            errors.extend(_extract_errors(item, path))
            path.pop()
    elif isinstance(exc, list):
        for i, item in enumerate(exc):
            # TODO: add ReturnList extraction
            # should_pop_path = True
            # if _is_error_dict(item):
            #     should_pop_path = False

            errors.extend(_extract_errors(item, path))

            # if should_pop_path:
            #     path.pop()

    return errors


def exception_handler(exc: Exception, context: dict) -> Optional[response.Response]:
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    resp = drf_exception_handler(exc, context)
    if isinstance(exc, exceptions.APIException):
        data = {"errors": _extract_errors(exc.get_full_details(), path=[])}
        resp.data = data
        return resp

    elif isinstance(exc, Http404):
        data = {"errors": [{"code": "not_found", "message": "Not found.", "field": "non_fields_error"}]}

        resp.data = data
        return resp

    elif isinstance(exc, PermissionDenied):
        data = {"errors": [{"code": "permission_denied", "message": "Permission denied.", "field": "non_fields_error"}]}

        resp.data = data
        return resp

    return None
