from django.db import transaction

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    BasePermission,
)
from rest_framework.response import Response

from .password_serializers import (
    LoginInputSerializer,
    PasswordChangeSerializer,
    ResetConfirmSerializer,
)
from . import password_services


class IsActiveSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_superuser
        )


def validated(serializer_class, data):
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


def private_response(data, status=200):
    return Response(
        data,
        status=status,
        headers={
            "Cache-Control": "no-store",
        },
    )


@transaction.non_atomic_requests
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    data = validated(
        LoginInputSerializer,
        request.data,
    )

    result = password_services.login_payload(
        data["username"],
        data["password"],
        request,
    )

    return private_response(result)


@transaction.non_atomic_requests
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    data = validated(
        PasswordChangeSerializer,
        request.data,
    )

    password_services.change_password(
        request.user.pk,
        data["old_password"],
        data["new_password"],
        request,
    )

    return private_response({
        "message":
            "Password changed. Sign in again.",
    })


@api_view(["POST"])
@permission_classes([IsActiveSuperuser])
def issue_reset_token(request, pk):
    data = password_services.issue_reset_token(
        request.user.pk,
        pk,
    )

    return private_response(
        data,
        status=201,
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def confirm_reset(request):
    data = validated(
        ResetConfirmSerializer,
        request.data,
    )

    password_services.confirm_reset(
        data["user"],
        data["token"],
        data["new_password"],
    )

    return private_response({
        "message":
            "Password reset. Sign in again.",
    })