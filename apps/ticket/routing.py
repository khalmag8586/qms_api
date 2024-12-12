# your_app/routing.py
from django.urls import re_path
from apps.ticket.consumers import TicketConsumer,TicketInProgressConsumer
# from apps.ticket.consumers import TicketConsumer

websocket_urlpatterns = [

    # re_path(r"^tickets/ahead/$", TicketConsumer.as_asgi()),  # No need for 'wss' in the route
    re_path(r'^ws/tickets/(?P<ticket_id>[a-f0-9\-]+)/$', TicketConsumer.as_asgi()),
    re_path(r'ws/tickets/in_progress/$', TicketInProgressConsumer.as_asgi()),

]
