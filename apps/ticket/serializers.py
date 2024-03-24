from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_name_ar = serializers.CharField(source="service.name_ar", read_only=True)
    service_symbol = serializers.CharField(source="service.symbol", read_only=True)
    served_by_name = serializers.CharField(source="served_by.name", read_only=True)
    counter_number = serializers.CharField(source="counter.number", read_only=True)

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
            "customers_ahead",
            "avg_wait_time",
        ]


class CallNextCustomerSerializer(serializers.Serializer):
    counter_id = serializers.UUIDField()

class TicketRedirectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Ticket
        fields=["id","counter"]