# --------------------------------------------------------------------------
# Handle logics related to Branch objects.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - branch.py
# Created at 2020-8-29,  16:50:7
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from datetime import datetime, timedelta

from django.db.models import CharField, F, Value
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions,
)
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.basic.versions.v1.services.cgrates import CGRateSService
from cgg.apps.finance.models import Branch, RuntimeConfig, Subscription
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.branch import (
    BranchSerializer,
    BranchesSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.core import api_exceptions
from cgg.core.cache import Cache
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools


class BranchService:

    @classmethod
    def get_branch(cls, branch_id):
        """
        Get details of a branch
        :param branch_id:
        :return:
        """
        Tools.uuid_validation(branch_id)
        try:
            branch_object = Branch.objects.get(
                id=branch_id
            )
        except Branch.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.BRANCH_404,
            )

        branch_serializer = BranchSerializer(branch_object)

        return branch_serializer.data

    @classmethod
    def get_branches(cls, request):
        """
        Get all branches based on query params
        :param request:
        :return:
        """
        branch_objects = Branch.objects.all()

        if request.query_params is not None:
            # All filters in branches
            if 'branch_code' in request.query_params:
                try:
                    branch_objects = branch_objects.filter(
                        branch_code__icontains=request.query_params[
                            'branch_code']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'branch_code': ErrorMessages.BRANCH_CODE_400
                        }
                    )
            if 'branch_name' in request.query_params:
                try:
                    branch_objects = branch_objects.filter(
                        branch_name__icontains=request.query_params[
                            'branch_name']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'branch_name': ErrorMessages.BRANCH_NAME_400
                        }
                    )
            # Order by
            branch_objects = CommonService.order_by_query(
                Branch,
                branch_objects,
                request.query_params
            )
        branch_objects, paginator = Paginator().paginate(
            request=request,
            queryset=branch_objects,
        )
        branches_serializer = BranchesSerializer(branch_objects, many=True)

        return branches_serializer.data, paginator

    @classmethod
    def get_branch_from_number(cls, number):
        """
        Convert a number to a branch object. eg. +982105452144 -> TehranBranch
        :param number:
        :return:
        """
        branch_object = Branch.objects.annotate(reverse_number=Value(
            number,
            output_field=CharField(),
        )).filter(
            reverse_number__istartswith=F('destinations__prefix'),
        )

        if branch_object.count() == 0:
            branch_object = cls.get_default_branch()
        elif branch_object.count() == 1:
            branch_object = branch_object[0]
        elif branch_object.count() > 1:
            raise api_exceptions.Conflict409(
                _('More than one branch is found with this prefix')
            )

        return branch_object

    @classmethod
    def get_default_branch(cls):
        """
        Return the default branch (Create if not exists)
        :return:
        """
        try:
            branch_object = Branch.objects.get(
                branch_code=FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[
                    0],
            )
        except Branch.DoesNotExist:
            branch_dict = {
                "branch_code":
                    FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[0],
                "branch_name":
                    FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[1],
            }
            branch_object = Branch.objects.create(
                **branch_dict
            )

        return branch_object

    @classmethod
    def add_branch(
            cls,
            body,
            renew_protocol=True,
    ):
        """
        Add a new branch if not exists and initialize attributes in CGRateS
        :param renew_protocol:
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        branch_serializer = BranchSerializer(data=body)
        if branch_serializer.is_valid(raise_exception=True):
            branch_serializer.save()
            if renew_protocol:
                cls.renew_corporate_numbers()

        cls.set_branch_in_cgrates(
            branch_serializer.data['id']
        )
        if renew_protocol:
            cls.renew_subscriptions_branch()

        return branch_serializer.data

    @classmethod
    def update_branch(cls, branch_id, body):
        """
        Update a branch in CGRateS as well as the object
        :param branch_id:
        :param body:
        :return:
        """
        Tools.uuid_validation(branch_id)
        body = Tools.get_dict_from_json(body)
        try:
            branch_object = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.BRANCH_404,
            )
        branch_serializer = BranchSerializer(
            branch_object,
            data=body,
            partial=True,
        )
        if branch_object.branch_code in (
                FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[0],
                FinanceConfigurations.Branch.DEFAULT_COUNTRY_BRANCH[0],
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
        ):
            raise api_exceptions.Conflict409(
                _("Default branches can not be updated directly")
            )
        if branch_serializer.is_valid(raise_exception=True):
            branch_serializer.save()
            cls.renew_corporate_numbers()

        cls.set_branch_in_cgrates(
            branch_id,
        )

        return branch_serializer.data

    @classmethod
    def set_branch_in_cgrates(cls, branch_id):
        """
        Creates destination rates, rating plans and profiles for branch in
        CGRateS
        :param branch_id:
        :return:
        """
        # 1. Add destination rate
        branch_object = Branch.objects.get(
            id=branch_id
        )
        branch_destinations = branch_object.destinations.all().distinct(
            'name',
            'code',
        )
        destination_rates = []
        for branch_destination in branch_destinations:
            destination_rates.append(
                {
                    "destination_id": CGRatesConventions.destination(
                        branch_destination.code,
                        branch_destination.name,
                    ),
                    # @TODO: Not a good way though, think of a way to make
                    #  this rate_id dynamic
                    "rate_id": "RT_29Rial",
                    "rounding_method": "*up",
                    "rounding_decimals": 4,
                    "max_cost": 0,
                    "max_cost_strategy": ""
                }
            )
        if destination_rates:
            destination_rate = {
                "id": branch_object.branch_code,
                "destination_rates": destination_rates,
            }
            CGRateSService.add_destination_rates(
                json.dumps(destination_rate)
            )
            # 2. Add rating plan
            rating_plan = {
                "id": branch_object.branch_code,
                "rating_plan_bindings": [
                    {
                        "destination_rates_id":
                            CGRatesConventions.destination_rate(
                                branch_object.branch_code
                            ),
                        "timing_id": "*any",
                        "weight": BasicConfigurations.Priority.HIGH,
                    },
                    {
                        "destination_rates_id": "DR_Default",
                        "timing_id": "*any",
                        "weight": BasicConfigurations.Priority.NORMAL,
                    },
                    {
                        "destination_rates_id": "DR_International",
                        "timing_id": "*any",
                        "weight": BasicConfigurations.Priority.NORMAL,
                    }
                ]
            }
            CGRateSService.add_rating_plans(
                json.dumps(rating_plan)
            )
            # 3. Add rating profile
            activation_time = datetime.strftime(
                (datetime.now() - timedelta(hours=12)),
                '%Y-%m-%dT%H:%M:%SZ'
            )
            rating_profile = {
                "category": CGRatesConventions.branch_name(
                    branch_object.branch_code
                ),
                "subject": "*any",
                "rating_plan_activations": [
                    {

                        "activation_time": activation_time,
                        "rating_plan_id": CGRatesConventions.rating_plan(
                            branch_object.branch_code
                        ),
                        "fallback_subjects": ""
                    }
                ]
            }
            CGRateSService.add_rating_profile(
                json.dumps(rating_profile)
            )

            Cache.delete(
                key=Cache.KEY_CONVENTIONS['maximum_rate'],
                values={
                    'branch_code': branch_object.branch_code,
                },
            )
            Cache.delete(
                key=Cache.KEY_CONVENTIONS['minimum_rate'],
                values={
                    'branch_code': branch_object.branch_code,
                },
            )

            try:
                BasicService.load_tariff_plan()
            except api_exceptions.APIException:
                pass

            return True

        return False

    @classmethod
    def renew_subscriptions_branch(cls, search_type=None):
        """
        Renew all subscriptions' branch related to deleted or updated branch
        :param search_type: not True in any kind means update
        :return:
        """
        if search_type:
            subscription_objects = Subscription.objects.filter(
                is_allocated=True,
                branch_id=None,
            )
        else:
            subscription_objects = Subscription.objects.filter(
                is_allocated=True,
            )
        for subscription_object in subscription_objects:
            new_branch = cls.get_branch_from_number(
                subscription_object.number,
            )
            subscription_object.branch_id = new_branch.id
            subscription_object.save()

            # 1. Remove old attribute profile if exists
            try:
                BasicService.remove_attribute_profile(
                    attribute_name=subscription_object.subscription_code,
                    attribute_type='None',
                )
            except (
                    api_exceptions.APIException,
                    api_exceptions.NotFound404,
            ):
                pass

            # 2. Renew branch based on subscription's number
            BasicService.set_attribute_profile_account(
                subscription_object.subscription_code,
                subscription_object.number,
                subscription_object.subscription_type,
                new_branch.branch_code,
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                BranchService.get_emergency_destinations(),
            )

    @classmethod
    def remove_branch(cls, branch_id):
        """
        Remove a branch from gateway, update it in CGRateS and renew
        subscriptions' branches
        :param branch_id:
        :return:
        """
        Tools.uuid_validation(branch_id)
        try:
            branch_object = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.BRANCH_404,
            )
        if branch_object.branch_code in (
                FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[0],
                FinanceConfigurations.Branch.DEFAULT_COUNTRY_BRANCH[0],
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
        ):
            raise api_exceptions.Conflict409(
                _("Default branches can not be removed")
            )

        try:
            CGRateSService.remove_destination_rate(
                CGRatesConventions.destination_rate(
                    branch_object.branch_code
                )
            )
        except api_exceptions.APIException:
            pass
        try:
            CGRateSService.remove_rating_plan(
                CGRatesConventions.rating_plan(
                    branch_object.branch_code
                )
            )
        except api_exceptions.APIException:
            pass
        try:
            CGRateSService.remove_rating_profile(
                CGRatesConventions.default_load_identifier(),
                json.dumps({
                    'subject': '*any',
                    'category': CGRatesConventions.branch_name(
                        branch_object.branch_code
                    ),
                })
            )
        except api_exceptions.APIException:
            pass
        branch_object.delete()
        cls.renew_corporate_numbers()
        # Renew branches
        cls.renew_subscriptions_branch(
            search_type='delete',
        )

    @classmethod
    def renew_corporate_numbers(cls):
        """
        Renew corporate numbers, calling save on RuntimeConfig object
        triggers Destination.post_save_runtime_config signal to create
        destination and CGRateS related calls
        :return:
        """
        try:
            rc = RuntimeConfig.objects.get(
                item_key=
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[2][0]
            )
            rc.save()
        except RuntimeConfig.DoesNotExist:
            pass

    @classmethod
    def get_emergency_destinations(cls):
        """
        Return emergency branch code and flat list of it's numbers
        :return:
        """
        try:
            dest_emergency = Branch.objects.get(
                branch_code=
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
            ).destinations.all().values_list('prefix', flat=True)
            dest_emergency = list(dest_emergency)
        except Branch.DoesNotExist:
            dest_emergency = []

        return dest_emergency

    @classmethod
    def get_not_default_destinations(cls, ):
        """
        Return all destinations of all branches excluding country and
        emergency branches
        :return:
        :rtype:
        """
        dest = []
        branches = Branch.objects.exclude(
            branch_code__in=[
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                FinanceConfigurations.Branch.DEFAULT_COUNTRY_BRANCH[0],
            ]
        )
        for b in branches:
            dest += list(
                b.destinations.all().values_list('prefix', flat=True)
            )

        return dest
