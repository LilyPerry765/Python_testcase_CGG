# --------------------------------------------------------------------------
#
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - tax.py
# Created at 2020-8-29,  17:45:45
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from cgg.apps.finance.models import Tax


class TaxService:

    @classmethod
    def get_tax_percent(cls, country_code='IRN'):
        """
        Get tax percent based on country_code
        :param country_code:
        :return:
        """
        try:
            tax_percent_object = Tax.objects.get(
                country_code=country_code,
            )
            tax_percent = tax_percent_object.tax_percent
        except Tax.DoesNotExist:
            tax_percent = 9

        return tax_percent
