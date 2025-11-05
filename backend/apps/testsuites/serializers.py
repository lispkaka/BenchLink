from rest_framework import serializers
from .models import TestSuite, TestSuiteTestCase
from apps.projects.serializers import ProjectSerializer
from apps.testcases.serializers import TestCaseSerializer
from apps.testcases.models import TestCase
from apps.environments.serializers import EnvironmentSerializer
from apps.projects.models import Project
from apps.environments.models import Environment


class TestCaseWithOrderSerializer(serializers.Serializer):
    """带执行顺序的测试用例序列化器"""
    id = serializers.IntegerField()
    name = serializers.CharField(read_only=True)
    method = serializers.CharField(read_only=True)
    order = serializers.IntegerField()
    
    # 完整的用例信息（读取时返回）
    testcase = TestCaseSerializer(read_only=True, source='*')


class TestSuiteSerializer(serializers.ModelSerializer):
    """测试套件序列化器"""
    project = ProjectSerializer(read_only=True)
    environment = EnvironmentSerializer(read_only=True)
    
    # 返回带order的测试用例列表
    testcases_with_order = serializers.SerializerMethodField()
    
    # 写入字段
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True,
        source='project',
        required=True
    )
    environment_id = serializers.PrimaryKeyRelatedField(
        queryset=Environment.objects.all(),
        write_only=True,
        source='environment',
        required=False,
        allow_null=True
    )
    
    # 接收带order的测试用例列表（格式：[{id: 1, order: 1}, {id: 2, order: 2}]）
    testcases_order = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = TestSuite
        fields = ['id', 'name', 'project', 'project_id', 'testcases_with_order', 'testcases_order',
                  'environment', 'environment_id', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_testcases_with_order(self, obj):
        """获取带顺序的测试用例列表"""
        # 获取关联关系，按order排序
        relations = TestSuiteTestCase.objects.filter(testsuite=obj).select_related('testcase').order_by('order', 'id')
        result = []
        for relation in relations:
            testcase_data = TestCaseSerializer(relation.testcase).data
            testcase_data['order'] = relation.order
            result.append(testcase_data)
        return result
    
    def create(self, validated_data):
        """创建测试套件并设置测试用例顺序"""
        testcases_order = validated_data.pop('testcases_order', [])
        testsuite = TestSuite.objects.create(**validated_data)
        
        # 创建测试用例关联并设置顺序
        for item in testcases_order:
            TestSuiteTestCase.objects.create(
                testsuite=testsuite,
                testcase_id=item['id'],
                order=item.get('order', 0)
            )
        
        return testsuite
    
    def update(self, instance, validated_data):
        """更新测试套件并更新测试用例顺序"""
        testcases_order = validated_data.pop('testcases_order', None)
        
        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 如果提供了testcases_order，则更新测试用例关联
        if testcases_order is not None:
            # 删除旧的关联
            TestSuiteTestCase.objects.filter(testsuite=instance).delete()
            # 创建新的关联
            for item in testcases_order:
                TestSuiteTestCase.objects.create(
                    testsuite=instance,
                    testcase_id=item['id'],
                    order=item.get('order', 0)
                )
        
        return instance



