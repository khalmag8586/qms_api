
# your_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

# class TicketConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.group_name = "global_notifications"

#         # Join the global group
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave the global group
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def ticket_update(self, event):
#         # Send the ticket update to the WebSocket
#         await self.send(text_data=json.dumps(event["message"]))

class TicketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "global_notifications"

        # Join the global group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the global group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ticket_ahead_notification(self, event):
        # Send the ticket ahead notification to the WebSocket
        await self.send(text_data=json.dumps(event["data"]))


# class TicketInProgressConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Create a unique group name to group all clients interested in ticket updates
#         self.group_name = "tickets_in_progress"

#         # Join the group
#         await self.channel_layer.group_add(self.group_name, self.channel_name)

#         # Accept the WebSocket connection
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave the group when the WebSocket connection is closed
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def receive(self, text_data):
#         # Handle messages from the client if needed
#         pass

#     async def send_ticket_update(self, event):
#         # Send ticket update to WebSocket
#         await self.send(text_data=json.dumps(event["message"]))
class TicketInProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "tickets_in_progress"

        # Join the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_ticket_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))
