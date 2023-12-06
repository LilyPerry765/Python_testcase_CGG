from django.test import TestCase

from cgg.apps.api_request.models import APIRequest


class APIRequestTestCase(TestCase):
    def setUp(self):
        self.valid_object = {
            'direction': 'in',
            'app_name': 'test',
            'label': 'test',
            'ip': 'test',
            'http_method': 'get',
            'uri': 'http://test.com',
            'status_code': 200,
            'request': "",
            'response': {
                'ok': 'nice answer',
            },
        }
        self.invalid_status_code = {
            'direction': 'out',
            'app_name': 'test',
            'label': 'test',
            'ip': 'test',
            'http_method': 'get',
            'uri': 'http://test.com',
            'status_code': 'error',
            'request': "",
            'response': {
                'ok': 'nice answer',
            },
        }
        self.invalid_response = {
            'direction': 'out',
            'app_name': 'test',
            'label': 'test',
            'ip': 'test',
            'http_method': 'get',
            'uri': 'http://test.com',
            'status_code': 401,
            'request': "",
            'response': 200,
        }

    def test_create_new_api_request(self):
        test1 = APIRequest.objects.create(
            **self.valid_object
        )
        self.assertTrue(isinstance(test1, APIRequest))

    def test_create_new_api_request_with_invalid_status_code(self):
        with self.assertRaises(ValueError):
            APIRequest.objects.create(
                **self.invalid_status_code
            )
