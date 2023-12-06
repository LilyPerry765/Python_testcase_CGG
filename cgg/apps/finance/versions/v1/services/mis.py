# --------------------------------------------------------------------------
# Generic method of MIS service (Subscription fee and etc)
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - mis.py
# Created at 2020-2-12,  16:1:12
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils.translation import gettext as _
from jdatetime import datetime as jdatetime
from rest_framework import status

from cgg.apps.finance.apps import FinanceConfig
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core import api_exceptions
from cgg.core.requests import Requests


class MisService:
    @classmethod
    def mis_get_response(
            cls,
            label,
            method,
            relative_url,
            body,
    ):
        """
        Generic method to create request and return response from MIS service
        :param method: post|patch|get|put
        :param relative_url: relative url of api
        :param label: label of request
        :param body: dict to convert to JSON
        :return:
        """
        base_url = settings.CGG['BASE_URLS'][
            'MIS_SERVICE'].strip("/")
        relative_url = relative_url.strip("/")
        url = f"{base_url}/{relative_url}/"
        basic_auth_username = settings.CGG['AUTH_TOKENS'][
            'MIS_BASIC_AUTHENTICATION']['USERNAME']
        basic_auth_password = settings.CGG['AUTH_TOKENS'][
            'MIS_BASIC_AUTHENTICATION']['PASSWORD']
        headers = {
            'Content-type': 'application/json',
        }
        if method in ('post', 'patch', 'put'):
            requests_rest_method = getattr(Requests, method)
            try:
                response = requests_rest_method(
                    app_name=FinanceConfig.name,
                    label=label,
                    url=url,
                    json=body,
                    headers=headers,
                    # Fine tune this timeout somehow!
                    timeout=5,
                    auth=(
                        basic_auth_username,
                        basic_auth_password,
                    )
                )
            except requests.exceptions.ConnectionError:
                raise api_exceptions.APIException(_("Connection error"))
            except requests.exceptions.Timeout:
                raise api_exceptions.TimeOut408(_("Timeout on connection"))
            except api_exceptions.NotFound404 as e:
                raise api_exceptions.NotFound404(e)
            except api_exceptions.ValidationError400 as e:
                raise api_exceptions.ValidationError400(e)
            except api_exceptions.AuthenticationFailed401 as e:
                raise api_exceptions.AuthenticationFailed401(e)
            except api_exceptions.APIException as e:
                raise api_exceptions.APIException(e)
        else:
            try:
                response = Requests.get(
                    app_name=FinanceConfig.name,
                    label=label,
                    url=url,
                    params=urlencode(body),
                    headers=headers,
                    # Fine tune this timeout somehow!
                    timeout=5,
                    auth=(
                        basic_auth_username,
                        basic_auth_password,
                    )
                )
            except requests.exceptions.ConnectionError:
                raise api_exceptions.APIException(_("Connection error"))
            except requests.exceptions.Timeout:
                raise api_exceptions.TimeOut408(_("Timeout on connection"))
            except api_exceptions.NotFound404 as e:
                raise api_exceptions.NotFound404(e)
            except api_exceptions.ValidationError400 as e:
                raise api_exceptions.ValidationError400(e)
            except api_exceptions.AuthenticationFailed401 as e:
                raise api_exceptions.AuthenticationFailed401(e)
            except api_exceptions.APIException as e:
                raise api_exceptions.APIException(e)

        if response.status_code == status.HTTP_200_OK:
            # Response is 200, move on
            try:
                data = response.json()
                return data
            except Exception:
                raise api_exceptions.ValidationError400(
                    _("Malformed REST response from MIS")
                )
        else:
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                raise api_exceptions.AuthenticationFailed401()
            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise api_exceptions.NotFound404()
            raise api_exceptions.APIException(
                _("Something went wrong in MIS service")
            )

    @classmethod
    def get_subscription_fee(
            cls,
            invoice_type_code: str,
            subscription_code: str,
            to_date: datetime,
    ):
        """
        @TODO: This functionality belongs to Nexfon, think of a way to make
        it independent from MIS
        Get subscription fee from MIS service based on
        http://crm.respina.net:5005/swagger/ui/index#!/Nexfon
        /Nexfon_calculateBill
        This method uses to_date of invoices and calculate a month period in
        jalali format before that date, this month period is used to get
        subscription fee from MIS service. As an agreement we do not use
        subscription fee in interim invoices and the date range for periodic
        invoices is independent from invoice's date range (Because we may
        have interim invoices in a period)
        :param invoice_type_code:
        :param subscription_code:
        :param to_date:
        :return:
        """
        if invoice_type_code == FinanceConfigurations.Invoice.TYPES[0][0]:
            today_jalali = jdatetime.fromgregorian(date=to_date)
            jalali_year = today_jalali.year
            jalali_month = today_jalali.month
            if 1 <= jalali_month <= 6:
                jalali_day = 31
            else:
                jalali_day = 30
                if jalali_month == 12 and not today_jalali.isleap():
                    jalali_day = 29

            from_date_jalali = jdatetime(
                year=jalali_year,
                month=jalali_month,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            to_date_jalali = jdatetime(
                year=jalali_year,
                month=jalali_month,
                day=jalali_day,
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
            )
            from_date = from_date_jalali.togregorian()
            to_date = to_date_jalali.togregorian()
            body = {
                "SubId": subscription_code,
                "Fdate": from_date.strftime(
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ),
                "Tdate": to_date.strftime(
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ),
            }
            try:
                label = FinanceConfigurations.APIRequestLabels \
                    .GET_SUBSCRIPTION_FEE
                subscription_fee_response = cls.mis_get_response(
                    label=label,
                    method='get',
                    relative_url=FinanceConfigurations.Mis.API_RELATIVE_URLS[
                        "SUBSCRIPTION_FEE"],
                    body=body,
                )
            except (requests.RequestException, api_exceptions.APIException):
                return Decimal(0).to_integral_exact(rounding=ROUND_CEILING)

            if subscription_fee_response:
                return Decimal(
                    subscription_fee_response["BillAmount"],
                ).to_integral_exact(rounding=ROUND_CEILING)

        return Decimal(0).to_integral_exact(rounding=ROUND_CEILING)
