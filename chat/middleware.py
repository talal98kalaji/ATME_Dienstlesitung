from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.contrib.auth.models import AnonymousUser

from rest_framework.exceptions import APIException
from rest_framework_simplejwt.authentication import (
    JWTAuthentication,
)


@database_sync_to_async
def authenticate_token(raw_token):
    try:
        authentication = JWTAuthentication()

        token = authentication.get_validated_token(
            raw_token
        )

        user = authentication.get_user(token)

        return user, int(token["exp"])

    except (
        APIException,
        KeyError,
        TypeError,
        ValueError,
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

        raw_token = query.get("token", [None])[0]

        if raw_token:
            user, expires_at = await authenticate_token(
                raw_token
            )
        else:
            user, expires_at = AnonymousUser(), 0

        scope["user"] = user
        scope["jwt_expires_at"] = expires_at
        scope["jwt_token"] = raw_token

        return await super().__call__(
            scope,
            receive,
            send,
        )