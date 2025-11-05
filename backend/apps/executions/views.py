from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, Max, Min, Prefetch
from django.db.models.functions import TruncHour, TruncDay
from datetime import datetime, timedelta
from collections import defaultdict
from .models import Execution
from .serializers import ExecutionSerializer
from apps.testsuites.models import TestSuite
from apps.testcases.models import TestCase
from .report_template import HTML_REPORT_TEMPLATE, generate_testcase_html


class ExecutionViewSet(viewsets.ModelViewSet):
    """测试执行视图集"""
    queryset = Execution.objects.all()
    serializer_class = ExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """导出报告不需要认证"""
        if self.action in ['export_report']:
            return []
        return super().get_permissions()

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        type_filter = self.request.query_params.get('type')  # suite/testcase/parameterized
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        
        queryset = Execution.objects.all()
        
        # 如果project_id存在，先过滤项目
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # 如果type存在，按执行类型过滤
        if type_filter:
            if type_filter == 'suite':
                # 套件执行：execution_type='suite' 且没有testcase（只有testsuite）
                queryset = queryset.filter(execution_type='suite', testsuite__isnull=False, testcase__isnull=True)
            elif type_filter == 'testcase':
                # 用例执行：有testcase的执行记录
                queryset = queryset.filter(testcase__isnull=False)
            elif type_filter == 'parameterized':
                # 参数化执行：execution_type='parameterized'
                queryset = queryset.filter(execution_type='parameterized')
        
        # 如果status存在，过滤状态
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 如果search存在，按名称模糊搜索
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # 默认只显示父记录（parent=null），这样参数化和套件执行只显示一行
        # 详情视图（retrieve）始终不过滤，允许查看所有记录
        if self.action != 'retrieve':
            queryset = queryset.filter(parent__isnull=True)  # 只显示父记录
        
        # 预加载子记录（用于展开显示）
        queryset = queryset.prefetch_related('children')
        
        return queryset

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """仪表盘统计数据"""
        # 获取并验证时间范围参数（默认最近24小时）
        try:
            hours = int(request.query_params.get('hours', 24))
            # 限制范围：1小时到30天（720小时），防止DoS攻击
            if hours < 1:
                hours = 1
            elif hours > 720:
                hours = 720
        except (ValueError, TypeError):
            hours = 24  # 默认值
        
        time_start = timezone.now() - timedelta(hours=hours)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. 总体统计（只统计父记录）
        total_suites = TestSuite.objects.filter(is_active=True).count()
        running_executions = Execution.objects.filter(status='running', parent__isnull=True).count()
        
        # 今日统计（只统计父记录）
        today_executions = Execution.objects.filter(created_at__gte=today_start, parent__isnull=True)
        passed_today = today_executions.filter(status='passed').count()
        failed_today = today_executions.filter(status='failed').count()
        skipped_today = today_executions.filter(status='skipped').count()
        
        total_today = passed_today + failed_today + skipped_today
        pass_rate = round((passed_today / total_today * 100), 2) if total_today > 0 else 0
        
        # 平均耗时（今日已完成的执行，只统计父记录）
        avg_duration = today_executions.filter(
            status__in=['passed', 'failed'],
            duration__isnull=False
        ).aggregate(avg=Avg('duration'))['avg']
        avg_duration_sec = round(avg_duration, 2) if avg_duration else 0

        # 2. 趋势数据（按小时聚合，只统计父记录）
        trend_data = []
        for i in range(hours):
            hour_start = time_start + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_executions = Execution.objects.filter(
                created_at__gte=hour_start,
                created_at__lt=hour_end,
                parent__isnull=True
            )
            
            trend_data.append({
                'name': f'{hour_start.hour}h',
                'runs': hour_executions.count(),
                'failures': hour_executions.filter(status='failed').count()
            })

        # 3. 通过/失败/跳过统计（指定时间段，只统计父记录）
        period_executions = Execution.objects.filter(created_at__gte=time_start, parent__isnull=True)
        pass_fail_data = [
            {
                'name': '通过',
                'value': period_executions.filter(status='passed').count()
            },
            {
                'name': '失败',
                'value': period_executions.filter(status='failed').count()
            },
            {
                'name': '跳过',
                'value': period_executions.filter(status='skipped').count()
            }
        ]

        # 4. 最近运行列表（最近10条，优先显示父记录）
        recent_runs = Execution.objects.filter(
            created_at__gte=time_start
        ).order_by('-created_at')[:10]
        
        recent_runs_data = []
        for run in recent_runs:
            recent_runs_data.append({
                'id': run.id,
                'suite': run.testsuite.name if run.testsuite else (run.testcase.project.name if run.testcase and run.testcase.project else '-'),
                'testcase': run.testcase.name if run.testcase else '-',
                'env': run.testsuite.environment.name if run.testsuite and run.testsuite.environment else '-',
                'startedAt': run.start_time.strftime('%Y-%m-%d %H:%M:%S') if run.start_time else (run.created_at.strftime('%Y-%m-%d %H:%M:%S') if run.created_at else '-'),
                'duration': f"{run.duration:.4f}s" if run.duration else '-',
                'status': self._get_status_text(run.status)
            })

        # 5. 失败趋势（按用例统计）
        # 统计所有有执行记录的用例，包括有失败和没有失败的
        case_stats = Execution.objects.filter(
            created_at__gte=time_start,
            testcase__isnull=False
        ).values('testcase__name').annotate(
            total=Count('id'),
            failures=Count('id', filter=Q(status='failed'))
        ).order_by('-failures', '-total')[:10]

        failure_trend = []
        for item in case_stats:
            # 优先显示有失败的用例，但也显示执行次数较多的用例（即使没有失败）
            failure_trend.append({
                'name': item['testcase__name'],
                'runs': item['total'],
                'failures': item['failures']
            })

        # 6. Flaky用例（最近7天，失败率>20%的用例）
        seven_days_ago = timezone.now() - timedelta(days=7)
        flaky_cases = []
        
        testcases_with_executions = TestCase.objects.filter(
            executions__created_at__gte=seven_days_ago
        ).distinct()
        
        for testcase in testcases_with_executions:
            recent_executions = testcase.executions.filter(created_at__gte=seven_days_ago)
            if recent_executions.count() >= 3:  # 至少执行3次
                total_count = recent_executions.count()
                failed_count = recent_executions.filter(status='failed').count()
                failure_rate = (failed_count / total_count) * 100
                avg_dur = recent_executions.filter(duration__isnull=False).aggregate(avg=Avg('duration'))['avg']
                
                if failure_rate > 20:  # 失败率超过20%认为是flaky
                    flaky_cases.append({
                        'name': testcase.name,
                        'desc': f'最近 {total_count} 次：失败 {failed_count} 次 · 平均耗时 {round(avg_dur or 0, 1)}s',
                        'risk': '高风险' if failure_rate > 50 else '中等',
                        'type': 'danger' if failure_rate > 50 else 'warning'
                    })
        
        # 取前5个
        flaky_cases = sorted(flaky_cases, key=lambda x: x.get('risk', ''), reverse=True)[:5]

        return Response({
            'summary': {
                'totalSuites': total_suites,
                'running': running_executions,
                'passedToday': passed_today,
                'failedToday': failed_today,
                'passRate': pass_rate,
                'avgDurationSec': avg_duration_sec
            },
            'trend': trend_data,
            'passFailData': pass_fail_data,
            'recentRuns': recent_runs_data,
            'failureTrend': failure_trend,
            'flakyCases': flaky_cases
        }, status=status.HTTP_200_OK)

    def _get_status_text(self, status):
        """获取状态文本"""
        status_map = {
            'pending': '待执行',
            'running': '运行中',
            'passed': '通过',
            'failed': '失败',
            'skipped': '跳过'
        }
        return status_map.get(status, status)
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """获取执行详情（包含断言结果、错误信息等）"""
        execution = self.get_object()
        
        result = execution.result or {}
        
        # 获取断言详情
        assertions = result.get('assertions', [])
        assertion_details = []
        for assertion in assertions:
            assertion_details.append({
                'type': assertion.get('type', 'unknown'),
                'description': assertion.get('description', ''),
                'expected': assertion.get('expected') or assertion.get('value', ''),
                'actual': assertion.get('actual', ''),
                'success': assertion.get('success', False),
                'message': assertion.get('message', '')
            })
        
        # 构建详细结果
        details = {
            'id': execution.id,
            'name': execution.name,
            'status': execution.status,
            'status_text': self._get_status_text(execution.status),
            'start_time': execution.start_time.isoformat() if execution.start_time else None,
            'end_time': execution.end_time.isoformat() if execution.end_time else None,
            'duration': execution.duration,
            'request': {
                'url': result.get('url', ''),
                'method': execution.testcase.api.method if execution.testcase and execution.testcase.api else 'N/A',
            },
            'response': {
                'status_code': result.get('status_code'),
                'headers': result.get('headers', {}),
                'body': result.get('body', ''),
                'json': result.get('json'),
                'time': result.get('time', 0),  # 响应时间（毫秒）
            },
            'assertions': assertion_details,
            'assertions_summary': {
                'total': len(assertions),
                'passed': sum(1 for a in assertions if a.get('success', False)),
                'failed': sum(1 for a in assertions if not a.get('success', True)),
            },
            'error': result.get('error'),
            'traceback': result.get('traceback'),
            'extracted_variables': result.get('extracted_variables', {}),
        }
        
        # 如果是套件执行，添加子用例信息
        if execution.testsuite and not execution.testcase:
            # 这是套件级别的执行记录
            suite_result = result.get('case_results', [])
            details['suite_summary'] = {
                'total': result.get('total', 0),
                'passed': result.get('passed', 0),
                'failed': result.get('failed', 0),
                'pass_rate': result.get('pass_rate', 0),
            }
            details['case_results'] = suite_result
        
        return Response(details, status=status.HTTP_200_OK)
    
    def perform_destroy(self, instance):
        """删除执行记录"""
        # 如果是套件执行记录，可以选择是否同时删除子用例执行记录
        # 这里先简单删除，后续可以根据需求添加选项
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """批量删除执行记录"""
        if not request.user.is_authenticated:
            return Response({'error': '需要认证'}, status=status.HTTP_401_UNAUTHORIZED)
        
        execution_ids = request.data.get('ids', [])
        if not execution_ids:
            return Response({
                'error': '请提供要删除的执行记录ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 限制批量删除数量，防止DoS攻击
        if len(execution_ids) > 100:
            return Response({
                'error': '一次最多只能删除100条记录'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证ID类型和格式
        try:
            execution_ids = [int(id) for id in execution_ids]
        except (ValueError, TypeError):
            return Response({
                'error': 'ID格式不正确，必须是整数列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证是否都是有效的ID（只查询存在的记录）
        executions = Execution.objects.filter(id__in=execution_ids)
        deleted_count = executions.count()
        
        # 执行删除
        executions.delete()
        
        return Response({
            'message': f'成功删除 {deleted_count} 条执行记录',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def export_report(self, request, pk=None):
        """导出测试报告为HTML"""
        execution = self.get_object()
        
        try:
            # 准备报告数据
            result = execution.result or {}
            
            # 基本信息
            execution_name = execution.name
            project_name = execution.project.name if execution.project else 'Unknown'
            start_time = execution.start_time.strftime('%Y-%m-%d %H:%M:%S') if execution.start_time else 'N/A'
            generated_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 统计信息
            if execution.testsuite and not execution.testcase:
                # 套件执行
                total_count = result.get('total', 0)
                passed_count = result.get('passed', 0)
                failed_count = result.get('failed', 0)
                pass_rate = result.get('pass_rate', 0)
                duration = round(execution.duration, 2) if execution.duration else 0
                
                # 生成测试用例HTML
                testcases_html = ''
                case_results = result.get('case_results', [])
                for case_result in case_results:
                    testcase_data = {
                        'name': case_result.get('testcase_name', 'Unknown'),
                        'status': case_result.get('status', 'unknown'),
                        'result': case_result.get('result', {}),
                        'method': 'GET'  # 默认
                    }
                    testcases_html += generate_testcase_html(testcase_data)
            else:
                # 单个用例执行
                total_count = 1
                passed_count = 1 if execution.status == 'passed' else 0
                failed_count = 1 if execution.status == 'failed' else 0
                pass_rate = 100 if execution.status == 'passed' else 0
                duration = round(execution.duration, 2) if execution.duration else 0
                
                # 生成测试用例HTML
                testcase_data = {
                    'name': execution.testcase.name if execution.testcase else execution.name,
                    'status': execution.status,
                    'result': result,
                    'method': execution.testcase.api.method if execution.testcase and execution.testcase.api else 'GET'
                }
                testcases_html = generate_testcase_html(testcase_data)
            
            # 通过率颜色
            if pass_rate >= 80:
                pass_rate_color = '#10b981'
            elif pass_rate >= 60:
                pass_rate_color = '#f59e0b'
            else:
                pass_rate_color = '#ef4444'
            
            # 生成HTML报告
            html_content = HTML_REPORT_TEMPLATE.format(
                execution_name=execution_name,
                project_name=project_name,
                start_time=start_time,
                generated_time=generated_time,
                total_count=total_count,
                passed_count=passed_count,
                failed_count=failed_count,
                pass_rate=pass_rate,
                pass_rate_color=pass_rate_color,
                duration=duration,
                testcases_html=testcases_html
            )
            
            # 返回HTML文件
            response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
            filename = f"test_report_{execution.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.html"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response({
                'error': f'导出报告失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



