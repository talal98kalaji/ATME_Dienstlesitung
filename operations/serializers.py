from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Site, Assignment

User = get_user_model()

# Maps a service type to the employee specialty (user_type) it requires.
SERVICE_TO_USER_TYPE = {
    'CLEANING': 'CLEANER',
    'SECURITY': 'SECURITY',
}


class SiteSerializer(serializers.ModelSerializer):
    site_type_display = serializers.CharField(source='get_site_type_display', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    assignments_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'site_type', 'site_type_display',
            'customer', 'customer_name',
            'street', 'house_number', 'post_number', 'city',
            'latitude', 'longitude', 'is_active',
            'assignments_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_assignments_count(self, obj):
        return obj.assignments.count()


class AssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.CharField(source='site.name', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id', 'site', 'site_name', 'employee', 'employee_name',
            'service_type', 'service_type_display',
            'start_date', 'end_date', 'is_active', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_name(self, obj):
        full_name = f"{obj.employee.first_name} {obj.employee.last_name}".strip()
        return full_name or obj.employee.username

    def validate(self, data):
        employee = data.get('employee') or getattr(self.instance, 'employee', None)
        service_type = data.get('service_type') or getattr(self.instance, 'service_type', None)

        # The employee's specialty must match the requested service.
        if employee and service_type:
            expected_type = SERVICE_TO_USER_TYPE.get(service_type)
            if employee.user_type != expected_type:
                raise serializers.ValidationError({
                    'employee': (
                        f"This employee's specialty ({employee.user_type}) does not match "
                        f"the service type ({service_type})."
                    )
                })

        start_date = data.get('start_date') or getattr(self.instance, 'start_date', None)
        end_date = data.get('end_date') or getattr(self.instance, 'end_date', None)
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({'end_date': "End date cannot be earlier than the start date."})

        return data
