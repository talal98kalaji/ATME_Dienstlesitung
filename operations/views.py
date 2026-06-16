from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Site, Assignment
from .serializers import SiteSerializer, AssignmentSerializer
from .filters import SiteFilter, AssignmentFilter
from accounts.permissions import IsDataEntryOrSuperUser


# Sites
@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_all_sites(request):
    queryset = Site.objects.select_related('customer').all()
    filterset = SiteFilter(request.GET, queryset=queryset)
    if not filterset.is_valid():
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginator.page_size_query_param = 'page_size'
    page = paginator.paginate_queryset(filterset.qs, request)
    serializer = SiteSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsDataEntryOrSuperUser])
def create_site(request):
    serializer = SiteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Site created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_site_detail(request, pk):
    try:
        site = Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        return Response({"error": "Site not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = SiteSerializer(site)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsDataEntryOrSuperUser])
def update_site(request, pk):
    try:
        site = Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        return Response({"error": "Site not found"}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = SiteSerializer(site, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Site updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsDataEntryOrSuperUser])
def delete_site(request, pk):
    try:
        site = Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        return Response({"error": "Site not found"}, status=status.HTTP_404_NOT_FOUND)
    site.delete()
    return Response({"message": "Site deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def site_assignments(request, pk):
    """All employees assigned to a given site."""
    try:
        site = Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        return Response({"error": "Site not found"}, status=status.HTTP_404_NOT_FOUND)
    queryset = site.assignments.select_related('employee').all()
    serializer = AssignmentSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Assignments (linking an employee to a site)
@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_all_assignments(request):
    queryset = Assignment.objects.select_related('site', 'employee').all()
    filterset = AssignmentFilter(request.GET, queryset=queryset)
    if not filterset.is_valid():
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginator.page_size_query_param = 'page_size'
    page = paginator.paginate_queryset(filterset.qs, request)
    serializer = AssignmentSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsDataEntryOrSuperUser])
def create_assignment(request):
    serializer = AssignmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Employee assigned successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsDataEntryOrSuperUser])
def update_assignment(request, pk):
    try:
        assignment = Assignment.objects.get(pk=pk)
    except Assignment.DoesNotExist:
        return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = AssignmentSerializer(assignment, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Assignment updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsDataEntryOrSuperUser])
def delete_assignment(request, pk):
    try:
        assignment = Assignment.objects.get(pk=pk)
    except Assignment.DoesNotExist:
        return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
    assignment.delete()
    return Response({"message": "Assignment removed successfully"}, status=status.HTTP_204_NO_CONTENT)


# Employee self-service
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_assignments(request):
    """The logged-in employee's own active assignments."""
    queryset = Assignment.objects.select_related('site').filter(employee=request.user, is_active=True)
    serializer = AssignmentSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
