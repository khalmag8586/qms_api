from rest_framework import serializers
from apps.counter.models import Counter
from apps.department.models import Department


class SimpleDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "name_ar"]


class CounterDisplaySerializer(serializers.ModelSerializer):
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

    departments = SimpleDepartmentSerializer(
        many=True,  read_only=True
    )

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
            "updated_by_user_name",
            "updated_by_user_name_ar",
            "departments",
            "employee",
            "employee_name",
            "employee_name_ar",
            "is_active",
        ]
        read_only_fields = ["id"]

    # def update(self, instance, validated_data):
    #     # Handle departments update
    #     departments_data = validated_data.pop("departments", None)
    #     if departments_data is not None:
    #         instance.departments.set(departments_data)  # Update M2M relationship

    #     # Update other fields
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)

    #     instance.save()
    #     return instance

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    def get_updated_at(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d")


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
    departments = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), many=True, write_only=True
    )


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
            "updated_by_user_name",
            "updated_by_user_name_ar",
            "departments",
            "employee",
            "employee_name",
            "employee_name_ar",
            "is_active",
        ]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        # Handle departments update
        departments_data = validated_data.pop("departments", None)
        if departments_data is not None:
            instance.departments.set(departments_data)  # Update M2M relationship

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

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
