from django.contrib import admin
from .models import NotificationChannel


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """通知渠道管理"""
    list_display = ('name', 'channel_type', 'project', 'is_active', 'notify_on_success', 'notify_on_failure', 'notify_on_complete', 'created_at')
    list_filter = ('channel_type', 'is_active', 'project', 'created_at')
    search_fields = ('name', 'webhook_url')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'channel_type', 'project', 'is_active')
        }),
        ('Webhook 配置', {
            'fields': ('webhook_url', 'secret')
        }),
        ('通知规则', {
            'fields': ('notify_on_success', 'notify_on_failure', 'notify_on_complete')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
