from django.utils.translation import get_language, gettext as _


class BasicConfigurations:
    @staticmethod
    def default_headers():
        return {
            'Accept-Language': get_language(),
        }

    class APIRequestLabels:
        RELOAD_PLANS = "Reload"
        DELETE_RATING_PROFILE = "Remove rating profile"
        REMOVE_RATING_PLAN = "Remove rating plan"
        SET_RATING_PLANS = "Set rating plan"
        DELETE_TIMING = "Delete timing"
        SET_TIMINGS = "Set timings"
        REMOVE_DESTINATION_RATE = "Remove destination rate"
        DELETE_RATE = "Delete rate"
        ADD_DESTINATION_RATES = "Add destination rates"
        ADD_RATE = 'Add rate'
        GET_RATING_PROFILES = 'Get rating profiles'
        GET_RATING_PROFILE = 'Get rating profile'
        GET_RATING_PLANS = 'Get rating plans'
        GET_RATING_PLAN = 'Get rating plan'
        GET_TIMINGS = "Get timings"
        GET_TIMING = "Get timing"
        GET_DESTINATION_RATE = "Get destination rate"
        GET_DESTINATION_RATES = "Get destination rates"
        GET_RATE = "Get rate"
        GET_RATES = "Get rates"
        GET_CHARGER = "Get charger"
        GET_CHARGERS = "Get chargers"
        GET_SUPPLIERS = "Get suppliers"
        GET_SUPPLIER = "Get supplier"
        GET_FILTERS = "Get filters"
        GET_FILTER = "Get filter"
        GET_THRESHOLD = "Get threshold"
        GET_THRESHOLDS = "Get thresholds"
        GET_DESTINATIONS = "Get destinations"
        GET_ATTRIBUTE = "Get attribute"
        GET_ATTRIBUTES = "Get attributes"
        GET_ACTIONS = "Get actions"
        GET_CDRS = "Get CDRs"
        GET_ACCOUNTS = "Get accounts"
        GET_ACCOUNT = "Get account"

    class Priority:
        """
        CGRateS weight (lower integer means greater priority)
        """
        VERY_LOW = 0
        LOW = 10
        MEDIUM = 20
        NORMAL = 30
        HIGH = 40
        CRITICAL = 50
        SUPER_CRITICAL = 60

    class Types:
        ACCOUNT_TYPE = (
            ('subscription', _('Subscription')),
            ('operator', _('Operator')),
        )
        ATTRIBUTE_TYPE = (
            ('account', _('Account')),
            ('inbound', _('Inbound')),
        )
