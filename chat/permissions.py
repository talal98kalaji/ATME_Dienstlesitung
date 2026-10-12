from django.db.models import Q

from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import BasePermission

from .models import Conversation


LEVELS = ("JUNIOR", "MID", "SENIOR")


def is_active(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
    )


def is_manager(user):
    return is_active(user) and (
        user.is_superuser
        or user.user_type == "MANAGER"
    )


def is_senior(user):
    return (
        is_active(user)
        and user.level == "SENIOR"
        and user.user_type not in ("DATA_ENTRY", "MANAGER")
    )


def can_create_group(user):
    return is_manager(user) or is_senior(user)


class IsChatUser(BasePermission):
    def has_permission(self, request, view):
        return is_active(request.user)


def membership_for(user, conversation):
    if not is_active(user):
        return None

    member = conversation.memberships.filter(
        user_id=user.pk
    ).first()

    # DataEntry لا يحصل على وصول تلقائي للمجموعات.
    if (
        member
        and conversation.conversation_type == Conversation.GROUP
        and user.user_type == "DATA_ENTRY"
        and not (
            member.can_send_messages
            or member.can_add_members
        )
    ):
        return None

    return member


def require_member(user, conversation):
    member = membership_for(user, conversation)

    if member is None:
        raise PermissionDenied(
            "You do not have access to this conversation."
        )

    return member


def can_manage_group(user, conversation):
    return bool(
        conversation.conversation_type == Conversation.GROUP
        and membership_for(user, conversation)
        and (
            is_manager(user)
            or (
                is_senior(user)
                and conversation.managed_by_id == user.pk
            )
        )
    )


def require_group_manager(user, conversation):
    if not can_manage_group(user, conversation):
        raise PermissionDenied(
            "Only the group manager can perform this action."
        )


def can_send(user, conversation):
    member = membership_for(user, conversation)

    if member is None:
        return False

    # المحادثة الخاصة لا تستعمل سياسة إرسال المجموعات.
    if conversation.conversation_type == Conversation.DIRECT:
        return True

    if can_manage_group(user, conversation):
        return True

    # ALL_MEMBERS لا يمنح DataEntry الإرسال تلقائيًا.
    if user.user_type == "DATA_ENTRY":
        return member.can_send_messages

    return (
        member.can_send_messages
        or conversation.send_policy == Conversation.ALL_MEMBERS
    )


def can_add(user, conversation):
    member = membership_for(user, conversation)

    return bool(
        conversation.conversation_type == Conversation.GROUP
        and member
        and (
            can_manage_group(user, conversation)
            or member.can_add_members
        )
    )


def validate_levels(user, levels):
    if not levels or any(level not in LEVELS for level in levels):
        raise ValidationError({
            "allowed_levels": "Choose at least one valid level."
        })

    if not is_manager(user) and "SENIOR" in levels:
        raise ValidationError({
            "allowed_levels":
                "A Senior can select JUNIOR and MID only."
        })


def validate_target(actor, conversation, target, flags):
    if not target.is_active:
        raise ValidationError({
            "members": "Inactive accounts cannot be added."
        })

    manages = can_manage_group(actor, conversation)

    # تفويض الإضافة لا يسمح بتفويض صلاحيات أخرى.
    if not manages and any(flags.values()):
        raise PermissionDenied(
            "Delegated members cannot grant permissions."
        )

    if is_manager(target):
        if not is_manager(actor):
            raise PermissionDenied(
                "You cannot add administrative accounts."
            )
        return

    if target.level not in conversation.allowed_levels:
        raise ValidationError({
            "members": "This level is not allowed in the group."
        })

    owner = conversation.managed_by

    if owner is None or not can_create_group(owner):
        raise PermissionDenied(
            "This group needs an active qualified manager."
        )

    if target.user_type == "DATA_ENTRY":
        if not manages:
            raise PermissionDenied(
                "Only the group manager can add DataEntry."
            )

        if not any(flags.values()):
            raise ValidationError({
                "members":
                    "DataEntry needs an explicit permission."
            })

    elif not is_manager(owner) and (
        target.user_type != owner.user_type
        or target.level == "SENIOR"
    ):
        raise ValidationError({
            "members":
                "Choose a JUNIOR or MID in the Senior specialty."
        })


def visible_messages(user, conversation):
    member = require_member(user, conversation)

    return (
        conversation.messages
        .filter(
            Q(created_at__gte=member.joined_at)
            | Q(is_pinned=True)
        )
        .select_related("sender")
        .order_by("created_at", "id")
    )