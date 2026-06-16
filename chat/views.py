from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Conversation, Participant, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import is_manager

User = get_user_model()


def _is_participant(user, conversation):
    return conversation.memberships.filter(user=user).exists()


def _broadcast(conversation_id, message_data):
    """Push a message to all WebSocket clients connected to this conversation."""
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation_id}",
            {"type": "chat.message", "message": message_data},
        )


# ==========================================
# Conversations
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_conversations(request):
    """List conversations the current user takes part in."""
    queryset = Conversation.objects.filter(memberships__user=request.user).distinct()
    serializer = ConversationSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_group(request):
    """Managers create group conversations and add members."""
    if not is_manager(request.user):
        return Response({"error": "Only managers can create groups."}, status=status.HTTP_403_FORBIDDEN)

    name = request.data.get('name')
    if not name:
        return Response({"error": "Group name is required."}, status=status.HTTP_400_BAD_REQUEST)

    member_ids = request.data.get('members', []) or []
    conversation = Conversation.objects.create(
        conversation_type=Conversation.GROUP, name=name, created_by=request.user
    )
    # creator is the group admin
    Participant.objects.create(conversation=conversation, user=request.user, role=Participant.ADMIN)
    # add the requested members
    valid_users = User.objects.filter(id__in=member_ids).exclude(id=request.user.id)
    for member in valid_users:
        Participant.objects.get_or_create(conversation=conversation, user=member)

    serializer = ConversationSerializer(conversation)
    return Response({"message": "Group created", "data": serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_direct(request):
    """Start a direct conversation. Allowed only between a manager and an employee."""
    target_id = request.data.get('user')
    if not target_id:
        return Response({"error": "Target 'user' id is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        target = User.objects.get(pk=target_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if target.id == request.user.id:
        return Response({"error": "You cannot start a chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)

    # Core rule: a direct chat must involve a manager. Employees talk to each other in groups only.
    if not (is_manager(request.user) or is_manager(target)):
        return Response(
            {"error": "Direct chats are only allowed between a manager and an employee. Employees must use groups."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Return the existing direct conversation if one already exists.
    existing = (
        Conversation.objects.filter(conversation_type=Conversation.DIRECT, memberships__user=request.user)
        .filter(memberships__user=target)
        .first()
    )
    if existing:
        return Response(
            {"message": "Conversation already exists", "data": ConversationSerializer(existing).data},
            status=status.HTTP_200_OK,
        )

    conversation = Conversation.objects.create(conversation_type=Conversation.DIRECT, created_by=request.user)
    Participant.objects.create(conversation=conversation, user=request.user)
    Participant.objects.create(conversation=conversation, user=target)

    serializer = ConversationSerializer(conversation)
    return Response({"message": "Direct conversation created", "data": serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_detail(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    if not _is_participant(request.user, conversation):
        return Response({"error": "You are not a participant of this conversation."}, status=status.HTTP_403_FORBIDDEN)
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_participants(request, pk):
    """Managers add members to a group."""
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    if conversation.conversation_type != Conversation.GROUP:
        return Response({"error": "Members can only be added to groups."}, status=status.HTTP_400_BAD_REQUEST)
    if not is_manager(request.user):
        return Response({"error": "Only managers can manage group members."}, status=status.HTTP_403_FORBIDDEN)

    member_ids = request.data.get('members', []) or []
    valid_users = User.objects.filter(id__in=member_ids)
    added = []
    for member in valid_users:
        _, created = Participant.objects.get_or_create(conversation=conversation, user=member)
        if created:
            added.append(member.username)
    return Response({"message": "Members added", "added": added}, status=status.HTTP_200_OK)


# ==========================================
# Messages
# ==========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    if not _is_participant(request.user, conversation):
        return Response({"error": "You are not a participant of this conversation."}, status=status.HTTP_403_FORBIDDEN)

    queryset = conversation.messages.select_related('sender').all()
    paginator = PageNumberPagination()
    paginator.page_size = 30
    paginator.page_size_query_param = 'page_size'
    page = paginator.paginate_queryset(queryset, request)
    serializer = MessageSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    if not _is_participant(request.user, conversation):
        return Response({"error": "You are not a participant of this conversation."}, status=status.HTTP_403_FORBIDDEN)

    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(sender=request.user, conversation=conversation)
        conversation.save()  # bump updated_at so the conversation rises to the top
        _broadcast(conversation.id, serializer.data)  # live push to WebSocket clients
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
