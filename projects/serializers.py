from rest_framework import serializers
from .models import Project, ProjectTask, ProjectComment


class ProjectCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProjectComment
        fields = ['id', 'project', 'user', 'user_name', 'content', 'created_at']
        read_only_fields = ['user']


class ProjectTaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectTask
        fields = ['id', 'project', 'title', 'description', 'assigned_to', 'assigned_to_name', 'status', 'order']

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
        return None



class ProjectReadSerializer(serializers.ModelSerializer):
    tasks = ProjectTaskSerializer(many=True, read_only=True)
    comments = ProjectCommentSerializer(many=True, read_only=True)    
    duration_in_days = serializers.ReadOnlyField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_type', 'customer', 'customer_name', 
            'employees', 'start_date', 'end_date', 'duration_in_days', 
            'description', 'status', 'created_at', 'updated_at',
            'tasks', 'comments' 
        ]


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name', 'project_type', 'customer', 'employees', 
            'start_date', 'end_date', 'description', 'status'
        ]

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "End date cannot be earlier than the start date. "
            })
            
        return data