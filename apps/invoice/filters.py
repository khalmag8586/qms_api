import django_filters
from apps.invoice.models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")
    created_at = django_filters.DateFromToRangeFilter(field_name="created_at")
    created_at = django_filters.CharFilter(
        field_name="created_at", lookup_expr="icontains"
    )
    contact_name = django_filters.CharFilter(
        field_name="contact_name", lookup_expr="icontains"
    )
    contact_no = django_filters.CharFilter(
        field_name="contact_no", lookup_expr="icontains"
    )

    class Meta:
        model = Invoice
        fields = ["id", "created_at", "contact_name", "contact_no"]
