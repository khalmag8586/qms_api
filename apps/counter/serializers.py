from rest_framework import serializers
from apps.counter.models import Counter


class CounterSerializer(serializers.ModelSerializer):
    # created at conf
    created_at = serializers.SerializerMethodField()
    created_by_user_name = serializers.CharField(
        source="created_by.name", read_only=True
    )
    created_by_user_name_ar = serializers.CharField(
        source="created_by.name_ar", read_only=True
    )
    # updated at conf
    updated_at = serializers.SerializerMethodField()
    updated_by_user_name = serializers.CharField(
        source="updated_by.name", read_only=True
    )
    updated_by_user_name_ar = serializers.CharField(
        source="updated_by.name_ar", read_only=True
    )
    # employee conf
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    employee_name_ar = serializers.CharField(source="employee.name_ar", read_only=True)
    # service conf
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_name_ar = serializers.CharField(source="service.name_ar", read_only=True)

    class Meta:
        model = Counter
        fields = [
            "id",
            "number",
            "created_at",
            "created_by",
            "created_by_user_name",
            "created_by_user_name_ar",
            "updated_at",
            "updated_by",
            "updated_by",
            "updated_by_user_name",
            "updated_by_user_name_ar",
            "service",
            "service_name",
            "service_name_ar",
            "employee",
            "employee_name",
            "employee_name_ar",
            "is_active",
        ]
        read_only_fields = ["id"]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    def get_updated_at(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d")


class CounterActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counter
        fields = ["is_active"]


class CounterDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counter
        fields = ["is_deleted"]


class CounterDialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counter
        fields = ["id", "number"]
