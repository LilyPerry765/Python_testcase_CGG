# --------------------------------------------------------------------------
# Handle Operator objects logics. Make directs changes in CGRateS for
# inbound calls of operators. Related to Profit models and services.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - operator.py
# Created at 2020-8-29,  17:29:2
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import Operator
from cgg.apps.finance.versions.v1.serializers.operator import (
    OperatorSerializer,
    OperatorsSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools


class OperatorService:

    @classmethod
    def get_operators(
            cls,
            request,
    ):
        """
        Get all operators based on filters
        :param request:
        :return:
        """
        query_params = request.query_params
        operator_objects = Operator.objects.all()

        if query_params is not None:
            if 'operator_code' in query_params:
                try:
                    operator_objects = operator_objects.filter(
                        operator_code__icontains=query_params['operator_code']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'operator_code': ErrorMessages.OPERATOR_CODE_400
                        }
                    )

            # Order by
            operator_objects = CommonService.order_by_query(
                Operator,
                operator_objects,
                query_params,
            )

        operator_objects, paginator = Paginator().paginate(
            request=request,
            queryset=operator_objects,
        )
        operator_serializer = OperatorsSerializer(
            operator_objects,
            many=True,
        )

        return operator_serializer.data, paginator

    @classmethod
    def add_operator(
            cls,
            body,
    ):
        """
        Add a new operator in CGRateS (AttributeS to handle inbound calls
        and 20/80 model) as well as here
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        operator_serializer = OperatorSerializer(
            data=body,
        )

        if operator_serializer.is_valid(raise_exception=True):
            operator_serializer.save()
            operator_object = Operator.objects.get(
                id=operator_serializer.data['id']
            )
            prefixes = list(operator_object.destinations.all().values_list(
                'prefix',
                flat=True,
            ))

            if prefixes:
                if cls.add_account_for_operator(
                        operator_object.operator_code
                ):
                    if BasicService.set_attribute_profile_inbound(
                            operator_object.operator_code,
                            prefixes,
                    ):
                        return operator_serializer.data
                    else:
                        operator_object.delete()
                else:
                    operator_object.delete()
            else:
                return operator_serializer.data

        raise api_exceptions.APIException(
            _("Something went wrong in creating operator profile")
        )

    @classmethod
    def remove_operator(
            cls,
            operator_id,
    ):
        """
        Remove an operator from CGRateS (Remove attribute
        for inbound calls) as well as here
        :param operator_id:
        :return:
        """
        Tools.uuid_validation(operator_id)
        try:
            operator_object = Operator.objects.get(
                id=operator_id,
            )
        except Operator.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.OPERATOR_404
            )
        try:
            BasicService.remove_account(
                operator_object.operator_code
            )
            BasicService.remove_attribute_profile(
                attribute_name=operator_object.operator_code,
                attribute_type=BasicConfigurations.Types.ATTRIBUTE_TYPE[1][0],
            )
        except api_exceptions.APIException:
            pass

        operator_object.delete()

        return True

    @classmethod
    def update_operator(
            cls,
            operator_id,
            body,
    ):
        """
        Update an operator in CGRateS as well as here
        :param operator_id:
        :param body:
        :return:
        """
        Tools.uuid_validation(operator_id)
        body = Tools.get_dict_from_json(body)

        try:
            operator_object = Operator.objects.get(
                id=operator_id,
            )
        except Operator.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.OPERATOR_404
            )

        operator_serializer = OperatorSerializer(
            operator_object,
            data=body,
            partial=True,
        )

        if operator_serializer.is_valid(raise_exception=True):
            operator_serializer.save()
            prefixes = list(operator_object.destinations.all().values_list(
                'prefix',
                flat=True,
            ))

            if prefixes:
                if cls.add_account_for_operator(
                        operator_object.operator_code
                ):
                    if BasicService.set_attribute_profile_inbound(
                            operator_object.operator_code,
                            prefixes,
                    ):
                        return operator_serializer.data
                    else:
                        operator_object.delete()
                else:
                    operator_object.delete()
            else:
                return operator_serializer.data

        raise api_exceptions.APIException(
            _("Something went wrong in updating operator profile")
        )

    @classmethod
    def get_operator(cls, operator_id):
        """
        Get details of an operator
        :param operator_id:
        :return:
        """
        Tools.uuid_validation(operator_id)

        try:
            operator_object = Operator.objects.get(
                id=operator_id,
            )
        except Operator.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.OPERATOR_404
            )

        operator_serializer = OperatorSerializer(
            operator_object
        )

        return operator_serializer.data

    @classmethod
    def add_account_for_operator(
            cls,
            operator_code,
    ):
        """
        Add a new account in CGRateS with AllowNegative=True to handle
        inbound calls of an operator
        :param operator_code:
        :return:
        """
        # 1. Add account to CGRateS
        if BasicService.set_account(
                operator_code,
                is_active=True,
                allow_negative=True,
                account_type=BasicConfigurations.Types.ACCOUNT_TYPE[1][0],
        ):
            # 2. Set balance
            if BasicService.set_balance(
                    operator_code,
                    value=0,
                    account_type=
                    BasicConfigurations.Types.ACCOUNT_TYPE[1][0],
            ):
                return True

        return False
