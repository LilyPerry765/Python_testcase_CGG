# --------------------------------------------------------------------------
# Helper function's to use across the whole project
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - tools.py
# Created at 2020-8-29,  16:4:3
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import re
import uuid
from datetime import datetime
from decimal import Decimal
from json import JSONDecodeError

import pytz
from django.utils.translation import gettext as _
from jdatetime import datetime as jdatetime

from cgg.apps.api_request.models import APIRequest
from cgg.core import api_exceptions


class Tools:
    @classmethod
    def jalali_month_name(cls, month):
        if month < 1:
            month = 1
        if month > 12:
            month = 12
        months = {
            1: "فروردین",
            2: "اردیبهشت",
            3: "خرداد",
            4: "تیر",
            5: "مرداد",
            6: "شهریور",
            7: "مهر",
            8: "آبان",
            9: "آذر",
            10: "دی",
            11: "بهمن",
            12: "اسفند",
        }

        return months[month]

    @classmethod
    def translator(cls, key):
        """
        Translate keys to the target language
        :param key:
        :return:
        """
        if key == "prepaid":
            return _("Prepaid")
        elif key == "postpaid":
            return _("Postpaid")
        elif key == "base_balance_invoice":
            return _("Base balance invoice")
        elif key == "credit_invoice":
            return _("Credit invoice")
        elif key == "invoice":
            return _("Invoice")
        elif key == "package_invoice":
            return _("Package invoice")
        elif key == "decrease":
            return _("Decrease")
        elif key == "increase":
            return _("Increase")

        return key

    @classmethod
    def to_string_for_export(cls, value, is_boolean=False):
        if value is not None:
            if is_boolean:
                if value:
                    return _("Yes")
                return _("No")
            return str(value)
        return " - "

    @classmethod
    def to_jalali_date(
            cls,
            gregorian_date,
            date_format="%Y/%m/%d %H:%M:%S",
            timezone='Asia/Tehran',
    ):
        if gregorian_date:
            return jdatetime.fromtimestamp(
                gregorian_date.timestamp(),
            ).astimezone(
                pytz.timezone(timezone)
            ).strftime(
                date_format,
            )
        return " - "

    @classmethod
    def convert_nano_seconds_to_minutes(cls, nanoseconds):
        nanoseconds = float(nanoseconds)
        if nanoseconds == 0:
            return nanoseconds

        minutes = float(float(nanoseconds / 1000000000) / 60)

        return str(round(minutes, 2))

    @classmethod
    def convert_nano_seconds_to_seconds(cls, nanoseconds):
        nanoseconds = float(nanoseconds)
        if nanoseconds == 0:
            return nanoseconds

        seconds = float(float(nanoseconds / 1000000000))

        return str(round(seconds, 2))

    @classmethod
    def log_outgoing_requests(
            cls,
            kwargs,
            response,
            app_name,
            label,
    ):
        api_request_obj = APIRequest()
        api_request_obj.uri = kwargs['url']
        api_request_obj.http_method = kwargs['method']
        api_request_obj.direction = 'out'
        api_request_obj.label = label
        api_request_obj.app_name = app_name

        try:
            if 'body' in kwargs:
                api_request_obj.request = json.loads(
                    (kwargs['body'] or b'{}').decode('utf-8'),
                )
            elif 'json' in kwargs:
                api_request_obj.request = kwargs['json']
        except JSONDecodeError:
            api_request_obj.request = {}

        try:
            api_request_obj.response = json.loads(
                response.content.decode('utf-8'),
            )
        except JSONDecodeError:
            api_request_obj.response = {}

        api_request_obj.status_code = response.status_code
        api_request_obj.save()

    @classmethod
    def to_snake_case(cls, word):
        word = word.lower()
        word = " ".join(word.split())
        word = word.replace(' ', '_')

        return word

    @classmethod
    def camelcase_to_snake_case(cls, word):
        word = word.replace(' ', '')
        snake = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', word)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake).lower()

    @classmethod
    def snake_case_to_camelcase(cls, word):
        word = word.replace(' ', '_')
        word = word.replace('__', '_')
        return ''.join(x.capitalize() or '_' for x in word.split('_'))

    @classmethod
    def get_dict_from_json(cls, json_string):
        """
        Convert json string to dict (API Exception handled)
        :param json_string:
        :return: dict
        """
        try:
            json_dict = json.loads(json_string)
        except JSONDecodeError:
            raise api_exceptions.ValidationError400({
                'non_fields': _('JSON is not valid')
            })

        return json_dict

    @classmethod
    def uuid_validation(cls, uuid_test):
        """
        Check if the string is a valid UUID (API exception handled)
        :param uuid_test:
        :return: None
        """
        try:
            if not isinstance(uuid_test, uuid.UUID):
                uuid_test = uuid.UUID(uuid_test)
            return uuid_test
        except ValueError:
            raise api_exceptions.ValidationError400(
                {
                    'id': _('Not a valid UUID')
                }
            )

    @classmethod
    def convert_dynamic_dict_to_list(cls, original_dict, replace_key: str):
        try:
            created_list = [{
                replace_key: key,
                **value
            } for key, value in dict(original_dict).items()]
        except (ValueError, TypeError):
            raise api_exceptions.ValidationError400({
                'non_fields': _('Conversion failed')
            })

        return created_list

    @classmethod
    def normalize_number(cls, number):
        """
        Normalize number based on this convention:
        https://git.respina.net/development/docs/blob/mehrdadep/projects
        /cgrates-gateway/number_conventions.md
        +[CountryCode][Number] -> e.g. +4425622569, +98912524256
        :param number:
        :return: Normalized number
        """
        if number and re.match(re.compile(r'^\+?\d+(?:,\d*)?$'), number):
            if number.startswith("+"):
                return number
            elif number.startswith("00"):
                return f"+{number[2:]}"
            elif number.startswith("0"):
                return f"+98{number[1:]}"
            else:
                return f"+98{number}"

        raise api_exceptions.ValidationError400({
            "number": _(
                "Malformed number, Use numbers with an optional plus sign at "
                "the beginning"
            ),
            "input_data": number
        })

    @classmethod
    def make_safe_payment_amount(cls, amount):
        """
        Return the amount the online payment gateways accept
        :param amount:
        :type amount:
        :return:
        :rtype:
        """
        if Decimal(amount) < Decimal(1000):
            return Decimal(1000)

        return Decimal(amount)

    @classmethod
    def get_file_name(cls, name="export"):
        return f"{name} - {str(datetime.now().timestamp())}"
