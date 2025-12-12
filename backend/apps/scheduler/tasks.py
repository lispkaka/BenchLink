"""
定时任务执行逻辑
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
import logging
from .models import ScheduleTask
from apps.executions.models import Execution
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

# 全局调度器
scheduler = BackgroundScheduler()


def execute_scheduled_task(task_id):
    """
    执行定时任务
    :param task_id: ScheduleTask的ID
    """
    try:
        task = ScheduleTask.objects.get(id=task_id, status='active')
        testsuite = task.testsuite
        
        # 手动执行测试套件
        testcases = testsuite.testcases.filter(is_active=True)
        
        if not testcases.exists():
            logger.warning(f"定时任务 {task.name} 的测试套件中没有可执行的测试用例")
            task.last_run_time = timezone.now()
            task.save()
            return
        
        # 创建套件执行记录
        suite_execution = Execution.objects.create(
            # 定时任务父级执行记录，名称固定前缀，避免列表出现多条
            name=f"[定时任务] {testsuite.name}",
            project=testsuite.project,
            testsuite=testsuite,
            executor=None,
            status='running',
            start_time=timezone.now(),
            execution_type='suite',
            parent=None
        )
        
        # 执行测试套件（复用TestSuiteViewSet的逻辑）
        from apps.testcases.executor import TestCaseExecutor
        from django.utils import timezone as tz
        
        suite_start_time = tz.now()
        case_results = []
        passed_count = 0
        failed_count = 0
        
        # 共享变量
        shared_variables = {}
        if testsuite.environment and testsuite.environment.variables:
            shared_variables.update(testsuite.environment.variables)
        
        # 批量执行测试用例
        for testcase in testcases:
            case_execution = Execution.objects.create(
                name=f"{testcase.name} - {tz.now().strftime('%Y-%m-%d %H:%M:%S')}",
                project=testcase.project,
                testsuite=testsuite,
                testcase=testcase,
                executor=None,
                status='running',
                start_time=tz.now(),
                execution_type='suite',
                parent=suite_execution  # 绑定父级，前端只展示父记录
            )
            
            try:
                executor = TestCaseExecutor(testcase, testsuite.environment or testcase.environment)
                executor.variables.update(shared_variables)
                
                result = executor.execute()
                
                extracted_vars = result.get('extracted_variables', {})
                if extracted_vars:
                    shared_variables.update(extracted_vars)
                
                case_end_time = tz.now()
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
                    'testcase_name': testcase.name,
                    'execution_id': case_execution.id,
                    'status': case_execution.status,
                    'duration': case_duration,
                    'result': result
                })
                
                if case_execution.status == 'passed':
                    passed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                case_end_time = tz.now()
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
        suite_end_time = tz.now()
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
        
        # 更新任务最后执行时间和下次执行时间
        task.last_run_time = timezone.now()
        
        # 获取下次执行时间
        job_id = f"scheduled_task_{task.id}"
        try:
            job = scheduler.get_job(job_id)
            if job and hasattr(job, 'next_run_time') and job.next_run_time:
                task.next_run_time = job.next_run_time
        except:
            pass
        
        task.save()
        
        logger.info(f"定时任务 {task.name} 执行完成: {passed_count}通过, {failed_count}失败")
        
    except ScheduleTask.DoesNotExist:
        logger.warning(f"定时任务 ID {task_id} 不存在或已停用")
    except Exception as e:
        logger.error(f"执行定时任务 {task_id} 时出错: {str(e)}", exc_info=True)


def parse_cron_expression(cron_expr):
    """
    解析Cron表达式
    格式: "分 时 日 月 周"
    例如: "0 9 * * *" 表示每天9点
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Cron表达式格式错误: {cron_expr}，应为5个部分（分 时 日 月 周）")
    
    minute, hour, day, month, day_of_week = parts
    
    return {
        'minute': minute if minute != '*' else None,
        'hour': hour if hour != '*' else None,
        'day': day if day != '*' else None,
        'month': month if month != '*' else None,
        'day_of_week': day_of_week if day_of_week != '*' else None,
    }


def schedule_task(task_id):
    """
    将任务添加到调度器
    """
    try:
        task = ScheduleTask.objects.get(id=task_id, status='active')
        job_id = f"scheduled_task_{task_id}"
        
        # 如果任务已存在，先删除
        try:
            scheduler.remove_job(job_id)
        except:
            pass
        
        # 解析Cron表达式
        cron_params = parse_cron_expression(task.cron_expression)
        
        # 添加任务到调度器
        trigger = CronTrigger(
            minute=cron_params['minute'],
            hour=cron_params['hour'],
            day=cron_params['day'],
            month=cron_params['month'],
            day_of_week=cron_params['day_of_week']
        )
        
        job = scheduler.add_job(
            execute_scheduled_task,
            trigger=trigger,
            id=job_id,
            args=[task_id],
            replace_existing=True
        )
        
        # 更新任务的下次执行时间
        if hasattr(job, 'next_run_time') and job.next_run_time:
            task.next_run_time = job.next_run_time
            task.save()
        
        logger.info(f"定时任务 {task.name} (ID: {task_id}) 已添加到调度器")
        return True
        
    except Exception as e:
        logger.error(f"调度任务 {task_id} 时出错: {str(e)}", exc_info=True)
        return False


def unschedule_task(task_id):
    """
    从调度器中移除任务
    """
    try:
        job_id = f"scheduled_task_{task_id}"
        scheduler.remove_job(job_id)
        logger.info(f"定时任务 {task_id} 已从调度器移除")
        return True
    except Exception as e:
        logger.error(f"移除任务 {task_id} 时出错: {str(e)}")
        return False


def start_scheduler():
    """
    启动调度器并加载所有激活的任务
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")
        
        # 加载所有激活的任务
        active_tasks = ScheduleTask.objects.filter(status='active')
        for task in active_tasks:
            schedule_task(task.id)
        
        logger.info(f"已加载 {active_tasks.count()} 个激活的定时任务")


def stop_scheduler():
    """
    停止调度器
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")





