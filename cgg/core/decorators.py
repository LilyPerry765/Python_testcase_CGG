import json
from json import JSONDecodeError

from cgg.apps.api_request.models import APIRequest


def get_client_ip(request):
    """
    Get IP of the client from request
    :param request:
    :return: ip of client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_api_request(app_name, label, direction='in'):
    """
    log api requests with app name and label
    :param direction: in/out
    :param app_name: the name of caller app
    :param label: the optional label for each api call
    :return:
    """

    def wrapper(view_method):
        def args_wrapper(class_view_obj, request, *args, **kwargs):
            view_result = view_method(class_view_obj, request, *args, **kwargs)

            api_request_obj = APIRequest()

            api_request_obj.uri = request.get_full_path()
            api_request_obj.http_method = request.method.lower()
            api_request_obj.direction = direction
            api_request_obj.label = label
            api_request_obj.app_name = app_name
            api_request_obj.ip = get_client_ip(request)

            try:
                api_request_obj.request = json.loads(
                    (request.body or b'{}').decode('utf-8'),
                )
            except JSONDecodeError:
                api_request_obj.request = {}

            api_request_obj.response = \
                view_result.data if hasattr(view_result, 'data') else str(
                    type(view_result)
                )
            api_request_obj.status_code = view_result.status_code

            api_request_obj.save()

            return view_result

        return args_wrapper

    return wrapper
