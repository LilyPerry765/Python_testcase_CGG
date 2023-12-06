from django.test import TestCase

from cgg.core.tools import *


class CoreMethodsTestCase(TestCase):
    def setUp(self):
        self.camel_case_string1 = ('CamelCaseTest', 'camel_case_test')
        self.camel_case_string2 = ('Camel Case Test', 'camel_case_test')
        self.snake_case_string1 = ('camel_case_test', 'CamelCaseTest')
        self.snake_case_string2 = ('camel _case_ test', 'CamelCaseTest')
        self.valid_json_string = json.dumps({
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3',
        })
        self.invalid_json_string = "{ 'key1' 'value1' , 'key2':'value2' }"
        self.valid_uuid_string = str(uuid.uuid4())
        self.invalid_uuid_string = str(uuid.uuid4()) + "error"
        self.valid_uuid_object = uuid.uuid4()
        self.invalid_uuid_object = "error"

    def test_convert_camelcase_to_snake_case(self):
        self.assertEqual(
            Tools.camelcase_to_snake_case(self.camel_case_string1[0]),
            self.camel_case_string1[1]
        )
        self.assertEqual(
            Tools.camelcase_to_snake_case(self.camel_case_string2[0]),
            self.camel_case_string2[1]
        )

    def test_convert_snake_case_to_camelcase(self):
        self.assertEqual(
            Tools.snake_case_to_camelcase(self.snake_case_string1[0]),
            self.snake_case_string1[1]
        )
        self.assertEqual(
            Tools.snake_case_to_camelcase(self.snake_case_string2[0]),
            self.snake_case_string2[1]
        )

    def test_get_dict_from_json_valid(self):
        self.assertTrue(
            isinstance(Tools.get_dict_from_json(self.valid_json_string), dict)
        )

    def test_get_dict_from_json_invalid(self):
        with self.assertRaises(api_exceptions.ValidationError400):
            Tools.get_dict_from_json(self.invalid_json_string)

    def test_check_uuid_validation_from_string_valid(self):
        self.assertEqual(
            Tools.uuid_validation(self.valid_uuid_string),
            None,
        )

    def test_check_uuid_validation_from_string_invalid(self):
        with self.assertRaises(api_exceptions.ValidationError400):
            Tools.uuid_validation(self.invalid_uuid_string)

    def test_check_uuid_validation_from_object_valid(self):
        self.assertEqual(
            Tools.uuid_validation(self.valid_uuid_object),
            None,
        )

    def test_check_uuid_validation_from_object_invalid(self):
        with self.assertRaises(api_exceptions.ValidationError400):
            Tools.uuid_validation(self.invalid_uuid_object)
