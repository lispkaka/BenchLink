from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
from django.http import FileResponse, Http404
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
from .models import TestCase, PerformanceTest
from .serializers import TestCaseSerializer, PerformanceTestSerializer
from .executor import TestCaseExecutor
from .locust_executor import LocustExecutor
from apps.executions.models import Execution


class TestCaseViewSet(viewsets.ModelViewSet):
    """测试用例视图集"""
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return TestCase.objects.filter(project_id=project_id)
        return TestCase.objects.all()

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行测试用例（支持参数化）"""
        testcase = self.get_object()
        
        # 获取请求参数
        data = request.data
        parameterized_mode = data.get('parameterized_mode')
        if parameterized_mode is None:
            # 如果前端未指定，使用用例定义的参数化模式
            parameterized_mode = testcase.parameterized_mode
        
        # 获取参数化数据（优先级：前端传入 > 用例定义）
        parameterized_data = data.get('parameterized_data') or testcase.parameterized_data
        
        # 验证参数化数据
        if parameterized_mode == 'enabled' and parameterized_data:
            if not isinstance(parameterized_data, list):
                return Response({'error': '参数化数据必须是列表'}, 
                              status=http_status.HTTP_400_BAD_REQUEST)
            
            # 限制参数化数据数量，防止DoS攻击
            if len(parameterized_data) > 100:
                return Response({'error': '参数化数据最多100条'}, 
                              status=http_status.HTTP_400_BAD_REQUEST)
        
        # 如果启用参数化且有参数化数据
        if parameterized_mode == 'enabled' and parameterized_data and isinstance(parameterized_data, list) and len(parameterized_data) > 0:
            # 参数化执行：先创建父记录，然后创建子记录
            parent_start_time = timezone.now()
            parent_execution = Execution.objects.create(
                name=f"{testcase.name} [参数化执行] - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                project=testcase.project,
                testcase=testcase,
                executor=request.user if request.user.is_authenticated else None,
                status='running',
                start_time=parent_start_time,
                execution_type='parameterized',
                parent=None  # 父记录
            )
            
            # 循环执行多次，创建子记录
            results = []
            execution_ids = []
            passed_count = 0
            failed_count = 0
            total_time = 0
            
            for idx, param_set in enumerate(parameterized_data):
                # 为每次执行创建子执行记录
                execution = Execution.objects.create(
                    name=f"{testcase.name} [参数化#{idx+1}] - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    project=testcase.project,
                    testcase=testcase,
                    executor=request.user if request.user.is_authenticated else None,
                    status='running',
                    start_time=timezone.now(),
                    execution_type='parameterized',
                    parent=parent_execution  # 关联到父记录
                )
                execution_ids.append(execution.id)
                
                try:
                    # 执行测试用例，传入参数化变量
                    executor = TestCaseExecutor(testcase, testcase.environment)
                    # 将参数化数据合并到执行器的变量中
                    executor.variables.update(param_set)
                    result = executor.execute()
                    
                    # 更新执行记录
                    end_time = timezone.now()
                    http_time = result.get('time')
                    if http_time:
                        duration = http_time / 1000.0
                    else:
                        duration = (end_time - execution.start_time).total_seconds()
                    
                    execution.status = 'passed' if result.get('success', False) else 'failed'
                    execution.result = result
                    execution.end_time = end_time
                    execution.duration = duration
                    execution.save()
                    
                    if result.get('success', False):
                        passed_count += 1
                    else:
                        failed_count += 1
                    total_time += result.get('time', 0)
                    
                    results.append({
                        'execution_id': execution.id,
                        'index': idx + 1,
                        'status': execution.status,
                        'result': result,
                        'duration': duration
                    })
                    
                except Exception as e:
                    # 执行失败，更新执行记录
                    import traceback
                    error_trace = traceback.format_exc()
                    
                    end_time = timezone.now()
                    duration = (end_time - execution.start_time).total_seconds()
                    
                    execution.status = 'failed'
                    execution.result = {
                        'error': str(e),
                        'traceback': error_trace,
                        'success': False
                    }
                    execution.end_time = end_time
                    execution.duration = duration
                    execution.save()
                    
                    failed_count += 1
                    results.append({
                        'execution_id': execution.id,
                        'index': idx + 1,
                        'status': 'failed',
                        'error': str(e),
                        'duration': duration
                    })
            
            # 更新父执行记录
            parent_end_time = timezone.now()
            parent_duration = (parent_end_time - parent_start_time).total_seconds()
            parent_execution.status = 'passed' if failed_count == 0 else 'failed'
            parent_execution.result = {
                'parameterized': True,
                'total': len(results),
                'passed': passed_count,
                'failed': failed_count,
                'total_time': round(total_time, 2),
                'results': results
            }
            parent_execution.end_time = parent_end_time
            parent_execution.duration = parent_duration
            parent_execution.save()
            
            return Response({
                'parameterized': True,
                'execution_id': parent_execution.id,  # 返回父记录的ID
                'total': len(results),
                'passed': passed_count,
                'failed': failed_count,
                'total_time': round(total_time, 2),
                'execution_ids': execution_ids,
                'results': results,
                'message': f'参数化执行完成：{passed_count}通过，{failed_count}失败'
            }, status=http_status.HTTP_200_OK)
        else:
            # 普通执行：单次
            # 创建执行记录
            execution = Execution.objects.create(
                name=f"{testcase.name} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                project=testcase.project,
                testcase=testcase,
                executor=request.user if request.user.is_authenticated else None,
                status='running',
                start_time=timezone.now()
            )
            
            try:
                # 执行测试用例
                executor = TestCaseExecutor(testcase, testcase.environment)
                result = executor.execute()
                
                # 更新执行记录
                end_time = timezone.now()
                # 优先使用HTTP请求的实际时间（result.time），如果没有则使用总执行时间
                http_time = result.get('time')
                if http_time:
                    # result.time是毫秒，转换为秒
                    duration = http_time / 1000.0
                else:
                    # 如果没有HTTP时间，使用总执行时间（包含程序执行时间）
                    duration = (end_time - execution.start_time).total_seconds()
                
                execution.status = 'passed' if result.get('success', False) else 'failed'
                execution.result = result
                execution.end_time = end_time
                execution.duration = duration
                execution.save()
                
                return Response({
                    'execution_id': execution.id,
                    'status': execution.status,
                    'result': result,
                    'message': '执行完成'
                }, status=http_status.HTTP_200_OK)
                
            except Exception as e:
                # 执行失败，更新执行记录
                import traceback
                error_trace = traceback.format_exc()
                
                end_time = timezone.now()
                # 执行失败时，使用总执行时间
                duration = (end_time - execution.start_time).total_seconds()
                
                execution.status = 'failed'
                execution.result = {
                    'error': str(e),
                    'traceback': error_trace,
                    'success': False
                }
                execution.end_time = end_time
                execution.duration = duration
                execution.save()
                
                return Response({
                    'execution_id': execution.id,
                    'status': 'failed',
                    'error': str(e),
                    'message': '执行失败'
                }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取测试用例统计数据"""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 今日执行的用例数
        today_executions = Execution.objects.filter(
            testcase__isnull=False,
            created_at__gte=today_start
        ).values('testcase').distinct().count()
        
        # 总用例数
        total = TestCase.objects.count()
        
        # 通过的用例数（基于最新执行记录）
        passed_count = 0
        failed_count = 0
        for testcase in TestCase.objects.all():
            latest_execution = Execution.objects.filter(testcase=testcase).order_by('-created_at').first()
            if latest_execution:
                if latest_execution.status == 'passed':
                    passed_count += 1
                elif latest_execution.status == 'failed':
                    failed_count += 1
        
        pass_rate = round((passed_count / total * 100), 2) if total > 0 else 0
        
        # 平均耗时（基于今日执行记录）
        today_durations = Execution.objects.filter(
            testcase__isnull=False,
            created_at__gte=today_start,
            duration__isnull=False
        ).aggregate(avg_duration=Avg('duration'))
        
        avg_duration = today_durations['avg_duration']
        if avg_duration:
            avg_duration_ms = avg_duration * 1000
            if avg_duration_ms < 1000:
                avg_duration_str = f"{int(avg_duration_ms)}ms"
            else:
                avg_duration_str = f"{(avg_duration_ms / 1000):.2f}s"
        else:
            avg_duration_str = '-'
        
        return Response({
            'total': total,
            'today_executed': today_executions,
            'pass_rate': pass_rate,
            'avg_duration': avg_duration_str
        }, status=http_status.HTTP_200_OK)


