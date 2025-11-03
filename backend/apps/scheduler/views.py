from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import ScheduleTask
from .serializers import ScheduleTaskSerializer
from .tasks import schedule_task, unschedule_task, start_scheduler


class ScheduleTaskViewSet(viewsets.ModelViewSet):
    """定时任务视图集"""
    queryset = ScheduleTask.objects.all()
    serializer_class = ScheduleTaskSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return ScheduleTask.objects.filter(project_id=project_id)
        return ScheduleTask.objects.all()
    
    def perform_create(self, serializer):
        """创建定时任务后，添加到调度器"""
        task = serializer.save()
        if task.status == 'active':
            schedule_task(task.id)
    
    def perform_update(self, serializer):
        """更新定时任务后，重新调度"""
        task = serializer.save()
        if task.status == 'active':
            schedule_task(task.id)
        else:
            unschedule_task(task.id)
    
    def perform_destroy(self, instance):
        """删除定时任务前，从调度器移除"""
        unschedule_task(instance.id)
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def execute_now(self, request, pk=None):
        """立即执行定时任务"""
        task = self.get_object()
        from .tasks import execute_scheduled_task
        import threading
        
        try:
            # 在后台线程中执行，避免阻塞API响应
            def run_task():
                execute_scheduled_task(task.id)
            
            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            
            # 重新获取任务以获取最新的last_run_time
            task.refresh_from_db()
            
            return Response({
                'message': '任务已开始执行（后台执行）',
                'last_run_time': task.last_run_time.isoformat() if task.last_run_time else None,
                'next_run_time': task.next_run_time.isoformat() if task.next_run_time else None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'任务执行失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def execution_history(self, request, pk=None):
        """获取定时任务的执行历史"""
        task = self.get_object()
        from apps.executions.models import Execution
        
        # 查询该任务相关的执行记录（通过测试套件名称匹配）
        executions = Execution.objects.filter(
            testsuite=task.testsuite,
            name__startswith=f"[定时任务] {task.testsuite.name}"
        ).order_by('-created_at')[:50]  # 最多返回50条
        
        history = []
        for execution in executions:
            history.append({
                'id': execution.id,
                'name': execution.name,
                'status': execution.status,
                'status_text': self._get_status_text(execution.status),
                'start_time': execution.start_time.isoformat() if execution.start_time else None,
                'end_time': execution.end_time.isoformat() if execution.end_time else None,
                'duration': execution.duration,
                'result': execution.result
            })
        
        return Response({
            'task_id': task.id,
            'task_name': task.name,
            'history': history,
            'total': len(history)
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def scheduler_status(self, request):
        """获取调度器状态"""
        from .tasks import scheduler
        
        jobs = scheduler.get_jobs()
        job_list = []
        for job in jobs:
            job_list.append({
                'id': job.id,
                'name': job.name if hasattr(job, 'name') else job.id,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            })
        
        return Response({
            'running': scheduler.running,
            'jobs_count': len(jobs),
            'jobs': job_list
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



