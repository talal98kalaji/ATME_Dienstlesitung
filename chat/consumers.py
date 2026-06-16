import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Conversation, Message, Participant
from .serializers import MessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    """Real-time chat for a single conversation.

    Connect with:  ws://host/ws/chat/<conversation_id>/?token=<access_token>
    Send:          {"content": "hello"}
    """

    async def connect(self):
        self.user = self.scope.get("user")
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chat_{self.conversation_id}"

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # unauthenticated
            return

        if not await self._is_participant():
            await self.close(code=4003)  # not a participant
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return
        content = (data.get("content") or "").strip()
        if not content:
            return
        message = await self._save_message(content)
        payload = await self._serialize(message)
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "message": payload}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"], default=str))

    # ---- database helpers ----
    @database_sync_to_async
    def _is_participant(self):
        return Participant.objects.filter(
            conversation_id=self.conversation_id, user=self.user
        ).exists()

    @database_sync_to_async
    def _save_message(self, content):
        message = Message.objects.create(
            conversation_id=self.conversation_id, sender=self.user, content=content
        )
        Conversation.objects.filter(id=self.conversation_id).update(updated_at=message.created_at)
        return message

    @database_sync_to_async
    def _serialize(self, message):
        return MessageSerializer(message).data
