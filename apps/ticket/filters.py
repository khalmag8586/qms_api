import django_filters
from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    # Define filters for the fields you want to filter/search
    number = django_filters.CharFilter(field_name="number", lookup_expr="icontains")
    created_at = django_filters.DateFromToRangeFilter(field_name="created_at")
    customer_name = django_filters.CharFilter(
        field_name="customer_name", lookup_expr="icontains"
    )
    mobile_number = django_filters.CharFilter(
        field_name="mobile_number", lookup_expr="icontains"
    )
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")

    class Meta:
        model = Ticket
        fields = [
            "number",
            "created_at",
            "customer_name",
            "mobile_number",
            "email",
            "status",
        ]
