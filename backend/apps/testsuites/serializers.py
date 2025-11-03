from rest_framework import serializers
from .models import TestSuite
from apps.projects.serializers import ProjectSerializer
from apps.testcases.serializers import TestCaseSerializer
from apps.testcases.models import TestCase
from apps.environments.serializers import EnvironmentSerializer
from apps.projects.models import Project
from apps.environments.models import Environment


class TestSuiteSerializer(serializers.ModelSerializer):
    """测试套件序列化器"""
    project = ProjectSerializer(read_only=True)
    testcases = TestCaseSerializer(many=True, read_only=True)
    environment = EnvironmentSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True,
        source='project',
        required=True
    )
    testcase_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TestCase.objects.all(),
        write_only=True,
        source='testcases',
        required=False
    )
    environment_id = serializers.PrimaryKeyRelatedField(
        queryset=Environment.objects.all(),
        write_only=True,
        source='environment',
        required=False,
        allow_null=True
    )

    class Meta:
        model = TestSuite
        fields = ['id', 'name', 'project', 'project_id', 'testcases', 'testcase_ids', 'environment', 'environment_id',
                  'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



