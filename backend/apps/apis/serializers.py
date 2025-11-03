from rest_framework import serializers
from .models import API
from apps.projects.serializers import ProjectSerializer
from apps.projects.models import Project


class APISerializer(serializers.ModelSerializer):
    """接口序列化器"""
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True,
        source='project',
        required=True
    )

    class Meta:
        model = API
        fields = ['id', 'name', 'url', 'method', 'project', 'project_id', 'description', 'headers',
                  'params', 'body', 'auth_type', 'auth_config', 'parameterized_mode', 
                  'parameterized_data', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



