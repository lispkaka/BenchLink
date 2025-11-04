from rest_framework import serializers
from .models import TestCase, PerformanceTest
from apps.projects.serializers import ProjectSerializer
from apps.apis.serializers import APISerializer
from apps.environments.serializers import EnvironmentSerializer
from apps.projects.models import Project
from apps.apis.models import API
from apps.environments.models import Environment
from apps.executions.models import Execution


class TestCaseSerializer(serializers.ModelSerializer):
    """测试用例序列化器"""
    project = ProjectSerializer(read_only=True)
    api = APISerializer(read_only=True)
    environment = EnvironmentSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True,
        source='project',
        required=True
    )
    api_id = serializers.PrimaryKeyRelatedField(
        queryset=API.objects.all(),
        write_only=True,
        source='api',
        required=True
    )
    environment_id = serializers.PrimaryKeyRelatedField(
        queryset=Environment.objects.all(),
        write_only=True,
        source='environment',
        required=False,
        allow_null=True
    )
    
    # 从执行记录中获取最新状态和耗时
    status = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = TestCase
        fields = ['id', 'name', 'project', 'project_id', 'api', 'api_id', 'environment', 'environment_id', 
                  'description', 'pre_script', 'post_script', 'assertions', 'variables', 
                  'url_override', 'headers_override', 'body_override', 'params_override',  # 方案A：用例覆盖字段
                  'parameterized_mode', 'parameterized_data',  # 参数化功能
                  'is_active', 'status', 'duration', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'duration']
    
    def get_status(self, obj):
        """获取最新执行状态"""
        latest_execution = Execution.objects.filter(testcase=obj).order_by('-created_at').first()
        if latest_execution:
            status_map = {
                'passed': '通过',
                'failed': '失败',
                'running': '执行中',
                'pending': '待执行',
                'skipped': '跳过'
            }
            return status_map.get(latest_execution.status, '未执行')
        return '未执行'
    
    def get_duration(self, obj):
        """获取最新执行耗时"""
        latest_execution = Execution.objects.filter(testcase=obj).order_by('-created_at').first()
        if latest_execution and latest_execution.duration:
            # 转换为毫秒
            duration_ms = latest_execution.duration * 1000
            if duration_ms < 1000:
                return f"{int(duration_ms)}ms"
            else:
                return f"{(duration_ms / 1000):.2f}s"
        return None


class PerformanceTestSerializer(serializers.ModelSerializer):
    """性能测试序列化器"""
    project = ProjectSerializer(read_only=True)
    api = APISerializer(read_only=True)
    environment = EnvironmentSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True,
        source='project',
        required=True
    )
    api_id = serializers.PrimaryKeyRelatedField(
        queryset=API.objects.all(),
        write_only=True,
        source='api',
        required=True
    )
    environment_id = serializers.PrimaryKeyRelatedField(
        queryset=Environment.objects.all(),
        write_only=True,
        source='environment',
        required=False,
        allow_null=True
    )

    class Meta:
        model = PerformanceTest
        fields = ['id', 'name', 'project', 'project_id', 'api', 'api_id', 'environment', 'environment_id',
                  'description', 'threads', 'ramp_up', 'duration', 'loops', 'jmx_file',
                  'last_result', 'last_execution_time', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_result', 'last_execution_time']



