from django.contrib import admin
from .models import Site, Assignment


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'site_type', 'customer', 'city', 'is_active', 'created_at')
    list_filter = ('site_type', 'is_active')
    search_fields = ('name', 'street', 'city')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'site', 'service_type', 'is_active', 'start_date', 'end_date')
    list_filter = ('service_type', 'is_active')
    search_fields = ('employee__username', 'site__name')
