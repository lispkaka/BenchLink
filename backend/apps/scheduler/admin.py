from django.contrib import admin
from .models import ScheduleTask


@admin.register(ScheduleTask)
class ScheduleTaskAdmin(admin.ModelAdmin):
    """定时任务管理"""
    list_display = ('name', 'project', 'testsuite', 'cron_expression', 'status', 'last_run_time', 'next_run_time', 'created_at')
    list_filter = ('status', 'project', 'created_at')
    search_fields = ('name', 'description', 'cron_expression')
    readonly_fields = ('last_run_time', 'next_run_time', 'created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'project', 'testsuite', 'description', 'status')
        }),
        ('定时配置', {
            'fields': ('cron_expression',)
        }),
        ('执行信息', {
            'fields': ('last_run_time', 'next_run_time'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

