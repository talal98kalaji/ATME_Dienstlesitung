from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import AccountsSerializers, EmployeeCreateSerializer, EmployeeUpdateSerializer, CustomLoginSerializer
from .permissions import IsDataEntryOrSuperUser
from .filters import EmployeeFilter
from rest_framework.pagination import PageNumberPagination






User = get_user_model()


@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_all_employees(request):
    queryset = User.objects.all().order_by('-date_joined') 
    filterset = EmployeeFilter(request.GET, queryset=queryset)
    if not filterset.is_valid():
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)    
    filtered_queryset = filterset.qs
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'page_size'     
    paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)    
    serializer = AccountsSerializers(paginated_queryset, many=True)    
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsDataEntryOrSuperUser])
def create_employee(request):
    serializer = EmployeeCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "The Employee Created Successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_employee_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "There no employee"}, status=status.HTTP_404_NOT_FOUND)        
    serializer = AccountsSerializers(user)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['PUT', 'PATCH'])
@permission_classes([IsDataEntryOrSuperUser])
def update_employee(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "There no employee"}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = EmployeeUpdateSerializer(user, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Employee Is Updated", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
@permission_classes([IsDataEntryOrSuperUser])
def delete_employee(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "There no employee"}, status=status.HTTP_404_NOT_FOUND)

    user.delete()
    return Response({"message": "Employee has Deleted"}, status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
@permission_classes([])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if not user.is_active:
            return Response({"error": "This account is Deactivated"}, status=status.HTTP_403_FORBIDDEN)            
        refresh = RefreshToken.for_user(user)        
        user_data = {
            'id': user.id,
            'username': user.username,
            'user_type': user.user_type,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active
        }
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        }, status=status.HTTP_200_OK)
        
    return Response({"error": "Password is incorrect"}, status=status.HTTP_401_UNAUTHORIZED)