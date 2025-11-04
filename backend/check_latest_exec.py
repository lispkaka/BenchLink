#!/usr/bin/env python
"""检查最新的执行记录"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BenchLink.settings')
django.setup()

from apps.executions.models import Execution

# 查看最新的套件执行
latest_suite = Execution.objects.filter(execution_type='suite').order_by('-created_at').first()

if latest_suite:
    print(f"\n{'='*80}")
    print(f"最新套件执行: ID {latest_suite.id}")
    print(f"{'='*80}")
    
    # 查看子执行
    children = Execution.objects.filter(parent=latest_suite).order_by('id')
    
    for idx, child in enumerate(children, 1):
        print(f"\n【执行 {idx}】{child.testcase.name if child.testcase else 'N/A'}")
        result = child.result or {}
        
        # 检查是否有extracted_variables
        extracted = result.get('extracted_variables', {})
        if extracted:
            print(f"  ✅ 提取的变量:")
            for key, value in extracted.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"    {key}: {value[:50]}...")
                else:
                    print(f"    {key}: {value}")
        else:
            print(f"  ❌ 没有提取到变量")
        
        # 检查响应
        status_code = result.get('status_code')
        body = result.get('body', '')
        if body:
            try:
                body_json = json.loads(body) if isinstance(body, str) else body
                print(f"  响应: code={body_json.get('code')}, msg={body_json.get('msg', '')[:30]}")
            except:
                print(f"  响应: {str(body)[:100]}")
        
        # 检查错误
        error = result.get('error')
        if error:
            print(f"  ❌ 错误: {error}")

