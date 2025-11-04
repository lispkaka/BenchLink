from django.db import models
from apps.projects.models import Project
from apps.testcases.models import TestCase
from apps.environments.models import Environment


class TestSuiteTestCase(models.Model):
    """测试套件-测试用例关联表（中间表），支持自定义排序"""
    testsuite = models.ForeignKey('TestSuite', on_delete=models.CASCADE, verbose_name='测试套件')
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE, verbose_name='测试用例')
    order = models.IntegerField(default=0, verbose_name='执行顺序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    
    class Meta:
        verbose_name = '套件用例关联'
        verbose_name_plural = '套件用例关联'
        ordering = ['order', 'id']  # 先按order排序，再按id排序
        unique_together = [['testsuite', 'testcase']]  # 同一个套件中不能重复添加同一个用例
    
    def __str__(self):
        return f'{self.testsuite.name} - {self.testcase.name} (顺序: {self.order})'


class TestSuite(models.Model):
    """测试套件模型"""
    name = models.CharField(max_length=200, verbose_name='套件名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testsuites', verbose_name='所属项目')
    testcases = models.ManyToManyField(
        TestCase, 
        through='TestSuiteTestCase',  # 使用自定义中间表
        related_name='testsuites', 
        verbose_name='测试用例'
    )
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='测试环境')
    description = models.TextField(blank=True, null=True, verbose_name='套件描述')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '测试套件'
        verbose_name_plural = '测试套件'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def get_ordered_testcases(self):
        """获取按顺序排列的测试用例"""
        return self.testcases.filter(is_active=True).order_by('testsuitetestcase__order', 'testsuitetestcase__id')



