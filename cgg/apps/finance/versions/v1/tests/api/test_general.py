from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class GeneralAPITestCase(TestCase):

    def test_authorization(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('subscriptions', kwargs={}),
            content_type='application/json',
            **{
                'HTTP_AUTHORIZATION': settings.CGG['AUTH_TOKENS'][
                    'TRUNK_IN']
            }
        )
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorization_failed(self):
        api_client = APIClient()
        response = api_client.get(
            reverse('subscriptions', kwargs={}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