class PerformanceTestViewSet(viewsets.ModelViewSet):
    """性能测试视图集"""
    queryset = PerformanceTest.objects.all()
    serializer_class = PerformanceTestSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return PerformanceTest.objects.filter(project_id=project_id)
        return PerformanceTest.objects.all()

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行性能测试（使用 Locust）"""
        performance_test = self.get_object()
        
        try:
            # 使用 Locust 执行器
            executor = LocustExecutor(performance_test)
            result = executor.execute()
            
            # 保存执行结果
            if result.get('success'):
                performance_test.last_result = result
                performance_test.last_execution_time = timezone.now()
                performance_test.save()
                
                return Response({
                    'success': True,
                    'message': '性能测试执行成功',
                    'result': result
                }, status=http_status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': '性能测试执行失败',
                    'error': result.get('error', '未知错误'),
                    'result': result
                }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"执行性能测试失败: {e}")
            return Response({
                'success': False,
                'error': f'执行失败: {str(e)}'
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def html_report(self, request, pk=None):
        """获取性能测试的HTML报告"""
        performance_test = self.get_object()
        
        # 获取HTML报告路径
        html_report_path = None
        if performance_test.last_result:
            html_report_path = performance_test.last_result.get('html_report')
            if not html_report_path:
                html_report_path = performance_test.last_result.get('result', {}).get('html_report')
        
        if not html_report_path:
            return Response({
                'error': '未找到HTML报告，请先执行性能测试'
            }, status=http_status.HTTP_404_NOT_FOUND)
        
        # 检查文件是否存在
        report_file = Path(html_report_path)
        if not report_file.exists():
            # 如果文件不存在，尝试查找HTML报告目录
            if report_file.suffix == '.html':
                # 如果路径是HTML文件但不存在，尝试查找同名的report目录
                report_dir = report_file.parent / 'report'
                if report_dir.exists():
                    index_file = report_dir / 'index.html'
                    if index_file.exists():
                        report_file = index_file
                    else:
                        return Response({
                            'error': 'HTML报告文件不存在'
                        }, status=http_status.HTTP_404_NOT_FOUND)
                else:
                    return Response({
                        'error': 'HTML报告文件不存在'
                    }, status=http_status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'error': 'HTML报告文件不存在'
                }, status=http_status.HTTP_404_NOT_FOUND)
        
        try:
            # 返回HTML文件（使用FileResponse）
            response = FileResponse(
                open(report_file, 'rb'),
                content_type='text/html; charset=utf-8',
                filename=report_file.name
            )
            # 添加CORS头，允许跨域访问
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            return response
        except Exception as e:
            logger.exception(f"读取HTML报告失败: {e}")
            return Response({
                'error': f'读取报告失败: {str(e)}'
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)



