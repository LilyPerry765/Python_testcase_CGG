# --------------------------------------------------------------------------
# Import all destination. Use it only once of system initialization.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_import_destinations.py
# Created at 2020-8-29,  16:38:51
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from json import JSONDecodeError

from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.destination import (
    DestinationService,
)
from cgg.core import api_exceptions


class Command(BaseCommand):
    help = "Import destinations from JSON file using destination service"

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Absolute path to destination json file'
        )

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[4][0])
    def handle(self, *args, **options):
        """
        Import destination from destination objects based on this structure:
        [
            {
                "prefix": "020",
                "name": "Other",
                "country_code": "IRN",
                "code": "landline_national",
            },
        ]
        :param args:
        :param options: contains file_path (Absolute path to json file)
        :return:
        """
        file_path = options['file_path']
        counter = int(0)
        try:
            with open(file_path) as json_file:
                destinations = json.load(json_file)
                for destination in destinations:
                    try:
                        DestinationService.add_destination(
                            json.dumps(destination)
                        )
                        counter += 1
                    except (api_exceptions.APIException, ValidationError):
                        pass
        except IOError as e:
            raise CommandError(e)
        except JSONDecodeError:
            raise CommandError("JSON is invalid")

        self.stdout.write(
            f"{counter} destinations are added into CGG",
        )
