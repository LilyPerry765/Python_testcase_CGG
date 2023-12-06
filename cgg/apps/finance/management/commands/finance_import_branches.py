# --------------------------------------------------------------------------
# Import branches and update subscription's based on them.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_import_branches.py
# Created at 2020-8-29,  16:38:0
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from json import JSONDecodeError

from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.branch import BranchService
from cgg.core import api_exceptions


class Command(BaseCommand):
    help = "Import branches from JSON file using branch service"

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Absolute path to destination json file'
        )

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[8][0])
    def handle(self, *args, **options):
        """
        Import branches from branch objects based on this structure:
        [
            {
                "branch_code": "tehran",
                "prefixes": [
                    "021",
                    "9821"
                ]
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
                branches = json.load(json_file)
                for branch in branches:
                    try:
                        BranchService.add_branch(
                            json.dumps(branch),
                            renew_protocol=False,
                        )
                        counter += 1
                    except (api_exceptions.APIException, ValidationError):
                        pass
        except IOError as e:
            raise CommandError(e)
        except JSONDecodeError:
            raise CommandError("JSON is invalid")

        self.stdout.write(
            f"{counter} new branches are added in CGG",
        )
