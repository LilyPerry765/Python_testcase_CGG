from django.db import DataError, IntegrityError
from django.test import TestCase

from cgg.apps.finance.models import Customer, Destination, Subscription, Tax


class CustomerTestCase(TestCase):
    def setUp(self):
        Customer.objects.create(customer_code='c1')

    def test_create_new_customer(self):
        test1 = Customer.objects.create(customer_code="c2")
        self.assertTrue(isinstance(test1, Customer))

    def test_create_new_customer_with_duplicate_code(self):
        with self.assertRaises(IntegrityError):
            Customer.objects.create(customer_code="c1")


class DestinationTestCase(TestCase):
    def setUp(self):
        Destination.objects.create(
            prefix='021',
            name='Tehran',
            country_code='IRN',
            code='landline_national',
        )
        Destination.objects.create(
            prefix='9821',
            name='Tehran',
            country_code='IRN',
            code='landline_national',
        )

    def test_create_new_destination(self):
        test1 = Destination.objects.create(
            prefix='9851',
            name='Shiraz',
            country_code='IRN',
            code='landline_national',
        )
        self.assertTrue(isinstance(test1, Destination))


class SubscriptionTestCase(TestCase):
    def setUp(self):
        customer = Customer.objects.create(customer_code='c1')
        Subscription.objects.create(
            subscription_code="test1",
            number="45455455",
            customer=customer,
        )

    def test_subscription_default_is_allocated(self):
        test1 = Subscription.objects.get(subscription_code="test1")
        self.assertEqual(test1.is_allocated, True)

    def test_create_new_subscription(self):
        test1 = Subscription.objects.create(
            subscription_code="test12",
            number="454554556",
            customer=Customer.objects.get(customer_code='c1'),
        )
        self.assertTrue(isinstance(test1, Subscription))

    def test_create_new_subscription_with_duplicate_code(self):
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(
                subscription_code="test1",
                number="454554556",
                customer=Customer.objects.get(customer_code='c1'),
            )

    def test_create_new_subscription_with_long_number(self):
        with self.assertRaises(DataError):
            Subscription.objects.create(
                subscription_code="new_test",
                number="ThisIsALongTextThisIsALongTextThisIsALongText"
                       "ThisIsALongTextThisIsALongTextThisIsALongText"
                       "ThisIsALongTextThisIsALongTextThisIsALongText",
                customer=Customer.objects.get(customer_code='c1'),
            )

    def test_update_is_allocated(self):
        test1 = Subscription.objects.get(subscription_code="test1")
        test1.is_allocated = False
        test1.save()
        self.assertFalse(test1.is_allocated)


class TaxTestCase(TestCase):
    def setUp(self):
        Tax.objects.create(tax_percent=10, country_code='IRN')

    def test_create_new_tax(self):
        test1 = Tax.objects.create(tax_percent=2, country_code='USA')
        self.assertTrue(isinstance(test1, Tax))

    def test_create_new_tax_without_percent(self):
        with self.assertRaises(IntegrityError):
            Tax.objects.create(country_code='IRN')

    def test_create_new_tax_with_duplicate_code(self):
        with self.assertRaises(IntegrityError):
            Tax.objects.create(country_code='IRN', tax_percent=2)

    def test_create_new_tax_string_percent(self):
        with self.assertRaises(ValueError):
            Tax.objects.create(tax_percent='asd2', country_code='BLS')
