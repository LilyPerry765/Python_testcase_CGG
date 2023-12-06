from datetime import datetime

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.views import exception_handler


def get_error_response(status_code: int, err):
    """
    This dict must match the one in cgg.core.response
    :param status_code: a HTTP status code (must be integer)
    :param err: error message (string or dict)
    :return:
    """
    return {
        "status": status_code,
        "error": err,
        "hint": None,
        "message": None,
        "user_id": None,
        "time": datetime.now().timestamp(),
        "data": None,
    }


def cgg_exception_handler(exc, context):
    """
    Modify and customize exceptions based on their status code
    :param exc:
    :param context:
    :return:
    """
    res = exception_handler(exc, context)
    if res and getattr(res, 'status_code'):
        if res.status_code == status.HTTP_401_UNAUTHORIZED:
            res.data = get_error_response(
                status.HTTP_401_UNAUTHORIZED,
                _("Authorization token is not valid"),
            )

    return res
