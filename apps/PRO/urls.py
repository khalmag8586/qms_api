from django.urls import path

from apps.PRO.views import (
    PROCreateView,
    PROListView,
    DeletedPROListView,
    PRORetrieveView,
    ActivePROListView,
    PROChangeActiveView,
    PROUpdateView,
    PRODeleteTemporaryView,
    PRORestoreView,
    PRODeleteView,PRODialogView,
)

app_name = "PRO"

urlpatterns = [
    path("pro_create/", PROCreateView.as_view(), name="PRO create"),
    path("pro_list/", PROListView.as_view(), name="PRO list"),
    path("deleted_pro_list/", DeletedPROListView.as_view(), name=" deleted PRO list"),
    path("pro_retrieve/", PRORetrieveView.as_view(), name="pro retrieve"),
    path("active_pro_list/", ActivePROListView.as_view(), name="active pro list"),
    path("Change_pro_status/", PROChangeActiveView.as_view(), name="pro change active"),
    path("pro_update/", PROUpdateView.as_view(), name="pro update"),
    path(
        "pro_delete_temporary/",
        PRODeleteTemporaryView.as_view(),
        name="pro delete temporary",
    ),
    path("pro_restore/", PRORestoreView.as_view(), name="pro restore"),
    path("pro_delete/", PRODeleteView.as_view(), name="pro delete"),
    path("pro_dialog/", PRODialogView.as_view(), name="pro dialog"),
]
