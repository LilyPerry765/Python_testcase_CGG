# --------------------------------------------------------------------------
# Handle logics related to Destination objects.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - destination.py
# Created at 2020-8-29,  17:19:43
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import (
    Branch,
    Destination,
    Operator,
    RuntimeConfig,
    Subscription,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.destination import (
    DestinationNamesSerializer,
    DestinationSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.runtime_config import (
    RuntimeConfigService,
)
from cgg.apps.finance.versions.v1.services.subscription import (
    SubscriptionService,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools


class DestinationService:

    @receiver(
        post_save,
        sender=RuntimeConfig,
    )
    def post_save_runtime_config(*args, **kwargs):
        """
        TODO: This method needs a big refactor to improve style and performance
        This method is a signal receiver for any updates on RuntimeConfig
        if any prefixes for national and states changes, this method updates
        destinations in CGG database and CGRateS Service.
        :param args:
        :param kwargs:
        :return:
        """
        corporate_prefixes = []
        emergency_prefixes = []
        instance = kwargs['instance']
        if instance.item_key in (
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[2][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[3][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[7][0],
        ):
            corporate_state_prefixes = RuntimeConfigService.get_value(
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[2][0],
            )
            corporate_national_prefixes = RuntimeConfigService.get_value(
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[3][0],
            )
            emergency_prefixes_config = RuntimeConfigService.get_value(
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[7][0],
            )
            branches = Branch.objects.exclude(
                branch_code__in=[
                    FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[0],
                    FinanceConfigurations.Branch.DEFAULT_COUNTRY_BRANCH[0],
                    FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                ]
            )
            land_prefixes = Destination.objects.filter(
                code=FinanceConfigurations.Destination.CODE_CHOICES[1][0],
            ).exclude(
                name=
                FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[1],
            ).exclude(
                name=
                FinanceConfigurations.Destination.EMERGENCY_NAME[1],
            )
            emergency_prefixes_config = emergency_prefixes_config.split(",")
            corporate_state_prefixes = corporate_state_prefixes.split(",")
            corporate_national_prefixes = corporate_national_prefixes.split(
                ",",
            )
            for branch in branches:
                branch_prefixes = branch.destinations.all()
                for branch_prefix in branch_prefixes:
                    for corporate_state_prefix in corporate_state_prefixes:
                        if corporate_state_prefix:
                            corporate_prefixes.append(
                                f"{branch_prefix.prefix}"
                                f"{corporate_state_prefix}"
                            )
            for land_prefix in land_prefixes:
                for emergency_prefix in emergency_prefixes_config:
                    if emergency_prefix:
                        emergency_prefixes.append(
                            f"{land_prefix.prefix}"
                            f"{emergency_prefix}"
                        )
            # Get country branch
            country_branch = Branch.objects.get(
                branch_code=
                FinanceConfigurations.Branch.DEFAULT_COUNTRY_BRANCH[0]
            )
            emergency_branch = Branch.objects.get(
                branch_code=
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0]
            )
            corporate_national_prefixes_normalized = []
            for corporate_national_prefix in corporate_national_prefixes:
                if corporate_national_prefix:
                    corporate_prefixes.append(
                        f"{Tools.normalize_number(corporate_national_prefix)}"
                    )
                    corporate_national_prefixes_normalized.append(
                        f"{Tools.normalize_number(corporate_national_prefix)}"
                    )
            # Delete all existing destination that not included in new
            # RuntimeConfig
            Destination.objects.filter(
                code=FinanceConfigurations.Destination.CODE_CHOICES[1][0],
                name=
                FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[1],
            ).exclude(
                prefix__in=corporate_prefixes,
            ).delete()
            Destination.objects.filter(
                code=FinanceConfigurations.Destination.CODE_CHOICES[1][0],
                name=
                FinanceConfigurations.Destination.EMERGENCY_NAME[1],
            ).exclude(
                prefix__in=emergency_prefixes,
            ).delete()
            default_code = \
                FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[0]
            default_name = \
                FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[1]
            emergency_code = \
                FinanceConfigurations.Destination.EMERGENCY_NAME[0]
            emergency_name = \
                FinanceConfigurations.Destination.EMERGENCY_NAME[1]

            for corporate_prefix in corporate_prefixes:
                try:
                    corporate_destination = Destination.objects.get(
                        prefix=corporate_prefix
                    )
                except Destination.DoesNotExist:
                    corporate_destination = Destination()
                    corporate_destination.name = default_name
                    corporate_destination.prefix = corporate_prefix
                    corporate_destination.country_code = "ir"
                    corporate_destination.code = \
                        FinanceConfigurations.Destination.CODE_CHOICES[1][0]
                    corporate_destination.save()
                if corporate_destination.prefix in \
                        corporate_national_prefixes_normalized:
                    country_branch.destinations.add(
                        corporate_destination
                    )

            for emergency_prefix in emergency_prefixes:
                try:
                    emergency_destination = Destination.objects.get(
                        prefix=emergency_prefix
                    )
                except Destination.DoesNotExist:
                    emergency_destination = Destination()
                    emergency_destination.name = emergency_name
                    emergency_destination.prefix = emergency_prefix
                    emergency_destination.country_code = "ir"
                    emergency_destination.code = \
                        FinanceConfigurations.Destination.CODE_CHOICES[1][0]
                    emergency_destination.save()

                emergency_branch.destinations.add(
                    emergency_destination
                )

            # Add all new destinations to CGRateS Service (This is used in
            # default rating plan to be free)
            try:
                cgrates_prefixes = Destination.objects.filter(
                    code=FinanceConfigurations.Destination.CODE_CHOICES[1][0],
                    name=default_name,
                ).values_list('prefix', flat=True)
                cgrates_prefixes = list(cgrates_prefixes)
                BasicService.set_destination(
                    FinanceConfigurations.Destination.CODE_CHOICES[1][0],
                    default_code,
                    cgrates_prefixes,
                )
            except api_exceptions.APIException:
                pass
            try:
                cgrates_emergency = Destination.objects.filter(
                    code=FinanceConfigurations.Destination.CODE_CHOICES[1][0],
                    name=emergency_name,
                ).values_list('prefix', flat=True)
                cgrates_emergency = list(cgrates_emergency)
                BasicService.set_destination(
                    FinanceConfigurations.Destination.CODE_CHOICES[1][0],
                    emergency_code,
                    cgrates_emergency,
                )
            except api_exceptions.APIException:
                pass
            try:
                BasicService.load_tariff_plan()
            except api_exceptions.APIException:
                pass
            # Renew subscription type
            subscription_objects = Subscription.objects.filter(
                is_allocated=True,
            )
            for subscription_object in subscription_objects:
                try:
                    SubscriptionService.renew_subscription_type(
                        subscription_id=subscription_object.id
                    )
                except api_exceptions.APIException:
                    pass

    @classmethod
    def get_destination_names(cls, request):
        """
        Get destination names based on query params, used types is a
        important part of the query as it filters the unused destinations in
        operators and branches
        :param request:
        :return:
        """
        query_params = request.query_params
        destinations_object = Destination.objects.all()

        if query_params is not None:
            # All filters in destinations
            if 'prefix' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        prefix__icontains=query_params['prefix']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'prefix': ErrorMessages.DESTINATION_PREFIX_400
                        }
                    )

            if 'name' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        name__icontains=query_params['name']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'name': ErrorMessages.DESTINATION_NAME_400
                        }
                    )
            if 'country_code' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        country_code__icontains=query_params['country_code']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'country_code':
                                ErrorMessages.DESTINATION_COUNTRY_CODE_400
                        }
                    )
            if 'code' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        code__in=[
                            x.strip() for x in query_params['code'].split(',')
                        ]
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'code': ErrorMessages.DESTINATION_CODE_400
                        }
                    )
            if 'unused' in query_params:
                used_destination_ids = []
                if query_params['unused'] == \
                        FinanceConfigurations.Destination.UNUSED_TYPES[0][0]:
                    operators = Operator.objects.all()
                    for operator in operators:
                        used_destination_ids.extend(
                            operator.destinations.values_list('id', flat=True)
                        )
                else:
                    branches = Branch.objects.all()
                    for branch in branches:
                        used_destination_ids.extend(
                            branch.destinations.values_list('id', flat=True)
                        )
                destinations_object = destinations_object.exclude(
                    id__in=list(used_destination_ids)
                )

            # Order by
            destinations_object = CommonService.order_by_query(
                Destination,
                destinations_object,
                query_params,
            )

        destinations_object = destinations_object.values(
            'name',
            'country_code',
        ).annotate(
            prefixes_count=Count('prefix'),
        )
        destinations_object, paginator = Paginator().paginate(
            request=request,
            queryset=destinations_object,
        )
        destinations_serializer = DestinationNamesSerializer(
            destinations_object,
            many=True
        )

        return destinations_serializer.data, paginator

    @classmethod
    def get_destinations(cls, request):
        """
        Get all destinations with details based on query params. used types
        is a important part of the query as it filters the unused
        destinations in operators and branches
        :param request:
        :return:
        """
        destinations_object = Destination.objects.all()
        query_params = request.query_params
        if query_params is not None:
            # All filters in destinations
            if 'prefix' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        prefix__icontains=query_params['prefix']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'prefix': ErrorMessages.DESTINATION_PREFIX_400
                        }
                    )

            if 'name' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        name__icontains=query_params['name']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'name': ErrorMessages.DESTINATION_NAME_400
                        }
                    )
            if 'country_code' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        country_code__icontains=query_params['country_code']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'country_code':
                                ErrorMessages.DESTINATION_COUNTRY_CODE_400
                        }
                    )
            if 'code' in query_params:
                try:
                    destinations_object = destinations_object.filter(
                        code__in=[
                            x.strip() for x in query_params['code'].split(',')
                        ]
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'code': ErrorMessages.DESTINATION_CODE_400
                        }
                    )

            if 'unused' in query_params:
                used_destination_ids = []
                if query_params['unused'] == \
                        FinanceConfigurations.Destination.UNUSED_TYPES[0][0]:
                    operators = Operator.objects.all()
                    for operator in operators:
                        used_destination_ids.extend(
                            operator.destinations.values_list('id', flat=True)
                        )
                else:
                    branches = Branch.objects.all()
                    for branch in branches:
                        used_destination_ids.extend(
                            branch.destinations.values_list('id', flat=True)
                        )
                destinations_object = destinations_object.exclude(
                    id__in=list(used_destination_ids)
                )

            # Order by
            if 'order_by' in query_params:
                order_field_error = []
                order_by = [
                    x.strip() for x in query_params
                    ['order_by'].split(',')
                ]
                for order in order_by:
                    if not Destination.model_field_exists(
                            order.replace('-', ''),
                    ):
                        order_field_error.append(order)

                if order_field_error:
                    raise api_exceptions.ValidationError400(
                        {
                            'non_fields': ErrorMessages.ORDER_BY_400,
                            'errors': order_field_error,
                        }
                    )

                destinations_object = destinations_object.order_by(
                    *order_by,
                )

        destinations_object, paginator = Paginator().paginate(
            request=request,
            queryset=destinations_object,
        )
        destinations_serializer = DestinationSerializer(
            destinations_object,
            many=True
        )

        return destinations_serializer.data, paginator

    @classmethod
    def get_destination(cls, destination_id):
        """
        Get a destination's details based on id
        :param destination_id:
        :return:
        """
        Tools.uuid_validation(destination_id)
        try:
            destination_object = Destination.objects.get(id=destination_id)
        except Destination.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.DESTINATION_404,
            )
        destination_serializer = DestinationSerializer(destination_object)

        return destination_serializer.data

    @classmethod
    def update_destination(cls, destination_id, body):
        """
        Update a destination based on JSON body
        :param destination_id:
        :param body:
        :return:
        """
        Tools.uuid_validation(destination_id)
        body = Tools.get_dict_from_json(body)
        try:
            destination_object = Destination.objects.get(id=destination_id)
        except Destination.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.DESTINATION_404,
            )
        destination_serializer = DestinationSerializer(
            destination_object,
            data=body,
            partial=True,
        )

        if destination_serializer.is_valid(raise_exception=True):
            destination_serializer.save()

        return destination_serializer.data

    @classmethod
    def add_destination(cls, body):
        """
        Add a destination in gateway as well as CGRateS based on conventions.
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        destination_serializer = DestinationSerializer(data=body)

        if destination_serializer.is_valid(raise_exception=True):
            prefixes = Destination.objects.filter(
                code=destination_serializer.validated_data['code'],
                name=destination_serializer.validated_data['name'],
            ).values_list('prefix', flat=True)
            prefixes = list(prefixes)
            prefixes.append(
                destination_serializer.validated_data['prefix'],
            )
            # Add to CGRateS Service
            if BasicService.set_destination(
                    destination_serializer.validated_data['code'],
                    destination_serializer.validated_data['name'],
                    prefixes,
            ):
                destination_serializer.save()

                return destination_serializer.data

            raise api_exceptions.APIException(
                _('Can not add new destination due to CGRateS Service problem')
            )

    @classmethod
    def remove_destination(cls, destination_id):
        """
        Remove a destination from gateway. This prevent removing last
        destination (destination_code)
        :param destination_id:
        :return:
        """
        Tools.uuid_validation(destination_id)
        try:
            destination_object = Destination.objects.get(id=destination_id)
        except Destination.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.DESTINATION_404,
            )

        prefixes = Destination.objects.filter(
            code=destination_object.code,
            name=destination_object.name,
        ).values_list('prefix', flat=True)
        prefixes = list(prefixes)
        prefixes.remove(
            destination_object.prefix,
        )
        # Add to CGRateS Service
        if len(prefixes) == 0:
            if BasicService.remove_destination(
                    destination_object.code,
                    destination_object.name,
            ):
                destination_object.delete()

                return True
        else:
            if BasicService.set_destination(
                    destination_object.code,
                    destination_object.name,
                    prefixes,
            ):
                destination_object.delete()

                return True

        raise api_exceptions.APIException(
            _('Can not remove destination due to CGRateS Service problem')
        )

    @classmethod
    def get_prefixes_mobile(cls):
        """
        Get all mobile prefixes
        :return:
        """
        return cls.get_destinations_prefixes(
            code='mobile_national'
        )

    @classmethod
    def get_prefixes_landline_long_distance(cls, subscription_code):
        """
        Get all long distance prefixes based on subscription code. Each
        subscription belongs to a branch, prefixes outside of that branch
        are long distance
        :param subscription_code:
        :return:
        """
        return cls.get_destinations_prefixes(
            code='landline_national',
            excludes=subscription_code,
        )

    @classmethod
    def get_prefixes_landline_local(cls, subscription_code):
        """
        Get all local prefixes based on subscription code. Each
        subscription belongs to a branch, prefixes inside of that branch
        are local prefixes
        :param subscription_code:
        :return:
        """
        return cls.get_destinations_prefixes(
            code='landline_national',
            includes=subscription_code,
        )


    @classmethod
    def get_prefixes_landline_corporate(cls):
        """
        Corporate prefixes defined in RuntimeConfig combined with branches
        :return:
        """
        return cls.get_destinations_prefixes(
            code='landline_national',
            only_corporate=True,
        )

    @classmethod
    def get_prefixes_international(cls):
        """
        Get all international prefixes
        :return:
        """
        landline_list = cls.get_destinations_prefixes(
            code='landline_international'
        )
        mobile_list = cls.get_destinations_prefixes(
            code='mobile_international'
        )

        return mobile_list + landline_list

    @classmethod
    def get_destinations_prefixes(
            cls,
            code,
            includes=None,
            excludes=None,
            only_corporate=False,
    ):
        """
        Get prefixes based on some criteria
        :param code:
        :param includes:
        :param excludes:
        :param only_corporate:
        :return:
        """
        print(code)
        print(includes)
        print(excludes)
        print(only_corporate)
        if only_corporate:
            prefixes = Destination.objects.filter(
                code=code,
                name=
                FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[1]
            )
        else:
            prefixes = Destination.objects.filter(
                code=code,
            ).exclude(
                name=
                FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[1]
            )

        if includes or excludes:
            branch_prefixes = []
            try:
                branch_object = Subscription.objects.get(
                    Q(subscription_code=includes) |
                    Q(subscription_code=excludes)
                ).branch
                if branch_object:
                    branch_prefixes = list(
                        branch_object.destinations.values_list(
                            'prefix',
                            flat=True,
                        ),
                    )
            except Subscription.DoesNotExist:
                raise api_exceptions.NotFound404(
                    ErrorMessages.SUBSCRIPTION_404
                )
            if includes:
                if branch_prefixes:
                    prefixes = prefixes.filter(
                        prefix__in=branch_prefixes,
                    )
                else:
                    return [FinanceConfigurations.Destination.NOT_FOUND_PREFIX]
            else:
                if branch_prefixes:
                    prefixes = prefixes.exclude(
                        prefix__in=branch_prefixes,
                    )
        prefixes = prefixes.values_list('prefix', flat=True)
        print(prefixes)
        if prefixes:
            return list(prefixes)
        else:
            return [FinanceConfigurations.Destination.NOT_FOUND_PREFIX]
