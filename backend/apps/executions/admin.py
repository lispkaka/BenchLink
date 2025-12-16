from django.contrib import admin
from .models import Execution


@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    """测试执行记录管理"""
    list_display = ('name', 'project', 'execution_type', 'status', 'executor', 'duration', 'start_time', 'created_at')
    list_filter = ('status', 'execution_type', 'project', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'project', 'execution_type', 'status', 'executor')
        }),
        ('关联信息', {
            'fields': ('testsuite', 'testcase', 'parent')
        }),
        ('执行信息', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('执行结果', {
            'fields': ('result',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """优化查询，减少数据库访问"""
        qs = super().get_queryset(request)
        return qs.select_related('project', 'testsuite', 'testcase', 'executor', 'parent')

