from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated ,IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Project, ProjectTask, ProjectComment
from .serializers import ( ProjectReadSerializer,  ProjectWriteSerializer,  ProjectTaskSerializer,  ProjectCommentSerializer)
from .permissions import IsSeniorFullStack, IsProjectMember, CanModifyTaskStatus
from django.utils import timezone



#Add Functions

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSeniorFullStack | IsAdminUser])
def create_task(request):
    serializer = ProjectTaskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Task added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectMember | IsAdminUser])
def add_project_comment(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)        
    if not (request.user.is_superuser or request.user.is_staff):
        if not IsProjectMember().has_object_permission(request, None, project):
            return Response({"error": "You must be a member of this project to comment."}, status=status.HTTP_403_FORBIDDEN)
    serializer = ProjectCommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, project=project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSeniorFullStack | IsAdminUser])
def create_project(request):
    serializer = ProjectWriteSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Project created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#Get Functions
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeniorFullStack | IsAdminUser])
def get_all_projects(request):
    user = request.user    
    if user.user_type == 'FULLSTACK_DEV' and user.level == 'SENIOR':
        queryset = Project.objects.all().order_by('-created_at')
    elif user.is_superuser or user.is_staff:
        queryset = Project.objects.all().order_by('-created_at')
    else:
        queryset = Project.objects.filter(employees=user).order_by('-created_at')
    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginated_queryset = paginator.paginate_queryset(queryset, request)   
    serializer = ProjectReadSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectMember | IsAdminUser])
def get_project_detail(request, pk):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)        
    if not (request.user.is_superuser or request.user.is_staff):
        if not IsProjectMember().has_object_permission(request, None, project):
            return Response({"error": "Access denied. You are not a member of this project."}, status=status.HTTP_403_FORBIDDEN)
            
    serializer = ProjectReadSerializer(project)
    return Response(serializer.data, status=status.HTTP_200_OK)


#Edit Or Update Functions
@api_view(['PATCH'])
@permission_classes([IsAuthenticated , IsSeniorFullStack | IsAdminUser])
def update_task_status(request, pk):
    try:
        task = ProjectTask.objects.get(pk=pk)
    except ProjectTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    if not CanModifyTaskStatus().has_object_permission(request, None, task):
        return Response({"error": "You do not have permission to modify this task's status."}, status=status.HTTP_403_FORBIDDEN)
    status_value = request.data.get('status')
    if status_value:
        task.status = status_value
        task.save()
        return Response({"message": f"Task status updated to {status_value}"}, status=status.HTTP_200_OK)
    
    return Response({"error": "Please provide a 'status' field."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsSeniorFullStack | IsAdminUser])
def update_project(request, pk):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = ProjectWriteSerializer(instance=project, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Project updated successfully"}, status=status.HTTP_200_OK)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





#Delete Functions
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsSeniorFullStack | IsAdminUser])
def delete_project(request, pk):
    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    project.delete()
    return Response({"message": "Project and all its related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsSeniorFullStack | IsAdminUser])
def delete_task(request, pk):
    try:
        task = ProjectTask.objects.get(pk=pk)
    except ProjectTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    task.delete()
    return Response({"message": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated]) 
def delete_project_comment(request, pk):
    try:
        comment = ProjectComment.objects.get(pk=pk)
    except ProjectComment.DoesNotExist:
        return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
    user = request.user    
    is_senior_or_admin = user.is_staff or (user.user_type == 'FULLSTACK_DEV' and user.level == 'SENIOR')
    is_author = comment.user == user
    time_difference = timezone.now() - comment.created_at
    is_within_5_minutes = time_difference.total_seconds() < 300 
    if is_senior_or_admin or (is_author and is_within_5_minutes):
        comment.delete()
        return Response({"message": "Comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    if is_author and not is_within_5_minutes:
        return Response(
            {"error": "Time limit exceeded. You can only delete your comment within 5 minutes of posting."}, 
            status=status.HTTP_403_FORBIDDEN
        )
        
    return Response(
        {"error": "You do not have permission to delete this comment."}, 
        status=status.HTTP_403_FORBIDDEN
    )