from django.urls import path
from apps.ticket.views import (
    TicketCreateView,
    TicketListView,
    TicketRetrieveView,
    CallNextCustomerView,
    TicketUpdateView,
    TicketInCounter,
    TicketRedirectToAnotherCounter,
    TicketDeleteView,
)

app_name = "ticket"

urlpatterns = [
    path("ticket_create/", TicketCreateView.as_view(), name="ticket-create"),
    path("ticket_list/", TicketListView.as_view(), name="ticket-list"),
    path("ticket_retrieve/", TicketRetrieveView.as_view(), name="ticket-retrieve"),
    path(
        "call_next_customer/", CallNextCustomerView.as_view(), name="call_next_customer"
    ),
    path(
        "ticket_redirect/",
        TicketRedirectToAnotherCounter.as_view(),
        name="ticket-redirect",
    ),
    path("ticket_update/", TicketUpdateView.as_view(), name="ticket-update"),
    path("ticket_in_counter/", TicketInCounter.as_view(), name="ticket-in-counter"),
    path("ticket_delete/", TicketDeleteView.as_view(), name="ticket-delete"),
]
