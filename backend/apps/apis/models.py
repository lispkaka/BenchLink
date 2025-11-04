from django.db import models
from apps.projects.models import Project


class API(models.Model):
    """接口模型"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    ]

    name = models.CharField(max_length=200, verbose_name='接口名称')
    url = models.CharField(max_length=500, verbose_name='接口路径')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='GET', verbose_name='请求方法')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='apis', verbose_name='所属项目')
    description = models.TextField(blank=True, null=True, verbose_name='接口描述')
    headers = models.JSONField(default=dict, verbose_name='请求头')
    params = models.JSONField(default=dict, verbose_name='查询参数')
    body = models.JSONField(default=dict, verbose_name='请求体')
    auth_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='认证类型')
    auth_config = models.JSONField(default=dict, verbose_name='认证配置')
    # 文件上传支持
    files = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='文件上传配置',
        help_text='格式: {"field_name": {"file_path": "/path/to/file", "content_type": "image/jpeg"}}'
    )
    # 参数化功能
    parameterized_mode = models.CharField(
        max_length=20,
        choices=[
            ('disabled', '禁用'),
            ('enabled', '启用'),
        ],
        default='disabled',
        verbose_name='参数化模式',
        help_text='启用后，接口将使用参数化数据循环执行多次'
    )
    parameterized_data = models.JSONField(
        default=list,
        blank=True,
        verbose_name='参数化数据',
        help_text='格式: [{"param1": "value1"}, {"param1": "value2"}]，每个字典代表一组参数'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '接口'
        verbose_name_plural = '接口'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.method} {self.name}"



