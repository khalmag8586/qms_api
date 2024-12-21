from rest_framework import serializers

from apps.department.models import Department


class DepartmentSerializer(serializers.ModelSerializer):
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
        model = Department
        fields = [
            "id",
            "name",
            "name_ar",
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


class DepartmentActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["is_active"]


class DepartmentDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["is_deleted"]


class DepartmentDialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "name_ar"]
