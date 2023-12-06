# --------------------------------------------------------------------------
# @DEPRECATED
# The functionality of this custom command has been moved to Trunk backend
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - finance_import_credits.py
# Created at 2020-3-3,  17:46:51
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from decimal import Decimal

import xlrd
from django.core.management.base import BaseCommand

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import Subscription
from cgg.apps.finance.versions.v1.config import FinanceConfigurations


class Command(BaseCommand):
    help = 'Import subscriptions credit'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Absolute path to excel file'
        )
        parser.add_argument(
            'subscription_column',
            type=str,
            help='Column name of subscription code'
        )
        parser.add_argument(
            'credit_column',
            type=str,
            help='Column name of credit'
        )

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[7][0])
    def handle(self, *args, **options):
        file_path = options['file_path']
        subscription_column = options['subscription_column']
        credit_column = options['credit_column']
        sheet = None
        updated_count = 0
        try:
            work_book = xlrd.open_workbook(file_path)
            sheet = work_book.sheet_by_index(0)
            sheet.cell_value(0, 0)
        except Exception as e:
            self.stderr.write(str(e))

        if sheet:
            subscription_index = -1
            credit_index = -1
            for cell_index in range(sheet.ncols):
                if sheet.cell_value(0, cell_index) == subscription_column:
                    subscription_index = cell_index
                if sheet.cell_value(0, cell_index) == credit_column:
                    credit_index = cell_index
            if subscription_index == -1 or credit_index == -1:
                self.stderr.write(
                    "Subscription and credit column does not exists!",
                )
            else:
                for row_index in range(0, sheet.nrows):
                    if sheet.cell_type(
                        row_index,
                        subscription_index,
                    ) != 1:
                        # 1 is Text,  if not text strip and split
                        subscription_code = str(sheet.cell_value(
                            row_index,
                            subscription_index,
                        )).strip().split(".")[0]
                    else:
                        subscription_code = str(sheet.cell_value(
                            row_index,
                            subscription_index,
                        )).strip()
                    credit = str(
                        sheet.cell_value(row_index, credit_index)
                    ).strip()
                    try:
                        subscription_object = Subscription.objects.get(
                            subscription_code=subscription_code,
                        )
                        subscription_object.customer.credit = Decimal(
                            float(credit),
                        )
                        subscription_object.save()
                        updated_count += 1
                    except (Subscription.DoesNotExist, ValueError):
                        pass
            self.stdout.write(
                f"{updated_count} of {sheet.nrows} subscriptions are updated "
                f"successfully"
            )
