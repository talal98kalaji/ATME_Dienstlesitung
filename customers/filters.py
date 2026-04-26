import django_filters
from .models import Customer

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    services = django_filters.CharFilter(lookup_expr='contains')

    class Meta:
        model = Customer
        fields = ['customer_type', 'name', 'services', 'post_number']