from django.urls import path
from apps.counter.views import (
    CounterCreateView,
    CounterListView,
    DeletedCounterListView,
    CounterRetrieveView,
    ActiveCounterListView,
    CounterChangeActiveView,
    CounterUpdateView,
    CounterDeleteTemporaryView,
    CounterRestoreView,
    CounterDeleteView,
    CounterDialogView,
    CounterTypeDialogView,
)

app_name = "counter"

urlpatterns = [
    path("counter_create/", CounterCreateView.as_view(), name="counter-create"),
    path("counter_list/", CounterListView.as_view(), name="counter-list"),
    path(
        "counter_deleted_list/",
        DeletedCounterListView.as_view(),
        name="deleted-counter-list",
    ),
    path("counter_retrieve/", CounterRetrieveView.as_view(), name="counter-retrieve"),
    path(
        "counter_active_list/", ActiveCounterListView.as_view(), name="counter-active"
    ),
    path(
        "change_counter_status/",
        CounterChangeActiveView.as_view(),
        name="change_counter_status",
    ),
    path("counter_update/", CounterUpdateView.as_view(), name="counter-update"),
    path(
        "counter_temp_delete/",
        CounterDeleteTemporaryView.as_view(),
        name="counter_temp_delete",
    ),
    path("counter_restore/", CounterRestoreView.as_view(), name="counter_restore"),
    path("counter_delete/", CounterDeleteView.as_view(), name="counter-delete"),
    path("counter_dialog/", CounterDialogView.as_view(), name="counter_dialog"),
    path("counter_types_dialog/", CounterTypeDialogView.as_view(), name="counter_types_dialog"),
]
