from django.db import models
from apps.projects.models import Project


class Environment(models.Model):
    """环境配置模型（配置管理）"""
    name = models.CharField(max_length=100, verbose_name='配置名称')
    base_url = models.URLField(verbose_name='基础URL')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments', verbose_name='所属项目')
    description = models.TextField(blank=True, null=True, verbose_name='配置描述')
    variables = models.JSONField(default=dict, verbose_name='局部变量')
    headers = models.JSONField(default=dict, verbose_name='公共请求头')
    pre_hook = models.TextField(blank=True, null=True, verbose_name='前置钩子函数')
    post_hook = models.TextField(blank=True, null=True, verbose_name='后置钩子函数')
    parameterized_data = models.JSONField(default=list, verbose_name='参数化内容')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '环境配置'
        verbose_name_plural = '环境配置'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class GlobalToken(models.Model):
    """全局 Token 配置模型"""
    AUTH_TYPE_CHOICES = [
        ('bearer', 'Bearer Token'),
        ('drf_token', 'Django REST Framework Token'),
        ('header', '自定义 Header'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Token 名称', help_text='用于标识不同的 Token，如：API Token、登录 Token 等')
    auth_type = models.CharField(
        max_length=20, 
        choices=AUTH_TYPE_CHOICES, 
        default='bearer',
        verbose_name='认证类型'
    )
    token = models.TextField(verbose_name='Token 值', help_text='Token 的实际值，支持变量 ${variable}')
    header_name = models.CharField(
        max_length=100, 
        default='Authorization', 
        verbose_name='Header 名称',
        help_text='当认证类型为自定义 Header 时使用'
    )
    token_format = models.CharField(
        max_length=50, 
        default='Bearer', 
        verbose_name='Token 格式',
        help_text='Token 的前缀，如 Bearer、Token 等，留空则不加前缀'
    )
    description = models.TextField(blank=True, null=True, verbose_name='描述', help_text='说明这个 Token 的用途')
    is_active = models.BooleanField(default=True, verbose_name='是否启用', help_text='启用后，接口未配置认证时会自动使用此 Token')
    is_default = models.BooleanField(default=False, verbose_name='默认 Token', help_text='如果有多个 Token，默认使用此 Token')
    variables = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name='变量配置',
        help_text='如果 Token 值中包含变量，可以在这里配置变量值'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '全局 Token'
        verbose_name_plural = '全局 Token'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_auth_type_display()})"
    
    def save(self, *args, **kwargs):
        # 如果设置为默认，则取消其他 Token 的默认状态
        if self.is_default:
            GlobalToken.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)



