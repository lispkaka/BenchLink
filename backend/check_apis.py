#!/usr/bin/env python
"""检查数据库中的接口数据"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BenchLink.settings')
django.setup()

from apps.apis.models import API

# 查询所有包含"积分"的接口
apis = API.objects.filter(name__icontains='积分')

print(f"\n找到 {apis.count()} 个包含'积分'的接口：\n")
print(f"{'ID':<6} {'名称':<30} {'方法':<8} {'项目ID':<10} {'项目名称'}")
print("-" * 80)

for api in apis:
    project_name = api.project.name if api.project else "无项目"
    project_id = api.project.id if api.project else "null"
    print(f"{api.id:<6} {api.name:<30} {api.method:<8} {str(project_id):<10} {project_name}")

print("\n" + "="*80)
print("所有接口总数:", API.objects.count())

