from django.urls import path
from apps.department.views import (
    DepartmentCreateView,
    DepartmentListView,
    DeletedDepartmentListView,
    DepartmentRetrieveView,
    DepartmentChangeActiveView,
    DepartmentDeleteTemporaryView,
    DepartmentRestoreView,
    DepartmentDeleteView,
)

app_name = "department"
urlpatterns = [
    path(
        "department_create/", DepartmentCreateView.as_view(), name="create department"
    ),
    path("department_list/", DepartmentListView.as_view(), name="department list"),
    path(
        "deleted_department_list/",
        DeletedDepartmentListView.as_view(),
        name="deleted department list",
    ),
    path(
        "department_retrieve/",
        DepartmentRetrieveView.as_view(),
        name="department retrieve",
    ),
    path(
        "department_change_status/",
        DepartmentChangeActiveView.as_view(),
        name="department_change_status",
    ),
    path(
        "department_temp_delete/",
        DepartmentDeleteTemporaryView.as_view(),
        name="department_temp_delete",
    ),
    path(
        "department_restore/",
        DepartmentRestoreView.as_view(),
        name="department_restore",
    ),
    path(
        "department_delete/", DepartmentDeleteView.as_view(), name="department_delete"
    ),
]
