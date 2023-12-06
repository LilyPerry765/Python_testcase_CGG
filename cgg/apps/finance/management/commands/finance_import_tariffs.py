# --------------------------------------------------------------------------
# As a convention we use Integer values for ConnectFee and Rate so consider
# that in new tariff plans
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - finance_import_tariffs.py
# Created at 2020-2-25,  10:24:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from json import JSONDecodeError

from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.basic.versions.v1.services.cgrates import CGRateSService
from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.operator import (
    OperatorService,
)
from cgg.core import api_exceptions


class Command(BaseCommand):
    help = "Import tariff plans from JSON file using basic APIs"

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Absolute path to tariff plans json file'
        )

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[5][0])
    def handle(self, *args, **options):
        """
        Import tariff plans. Four keys are mandatory: rates.
        destination_rates, rating_plans, rating_profiles.
        This command uses CGRateS Service from basic app so all objects must
        match with reverse serializers defined in basic app
        :param args:
        :param options: contains file_path (Absolute path to json file)
        :return:
        """
        file_path = options['file_path']
        try:
            with open(file_path) as json_file:
                tariffs = json.load(json_file)

                if all(
                        key in tariffs for key in (
                                'rates',
                                'destination_rates',
                                'rating_plans',
                                'rating_profiles',
                                'default_operator',
                        )
                ):
                    for rate in tariffs['rates']:
                        try:
                            CGRateSService.add_rate(
                                json.dumps(rate)
                            )
                        except (
                                api_exceptions.APIException,
                                ValidationError,
                        ) as e:
                            self.stdout.write(e)
                            pass
                    for destination_rate in tariffs['destination_rates']:
                        try:
                            CGRateSService.add_destination_rates(
                                json.dumps(destination_rate)
                            )
                        except (
                                api_exceptions.APIException,
                                ValidationError,
                        ) as e:
                            self.stdout.write(e)
                            pass
                    for rating_plan in tariffs['rating_plans']:
                        try:
                            CGRateSService.add_rating_plans(
                                json.dumps(rating_plan)
                            )
                        except (
                                api_exceptions.APIException,
                                ValidationError,
                        ) as e:
                            self.stdout.write(e)
                            pass
                    for rating_profile in tariffs['rating_profiles']:
                        try:
                            CGRateSService.add_rating_profile(
                                json.dumps(rating_profile)
                            )
                        except (
                                api_exceptions.APIException,
                                ValidationError,
                        ) as e:
                            self.stdout.write(e)
                            pass
                    if 'default_operator' in tariffs:
                        try:
                            OperatorService.add_account_for_operator(
                                tariffs["default_operator"]["code"]
                            )
                            BasicService.set_attribute_profile_inbound(
                                tariffs["default_operator"]["code"],
                                tariffs["default_operator"]["prefixes"],
                                BasicConfigurations.Priority.VERY_LOW,
                            )
                        except (
                                api_exceptions.APIException,
                                ValidationError,
                        ) as e:
                            self.stdout.write(e)
                            pass
                else:
                    raise CommandError("Some keys are missing")
        except IOError as e:
            raise CommandError(e)
        except JSONDecodeError:
            raise CommandError("JSON is invalid")

        CGRateSService.reload_plans()
        self.stdout.write(
            "Tariff plans loaded successfully",
        )
