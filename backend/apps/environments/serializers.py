from rest_framework import serializers
from .models import Environment, GlobalToken
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer


class EnvironmentSerializer(serializers.ModelSerializer):
    """环境序列化器"""
    project = ProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Environment
        fields = ['id', 'name', 'base_url', 'project', 'project_id', 'description', 
                  'variables', 'headers', 'pre_hook', 'post_hook', 'parameterized_data',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """创建时处理关联对象"""
        project_id = validated_data.pop('project_id', None)
        if project_id:
            validated_data['project'] = Project.objects.get(id=project_id)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新时处理关联对象"""
        project_id = validated_data.pop('project_id', None)
        if project_id:
            instance.project = Project.objects.get(id=project_id)
        return super().update(instance, validated_data)


class GlobalTokenSerializer(serializers.ModelSerializer):
    """全局 Token 序列化器"""
    
    class Meta:
        model = GlobalToken
        fields = ['id', 'name', 'auth_type', 'token', 'header_name', 'token_format',
                  'description', 'is_active', 'is_default', 'variables',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



