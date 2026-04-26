from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Customer
from .serializers import CustomerListDetailSerializer, CustomerCreateSerializer, CustomerUpdateSerializer
from .filters import CustomerFilter
from accounts.permissions import IsDataEntryOrSuperUser



@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_all_customers(request):
    queryset = Customer.objects.all().order_by('-id')    
    filterset = CustomerFilter(request.GET, queryset=queryset)
    if not filterset.is_valid():
        return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)    
    filtered_queryset = filterset.qs
    paginator = PageNumberPagination()
    paginator.page_size = 10 
    paginator.page_size_query_param = 'page_size'     
    paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
    serializer = CustomerListDetailSerializer(paginated_queryset, many=True)   
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsDataEntryOrSuperUser])
def create_customer(request):
    serializer = CustomerCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Customer created successfully", 
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)       
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsDataEntryOrSuperUser])
def get_customer_detail(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)        
    serializer = CustomerListDetailSerializer(customer)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsDataEntryOrSuperUser])
def update_customer(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'    
    serializer = CustomerUpdateSerializer(instance=customer, data=request.data, partial=partial)    
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Customer updated successfully", 
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsDataEntryOrSuperUser])
def delete_customer(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    customer.delete()
    return Response({"message": "Customer deleted successfully"}, status=status.HTTP_204_NO_CONTENT)