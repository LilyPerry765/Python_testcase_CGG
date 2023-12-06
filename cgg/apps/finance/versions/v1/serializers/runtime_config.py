from rest_framework import serializers


class RuntimeConfigsSerializer(serializers.Serializer):
    discount_percent = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
    )
    discount_value = serializers.IntegerField(
        required=False,
        min_value=0,
    )
    issue_hour = serializers.IntegerField(
        required=False,
        min_value=0,
    )
    due_date = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=12,
    )
    deallocation_due = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    black_list_in_days = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    payment_cool_down = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=59,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

