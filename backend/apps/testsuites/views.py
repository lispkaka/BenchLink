from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import TestSuite
from .serializers import TestSuiteSerializer
from apps.testcases.executor import TestCaseExecutor
from apps.executions.models import Execution


class TestSuiteViewSet(viewsets.ModelViewSet):
    """测试套件视图集"""
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return TestSuite.objects.filter(project_id=project_id)
        return TestSuite.objects.all()

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行测试套件（批量执行测试用例）"""
        testsuite = self.get_object()
        
        # 获取套件中的所有测试用例
        testcases = testsuite.testcases.filter(is_active=True)
        
        if not testcases.exists():
            return Response({
                'error': '测试套件中没有可执行的测试用例'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建套件执行记录（父记录）
        suite_start_time = timezone.now()
        suite_execution = Execution.objects.create(
            name=f"{testsuite.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
            project=testsuite.project,
            testsuite=testsuite,
            executor=request.user if request.user.is_authenticated else None,
            status='running',
            start_time=suite_start_time,
            execution_type='suite',
            parent=None  # 父记录
        )
        
        # 执行结果汇总
        case_results = []
        passed_count = 0
        failed_count = 0
        
        # 共享变量（用于在不同测试用例之间传递数据）
        shared_variables = {}
        # 合并环境变量
        if testsuite.environment and testsuite.environment.variables:
            shared_variables.update(testsuite.environment.variables)
        
        # 批量执行测试用例（创建子记录）
        for testcase in testcases:
            # 检查是否是参数化用例
            parameterized_mode = testcase.parameterized_mode or 'disabled'
            parameterized_data = testcase.parameterized_data or []
            is_parameterized = (parameterized_mode == 'enabled' and 
                              isinstance(parameterized_data, list) and 
                              len(parameterized_data) > 0)
            
            if is_parameterized:
                # 参数化用例：循环执行多次，每次创建一个子记录
                for idx, param_set in enumerate(parameterized_data):
                    case_execution = Execution.objects.create(
                        name=f"{testcase.name} [参数化#{idx+1}/{len(parameterized_data)}] - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        project=testcase.project,
                        testsuite=testsuite,
                        testcase=testcase,
                        executor=request.user if request.user.is_authenticated else None,
                        status='running',
                        start_time=timezone.now(),
                        execution_type='suite',  # 套件内的执行
                        parent=suite_execution  # 关联到父记录（套件执行）
                    )
                    
                    try:
                        # 创建执行器，并传入共享变量
                        executor = TestCaseExecutor(testcase, testsuite.environment or testcase.environment)
                        # 将之前提取的变量传递给当前执行器
                        executor.variables.update(shared_variables)
                        # 将参数化数据合并到执行器的变量中
                        executor.variables.update(param_set)
                        
                        # 执行测试用例
                        result = executor.execute()
                        
                        # 将当前执行提取的变量合并到共享变量中，供后续用例使用
                        extracted_vars = result.get('extracted_variables', {})
                        if extracted_vars:
                            shared_variables.update(extracted_vars)
                        
                        # 更新用例执行记录
                        case_end_time = timezone.now()
                        http_time = result.get('time')
                        if http_time:
                            case_duration = http_time / 1000.0
                        else:
                            case_duration = (case_end_time - case_execution.start_time).total_seconds()
                        
                        case_execution.status = 'passed' if result.get('success', False) else 'failed'
                        case_execution.result = result
                        case_execution.end_time = case_end_time
                        case_execution.duration = case_duration
                        case_execution.save()
                        
                        case_results.append({
                            'testcase_id': testcase.id,
                            'testcase_name': f"{testcase.name} [参数化#{idx+1}]",
                            'execution_id': case_execution.id,
                            'status': case_execution.status,
                            'duration': case_duration,
                            'result': result,
                            'parameterized_index': idx + 1,
                            'parameterized_total': len(parameterized_data)
                        })
                        
                        if case_execution.status == 'passed':
                            passed_count += 1
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        # 用例执行失败
                        case_end_time = timezone.now()
                        case_duration = (case_end_time - case_execution.start_time).total_seconds()
                        
                        case_execution.status = 'failed'
                        case_execution.result = {
                            'error': str(e),
                            'success': False
                        }
                        case_execution.end_time = case_end_time
                        case_execution.duration = case_duration
                        case_execution.save()
                        
                        case_results.append({
                            'testcase_id': testcase.id,
                            'testcase_name': f"{testcase.name} [参数化#{idx+1}]",
                            'execution_id': case_execution.id,
                            'status': 'failed',
                            'duration': case_duration,
                            'error': str(e),
                            'parameterized_index': idx + 1,
                            'parameterized_total': len(parameterized_data)
                        })
                        failed_count += 1
            else:
                # 普通用例：执行一次，创建一个子记录
                case_execution = Execution.objects.create(
                    name=f"{testcase.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    project=testcase.project,
                    testsuite=testsuite,
                    testcase=testcase,
                    executor=request.user if request.user.is_authenticated else None,
                    status='running',
                    start_time=timezone.now(),
                    execution_type='suite',
                    parent=suite_execution  # 关联到父记录（套件执行）
                )
                
                try:
                    # 创建执行器，并传入共享变量
                    executor = TestCaseExecutor(testcase, testsuite.environment or testcase.environment)
                    # 将之前提取的变量传递给当前执行器
                    executor.variables.update(shared_variables)
                    
                    # 执行测试用例
                    result = executor.execute()
                    
                    # 将当前执行提取的变量合并到共享变量中，供后续用例使用
                    extracted_vars = result.get('extracted_variables', {})
                    if extracted_vars:
                        shared_variables.update(extracted_vars)
                    
                    # 更新用例执行记录
                    case_end_time = timezone.now()
                    # 优先使用HTTP请求的实际时间（result.time），如果没有则使用总执行时间
                    http_time = result.get('time')
                    if http_time:
                        # result.time是毫秒，转换为秒
                        case_duration = http_time / 1000.0
                    else:
                        # 如果没有HTTP时间，使用总执行时间（包含程序执行时间）
                        case_duration = (case_end_time - case_execution.start_time).total_seconds()
                    
                    case_execution.status = 'passed' if result.get('success', False) else 'failed'
                    case_execution.result = result
                    case_execution.end_time = case_end_time
                    case_execution.duration = case_duration
                    case_execution.save()
                    
                    case_results.append({
                        'testcase_id': testcase.id,
                        'testcase_name': testcase.name,
                        'execution_id': case_execution.id,
                        'status': case_execution.status,
                        'duration': case_duration,  # 这是HTTP请求的实际时间（秒）
                        'result': result
                    })
                    
                    if case_execution.status == 'passed':
                        passed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    # 用例执行失败
                    case_end_time = timezone.now()
                    case_duration = (case_end_time - case_execution.start_time).total_seconds()
                    
                    case_execution.status = 'failed'
                    case_execution.result = {
                        'error': str(e),
                        'success': False
                    }
                    case_execution.end_time = case_end_time
                    case_execution.duration = case_duration
                    case_execution.save()
                    
                    case_results.append({
                        'testcase_id': testcase.id,
                        'testcase_name': testcase.name,
                        'execution_id': case_execution.id,
                        'status': 'failed',
                        'duration': case_duration,
                        'error': str(e)
                    })
                    failed_count += 1
        
        # 更新套件执行记录
        suite_end_time = timezone.now()
        suite_duration = (suite_end_time - suite_start_time).total_seconds()
        
        suite_execution.status = 'passed' if failed_count == 0 else 'failed'
        suite_execution.result = {
            'total': len(testcases),
            'passed': passed_count,
            'failed': failed_count,
            'pass_rate': round(passed_count / len(testcases) * 100, 2) if len(testcases) > 0 else 0,
            'case_results': case_results
        }
        suite_execution.end_time = suite_end_time
        suite_execution.duration = suite_duration
        suite_execution.save()
        
        return Response({
            'execution_id': suite_execution.id,
            'status': suite_execution.status,
            'summary': {
                'total': len(testcases),
                'passed': passed_count,
                'failed': failed_count,
                'pass_rate': suite_execution.result['pass_rate'],
                'duration': suite_duration
            },
            'case_results': case_results,
            'message': '套件执行完成'
        }, status=status.HTTP_200_OK)



