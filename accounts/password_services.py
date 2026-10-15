import math
import secrets

from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import (
    constant_time_compare,
    salted_hmac,
)

from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
    Throttled,
    ValidationError,
)

from rest_framework_simplejwt.tokens import RefreshToken

from .models import LoginSecurity
from .password_validation import validate_api_password


User = get_user_model()


class InvalidCredentials(APIException):
    status_code = 401
    default_detail = "Invalid username or password."
    default_code = "invalid_credentials"


def reject_login(username):
    state = LoginSecurity.objects.filter(
        user__username=User.normalize_username(username),
        user__is_active=True,
    ).first()

    if state and state.locked_until:
        remaining = math.ceil(
            (
                state.locked_until
                - timezone.now()
            ).total_seconds()
        )

        if remaining > 0:
            raise Throttled(
                wait=remaining,
                detail="Account temporarily locked.",
            )

    raise InvalidCredentials()


def login_payload(username, password, request=None):
    user = authenticate(
        request=request,
        username=username,
        password=password,
    )

    if user is None:
        reject_login(username)

    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
            key: getattr(user, key)
            for key in (
                "id",
                "username",
                "user_type",
                "level",
                "first_name",
                "last_name",
                "is_superuser",
                "is_staff",
                "is_active",
            )
        },
    }


def reset_digest(token):
    return salted_hmac(
        "accounts.password-reset",
        token,
        algorithm="sha256",
    ).hexdigest()


def finish_password_change(user, state, password):
    validate_api_password(password, user)

    if user.check_password(password):
        raise ValidationError({
            "password": (
                "Choose a password different "
                "from the current one."
            ),
        })

    user.set_password(password)
    user.save(update_fields=["password"])

    state.failed_attempts = 0
    state.locked_until = None

    state.reset_token_hash = ""
    state.reset_password_snapshot = ""
    state.reset_expires_at = None
    state.reset_issued_by = None

    state.save()


def change_password(
    user_id,
    old_password,
    new_password,
    request=None,
):
    current = get_object_or_404(
        User,
        pk=user_id,
        is_active=True,
    )

    # الـBackend يحفظ المحاولة قبل إرجاع خطأ الـAPI.
    verified = authenticate(
        request=request,
        username=current.username,
        password=old_password,
    )

    if verified is None:
        reject_login(current.username)

    with transaction.atomic():
        user = get_object_or_404(
            User.objects.select_for_update(),
            pk=user_id,
            is_active=True,
        )

        if user.password != verified.password:
            raise AuthenticationFailed(
                "Password changed during this request. "
                "Sign in again."
            )

        state, _ = LoginSecurity.objects.get_or_create(
            user=user,
        )

        finish_password_change(
            user,
            state,
            new_password,
        )


@transaction.atomic
def issue_reset_token(issuer_id, user_id):
    issuer = User.objects.filter(
        pk=issuer_id,
        is_active=True,
        is_superuser=True,
    ).first()

    if issuer is None:
        raise PermissionDenied(
            "Only an active Superuser "
            "can issue reset tokens."
        )

    user = get_object_or_404(
        User.objects.select_for_update(),
        pk=user_id,
        is_active=True,
    )

    state, _ = LoginSecurity.objects.get_or_create(
        user=user,
    )

    token = secrets.token_urlsafe(32)

    state.reset_token_hash = reset_digest(token)
    state.reset_password_snapshot = user.password

    state.reset_expires_at = (
        timezone.now()
        + timedelta(minutes=30)
    )

    state.reset_issued_by = issuer

    state.save(
        update_fields=[
            "reset_token_hash",
            "reset_password_snapshot",
            "reset_expires_at",
            "reset_issued_by",
        ]
    )

    return {
        "user": user.pk,
        "token": token,
        "expires_at": state.reset_expires_at,
        "expires_in": 1800,
    }


@transaction.atomic
def confirm_reset(user_id, token, password):
    user = (
        User.objects
        .select_for_update()
        .filter(
            pk=user_id,
            is_active=True,
        )
        .first()
    )

    state = (
        LoginSecurity.objects.filter(user=user).first()
        if user
        else None
    )

    valid = (
        state
        and state.reset_token_hash
        and state.reset_expires_at
        and state.reset_expires_at > timezone.now()
        and constant_time_compare(
            state.reset_token_hash,
            reset_digest(token),
        )
        and constant_time_compare(
            state.reset_password_snapshot,
            user.password,
        )
    )

    if not valid:
        raise ValidationError({
            "token": "Invalid or expired reset token.",
        })

    finish_password_change(
        user,
        state,
        password,
    )