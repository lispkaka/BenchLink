from rest_framework import serializers
from .models import ScheduleTask
from apps.projects.serializers import ProjectSerializer
from apps.testsuites.serializers import TestSuiteSerializer


class ScheduleTaskSerializer(serializers.ModelSerializer):
    """定时任务序列化器"""
    project = ProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True, required=False)
    testsuite = TestSuiteSerializer(read_only=True)
    testsuite_id = serializers.IntegerField(write_only=True, required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ScheduleTask
        fields = ['id', 'name', 'project', 'project_id', 'testsuite', 'testsuite_id', 
                  'cron_expression', 'status', 'status_display', 'description', 
                  'last_run_time', 'next_run_time', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """创建时处理关联对象"""
        project_id = validated_data.pop('project_id', None)
        testsuite_id = validated_data.pop('testsuite_id', None)
        
        if project_id:
            from apps.projects.models import Project
            validated_data['project'] = Project.objects.get(id=project_id)
        if testsuite_id:
            from apps.testsuites.models import TestSuite
            validated_data['testsuite'] = TestSuite.objects.get(id=testsuite_id)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新时处理关联对象"""
        project_id = validated_data.pop('project_id', None)
        testsuite_id = validated_data.pop('testsuite_id', None)
        
        if project_id:
            from apps.projects.models import Project
            instance.project = Project.objects.get(id=project_id)
        if testsuite_id:
            from apps.testsuites.models import TestSuite
            instance.testsuite = TestSuite.objects.get(id=testsuite_id)
        
        return super().update(instance, validated_data)



