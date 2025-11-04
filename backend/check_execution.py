#!/usr/bin/env python
"""检查最近的执行记录"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BenchLink.settings')
django.setup()

from apps.executions.models import Execution

# 查看最近的套件执行记录(ID 126)
print("\n" + "="*80)
print("执行记录 ID 126 (套件执行)")
print("="*80)

suite_exec = Execution.objects.filter(id=126).first()
if suite_exec:
    print(f"\n执行类型: {suite_exec.execution_type}")
    print(f"状态: {suite_exec.status}")
    print(f"\n执行结果概要:")
    result = suite_exec.result or {}
    for key, value in result.items():
        if key not in ['test_results']:  # 跳过详细结果
            print(f"  {key}: {value}")
    
    # 查看子执行记录
    child_execs = Execution.objects.filter(parent=suite_exec).order_by('id')
    print(f"\n子执行记录数: {child_execs.count()}")
    
    for idx, child in enumerate(child_execs, 1):
        print(f"\n{'='*80}")
        print(f"【子执行 {idx}】 测试用例: {child.testcase.name if child.testcase else 'N/A'}")
        print(f"{'='*80}")
        print(f"  状态: {child.status}")
        
        # 从result字段获取详细信息
        result = child.result or {}
        print(f"\n  执行结果:")
        status_code = result.get('status_code')
        if status_code:
            print(f"    状态码: {status_code}")
        
        error = result.get('error')
        if error:
            print(f"    错误: {error}")
        
        headers = result.get('headers', {})
        if 'Authorization' in str(headers):
            print(f"\n  请求中的Authorization头:")
            auth_value = None
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    auth_value = value
                    break
            if auth_value:
                print(f"    {auth_value[:80] if len(str(auth_value)) > 80 else auth_value}...")
            else:
                print("    未找到")
        
        body = result.get('body', '')
        if body:
            print(f"\n  响应体 (前200字符):")
            print(f"    {str(body)[:200]}")

# 也查看单独执行的用例22
print("\n" + "="*80)
print("执行记录 ID 129 (单独执行用例22)")
print("="*80)

single_exec = Execution.objects.filter(id=129).first()
if single_exec:
    print(f"\n测试用例: {single_exec.testcase.name if single_exec.testcase else 'N/A'}")
    print(f"状态: {single_exec.status}")
    
    result = single_exec.result or {}
    print(f"\n执行结果:")
    if result.get('status_code'):
        print(f"  状态码: {result.get('status_code')}")
    if result.get('error'):
        print(f"  错误: {result.get('error')}")
    if result.get('body'):
        print(f"  响应体 (前200字符):")
        print(f"    {str(result.get('body'))[:200]}")

