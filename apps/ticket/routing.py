# your_app/routing.py
from django.urls import re_path
from apps.ticket.consumers import TicketConsumer,TicketInProgressConsumer

websocket_urlpatterns = [
    re_path(r"wss/tickets/ahead", TicketConsumer.as_asgi()),
    re_path(r"wss/tickets/in_progress/", TicketInProgressConsumer.as_asgi()),

]
