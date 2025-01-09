import json
from channels.generic.websocket import AsyncWebsocketConsumer


class InvoiceNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.group_name = "invoice_notifications"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Error during connection: {e}")  # Debugging
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception as e:
            print(f"Error during disconnection: {e}")  # Debugging

    async def invoice_created(self, event):
        try:
            message = event["message"]
            await self.send(
                text_data=json.dumps(
                    {
                        "id": message["id"],
                        "token_no": message["token_no"],
                        "contact_name": message["contact_name"],
                        "contact_no": message["contact_no"],
                        "is_paid": message["is_paid"],
                        "is_cancelled": message["is_cancelled"],
                        "created_at": message["created_at"],
                        "line_items": message.get("line_items", []),  # Include line items
                    }
                )
            )
        except KeyError as e:
            print(f"KeyError in invoice_created: {e}")  # Debugging
        except Exception as e:
            print(f"Error in invoice_created: {e}")  # Debugging