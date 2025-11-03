from rest_framework import serializers
from datetime import timedelta
from django.utils import timezone
from .models import Execution
from apps.projects.serializers import ProjectSerializer
from apps.testcases.serializers import TestCaseSerializer
from apps.testsuites.serializers import TestSuiteSerializer
from apps.users.serializers import UserSerializer


class ExecutionSerializer(serializers.ModelSerializer):
    """测试执行序列化器"""
    project = ProjectSerializer(read_only=True)
    testsuite = TestSuiteSerializer(read_only=True)
    testcase = TestCaseSerializer(read_only=True)
    executor = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()  # 使用parent字段获取子记录
    execution_type = serializers.CharField(read_only=True)
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Execution
        fields = ['id', 'name', 'project', 'testsuite', 'testcase', 'executor',
                  'status', 'result', 'start_time', 'end_time', 'duration', 'created_at',
                  'execution_type', 'parent_id', 'children', 'children_count']
        read_only_fields = ['id', 'created_at']

    def get_children(self, obj):
        """获取子执行记录（通过parent字段）"""
        # 使用prefetch_related预加载的children，或查询children
        if hasattr(obj, 'children'):
            # 如果已经预加载
            children = obj.children.all()
        else:
            # 如果没有预加载，直接查询
            children = Execution.objects.filter(parent=obj).order_by('created_at')
        
        if children.exists():
            # 使用简化版序列化器（避免递归）
            return SimpleExecutionSerializer(children, many=True).data
        return []
    
    def get_children_count(self, obj):
        """获取子记录数量"""
        if hasattr(obj, 'children'):
            return obj.children.count()
        return Execution.objects.filter(parent=obj).count()


class SimpleExecutionSerializer(serializers.ModelSerializer):
    """简化的执行记录序列化器（用于子记录，避免递归）"""
    class Meta:
        model = Execution
        fields = ['id', 'name', 'testcase', 'status', 'start_time', 'end_time', 'duration', 'result', 'execution_type']
        read_only_fields = ['id']




    def get_child_executions(self, obj):
        """获取套件执行的所有子用例执行记录"""
        # 如果是套件执行记录（有testsuite但没有testcase），返回所有子用例执行记录
        if obj.testsuite and not obj.testcase:
            # 优先从result中的case_results获取execution_id（最准确）
            child_ids = []
            if obj.result and isinstance(obj.result, dict):
                case_results = obj.result.get('case_results', [])
                child_ids = [case.get('execution_id') for case in case_results if case.get('execution_id')]
            
            if child_ids:
                # 如果result中有execution_id，直接使用
                child_executions = Execution.objects.filter(id__in=child_ids).order_by('created_at')
            else:
                # 否则，根据套件执行的时间范围来查找子用例（兼容旧数据）
                start_window = obj.start_time if obj.start_time else obj.created_at
                if obj.end_time:
                    end_window = obj.end_time + timedelta(minutes=1)
                else:
                    end_window = timezone.now()
                
                child_executions = Execution.objects.filter(
                    testsuite=obj.testsuite,
                    testcase__isnull=False,
                    created_at__gte=start_window - timedelta(minutes=1),
                    created_at__lte=end_window
                ).order_by('created_at')
            
            return ExecutionSerializer(child_executions, many=True).data
        return []
    
    def get_parent_suite_execution_id(self, obj):
        """获取子用例对应的父套件执行ID"""
        # 如果是子用例（有testsuite和testcase），查找对应的套件执行记录
        if obj.testsuite and obj.testcase:
            # 查找同一套件、同一时间段、没有testcase的执行记录
            # 查找在子用例创建时间前后5分钟内的套件执行记录
            start_window = obj.start_time if obj.start_time else obj.created_at
            
            # 查找套件执行记录（有testsuite但没有testcase）
            suite_executions = Execution.objects.filter(
                testsuite=obj.testsuite,
                testcase__isnull=True,
                created_at__gte=start_window - timedelta(minutes=5),
                created_at__lte=start_window + timedelta(minutes=5)
            ).order_by('-created_at')
            
            if suite_executions.exists():
                # 检查该套件执行记录的result中是否包含当前子用例
                for suite_exec in suite_executions:
                    if suite_exec.result and isinstance(suite_exec.result, dict):
                        case_results = suite_exec.result.get('case_results', [])
                        child_ids = [case.get('execution_id') for case in case_results]
                        if obj.id in child_ids:
                            return suite_exec.id
                
                # 如果没有在result中找到，返回时间最接近的套件执行记录
                return suite_executions.first().id
            
        return None



