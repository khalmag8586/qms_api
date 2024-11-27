# your_app/routing.py
from django.urls import re_path
from apps.ticket.consumers import TicketConsumer

websocket_urlpatterns = [
    re_path(r"wss/tickets/(?P<counter_id>[a-zA-Z0-9\-]+)/$", TicketConsumer.as_asgi()),
]
