# --------------------------------------------------------------------------
# Related to OperatorService and handles the logic for their profits.
# Profits are invoices for operators, so their data relies on CGRateS.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - profit.py
# Created at 2020-8-29,  17:38:18
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime
from decimal import Decimal, ROUND_CEILING

from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions,
)
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import Operator, Profit
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.profit import (
    CreateProfitSerializer,
    ProfitExportSerializer,
    ProfitSerializer, ProfitsSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools


class ProfitService:

    @classmethod
    def get_profits(
            cls,
            request,
            export_type=FinanceConfigurations.Export.Format.JSON,
    ):
        """
        Get details of all profits based on query params
        :param export_type:
        :type export_type:
        :param request:
        :return:
        """
        query_params = request.query_params
        profits_query = Profit.objects.all()

        if query_params is not None:
            profits_query = CommonService.filter_query_common(
                profits_query,
                query_params,
            )
            profits_query = CommonService.filter_from_and_to_date(
                profits_query,
                query_params,
            )
            if 'operator_code' in query_params:
                try:
                    profits_query = profits_query.filter(
                        operator__operator_code__icontains=query_params[
                            'operator_code']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'operator_code': ErrorMessages.OPERATOR_CODE_400
                        }
                    )
            if 'status_code' in query_params:
                valid_status_codes = []
                for sts in FinanceConfigurations.Profit.STATE_CHOICES:
                    valid_status_codes.append(sts[0])
                status_code_query = [
                    x.strip() for x in query_params['status_code'].split(',')
                ]
                if all(elem in valid_status_codes
                       for elem in status_code_query):
                    profits_query = profits_query.filter(
                        status_code__in=status_code_query
                    )
                else:
                    valid_status_codes = '/'.join(
                        valid_status_codes,
                    )
                    raise api_exceptions.ValidationError400(
                        {
                            'status_code':
                                f"{ErrorMessages.VALID_CHOICES_400}: "
                                f"{valid_status_codes}"
                        }
                    )

            profits_query = CommonService.order_by_query(
                Profit,
                profits_query,
                query_params,
            )
        if FinanceConfigurations.Export.Format.is_json(export_type):
            profits_query, paginator = Paginator().paginate(
                request=request,
                queryset=profits_query,
            )
            profits_serializer = ProfitsSerializer(
                profits_query,
                many=True,
            )
            data = profits_serializer.data, paginator
        else:
            profits_serializer = ProfitExportSerializer(
                profits_query,
                many=True,
            )
            data = profits_serializer.data

        return data

    @classmethod
    def add_profit(
            cls,
            body,
    ):
        """
        Add a new profit for operator based on CDRs. This method handles
        20/80 bossiness model.
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        profit_serializer = CreateProfitSerializer(
            data=body,
        )
        create_profit_data = None
        if profit_serializer.is_valid(raise_exception=True):
            create_profit_data = profit_serializer.data
            create_profit_data['updated_status_at'] = datetime.now()
            create_profit_data['from_date'] = datetime.fromtimestamp(
                float(create_profit_data['from_date']),
            )
            create_profit_data['to_date'] = datetime.fromtimestamp(
                float(create_profit_data['to_date']),
            )

        if create_profit_data:
            try:
                operator_object = Operator.objects.get(
                    id=create_profit_data['operator_id'],
                )
            except Operator.DoesNotExist:
                raise api_exceptions.NotFound404(
                    ErrorMessages.OPERATOR_404
                )
            prefixes = list(operator_object.destinations.values_list(
                'prefix',
                flat=True,
            ))
            # Get CDRs from CGRateS
            extra_inbound_with_operator = {
                **CGRatesConventions.extra_field_inbound(),
                **CGRatesConventions.extra_field(
                    CGRatesConventions.extra_field_operator(),
                    operator_object.operator_code,
                )
            }
            operator_cdrs_inbound = BasicService.get_cdrs(
                created_at_start=
                str(create_profit_data['from_date'].timestamp()).split('.')[0],
                created_at_end=
                str(create_profit_data['to_date'].timestamp()).split('.')[0],
                extra_fields=extra_inbound_with_operator,
            )
            operator_cdrs_outbound = BasicService.get_cdrs(
                created_at_start=
                str(create_profit_data['from_date'].timestamp()).split('.')[0],
                created_at_end=
                str(create_profit_data['to_date'].timestamp()).split('.')[0],
                destination_prefixes=prefixes,
                extra_fields=CGRatesConventions.extra_field_outbound(),
            )
            operator_cdrs_inbound_list = \
                BasicService.cdrs_minimal_object(
                    operator_cdrs_inbound,
                )
            operator_cdrs_outbound_list = \
                BasicService.cdrs_minimal_object(
                    operator_cdrs_outbound,
                )
            inbound_usage_nano = Decimal(0)
            outbound_usage_nano = Decimal(0)

            for operator_cdrs_inbound in operator_cdrs_inbound_list:
                inbound_usage_nano += Decimal(
                    operator_cdrs_inbound['usage'],
                )

            for operator_cdrs_outbound in operator_cdrs_outbound_list:
                outbound_usage_nano += Decimal(
                    operator_cdrs_outbound['usage'],
                )
            if operator_object.rate_time_type == \
                    FinanceConfigurations.Profit.RATE_TIME_TYPE[0][0]:
                # Convert to seconds
                operator_cdrs_inbound_usage = \
                    Tools.convert_nano_seconds_to_seconds(
                        inbound_usage_nano,
                    )
                operator_cdrs_outbound_usage = \
                    Tools.convert_nano_seconds_to_seconds(
                        outbound_usage_nano,
                    )
            else:
                # Convert to minutes
                operator_cdrs_inbound_usage = \
                    Tools.convert_nano_seconds_to_minutes(
                        inbound_usage_nano,
                    )
                operator_cdrs_outbound_usage = \
                    Tools.convert_nano_seconds_to_minutes(
                        outbound_usage_nano,
                    )
            rate_span = Decimal(operator_object.rate_time)
            inbound_rate = Decimal(operator_object.inbound_rate)
            outbound_rate = Decimal(operator_object.outbound_rate)
            inbound_divide_on_percent = int(
                operator_object.inbound_divide_on_percent
            )
            outbound_divide_on_percent = int(
                operator_object.outbound_divide_on_percent
            )
            total_inbound_usage = (Decimal(
                operator_cdrs_inbound_usage
            ) / rate_span) * inbound_rate
            total_outbound_usage = (Decimal(
                operator_cdrs_outbound_usage
            ) / rate_span) * outbound_rate
            inbound_first_part = Decimal(
                (total_inbound_usage * inbound_divide_on_percent) / 100
            )
            inbound_second_part = total_inbound_usage - inbound_first_part
            outbound_first_part = Decimal(
                (total_outbound_usage * outbound_divide_on_percent) / 100)
            outbound_second_part = total_outbound_usage - outbound_first_part
            profit_serializer = ProfitSerializer(
                data={
                    "operator_id": operator_object.id,
                    "inbound_used_percent":
                        operator_object.inbound_divide_on_percent,
                    "outbound_used_percent":
                        operator_object.outbound_divide_on_percent,
                    "inbound_cost_first_part":
                        inbound_first_part.to_integral_exact(
                            rounding=ROUND_CEILING,
                        ),
                    "inbound_cost_second_part":
                        inbound_second_part.to_integral_exact(
                            rounding=ROUND_CEILING,
                        ),
                    "outbound_cost_first_part":
                        outbound_first_part.to_integral_exact(
                            rounding=ROUND_CEILING,
                        ),
                    "outbound_cost_second_part":
                        outbound_second_part.to_integral_exact(
                            rounding=ROUND_CEILING,
                        ),
                    "inbound_usage":
                        Decimal(inbound_usage_nano).to_integral_exact(
                            rounding=ROUND_CEILING,
                        ),
                    "outbound_usage":
                        Decimal(outbound_usage_nano).to_integral_exact(
                            rounding=ROUND_CEILING,
                        ),
                    "from_date": create_profit_data['from_date'],
                    "to_date": create_profit_data['to_date'],
                    "updated_status_at":
                        create_profit_data['updated_status_at'],
                }
            )
            if profit_serializer.is_valid(raise_exception=True):
                profit_serializer.save()

            return profit_serializer.data

        raise api_exceptions.APIException(
            _('Something went wrong in creating profit')
        )

    @classmethod
    def get_profit(cls, profit_id):
        """
        Get details of a profit based on id
        :param profit_id:
        :return:
        """
        Tools.uuid_validation(profit_id)
        try:
            profit_object = Profit.objects.get(
                id=profit_id,
            )
        except Profit.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PROFIT_404,
            )

        profits_serializer = ProfitSerializer(
            profit_object
        )

        return profits_serializer.data

    @classmethod
    def update_profit(
            cls,
            profit_id,
            body,
    ):
        """
        Update the status code of a profit
        :param body:
        :type body:
        :param profit_id:
        :return:
        """
        Tools.uuid_validation(profit_id)
        body = Tools.get_dict_from_json(body)
        try:
            profit_object = Profit.objects.get(
                id=profit_id,
            )
        except Profit.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PROFIT_404,
            )

        profits_serializer = ProfitSerializer(
            profit_object,
            body,
            partial=True,
        )

        if profits_serializer.is_valid(raise_exception=True):
            profits_serializer.save()

        return profits_serializer.data
