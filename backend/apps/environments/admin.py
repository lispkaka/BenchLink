from django.contrib import admin
from .models import Environment, GlobalToken


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    """环境配置管理"""
    list_display = ('name', 'project', 'base_url', 'is_active', 'created_at')
    list_filter = ('is_active', 'project', 'created_at')
    search_fields = ('name', 'base_url', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'project', 'base_url', 'description', 'is_active')
        }),
        ('配置项', {
            'fields': ('variables', 'headers'),
            'classes': ('collapse',)
        }),
        ('钩子函数', {
            'fields': ('pre_hook', 'post_hook'),
            'classes': ('collapse',)
        }),
        ('参数化数据', {
            'fields': ('parameterized_data',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GlobalToken)
class GlobalTokenAdmin(admin.ModelAdmin):
    """全局 Token 管理"""
    list_display = ('name', 'auth_type', 'is_default', 'is_active', 'created_at')
    list_filter = ('auth_type', 'is_default', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'is_active', 'is_default')
        }),
        ('认证配置', {
            'fields': ('auth_type', 'token', 'header_name', 'token_format')
        }),
        ('变量配置', {
            'fields': ('variables',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

