from django.contrib import admin
from .models import API


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    """接口管理"""
    list_display = ('name', 'method', 'url', 'project', 'parameterized_mode', 'created_at')
    list_filter = ('method', 'parameterized_mode', 'project', 'created_at')
    search_fields = ('name', 'url', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'url', 'method', 'project', 'description')
        }),
        ('请求配置', {
            'fields': ('headers', 'params', 'body', 'files'),
            'classes': ('collapse',)
        }),
        ('认证配置', {
            'fields': ('auth_type', 'auth_config'),
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

