from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Conversation
from .permissions import (
    IsChatUser,
    membership_for,
    require_member,
    visible_messages,
)
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    GroupCreateSerializer,
    GroupSettingsSerializer,
    AddMembersSerializer,
    MemberPermissionsSerializer,
    MessageInputSerializer,
    DirectInputSerializer,
    PinInputSerializer,
)
from . import services


def validated(serializer_class, data):
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def conversation_data(request, conversation):
    return ConversationSerializer(
        conversation,
        context={"request": request},
    ).data


def accessible_conversation(request, pk):
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
    )

    require_member(request.user, conversation)

    return conversation


@api_view(["GET"])
@permission_classes([IsChatUser])
def get_my_conversations(request):
    conversations = (
        Conversation.objects
        .filter(memberships__user=request.user)
        .distinct()
    )

    conversations = [
        item
        for item in conversations
        if membership_for(request.user, item)
    ]

    return Response(
        ConversationSerializer(
            conversations,
            many=True,
            context={"request": request},
        ).data
    )


@api_view(["POST"])
@permission_classes([IsChatUser])
def create_group(request):
    data = validated(
        GroupCreateSerializer,
        request.data,
    )

    conversation = services.create_group(
        request.user.pk,
        data,
    )

    return Response(
        conversation_data(request, conversation),
        status=201,
    )


@api_view(["POST"])
@permission_classes([IsChatUser])
def create_direct(request):
    data = validated(
        DirectInputSerializer,
        request.data,
    )

    conversation, created = services.create_direct(
        request.user.pk,
        data["user"],
    )

    return Response(
        conversation_data(request, conversation),
        status=201 if created else 200,
    )


@api_view(["GET"])
@permission_classes([IsChatUser])
def get_conversation_detail(request, pk):
    conversation = accessible_conversation(
        request,
        pk,
    )

    return Response(
        conversation_data(request, conversation)
    )


@api_view(["PATCH"])
@permission_classes([IsChatUser])
def group_settings(request, pk):
    data = validated(
        GroupSettingsSerializer,
        request.data,
    )

    conversation = services.change_settings(
        request.user.pk,
        pk,
        data,
    )

    return Response(
        conversation_data(request, conversation)
    )


@api_view(["POST"])
@permission_classes([IsChatUser])
def add_participants(request, pk):
    data = validated(
        AddMembersSerializer,
        request.data,
    )

    added = services.add_members(
        request.user.pk,
        pk,
        data,
    )

    return Response({"added": added})


@api_view(["PATCH", "DELETE"])
@permission_classes([IsChatUser])
def member_detail(request, pk, user_id):
    if request.method == "DELETE":
        services.change_member(
            request.user.pk,
            pk,
            user_id,
            remove=True,
        )

        return Response(status=204)

    data = validated(
        MemberPermissionsSerializer,
        request.data,
    )

    services.change_member(
        request.user.pk,
        pk,
        user_id,
        data=data,
    )

    return Response({
        "message": "Permissions updated."
    })


@api_view(["GET"])
@permission_classes([IsChatUser])
def get_messages(request, pk):
    conversation = accessible_conversation(
        request,
        pk,
    )

    queryset = visible_messages(
        request.user,
        conversation,
    ).order_by("-created_at", "-id")

    paginator = PageNumberPagination()
    paginator.page_size = 30
    paginator.max_page_size = 100
    paginator.page_size_query_param = "page_size"

    page = paginator.paginate_queryset(
        queryset,
        request,
    )

    return paginator.get_paginated_response(
        MessageSerializer(page, many=True).data
    )


@api_view(["GET"])
@permission_classes([IsChatUser])
def get_pinned_messages(request, pk):
    conversation = accessible_conversation(
        request,
        pk,
    )

    messages = visible_messages(
        request.user,
        conversation,
    ).filter(is_pinned=True)

    return Response(
        MessageSerializer(messages, many=True).data
    )


@api_view(["POST"])
@permission_classes([IsChatUser])
def send_message(request, pk):
    data = validated(
        MessageInputSerializer,
        request.data,
    )

    message = services.create_message(
        request.user.pk,
        pk,
        data,
    )

    return Response(
        MessageSerializer(message).data,
        status=201,
    )


@api_view(["PATCH"])
@permission_classes([IsChatUser])
def message_pin(request, pk, message_id):
    data = validated(
        PinInputSerializer,
        request.data,
    )

    message = services.pin_message(
        request.user.pk,
        pk,
        message_id,
        data["is_pinned"],
    )

    return Response(
        MessageSerializer(message).data
    )


@api_view(["GET"])
@permission_classes([IsChatUser])
def message_image(request, pk, message_id):
    conversation = accessible_conversation(
        request,
        pk,
    )

    message = get_object_or_404(
        visible_messages(
            request.user,
            conversation,
        ),
        pk=message_id,
    )

    if not message.image:
        raise Http404

    try:
        image = message.image.open("rb")
    except FileNotFoundError:
        raise Http404

    response = FileResponse(
        image,
        as_attachment=True,
        filename=Path(message.image.name).name,
    )

    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"

    return response