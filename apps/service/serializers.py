from rest_framework import serializers

from apps.service.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    created_by_user_name = serializers.CharField(
        source="created_by.name", read_only=True
    )
    created_by_user_name_ar = serializers.CharField(
        source="created_by.name_ar", read_only=True
    )
    updated_at = serializers.SerializerMethodField()
    updated_by_user_name = serializers.CharField(
        source="updated_by.name", read_only=True
    )
    updated_by_user_name_ar = serializers.CharField(
        source="updated_by.name_ar", read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "name_ar",
            "service_symbol",
            "description",
            "cost",
            "vat",
            "final_cost",
            "created_at",
            "created_by",
            "created_by_user_name",
            "created_by_user_name_ar",
            "updated_at",
            "updated_by",
            "updated_by_user_name",
            "updated_by_user_name_ar",
            "is_active",
        ]
        read_only_fields = ["id", "final_cost"]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    def get_updated_at(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d")


class ServiceActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["is_active"]


class ServiceDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["is_deleted"]


# dialog serializers
class ServiceDialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "name_ar", "service_symbol"]


class AvailableSymbolsSerializer(serializers.Serializer):
    available_letters = serializers.ListField(child=serializers.CharField())
