import django_filters
from .models import Site, Assignment


class SiteFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Site
        fields = ['site_type', 'customer', 'is_active', 'city', 'name']


class AssignmentFilter(django_filters.FilterSet):
    class Meta:
        model = Assignment
        fields = ['site', 'employee', 'service_type', 'is_active']
