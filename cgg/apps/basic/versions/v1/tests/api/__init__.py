from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class BasicTestCase(TestCase):

    def setUp(self):
        self.valid_token = {
            'HTTP_AUTHORIZATION': settings.CGG['AUTH_TOKENS'][
                'CGRATES_DASHBOARD'],
        }
        self.invalid_token = {
            'HTTP_AUTHORIZATION': 'CGRATES_DASHBOARD',
        }
        self.invalid_account = 'NOT_FOUND_ACCOUNT_TEST_ID'
        self.limit_offset_query_params = {
            'QUERY_STRING': 'limit=2&offset=0',
        }

    def test_authorization(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('basic_accounts', kwargs={}),
            content_type='application/json',
            **self.valid_token,
        )
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorization_failed(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('basic_accounts', kwargs={}),
            content_type='application/json',
            **self.invalid_token,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_actions(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('basic_actions', kwargs={}),
            content_type='application/json',
            **self.valid_token,

        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_an_non_existing_account(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('basic_account', kwargs={'account': self.invalid_account}),
            content_type='application/json',
            **self.valid_token,

        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_limit_and_offset_on_filters(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('basic_filters', kwargs={}),
            content_type='application/json',
            **self.valid_token,
            **self.limit_offset_query_params,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)
