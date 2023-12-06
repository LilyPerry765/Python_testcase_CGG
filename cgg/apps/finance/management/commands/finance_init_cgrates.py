# --------------------------------------------------------------------------
# Sets call url actions (80 and 100 percent), suppliers and chargers in
# CGRateS. Use it only once in system initialization.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_init_cgrates.py
# Created at 2020-8-29,  16:39:35
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.core.management.base import BaseCommand

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core import api_exceptions


class Command(BaseCommand):
    help = "Initialize supplier, charger and actions for CGRateS"

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[6][0])
    def handle(self, *args, **options):
        """
        Initialize supplier, charger and actions for CGRateS
        :param args:
        :param options:
        :return:
        """
        # 1. Set call_url actions
        try:
            BasicService.set_call_url_action_80()
            BasicService.set_call_url_action_100()
        except api_exceptions.APIException:
            self.stdout.write(
                "Error in adding call url actions",
            )
        try:
            BasicService.set_supplier_profile()
        except api_exceptions.APIException:
            self.stdout.write(
                "Error in adding default supplier profile",
            )
        try:
            BasicService.set_charger_profile()
        except api_exceptions.APIException:
            self.stdout.write(
                "Error in adding default charger profile",
            )

        self.stdout.write(
            "CGRateS initialized successfully",
        )
