from django.urls import re_path

from cgg.apps.basic.versions.v1.api import api

urls = [
    ############################################
    #            Account related URLs          #
    ############################################
    # Get all accounts
    re_path(
        r'^(?:v1/)?accounts(?:/)?$',
        api.AccountsAPIView.as_view(),
        name='basic_accounts'
    ),
    # Get an account details
    re_path(
        r'^(?:v1/)?accounts/(?P<account>[^/]+)(?:/)?$',
        api.AccountAPIView.as_view(),
        name='basic_account'
    ),
    ############################################
    #            CDRs related URLs          #
    ############################################
    # Get all CDRs
    re_path(
        r'^(?:v1/)?cdrs(?:/)?$',
        api.CDRsAPIView.as_view(),
        name='basic_cdrs'
    ),
    ############################################
    #            Actions related URLs          #
    ############################################
    # Get all Actions
    re_path(
        r'^(?:v1/)?actions(?:/)?$',
        api.ActionsAPIView.as_view(),
        name='basic_actions'
    ),
    ############################################
    #            Threshold related URLs          #
    ############################################
    # Get all Thresholds
    re_path(
        r'^(?:v1/)?thresholds(?:/)?$',
        api.ThresholdsAPIView.as_view(),
        name='basic_thresholds'
    ),
    # Get an Threshold
    re_path(
        r'^(?:v1/)?thresholds/(?P<threshold>[^/]+)(?:/)?$',
        api.ThresholdAPIView.as_view(),
        name='basic_threshold'
    ),
    ############################################
    #            Attributes related URLs          #
    ############################################
    # Get all Attributes
    re_path(
        r'^(?:v1/)?attributes(?:/)?$',
        api.AttributesAPIView.as_view(),
        name='basic_attributes'
    ),
    # Get an Attribute
    re_path(
        r'^(?:v1/)?attributes/(?P<attribute>[^/]+)(?:/)?$',
        api.AttributeAPIView.as_view(),
        name='basic_attribute'
    ),
    ############################################
    #            Destinations related URLs          #
    ############################################
    # Get all Actions
    re_path(
        r'^(?:v1/)?destinations(?:/)?$',
        api.DestinationsAPIView.as_view(),
        name='basic_actions'
    ),
    ############################################
    #            Filters related URLs          #
    ############################################
    # Get all Filters
    re_path(
        r'^(?:v1/)?filters(?:/)?$',
        api.FiltersAPIView.as_view(),
        name='basic_filters'
    ),
    # Get a Filter
    re_path(
        r'^(?:v1/)?filters/(?P<filter_name>[^/]+)(?:/)?$',
        api.FilterAPIView.as_view(),
        name='basic_filter'
    ),
    ############################################
    #            Supplier related URLs          #
    ############################################
    # Get all Suppliers
    re_path(
        r'^(?:v1/)?suppliers(?:/)?$',
        api.SuppliersAPIView.as_view(),
        name='basic_suppliers'
    ),
    # Get a Supplier
    re_path(
        r'^(?:v1/)?suppliers/(?P<supplier>[^/]+)(?:/)?$',
        api.SupplierAPIView.as_view(),
        name='basic_supplier'
    ),
    ############################################
    #            Charger related URLs          #
    ############################################
    # Get all Chargers
    re_path(
        r'^(?:v1/)?chargers(?:/)?$',
        api.ChargersAPIView.as_view(),
        name='basic_chargers'
    ),
    # Get a charger
    re_path(
        r'^(?:v1/)?chargers/(?P<charger>[^/]+)(?:/)?$',
        api.ChargerAPIView.as_view(),
        name='basic_charger'
    ),
    ############################################
    #            Rating related URLs          #
    ############################################
    # Get all Rates
    re_path(
        r'^(?:v1/)?rates(?:/)?$',
        api.RatesAPIView.as_view(),
        name='basic_rates'
    ),
    # Get a Rate
    re_path(
        r'^(?:v1/)?rates/(?P<rate>[^/]+)(?:/)?$',
        api.RateAPIView.as_view(),
        name='basic_rate'
    ),
    # Get all Destinations Rates
    re_path(
        r'^(?:v1/)?destination-rates(?:/)?$',
        api.DestinationRatesAPIView.as_view(),
        name='basic_destination_rates'
    ),
    # Get a Destinations Rates
    re_path(
        r'^(?:v1/)?destination-rates/(?P<destination_rate>[^/]+)(?:/)?$',
        api.DestinationRateAPIView.as_view(),
        name='basic_destination_rate'
    ),
    # Get all timings
    re_path(
        r'^(?:v1/)?timings(?:/)?$',
        api.TimingsAPIView.as_view(),
        name='basic_timings'
    ),
    # Get a timing
    re_path(
        r'^(?:v1/)?timings/(?P<timing>[^/]+)(?:/)?$',
        api.TimingAPIView.as_view(),
        name='basic_timing'
    ),
    # Get all rating plans
    re_path(
        r'^(?:v1/)?rating-plans(?:/)?$',
        api.RatingPlansAPIView.as_view(),
        name='basic_rating_plans'
    ),
    # Get a rating plan
    re_path(
        r'^(?:v1/)?rating-plans/(?P<rating_plan>[^/]+)(?:/)?$',
        api.RatingPlanAPIView.as_view(),
        name='basic_rating_plan'
    ),
    # Get all rating profiles
    re_path(
        r'^(?:v1/)?rating-profiles(?:/)?$',
        api.RatingProfilesAPIView.as_view(),
        name='basic_rating_profiles'
    ),
    # Get a rating profile
    re_path(
        r'^(?:v1/)?rating-profiles/(?P<rating_profile>[^/]+)(?:/)?$',
        api.RatingProfileAPIView.as_view(),
        name='basic_rating_profile'
    ),
    # Delete a rating profile
    re_path(
        r'^(?:v1/)?rating-profiles/(?P<rating_profile>[^/]+)/remove(?:/)?$',
        api.RatingProfileDeleteAPIView.as_view(),
        name='basic_delete_rating_profile'
    ),
    ############################################
    #         Reload plans related URLs        #
    ############################################
    # Reload from store db to data db
    re_path(
        r'^(?:v1/)?reload-plans(?:/)?$',
        api.ReloadPlansAPIView.as_view(),
        name='basic_reload_plans'
    ),

    ############################################
    #              API for testing             #
    ############################################
    # Reload from store db to data db
    re_path(
        r'^(?:v1/)?testing(?:/)?$',
        api.TestAPIView.as_view(),
        name='test'
    ),



]
