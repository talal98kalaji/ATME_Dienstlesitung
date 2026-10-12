import asyncio
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer,
)

from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import APIException

from .models import Conversation
from .permissions import require_member, visible_messages
from .serializers import (
    MessageInputSerializer,
    MessageSerializer,
)
from . import services


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.expiry_task = None
        self.joined_group = False

        user = self.scope.get("user")
        self.expires_at = self.scope.get(
            "jwt_expires_at",
            0,
        )

        if (
            not user
            or not user.is_authenticated
            or self.expires_at <= time.time()
        ):
            await self.close(code=4001)
            return

        self.user_id = user.pk

        self.conversation_id = int(
            self.scope["url_route"]["kwargs"]["conversation_id"]
        )

        self.group_name = f"chat_{self.conversation_id}"

        if not await self.access_allowed():
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        self.joined_group = True

        await self.accept()

        self.expiry_task = asyncio.create_task(
            self.expire_connection()
        )

    async def expire_connection(self):
        await asyncio.sleep(
            max(
                0,
                self.expires_at - time.time(),
            )
        )

        await self.close(code=4001)

    async def disconnect(self, close_code):
        if self.expiry_task:
            self.expiry_task.cancel()

        if self.joined_group:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(
        self,
        text_data=None,
        bytes_data=None,
        **kwargs,
    ):
        if text_data is None or len(text_data) > 20000:
            await self.send_json({
                "type": "error",
                "detail": "Send a small JSON text message.",
            })
            return

        try:
            data = await self.decode_json(text_data)
        except ValueError:
            await self.send_json({
                "type": "error",
                "detail": "Invalid JSON.",
            })
            return

        await self.receive_json(data)

    async def receive_json(self, content, **kwargs):
        if (
            self.expires_at <= time.time()
            or not await self.access_allowed()
        ):
            await self.close(code=4003)
            return

        if (
            not isinstance(content, dict)
            or set(content) != {"content"}
        ):
            await self.send_json({
                "type": "error",
                "detail": 'Use {"content": "text"}.',
            })
            return

        try:
            await self.save_message(content)

        except (APIException, Http404) as exc:
            await self.send_json({
                "type": "error",
                "detail": str(exc),
            })

    async def chat_event(self, event):
        if self.expires_at <= time.time():
            await self.close(code=4001)
            return

        try:
            payload = await self.event_payload(
                event.get("message_id")
            )

        except (APIException, Http404):
            await self.close(code=4003)
            return

        if payload is not None:
            await self.send_json(payload)

    @database_sync_to_async
    def access_allowed(self):
        try:
            actor = services.fresh_user(self.user_id)

            conversation = Conversation.objects.get(
                pk=self.conversation_id
            )

            require_member(actor, conversation)

            return True

        except (
            APIException,
            Conversation.DoesNotExist,
        ):
            return False

    @database_sync_to_async
    def save_message(self, data):
        serializer = MessageInputSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        services.create_message(
            self.user_id,
            self.conversation_id,
            serializer.validated_data,
        )

    @database_sync_to_async
    def event_payload(self, message_id):
        actor = services.fresh_user(self.user_id)

        conversation = get_object_or_404(
            Conversation,
            pk=self.conversation_id,
        )

        require_member(actor, conversation)

        if message_id is None:
            return {
                "type": "conversation_updated"
            }

        message = (
            visible_messages(actor, conversation)
            .filter(pk=message_id)
            .first()
        )

        if message is None:
            return None

        return {
            "type": "message",
            "data": MessageSerializer(message).data,
        }