from datetime import timedelta

from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.utils import timezone

from .models import LoginSecurity


def failure_delay(attempts):
    if attempts < 5:
        return None

    if attempts <= 7:
        return timedelta(hours=1)

    if attempts == 8:
        return timedelta(days=1)

    if attempts == 9:
        return timedelta(days=7)

    return timedelta(days=30)


class AccountLockoutBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        User = get_user_model()

        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if (
            not isinstance(username, str)
            or not isinstance(password, str)
        ):
            return None

        username = User.normalize_username(username)

        with transaction.atomic():
            user = (
                User.objects
                .select_for_update()
                .filter(username=username)
                .first()
            )

            if user is None:
                # تنفيذ حساب hash حتى للحساب غير الموجود.
                User().set_password(password)
                return None

            if not self.user_can_authenticate(user):
                return None

            state, _ = LoginSecurity.objects.get_or_create(
                user=user,
            )

            now = timezone.now()

            if (
                state.locked_until
                and state.locked_until > now
            ):
                return None

            if user.check_password(password):
                state.failed_attempts = 0
                state.locked_until = None

                state.save(
                    update_fields=[
                        "failed_attempts",
                        "locked_until",
                    ]
                )

                return user

            state.failed_attempts += 1

            delay = failure_delay(
                state.failed_attempts
            )

            state.locked_until = (
                now + delay
                if delay
                else None
            )

            state.save(
                update_fields=[
                    "failed_attempts",
                    "locked_until",
                ]
            )

        return None

    async def aauthenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        return await sync_to_async(
            self.authenticate,
            thread_sensitive=True,
        )(
            request,
            username=username,
            password=password,
            **kwargs,
        )