# --------------------------------------------------------------------------
# A proxy for CGRateS APIerS method names. Do not use method names directly.
# https://godoc.org/github.com/cgrates/cgrates/apier/v1
# https://godoc.org/github.com/cgrates/cgrates/apier/v2
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - cgrates_methods.py
# Created at 2020-8-29,  16:24:6
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

class CGRatesMethods:

    @classmethod
    def get_active_sessions(cls):
        return "SessionSv1.GetActiveSessions"

    @classmethod
    def force_disconnect(cls):
        return "SessionSv1.ForceDisconnect"

    @classmethod
    def get_account(cls):
        return "APIerSv2.GetAccount"

    @classmethod
    def get_accounts(cls):
        return "APIerSv2.GetAccounts"

    @classmethod
    def set_account(cls):
        return "APIerSv2.SetAccount"

    @classmethod
    def remove_account(cls):
        return "APIerSv1.RemoveAccount"

    @classmethod
    def ping(cls):
        return "APIerSv1.Ping"

    @classmethod
    def get_actions_v1(cls):
        return "APIerSv1.GetActions"

    @classmethod
    def set_action_plan(cls):
        return "APIerSv1.SetActionPlan"

    @classmethod
    def remove_action_plan(cls):
        return "APIerSv1.RemoveActionPlan"

    @classmethod
    def get_actions_v2(cls):
        return "APIerSv2.GetActions"

    @classmethod
    def remove_actions_v2(cls):
        return "APIerSv2.RemoveActions"

    @classmethod
    def get_filter_ids(cls):
        return "APIerSv1.GetFilterIDs"

    @classmethod
    def get_filter(cls):
        return "APIerSv1.GetFilter"

    @classmethod
    def get_supplier_profile_ids(cls):
        return "APIerSv1.GetSupplierProfileIDs"

    @classmethod
    def get_supplier_profile(cls):
        return "APIerSv1.GetSupplierProfile"

    @classmethod
    def get_charger_profile_ids(cls):
        return "APIerSv1.GetChargerProfileIDs"

    @classmethod
    def get_charger_profile(cls):
        return "APIerSv1.GetChargerProfile"

    @classmethod
    def set_charger_profile(cls):
        return "APIerSv1.SetChargerProfile"

    @classmethod
    def set_tp_destination_rate(cls):
        return "APIerSv1.SetTPDestinationRate"

    @classmethod
    def set_tp_rate(cls):
        return "APIerSv1.SetTPRate"

    @classmethod
    def remove_tp_rate(cls):
        return "APIerSv1.RemoveTPRate"

    @classmethod
    def get_rate_ids(cls):
        return "APIerSv1.GetTPRateIds"

    @classmethod
    def get_rate(cls):
        return "APIerSv1.GetTPRate"

    @classmethod
    def get_destination_rate_ids(cls):
        return "APIerSv1.GetTPDestinationRateIds"

    @classmethod
    def get_destination_rate(cls):
        return "APIerSv1.GetTPDestinationRate"

    @classmethod
    def set_destination(cls):
        return "APIerSv1.SetTPDestination"

    @classmethod
    def remove_tp_destination(cls):
        return "APIerSv1.RemoveTPDestination"

    @classmethod
    def remove_tp_destination_rate(cls):
        return "APIerSv1.RemoveTPDestinationRate"

    @classmethod
    def remove_destination(cls):
        return "APIerSv1.RemoveDestination"

    @classmethod
    def get_timing_ids(cls):
        return "APIerSv1.GetTPTimingIds"

    @classmethod
    def get_timing(cls):
        return "APIerSv1.GetTPTiming"

    @classmethod
    def set_tp_timing(cls):
        return "APIerSv1.SetTPTiming"

    @classmethod
    def remove_tp_timing(cls):
        return "APIerSv1.RemoveTPTiming"

    @classmethod
    def get_rating_plan(cls):
        return "APIerSv1.GetTPRatingPlan"

    @classmethod
    def remove_rating_plan(cls):
        return "APIerSv1.RemoveTPRatingPlan"

    @classmethod
    def get_rating_plan_ids(cls):
        return "APIerSv1.GetTPRatingPlanIds"

    @classmethod
    def set_rating_plan(cls):
        return "APIerSv1.SetTPRatingPlan"

    @classmethod
    def set_rating_profile(cls):
        return "APIerSv1.SetTPRatingProfile"

    @classmethod
    def remove_rating_profile(cls):
        return "APIerSv1.RemoveTPRatingProfile"

    @classmethod
    def get_rating_profile(cls):
        return "APIerSv1.GetTPRatingProfilesByLoadID"

    @classmethod
    def get_rating_profile_ids(cls):
        return "APIerSv1.GetTPRatingProfileLoadIds"

    @classmethod
    def get_threshold_profile_ids(cls):
        return "APIerSv1.GetThresholdProfileIDs"

    @classmethod
    def get_threshold_profile(cls):
        return "APIerSv1.GetThresholdProfile"

    @classmethod
    def set_threshold_profile(cls):
        return "APIerSv1.SetThresholdProfile"

    @classmethod
    def remove_threshold_profile(cls):
        return "APIerSv1.RemoveThresholdProfile"

    @classmethod
    def set_filter(cls):
        return "APIerSv1.SetFilter"

    @classmethod
    def get_cdrs(cls):
        return "CDRsV2.GetCDRs"

    @classmethod
    def get_attribute_profile_ids(cls):
        return "APIerSv1.GetAttributeProfileIDs"

    @classmethod
    def remove_attribute_profile(cls):
        return "APIerSv1.RemoveAttributeProfile"

    @classmethod
    def get_destinations(cls):
        return "APIerSv2.GetDestinations"

    @classmethod
    def get_attribute_profile(cls):
        return "APIerSv2.GetAttributeProfile"

    @classmethod
    def get_cdrs_count(cls):
        return "APIerSv2.CountCDRs"

    @classmethod
    def set_tp_supplier_profile(cls):
        return "APIerSv1.SetTPSupplierProfile"

    @classmethod
    def execute_action(cls):
        return "APIerSv1.ExecuteAction"

    @classmethod
    def add_balance(cls):
        return "APIerSv1.AddBalance"

    @classmethod
    def set_balance(cls):
        return "APIerSv1.SetBalance"

    @classmethod
    def remove_balance(cls):
        return "APIerSv1.RemoveBalances"

    @classmethod
    def debit_balance(cls):
        return "APIerSv1.DebitBalance"

    @classmethod
    def set_attribute_profile(cls):
        return "APIerSv2.SetAttributeProfile"

    @classmethod
    def set_actions(cls):
        return "APIerSv2.SetActions"

    @classmethod
    def load_tariff_plan_from_database(cls):
        return "APIerSv1.LoadTariffPlanFromStorDb"
