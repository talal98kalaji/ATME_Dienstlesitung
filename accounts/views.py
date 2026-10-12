from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .filters import EmployeeFilter
from .permissions import IsSuperuserOrManager
from .serializers import (
    AccountsSerializers,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
)


User = get_user_model()


@api_view(['GET'])
@permission_classes([IsSuperuserOrManager])
def get_all_employees(request):
    queryset = User.objects.all().order_by('-date_joined')
    filterset = EmployeeFilter(
        request.GET,
        queryset=queryset
    )

    if not filterset.is_valid():
        return Response(
            filterset.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'page_size'
    page = paginator.paginate_queryset(
        filterset.qs,
        request
    )
    serializer = AccountsSerializers(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsSuperuserOrManager])
def create_employee(request):
    serializer = EmployeeCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {
            'message': 'Employee created successfully.',
            'data': serializer.data,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsSuperuserOrManager])
def get_employee_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = AccountsSerializers(user)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsSuperuserOrManager])
@transaction.atomic
def update_employee(request, pk):
    try:
        user = User.objects.select_for_update().get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    permission = IsSuperuserOrManager()
    if not permission.has_object_permission(
        request,
        None,
        user
    ):
        raise PermissionDenied(
            'Only a superuser can modify a superuser account.'
        )

    serializer = EmployeeUpdateSerializer(
        instance=user,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {
            'message': 'Employee updated successfully.',
            'data': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsSuperuserOrManager])
@transaction.atomic
def delete_employee(request, pk):
    try:
        user = User.objects.select_for_update().get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'error': 'Employee not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    permission = IsSuperuserOrManager()

    if not permission.has_object_permission(
        request,
        None,
        user
    ):
        raise PermissionDenied(
            'Only a superuser can delete a superuser account.'
        )

    user.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(
        username=username,
        password=password
    )

    if user is None:
        return Response(
            {'error': 'Invalid login credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'This account is deactivated.'},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'user_type': user.user_type,
                'level': user.level,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
            },
        },
        status=status.HTTP_200_OK
    )