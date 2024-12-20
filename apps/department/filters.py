from django_filters import FilterSet, OrderingFilter
from apps.department.models import Department


class DepartmentFilter(FilterSet):
    ordering = OrderingFilter(
        fields=(
            ("name", "name"),  # Ascending order by name
            ("-name", "name_desc"),  # Descending order by name
            ("name_ar", "name_ar"),  # Ascending order by name_ar
            ("-name_ar", "name_ar_desc"),  # Descending order by name_ar
        ),
        field_labels={
            "name": "Name (ascending)",
            "name_desc": "Name (descending)",
            "name_ar": "Name (Arabic ascending)",
            "name_ar_desc": "Name (Arabic descending)",
        },
    )

    class Meta:
        model = Department
        fields = [
            "name",
            "name_ar",
        ]
