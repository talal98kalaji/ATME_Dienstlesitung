import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()

class EmployeeFilter(django_filters.FilterSet):
    class Meta:
        model = User

        fields = {
            'user_type': ['exact'],      
            'level': ['exact'],         
            'is_active': ['exact'],  
            'post_number': ['exact'],  
            'first_name': ['icontains'], 
        }