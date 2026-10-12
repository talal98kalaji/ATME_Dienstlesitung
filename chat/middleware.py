from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def authenticate_token(raw_token):
    try:
        token = AccessToken(raw_token)

        user = get_user_model().objects.get(
            pk=token["user_id"],
            is_active=True,
        )

        return user, int(token["exp"])

    except (
        TokenError,
        KeyError,
        TypeError,
        ValueError,
        get_user_model().DoesNotExist,
    ):
        return AnonymousUser(), 0


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope = dict(scope)

        query = parse_qs(
            scope.get(
                "query_string",
                b"",
            ).decode(errors="replace")
        )

        token = query.get("token", [None])[0]

        if token:
            user, expires_at = await authenticate_token(token)
        else:
            user, expires_at = AnonymousUser(), 0

        scope["user"] = user
        scope["jwt_expires_at"] = expires_at

        return await super().__call__(
            scope,
            receive,
            send,
        )