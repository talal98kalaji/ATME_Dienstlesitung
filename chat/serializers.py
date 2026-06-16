from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Participant, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'content', 'image', 'created_at']
        read_only_fields = ['conversation', 'sender', 'created_at']

    def get_sender_name(self, obj):
        if not obj.sender:
            return None
        full_name = f"{obj.sender.first_name} {obj.sender.last_name}".strip()
        return full_name or obj.sender.username

    def validate(self, data):
        # A message must carry text or an image (for documenting situations).
        if not data.get('content') and not data.get('image'):
            raise serializers.ValidationError("A message must contain text or an image.")
        return data


class ParticipantSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ['id', 'user', 'username', 'full_name', 'role', 'joined_at']

    def get_full_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.username


class ConversationSerializer(serializers.ModelSerializer):
    participants_info = ParticipantSerializer(source='memberships', many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_type', 'name', 'created_by',
            'participants_info', 'last_message', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if not msg:
            return None
        return {
            'id': msg.id,
            'content': msg.content,
            'has_image': bool(msg.image),
            'sender': msg.sender_id,
            'created_at': msg.created_at,
        }
