# --------------------------------------------------------------------------
# Handle Package related logics
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - package.py
# Created at 2020-8-29,  17:32:5
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils.translation import gettext as _

from cgg.apps.finance.models import Package
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.package import (
    PackageSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools


class PackageService:

    @classmethod
    def get_packages(
            cls,
            request,
    ):
        """
        Get all packages based on filters
        :param request:
        :return:
        """
        query_params = request.query_params
        package_objects = Package.objects.all()

        if query_params is not None:
            if FinanceConfigurations.QueryParams.GENERIC_OR in query_params:
                value = query_params[
                    FinanceConfigurations.QueryParams.GENERIC_OR
                ]
                try:
                    decimal_value = Decimal(value)
                except (ValueError, InvalidOperation):
                    decimal_value = 0
                package_objects = package_objects.filter(
                    Q(package_name__icontains=value) |
                    Q(package_code__icontains=value) |
                    Q(package_due=value) |
                    Q(package_price=decimal_value) |
                    Q(package_value=decimal_value)
                ).distinct()

            if 'package_code' in query_params:
                try:
                    package_objects = package_objects.filter(
                        package_code__icontains=query_params['package_code']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'package_name': ErrorMessages.PACKAGE_NAME_400
                        }
                    )
            if 'package_name' in query_params:
                try:
                    package_objects = package_objects.filter(
                        package_name__icontains=query_params['package_name']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'package_name': ErrorMessages.PACKAGE_NAME_400
                        }
                    )
            if 'package_price' in query_params:
                try:
                    package_objects = package_objects.filter(
                        package_price=query_params['package_price']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'package_price': ErrorMessages.PACKAGE_PRICE_400
                        }
                    )
            if 'package_value' in query_params:
                try:
                    package_objects = package_objects.filter(
                        package_value=query_params['package_value']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'package_value': ErrorMessages.PACKAGE_VALUE_400
                        }
                    )
            if 'package_due' in query_params:
                try:
                    package_objects = package_objects.filter(
                        package_due=query_params['package_due']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'package_due': ErrorMessages.PACKAGE_DUE_400
                        }
                    )
            if 'is_active' in query_params:
                try:
                    package_objects = package_objects.filter(
                        is_active=False if query_params['is_active'] in (
                            "False", 'false', 0, "0") else True
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'is_active': ErrorMessages.PACKAGE_IS_ACTIVE_400
                        }
                    )
            if 'is_featured' in query_params:
                try:
                    package_objects = package_objects.filter(
                        is_featured=False if query_params['is_featured'] in (
                            "False", 'false', 0, "0") else True
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'is_featured':
                                ErrorMessages.PACKAGE_IS_FEATURED_400
                        }
                    )
            if 'is_enable' in query_params:
                date_now = datetime.now()
                if query_params['is_enable'] in ("False", 'false', 0, "0"):
                    package_objects = package_objects.filter(
                        Q(
                            start_at__gte=date_now,
                        ) |
                        Q(
                            end_at__lte=date_now,
                        )
                    )
                else:
                    package_objects = package_objects.exclude(
                        Q(
                            start_at__gte=date_now,
                        ) |
                        Q(
                            end_at__lte=date_now,
                        )
                    )

            # Common filters
            package_objects = CommonService.filter_query_common(
                package_objects,
                query_params,
            )

            # Order by
            package_objects = CommonService.order_by_query(
                Package,
                package_objects,
                query_params,
            )

        package_objects, paginator = Paginator().paginate(
            request=request,
            queryset=package_objects,
        )
        package_serializer = PackageSerializer(
            package_objects,
            many=True,
        )

        return package_serializer.data, paginator

    @classmethod
    def add_package(
            cls,
            body,
    ):
        """
        Add a new package
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        package_serializer = PackageSerializer(
            data=body,
        )

        if package_serializer.is_valid(raise_exception=True):
            package_serializer.save()

            return package_serializer.data

    @classmethod
    def remove_package(
            cls,
            package_id,
    ):
        """
        Remove a package (Default package is restricted)
        :param package_id:
        :return:
        """
        Tools.uuid_validation(package_id)
        try:
            package_object = Package.objects.get(
                id=package_id,
            )
        except Package.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PACKAGE_404
            )
        if package_object.package_code == \
                FinanceConfigurations.Package.DEFAULT_PACKAGE_CODE[0]:
            raise api_exceptions.Conflict409(
                _("Can not remove the default package")
            )

        package_object.delete()

        return True

    @classmethod
    def update_package(
            cls,
            package_id,
            body,
    ):
        """
        Update a package
        :param package_id:
        :param body:
        :return:
        """
        Tools.uuid_validation(package_id)
        body = Tools.get_dict_from_json(body)
        try:
            package_object = Package.objects.get(
                id=package_id,
            )
        except Package.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PACKAGE_404
            )

        package_serializer = PackageSerializer(
            package_object,
            data=body,
            partial=True,
        )

        if package_serializer.is_valid(raise_exception=True):
            package_serializer.save()

            return package_serializer.data

    @classmethod
    def get_package(cls, package_id):
        """
        Get details of a package
        :param package_id:
        :return:
        """
        Tools.uuid_validation(package_id)
        try:
            package_object = Package.objects.get(
                id=package_id,
            )
        except Package.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PACKAGE_404
            )

        package_serializer = PackageSerializer(
            package_object
        )

        return package_serializer.data
