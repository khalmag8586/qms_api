# routing.py
from django.urls import re_path
from apps.invoice.consumers import InvoiceNotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/invoice/notifications/", InvoiceNotificationConsumer.as_asgi()),
]
