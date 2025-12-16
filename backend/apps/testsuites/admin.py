from django.contrib import admin
from .models import TestSuite, TestSuiteTestCase


class TestSuiteTestCaseInline(admin.TabularInline):
    """测试套件-用例关联内联"""
    model = TestSuiteTestCase
    extra = 1
    ordering = ('order',)


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    """测试套件管理"""
    list_display = ('name', 'project', 'environment', 'is_active', 'created_at')
    list_filter = ('is_active', 'project', 'environment', 'created_at')
    search_fields = ('name', 'description')
    inlines = [TestSuiteTestCaseInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'project', 'environment', 'description', 'is_active')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestSuiteTestCase)
class TestSuiteTestCaseAdmin(admin.ModelAdmin):
    """套件用例关联管理"""
    list_display = ('testsuite', 'testcase', 'order', 'created_at')
    list_filter = ('testsuite', 'created_at')
    search_fields = ('testsuite__name', 'testcase__name')
    ordering = ('testsuite', 'order', 'id')

