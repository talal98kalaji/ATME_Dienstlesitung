from django.urls import reverse

from rest_framework import serializers

from .models import Conversation, Participant, Message
from .permissions import LEVELS, visible_messages


class MemberInputSerializer(serializers.Serializer):
    user = serializers.IntegerField(min_value=1)

    can_send_messages = serializers.BooleanField(
        default=False
    )

    can_add_members = serializers.BooleanField(
        default=False
    )


class AddMembersSerializer(serializers.Serializer):
    members = MemberInputSerializer(
        many=True,
        allow_empty=False,
        max_length=100,
    )

    def validate_members(self, members):
        ids = [member["user"] for member in members]

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Duplicate user IDs."
            )

        return members


class GroupCreateSerializer(AddMembersSerializer):
    name = serializers.CharField(max_length=255)

    allowed_levels = serializers.ListField(
        child=serializers.ChoiceField(choices=LEVELS),
        allow_empty=False,
    )

    send_policy = serializers.ChoiceField(
        choices=Conversation.SEND_POLICY_CHOICES,
        default=Conversation.ADMIN_ONLY,
    )

    members = MemberInputSerializer(
        many=True,
        required=False,
        default=list,
        max_length=100,
    )


class GroupSettingsSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=255,
        required=False,
    )

    allowed_levels = serializers.ListField(
        child=serializers.ChoiceField(choices=LEVELS),
        allow_empty=False,
        required=False,
    )

    send_policy = serializers.ChoiceField(
        choices=Conversation.SEND_POLICY_CHOICES,
        required=False,
    )


class MemberPermissionsSerializer(serializers.Serializer):
    can_send_messages = serializers.BooleanField(
        required=False
    )

    can_add_members = serializers.BooleanField(
        required=False
    )

    def validate(self, data):
        if not data:
            raise serializers.ValidationError(
                "Provide at least one permission."
            )

        return data


class DirectInputSerializer(serializers.Serializer):
    user = serializers.IntegerField(min_value=1)


class PinInputSerializer(serializers.Serializer):
    is_pinned = serializers.BooleanField()


class MessageInputSerializer(serializers.Serializer):
    content = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        max_length=4000,
    )

    image = serializers.ImageField(required=False)

    def validate_image(self, image):
        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Maximum image size is 5 MB."
            )

        return image

    def validate(self, data):
        if (
            not data.get("content", "").strip()
            and not data.get("image")
        ):
            raise serializers.ValidationError(
                "Provide text or an image."
            )

        return data


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Message

        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "content",
            "image",
            "is_pinned",
            "pinned_by",
            "pinned_at",
            "created_at",
        ]

        read_only_fields = fields

    def get_sender_name(self, obj):
        if obj.sender is None:
            return None

        return (
            obj.sender.get_full_name()
            or obj.sender.username
        )

    def get_image(self, obj):
        if not obj.image:
            return None

        return reverse(
            "chat-message-image",
            kwargs={
                "pk": obj.conversation_id,
                "message_id": obj.pk,
            },
        )


class ParticipantSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = Participant

        fields = [
            "id",
            "user",
            "username",
            "role",
            "can_send_messages",
            "can_add_members",
            "added_by",
            "joined_at",
        ]

        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    participants_info = ParticipantSerializer(
        source="memberships",
        many=True,
        read_only=True,
    )

    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation

        fields = [
            "id",
            "conversation_type",
            "name",
            "created_by",
            "managed_by",
            "send_policy",
            "allowed_levels",
            "participants_info",
            "last_message",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_last_message(self, obj):
        user = self.context["request"].user

        message = visible_messages(user, obj).last()

        if message is None:
            return None

        return MessageSerializer(message).data