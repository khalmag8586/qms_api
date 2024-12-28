import django_filters
from django_filters import FilterSet

from apps.PRO.models import PRO


class PROFilter(FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    name_ar = django_filters.CharFilter(field_name="name_ar", lookup_expr="icontains")
    mobile_number = django_filters.CharFilter(
        field_name="mobile_number", lookup_expr="icontains"
    )
    company_name = django_filters.CharFilter(
        field_name="company_name", lookup_expr="icontains"
    )
    company_number = django_filters.CharFilter(
        field_name="company_number", lookup_expr="icontains"
    )
    created_at = django_filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = PRO
        fields = ["name", "name_ar", "company_name", "company_number", "created_at"]
