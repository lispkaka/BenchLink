from django.db import models
from apps.projects.models import Project
from apps.apis.models import API
from apps.environments.models import Environment


class TestCase(models.Model):
    """测试用例模型"""
    name = models.CharField(max_length=200, verbose_name='用例名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testcases', verbose_name='所属项目')
    api = models.ForeignKey(API, on_delete=models.CASCADE, related_name='testcases', verbose_name='关联接口')
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='测试环境')
    description = models.TextField(blank=True, null=True, verbose_name='用例描述')
    pre_script = models.TextField(blank=True, null=True, verbose_name='前置脚本')
    post_script = models.TextField(blank=True, null=True, verbose_name='后置脚本')
    assertions = models.JSONField(default=list, verbose_name='断言规则')
    variables = models.JSONField(default=dict, verbose_name='变量')
    # 用例级别的参数覆盖（方案A）
    url_override = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='URL覆盖（支持变量）',
        help_text='覆盖接口定义的URL，支持${variable}变量，留空则使用接口定义的URL'
    )
    headers_override = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='请求头覆盖（支持变量）',
        help_text='覆盖接口定义的请求头，支持${variable}变量，留空则使用接口定义的请求头'
    )
    body_override = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='请求体覆盖（支持变量）',
        help_text='覆盖接口定义的请求体，支持${variable}变量，留空则使用接口定义的请求体'
    )
    params_override = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='查询参数覆盖（支持变量）',
        help_text='覆盖接口定义的查询参数，支持${variable}变量，留空则使用接口定义的查询参数'
    )
    # 参数化功能（用例级别）
    parameterized_mode = models.CharField(
        max_length=20,
        choices=[
            ('disabled', '禁用'),
            ('enabled', '启用'),
        ],
        default='disabled',
        verbose_name='参数化模式',
        help_text='启用后，用例将使用参数化数据循环执行多次'
    )
    parameterized_data = models.JSONField(
        default=list,
        blank=True,
        verbose_name='参数化数据',
        help_text='格式: [{"param1": "value1"}, {"param1": "value2"}]，每个字典代表一组参数，会替换用例中的${变量名}'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'
        ordering = ['-created_at']

    def __str__(self):
        return self.name



