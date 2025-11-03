from django.db import models
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.testcases.models import TestCase
from apps.testsuites.models import TestSuite

User = get_user_model()


class Execution(models.Model):
    """测试执行记录模型"""
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('passed', '通过'),
        ('failed', '失败'),
        ('skipped', '跳过'),
    ]

    name = models.CharField(max_length=200, verbose_name='执行名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='executions', verbose_name='所属项目')
    testsuite = models.ForeignKey(TestSuite, on_delete=models.SET_NULL, null=True, blank=True, related_name='executions', verbose_name='测试套件')
    testcase = models.ForeignKey(TestCase, on_delete=models.SET_NULL, null=True, blank=True, related_name='executions', verbose_name='测试用例')
    executor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executions', verbose_name='执行人')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='执行状态')
    result = models.JSONField(default=dict, verbose_name='执行结果')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.FloatField(null=True, blank=True, verbose_name='执行时长(秒)')
    # 父子关系：支持参数化和套件执行的聚合显示
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='父执行记录')
    execution_type = models.CharField(
        max_length=20,
        choices=[
            ('normal', '普通执行'),
            ('parameterized', '参数化执行'),
            ('suite', '套件执行'),
        ],
        default='normal',
        verbose_name='执行类型'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '测试执行'
        verbose_name_plural = '测试执行'
        ordering = ['-created_at']

    def __str__(self):
        return self.name



