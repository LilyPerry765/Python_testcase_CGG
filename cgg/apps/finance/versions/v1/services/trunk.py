# --------------------------------------------------------------------------
# Handle jobs related to talking to Trunk backend APIs
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - trunk.py
# Created at 2020-8-29,  17:45:55
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from json import JSONDecodeError

import requests
from django.utils.translation import gettext as _
from rest_framework import status

from cgg.apps.finance.apps import FinanceConfig
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core import api_exceptions
from cgg.core.requests import Requests


class TrunkService:

    @classmethod
    def get_truck_response(cls, url, body):
        """
        Generic method to create request and return response from Trunk backend
        :param url: full url in string
        :param body: body to convert to JSON
        :return: response from Trunk
        """
        try:
            headers = FinanceConfigurations.TrunkBackend.default_headers()
            response = Requests.post(
                app_name=FinanceConfig.name,
                label=FinanceConfigurations.APIRequestLabels.POST_TO_TRUNK,
                url=url,
                json=body,
                headers=headers,
                # Fine tune this timeout somehow!
                timeout=5,
            )
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return True
            try:
                data = response.json()
                if data['status'] == status.HTTP_200_OK:
                    return data['data']
                else:
                    raise api_exceptions.APIException(data['error'])
            except JSONDecodeError:
                raise api_exceptions.ValidationError400(
                    {
                        'non_fields': _('JSON decode error'),
                        'url': url,
                    }
                )
        except requests.exceptions.Timeout:
            raise api_exceptions.TimeOut408(
                detail=_("Timeout on connection"),
            )
        except (api_exceptions.APIException, Exception) as e:
            raise api_exceptions.APIException(e)

    @classmethod
    def notify_trunk_backend(
            cls,
            notify_type_code,
            notify_object,
    ):
        """
        Notify trunk backend about internal events
        :param notify_type_code: string with these choices ->
        FinanceConfigurations.TrunkBackend.NOTIFY
        :param notify_object:
        :return:
        """
        tb = FinanceConfigurations.TrunkBackend
        if notify_type_code == tb.Notify.PERIODIC_INVOICE:
            return cls.get_truck_response(
                tb.url_periodic_invoice(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.INTERIM_INVOICE:
            return cls.get_truck_response(
                tb.url_interim_invoice(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.INTERIM_INVOICE_AUTO_PAYED:
            return cls.get_truck_response(
                tb.url_interim_invoice_auto_payed(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.POSTPAID_MAX_USAGE:
            return cls.get_truck_response(
                tb.url_postpaid_max_usage(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.DUE_DATE_WARNING_1:
            return cls.get_truck_response(
                tb.url_due_date(1),
                notify_object,
            )
        elif notify_type_code == tb.Notify.DUE_DATE_WARNING_2:
            return cls.get_truck_response(
                tb.url_due_date(2),
                notify_object,
            )
        elif notify_type_code == tb.Notify.DUE_DATE_WARNING_3:
            return cls.get_truck_response(
                tb.url_due_date(3),
                notify_object,
            )
        elif notify_type_code == tb.Notify.DUE_DATE_WARNING_4:
            return cls.get_truck_response(
                tb.url_due_date(4),
                notify_object,
            )
        elif notify_type_code == tb.Notify.PREPAID_EIGHTY_PERCENT:
            return cls.get_truck_response(
                tb.url_prepaid_eighty_percent(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.PREPAID_MAX_USAGE:
            return cls.get_truck_response(
                tb.url_prepaid_max_usage(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.PREPAID_EXPIRED:
            return cls.get_truck_response(
                tb.url_prepaid_expired(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.PREPAID_RENEWED:
            return cls.get_truck_response(
                tb.url_prepaid_renewed(),
                notify_object,
            )
        elif notify_type_code == tb.Notify.DEALLOCATION_WARNING_1:
            return cls.get_truck_response(
                tb.url_deallocation(1),
                notify_object,
            )
        elif notify_type_code == tb.Notify.DEALLOCATION_WARNING_2:
            return cls.get_truck_response(
                tb.url_deallocation(2),
                notify_object,
            )
