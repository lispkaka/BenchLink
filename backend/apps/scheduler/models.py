from django.db import models
from apps.projects.models import Project
from apps.testsuites.models import TestSuite


class ScheduleTask(models.Model):
    """定时任务模型"""
    STATUS_CHOICES = [
        ('active', '激活'),
        ('inactive', '停用'),
    ]

    name = models.CharField(max_length=200, verbose_name='任务名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='schedules', verbose_name='所属项目')
    testsuite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, related_name='schedules', verbose_name='测试套件')
    cron_expression = models.CharField(max_length=100, verbose_name='Cron表达式')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='任务状态')
    description = models.TextField(blank=True, null=True, verbose_name='任务描述')
    last_run_time = models.DateTimeField(null=True, blank=True, verbose_name='最后执行时间')
    next_run_time = models.DateTimeField(null=True, blank=True, verbose_name='下次执行时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '定时任务'
        verbose_name_plural = '定时任务'
        ordering = ['-created_at']

    def __str__(self):
        return self.name



