# your_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.ticket.models import Ticket

class TicketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.counter_id = self.scope["url_route"]["kwargs"]["counter_id"]
        self.group_name = f"counter_{self.counter_id}"

        # Join the counter group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the counter group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ticket_update(self, event):
        # Send the ticket update to the WebSocket
        await self.send(text_data=json.dumps(event["message"]))
