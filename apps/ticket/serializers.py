from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_name_ar = serializers.CharField(source="service.name_ar", read_only=True)
    service_symbol = serializers.CharField(source="service.symbol", read_only=True)
    served_by_name = serializers.CharField(source="served_by.name", read_only=True)
    redirect_to_number = serializers.CharField(
        source="redirect_to.number", read_only=True
    )
    counter_number = serializers.CharField(source="counter.number", read_only=True)
    called_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "number",
            "service",
            "service_name",
            "service_name_ar",
            "service_symbol",
            "customer_name",
            "customer_name_ar",
            "nationality",
            "mobile_number",
            "email",
            "created_at",
            "called_at",
            "status",
            "served_by",
            "served_by_name",
            "counter",
            "counter_number",
            "hold_reason",
            "redirect_to",
            "redirect_to_number",
            "customers_ahead",
            "avg_wait_time",
        ]
        read_only_fields = [
            "id",
            "number",
            "service_name",
            "service_name_ar",
            "service_symbol",
            "created_at",
            "called_at",
            "status",
            "served_by",
            "served_by_name",
            "counter_number",
            "hold_reason",
            "redirect_to",
            "redirect_to_name",
            "customers_ahead",
            "avg_wait_time",
        ]

    def get_called_at(self, obj):
        return obj.called_at.strftime("%Y-%m-%d %H:%M:%S") if obj.called_at else None

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")


class CallNextCustomerSerializer(serializers.Serializer):
    counter_id = serializers.UUIDField()


class TicketRedirectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "counter"]


class TicketDialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "number"]


class TicketStatusDialogSerializer(serializers.Serializer):
    value = serializers.CharField()
    display = serializers.CharField()
