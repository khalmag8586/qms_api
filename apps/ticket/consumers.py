# your_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from apps.ticket.models import in_progress_tickets


class TicketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the ticket UUID from the WebSocket URL
        self.ticket_id = self.scope["url_route"]["kwargs"]["ticket_id"]
        self.group_name = f"ticket_{self.ticket_id}"

        # Add the WebSocket connection to the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Remove the WebSocket connection from the group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ticket_notification(self, event):
        # Send the notification to the client
        await self.send(text_data=json.dumps(event["data"]))

class TicketInProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "tickets_in_progress"

        # Join the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send all tickets in "in_progress" status to the client on connection
        await self.send_initial_tickets()

        print("Client connected to TicketInProgressConsumer")

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Client disconnected from TicketInProgressConsumer")

    async def send_ticket_update(self, event):
        """Handles incoming events from the group send."""
        # Send ticket update to WebSocket
        print("Received ticket update:", event)
        await self.send(text_data=json.dumps({"type": "update_tickets", "tickets": event["message"]}))

    async def send_initial_tickets(self):
        """Send all tickets in the 'in_progress' status when a client connects."""
        # Prepare ticket data from the in-progress tickets list
        ticket_data = in_progress_tickets.get("tickets_in_progress", [])

        # Send the ticket data to the WebSocket client
        await self.send(
            text_data=json.dumps(
                {
                    "type": "initial_tickets",
                    "tickets": ticket_data,
                }
            )
        )
