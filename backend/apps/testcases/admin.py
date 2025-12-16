from django.contrib import admin
from .models import TestCase, PerformanceTest


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """测试用例管理"""
    list_display = ('name', 'project', 'api', 'environment', 'parameterized_mode', 'is_active', 'created_at')
    list_filter = ('is_active', 'parameterized_mode', 'project', 'environment', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'project', 'api', 'environment', 'description', 'is_active')
        }),
        ('脚本配置', {
            'fields': ('pre_script', 'post_script'),
            'classes': ('collapse',)
        }),
        ('断言和变量', {
            'fields': ('assertions', 'variables'),
            'classes': ('collapse',)
        }),
        ('覆盖配置', {
            'fields': ('url_override', 'headers_override', 'params_override', 'body_override', 'files_override'),
            'classes': ('collapse',)
        }),
        ('参数化配置', {
            'fields': ('parameterized_mode', 'parameterized_data'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PerformanceTest)
class PerformanceTestAdmin(admin.ModelAdmin):
    """性能测试管理"""
    list_display = ('name', 'project', 'api', 'threads', 'duration', 'is_active', 'last_execution_time')
    list_filter = ('is_active', 'project', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('last_execution_time', 'created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'project', 'api', 'environment', 'description', 'is_active')
        }),
        ('性能参数', {
            'fields': ('threads', 'ramp_up', 'duration', 'loops')
        }),
        ('JMeter 配置', {
            'fields': ('jmx_file',),
            'classes': ('collapse',)
        }),
        ('执行结果', {
            'fields': ('last_result', 'last_execution_time'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

