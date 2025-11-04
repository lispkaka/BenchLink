#!/usr/bin/env python
"""检查测试用例配置"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BenchLink.settings')
django.setup()

from apps.testcases.models import TestCase
from apps.testsuites.models import TestSuite

# 查看套件5的配置
suite = TestSuite.objects.filter(id=5).first()
if suite:
    print(f"\n{'='*80}")
    print(f"测试套件: {suite.name} (ID: {suite.id})")
    print(f"{'='*80}")
    
    cases = suite.testcases.all().order_by('id')
    for idx, case in enumerate(cases, 1):
        print(f"\n【用例 {idx}】 {case.name} (ID: {case.id})")
        print(f"  接口: [{case.api.method}] {case.api.name}")
        print(f"  URL覆盖: {case.url_override or '无'}")
        
        print(f"\n  Headers覆盖:")
        if case.headers_override:
            print(f"    {json.dumps(case.headers_override, indent=4, ensure_ascii=False)}")
        else:
            print("    无")
        
        print(f"\n  Body覆盖:")
        if case.body_override:
            print(f"    {json.dumps(case.body_override, indent=4, ensure_ascii=False)}")
        else:
            print("    无")
        
        print(f"\n  后置脚本:")
        if case.post_script:
            for line in case.post_script.split('\n'):
                print(f"    {line}")
        else:
            print("    无")
        
        print(f"\n" + "-"*80)
else:
    print("未找到套件ID 5")

# 查看最近的测试用例
print(f"\n{'='*80}")
print("最近创建的测试用例:")
print(f"{'='*80}")
recent_cases = TestCase.objects.all().order_by('-id')[:5]
for case in recent_cases:
    print(f"\nID: {case.id} - {case.name}")
    print(f"  接口: [{case.api.method}] {case.api.name}")
    if case.post_script:
        print(f"  后置脚本: {case.post_script[:100]}...")
    if case.headers_override:
        print(f"  Headers覆盖: {case.headers_override}")

