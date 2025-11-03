# 方案A对参数化功能的支持说明

## 回答：方案A完全符合参数化功能要求！

### 一、参数化功能需求

您提到的"单个接口实现参数化功能"，通常是指：
- 同一个接口用不同的参数值执行多次
- 例如：测试 `/posts/1`, `/posts/2`, `/posts/3` 三个不同ID的文章

### 二、方案A如何支持参数化

#### 方式1：API定义使用占位符 + 参数化数据（推荐）

```python
# API 模型定义
{
    "name": "获取文章详情",
    "method": "GET",
    "url": "/posts/${post_id}",  # 使用变量占位符
    "parameterized_mode": "enabled",
    "parameterized_data": [
        {"post_id": 1},
        {"post_id": 2},
        {"post_id": 3}
    ]
}

# 单独测试（非参数化）：使用默认值 post_id=1 → /posts/1
# 参数化测试：循环执行3次
#   第1次：/posts/1
#   第2次：/posts/2
#   第3次：/posts/3
```

#### 方式2：API定义使用原始值 + 参数化覆盖

```python
# API 模型定义
{
    "name": "获取文章详情",
    "method": "GET",
    "url": "/posts/1",  # 原始值（示例）
    "parameterized_mode": "enabled",
    "parameterized_data": [
        {"post_id": 1},
        {"post_id": 2},
        {"post_id": 3}
    ],
    "parameterized_url_template": "/posts/${post_id}"  # 参数化时使用的模板
}

# 单独测试：使用原始值 /posts/1
# 参数化测试：使用模板 /posts/${post_id} + 参数数据
```

### 三、参数化数据来源（三种方式）

1. **API自身定义**：`API.parameterized_data`
2. **环境配置提供**：`Environment.parameterized_data`（已有字段）
3. **执行时临时传入**：前端调用时传入参数化数据

### 四、实现细节

#### API 模型新增字段

```python
class API(models.Model):
    # ... 现有字段 ...
    
    # 参数化数据
    parameterized_data = models.JSONField(
        default=list,
        verbose_name='参数化数据',
        help_text='格式: [{"param1": "value1"}, {"param1": "value2"}]'
    )
    
    # 参数化模式
    parameterized_mode = models.CharField(
        max_length=20,
        choices=[('disabled', '禁用'), ('enabled', '启用')],
        default='disabled',
        verbose_name='参数化模式'
    )
```

#### APIViewSet.execute 方法改造

```python
@action(detail=True, methods=['post'])
def execute(self, request, pk=None):
    api_instance = self.get_object()
    variables = request.data.get('variables', {})
    
    # 检查参数化模式
    if api_instance.parameterized_mode == 'enabled':
        param_data = (
            request.data.get('parameterized_data') or  # 优先使用临时传入的
            api_instance.parameterized_data  # 其次使用API定义的
        )
        
        if param_data:
            # 参数化执行：循环多次
            results = []
            for param_set in param_data:
                # 合并变量：临时变量 + 参数化数据
                merged_vars = {**variables, **param_set}
                result = self._execute_single_request(api_instance, merged_vars)
                results.append(result)
            
            return Response({
                'parameterized': True,
                'total': len(results),
                'passed': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success']),
                'results': results
            })
    
    # 普通执行：单次
    result = self._execute_single_request(api_instance, variables)
    return Response(result)
```

### 五、优势总结

✅ **完全支持参数化**：API可以独立进行参数化测试
✅ **多种数据来源**：API定义、环境配置、临时传入
✅ **灵活切换**：可以启用/禁用参数化模式
✅ **结果统计**：自动统计通过/失败数量
✅ **兼容用例参数化**：测试用例层面也支持参数化

### 六、与HttpRunner对比

**HttpRunner的参数化：**
```yaml
parameters:
  post_id: [1, 2, 3]
```

**方案A的参数化（等价实现）：**
```python
parameterized_data: [
    {"post_id": 1},
    {"post_id": 2},
    {"post_id": 3}
]
```

**结论：方案A的参数化方式与HttpRunner完全一致，且更灵活！**

---

## 总结

**问题：方案A是否符合参数化功能要求？**

**答案：完全符合！✅**

方案A不仅支持参数化，而且：
1. 支持API层面的参数化（单个接口批量测试）
2. 支持用例层面的参数化（用例批量执行）
3. 支持环境层面的参数化（全局参数化数据）
4. 实现方式与HttpRunner/LunarLink一致
5. 提供多种参数化数据来源，使用灵活

