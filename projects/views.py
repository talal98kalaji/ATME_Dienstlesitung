from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Project, ProjectTask, ProjectComment
from .serializers import (
    ProjectReadSerializer,
    ProjectWriteSerializer,
    ProjectTaskSerializer,
    ProjectCommentSerializer,
)

from .permissions import (
    IsProjectAdministrator,
    IsProjectMember,
    CanModifyTaskStatus,
    can_manage_projects,
)


@api_view(['POST'])
@permission_classes([IsProjectAdministrator])
def create_project(request):
    serializer = ProjectWriteSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {
            'message': 'Project created successfully.',
            'data': serializer.data,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_projects(request):
    user = request.user

    if can_manage_projects(user):
        queryset = Project.objects.all()
    else:
        queryset = Project.objects.filter(employees=user)

    queryset = queryset.order_by('-created_at')

    paginator = PageNumberPagination()
    paginator.page_size = 10

    page = paginator.paginate_queryset(queryset, request)

    serializer = ProjectReadSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsProjectMember])
def get_project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    permission = IsProjectMember()

    if not permission.has_object_permission(
        request,
        None,
        project
    ):
        raise PermissionDenied(
            'You are not a member of this project.'
        )

    serializer = ProjectReadSerializer(project)

    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsProjectAdministrator])
def update_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    serializer = ProjectWriteSerializer(
        instance=project,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {
            'message': 'Project updated successfully.',
            'data': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsProjectAdministrator])
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsProjectAdministrator])
def create_task(request):
    serializer = ProjectTaskSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {
            'message': 'Task added successfully.',
            'data': serializer.data,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_task_status(request, pk):
    task = get_object_or_404(ProjectTask, pk=pk)

    permission = CanModifyTaskStatus()

    if not permission.has_object_permission(
        request,
        None,
        task
    ):
        raise PermissionDenied(
            'You cannot modify this task.'
        )

    serializer = ProjectTaskSerializer(
        instance=task,
        data={
            'status': request.data.get('status')
        },
        partial=True
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {
            'message': 'Task status updated successfully.',
            'data': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsProjectAdministrator])
def delete_task(request, pk):
    task = get_object_or_404(ProjectTask, pk=pk)
    task.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsProjectMember])
def add_project_comment(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    permission = IsProjectMember()

    if not permission.has_object_permission(
        request,
        None,
        project
    ):
        raise PermissionDenied(
            'You cannot comment on this project.'
        )

    data = request.data.copy()

    data['project'] = project.pk

    serializer = ProjectCommentSerializer(data=data)

    serializer.is_valid(raise_exception=True)

    serializer.save(
        user=request.user,
        project=project
    )

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_project_comment(request, pk):
    comment = get_object_or_404(ProjectComment, pk=pk)
    user = request.user

    if can_manage_projects(user):
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    is_author = comment.user_id == user.pk

    time_difference = timezone.now() - comment.created_at
    is_within_5_minutes = time_difference.total_seconds() < 300

    if is_author and is_within_5_minutes:
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if is_author:
        raise PermissionDenied(
            'You can only delete your comment within 5 minutes.'
        )

    raise PermissionDenied(
        'You cannot delete this comment.'
    )