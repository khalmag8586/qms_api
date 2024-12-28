from rest_framework import serializers

from apps.PRO.models import PRO


class PROSerializer(serializers.ModelSerializer):
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
        model = PRO
        fields = [
            "id",
            "name",
            "name_ar",
            "mobile_number",
            "company_name",
            "company_number",
            "company_tax_number",
            "remarks",
            "commission_percentage",
            "is_active",
            "created_at",
            "created_by",
            "created_by_user_name",
            "created_by_user_name_ar",
            "updated_at",
            "updated_by",
            "updated_by_user_name",
            "updated_by_user_name_ar",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "is_active",
        ]

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    def get_updated_at(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d")


class PROActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PRO
        fields = ["is_active"]


class PRODeletedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PRO
        fields = ["is_deleted"]


class PRODialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PRO
        fields = ["id", "name", "name_ar"]
