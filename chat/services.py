from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import (PermissionDenied, ValidationError,)
from .models import Conversation, Participant
from .permissions import (
    can_create_group,
    can_add,
    can_send,
    is_manager,
    require_group_manager,
    validate_levels,
    validate_target,
    visible_messages,
)


User = get_user_model()


def fresh_user(user_id):
    user = User.objects.filter(
        pk=user_id,
        is_active=True,
    ).first()

    if user is None:
        raise PermissionDenied("This account is unavailable.")
    return user


def locked_conversation(pk):
    conversation = get_object_or_404(
        Conversation.objects.select_for_update(),pk=pk,)

    if conversation.managed_by_id:
        conversation.managed_by = User.objects.filter(
            pk=conversation.managed_by_id).first()
            
    return conversation


def notify(conversation_id, message_id=None):
    def push():
        layer = get_channel_layer()

        if layer is not None:
            async_to_sync(layer.group_send)(
                f"chat_{conversation_id}",
                { "type": "chat.event", "message_id": message_id,},)
    transaction.on_commit(push, robust=True)


def add_members_to_group(actor, conversation, members):
    if not can_add(actor, conversation):
        raise PermissionDenied( "You cannot add members.")

    added = []

    for item in members:
        target = get_object_or_404( User, pk=item["user"],)

        flags = {
            "can_send_messages": item["can_send_messages"],
            "can_add_members": item["can_add_members"], }

        validate_target( actor, conversation, target, flags, )

        if conversation.memberships.filter(
            user=target).exists():
            raise ValidationError({
                "members": f"User {target.pk} is already a member." })

        Participant.objects.create(
            conversation=conversation, user=target, added_by=actor,  **flags, )

        added.append(target.pk)

    return added


@transaction.atomic
def create_group(user_id, data):
    actor = fresh_user(user_id)

    if not can_create_group(actor):
        raise PermissionDenied( "Only Superuser, Manager or Senior can create groups." )

    validate_levels(actor, data["allowed_levels"])

    conversation = Conversation.objects.create(
        conversation_type=Conversation.GROUP,
        created_by=actor, managed_by=actor, name=data["name"],
        allowed_levels=list( dict.fromkeys(data["allowed_levels"])),
        send_policy=data["send_policy"], )

    Participant.objects.create(
        conversation=conversation,
        user=actor,
        role=Participant.ADMIN,
        added_by=actor,
        can_send_messages=True,
        can_add_members=True,
    )

    add_members_to_group(
        actor,
        conversation,
        data["members"],
    )

    return conversation


@transaction.atomic
def create_direct(user_id, target_id):
    users = {
        user.pk: user
        for user in (
            User.objects
            .select_for_update()
            .filter(
                pk__in=[user_id, target_id],
                is_active=True,
            )
            .order_by("pk")
        )
    }

    actor = users.get(user_id)
    target = users.get(target_id)

    if actor is None or not is_manager(actor):
        raise PermissionDenied(
            "Only Superuser or Manager can start direct chats."
        )

    if target is None:
        raise ValidationError({
            "user": "Active user not found."
        })

    if actor.pk == target.pk:
        raise ValidationError({
            "user": "You cannot chat with yourself."
        })

    existing = (
        Conversation.objects
        .filter(
            conversation_type=Conversation.DIRECT,
            memberships__user=actor,
        )
        .filter(memberships__user=target)
        .first()
    )

    if existing:
        return existing, False

    conversation = Conversation.objects.create(
        conversation_type=Conversation.DIRECT,
        created_by=actor,
    )

    for user in (actor, target):
        Participant.objects.create(
            conversation=conversation,
            user=user,
            added_by=actor,
        )

    return conversation, True


@transaction.atomic
def add_members(user_id, pk, data):
    actor = fresh_user(user_id)
    conversation = locked_conversation(pk)

    added = add_members_to_group(
        actor,
        conversation,
        data["members"],
    )

    notify(pk)

    return added


@transaction.atomic
def change_settings(user_id, pk, data):
    actor = fresh_user(user_id)
    conversation = locked_conversation(pk)

    require_group_manager(actor, conversation)

    if "allowed_levels" in data:
        validate_levels(
            conversation.managed_by,
            data["allowed_levels"],
        )

        data["allowed_levels"] = list(
            dict.fromkeys(data["allowed_levels"])
        )

    for key, value in data.items():
        setattr(conversation, key, value)

    conversation.save()

    notify(pk)

    return conversation


@transaction.atomic
def change_member(
    user_id,
    pk,
    target_id,
    data=None,
    remove=False,
):
    actor = fresh_user(user_id)
    conversation = locked_conversation(pk)

    require_group_manager(actor, conversation)

    member = get_object_or_404(
        Participant.objects.select_related("user"),
        conversation=conversation,
        user_id=target_id,
    )

    if member.user_id == conversation.managed_by_id:
        raise ValidationError(
            "The responsible group manager cannot "
            "be removed or demoted here."
        )

    if is_manager(member.user) and not is_manager(actor):
        raise PermissionDenied(
            "A Senior cannot change administrative members."
        )

    if remove:
        member.delete()

    else:
        for key, value in data.items():
            setattr(member, key, value)

        member.save(update_fields=list(data))

    notify(pk)


@transaction.atomic
def create_message(user_id, pk, data):
    actor = fresh_user(user_id)
    conversation = locked_conversation(pk)

    if not can_send(actor, conversation):
        raise PermissionDenied(
            "You cannot send messages in this conversation."
        )

    message = conversation.messages.create(
        sender=actor,
        **data,
    )

    conversation.updated_at = message.created_at

    conversation.save(
        update_fields=["updated_at"]
    )

    notify(pk, message.pk)

    return message


@transaction.atomic
def pin_message(user_id, pk, message_id, pinned):
    actor = fresh_user(user_id)
    conversation = locked_conversation(pk)

    require_group_manager(actor, conversation)

    message = get_object_or_404(
        visible_messages(actor, conversation),
        pk=message_id,
    )

    message.is_pinned = pinned
    message.pinned_by = actor if pinned else None
    message.pinned_at = timezone.now() if pinned else None

    message.save(
        update_fields=[
            "is_pinned",
            "pinned_by",
            "pinned_at",
        ]
    )

    notify(pk)

    return message