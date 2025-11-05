from django.db import models
from apps.projects.models import Project


class NotificationChannel(models.Model):
    """通知渠道配置"""
    
    CHANNEL_TYPES = [
        ('wecom', '企业微信'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
        ('telegram', 'Telegram'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='渠道名称')
    channel_type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPES,
        verbose_name='渠道类型'
    )
    webhook_url = models.URLField(verbose_name='Webhook URL')
    secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='加签密钥'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notification_channels',
        verbose_name='所属项目'
    )
    
    # 通知规则
    notify_on_success = models.BooleanField(default=False, verbose_name='成功时通知')
    notify_on_failure = models.BooleanField(default=True, verbose_name='失败时通知')
    notify_on_complete = models.BooleanField(default=False, verbose_name='完成时通知')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '通知渠道'
        verbose_name_plural = '通知渠道'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} ({self.get_channel_type_display()})'
