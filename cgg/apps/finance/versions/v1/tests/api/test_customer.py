import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from cgg.apps.finance.models import Customer
from cgg.apps.finance.versions.v1.serializers.customer import (
    CustomerSerializer,
    CustomersSerializer,
)


class CustomerAPITestCase(TestCase):

    def setUp(self):
        Customer.objects.create(customer_code='c1')
        Customer.objects.create(customer_code='c2')
        Customer.objects.create(customer_code='c3')
        Customer.objects.create(customer_code='c4')
        Customer.objects.create(customer_code='c5')

        self.valid_payload = {
            'customer_code': 'c6'
        }
        self.invalid_payload = {
            'customer_codes': 'c6'
        }
        self.duplicate_payload = {
            'customer_codes': 'c5'
        }

    def test_get_customers(self):
        api_client = APIClient()
        customers = Customer.objects.all()
        serializer = CustomersSerializer(customers, many=True)
        response = api_client.get(
            reverse('customers', kwargs={}),
            content_type='application/json',
            **{
                'HTTP_AUTHORIZATION': settings.CGG['AUTH_TOKENS'][
                    'TRUNK_IN']
            },
        )
        self.assertEqual(response.data['data'], serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_customer(self):
        api_client = APIClient()
        customer = Customer.objects.get(customer_code='c1')
        serializer = CustomerSerializer(customer)
        response = api_client.get(
            reverse('customer', kwargs={'customer': 'c1'}),
            content_type='application/json',
            **{
                'HTTP_AUTHORIZATION': settings.CGG['AUTH_TOKENS'][
                    'TRUNK_IN']
            },
        )
        self.assertEqual(response.data['data'], serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_valid_customer(self):
        api_client = APIClient()
        response = api_client.post(
            reverse('customers', kwargs={}),
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            **{
                'HTTP_AUTHORIZATION': settings.CGG['AUTH_TOKENS'][
                    'TRUNK_IN']
            },
        )
        customer = Customer.objects.get(customer_code=self.valid_payload[
            'customer_code'])
        serializer = CustomerSerializer(customer)
        self.assertEqual(response.data['data'], serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
