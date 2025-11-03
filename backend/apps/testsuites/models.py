from django.db import models
from apps.projects.models import Project
from apps.testcases.models import TestCase
from apps.environments.models import Environment


class TestSuite(models.Model):
    """测试套件模型"""
    name = models.CharField(max_length=200, verbose_name='套件名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testsuites', verbose_name='所属项目')
    testcases = models.ManyToManyField(TestCase, related_name='testsuites', verbose_name='测试用例')
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



