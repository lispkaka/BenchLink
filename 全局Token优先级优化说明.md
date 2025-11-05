# 全局Token优先级优化说明

## 问题背景

### 原有设计的问题

1. **全局Token会覆盖测试套件中的动态Token**
   - 全局Token在执行器初始化时注入到`variables['token']`
   - 测试套件中登录接口提取的动态Token也会更新到`variables['token']`
   - 但在构建认证时，直接使用全局Token的静态值，忽略了动态Token

2. **测试套件执行失败**
   - 即使登录成功获取了新Token
   - 后续接口仍然使用全局Token的旧值
   - 导致所有接口返回401（Token过期）

3. **违背全局Token的便利性**
   - 为了使用动态Token，需要在每个接口配置`headers_override`
   - 这样就失去了全局Token"零配置"的优势

## 优化方案

### 核心思想：**动态Token优先于全局Token**

```
Token优先级（从高到低）：
1. 接口配置的auth_type（明确配置）
2. 动态Token（从测试套件中前置用例提取）⭐ 新增
3. 全局Token（静态配置）
4. 无认证
```

### 实现逻辑

#### 1. 初始化时保留全局Token的静态值

```python
# executor.py __init__方法
global_token = self._get_global_token()
if global_token:
    if global_token.variables:
        self.variables.update(global_token.variables)
    # 将全局Token保存为特殊变量，不直接注入到'token'
    if global_token.token:
        self.variables['_global_token_static'] = global_token.token
```

**改进点：**
- ✅ 不再直接注入到`variables['token']`
- ✅ 使用`_global_token_static`保存全局Token的静态值
- ✅ 为动态Token留出空间

#### 2. 构建认证时优先使用动态Token

```python
# executor.py _build_auth方法
# 如果接口未配置认证，尝试使用Token
dynamic_token = self.variables.get('token')
global_token_static = self.variables.get('_global_token_static')

# 优先使用动态Token（从测试套件中提取的）
if dynamic_token and dynamic_token != global_token_static:
    # 使用动态Token ⭐
    token_value = self._replace_variables(str(dynamic_token))
    # 使用全局Token配置的认证类型
    global_token = self._get_global_token()
    if global_token:
        if global_token.auth_type == 'bearer':
            return ('Bearer', token_value)
        elif global_token.auth_type == 'drf_token':
            return ('Token', token_value)
    else:
        return ('Bearer', token_value)  # 默认Bearer

# 如果没有动态Token，使用全局Token的静态值
global_token = self._get_global_token()
if global_token:
    token_value = global_token.token
    token_value = self._replace_variables(token_value)
    if global_token.auth_type == 'bearer':
        return ('Bearer', token_value)
    elif global_token.auth_type == 'drf_token':
        return ('Token', token_value)
```

**改进点：**
- ✅ 判断`variables['token']`是否存在且与全局Token不同
- ✅ 如果是动态Token，优先使用
- ✅ 如果没有动态Token，回退到全局Token

#### 3. 配置登录用例的变量提取器

```python
# 登录用例的variables配置
{
  "extractors": {
    "token": "$.data.accessToken",  # 提取到token变量
    "user_id": "$.data.userId"
  }
}
```

**改进点：**
- ✅ 从登录响应中提取accessToken到`token`变量
- ✅ 测试套件执行时会自动传递给后续用例

## 使用场景

### 场景1：单独执行测试用例（使用全局Token）

```
执行流程：
1. 初始化执行器
   - variables['_global_token_static'] = 全局Token静态值
   - variables['token'] 为空

2. 构建认证
   - variables['token']不存在
   - 使用variables['_global_token_static']（全局Token）

3. 发送请求
   - Authorization: Bearer <全局Token>
```

**结果：** ✅ 使用全局Token，无需任何配置

### 场景2：测试套件执行（使用动态Token）

```
执行流程：
1. 执行登录用例
   - 初始化：variables['_global_token_static'] = 全局Token静态值
   - 登录成功：提取variables['token'] = 新Token（动态）
   - shared_variables['token'] = 新Token

2. 执行后续用例
   - 初始化：variables['_global_token_static'] = 全局Token静态值
   - 更新：executor.variables.update(shared_variables)
            → variables['token'] = 新Token（从登录用例传递）
   
3. 构建认证
   - variables['token']存在且与_global_token_static不同
   - 使用variables['token']（动态Token，优先级高）

4. 发送请求
   - Authorization: Bearer <动态Token>
```

**结果：** ✅ 使用动态Token，自动覆盖全局Token

### 场景3：禁用全局Token（完全动态）

```
执行流程：
1. 全局Token设置为未启用（is_active=False）
   - variables['_global_token_static'] 不会注入

2. 执行测试套件
   - 登录用例提取variables['token'] = 新Token
   - 后续用例使用动态Token

3. 构建认证
   - variables['token']存在
   - 使用variables['token']（动态Token）

4. 发送请求
   - Authorization: Bearer <动态Token>
```

**结果：** ✅ 纯动态Token，不依赖全局Token

## 优势总结

### 1. 智能优先级
- ✅ 单独执行用例：自动使用全局Token（便捷）
- ✅ 测试套件执行：自动使用动态Token（准确）
- ✅ 无需手动配置headers_override

### 2. 零配置
- ✅ 接口不需要配置认证
- ✅ 测试用例不需要配置headers_override
- ✅ 只需要配置登录用例的变量提取器

### 3. 灵活性
- ✅ 支持全局Token作为默认值
- ✅ 支持测试套件中动态获取Token
- ✅ 支持接口级别的认证覆盖

### 4. 向后兼容
- ✅ 不影响现有接口
- ✅ 不影响现有测试用例
- ✅ 渐进式优化

## 最佳实践

### 1. 全局Token配置
- 用途：快速测试、单个接口调试
- 配置：设置默认Token，启用
- 场景：开发调试时使用

### 2. 测试套件配置
- 用途：完整流程测试、持续集成
- 配置：
  - 第一个用例：登录接口，配置变量提取器
  - 后续用例：不配置认证，自动使用动态Token
- 场景：正式测试时使用

### 3. 登录用例配置示例

```json
{
  "name": "登录",
  "variables": {
    "extractors": {
      "token": "$.data.accessToken",
      "refresh_token": "$.data.refreshToken",
      "user_id": "$.data.userId"
    }
  }
}
```

### 4. 测试套件配置示例

```
测试套件：用户管理流程
├── 1. 登录接口 （提取token）
├── 2. 获取用户信息 （使用动态token）⭐
├── 3. 更新用户信息 （使用动态token）⭐
└── 4. 退出登录 （使用动态token）⭐
```

**所有接口都不需要配置认证，自动使用动态Token！**

## 技术细节

### Token识别逻辑

```python
# 判断是否为动态Token
if variables['token'] != variables['_global_token_static']:
    # 动态Token（优先使用）
else:
    # 全局Token或无Token
```

### 变量传递机制

```python
# 测试套件执行时（testsuites/views.py）
shared_variables = {}  # 共享变量池

for testcase in testcases:
    executor = TestCaseExecutor(testcase, environment)
    executor.variables.update(shared_variables)  # 注入前置用例的变量
    
    result = executor.execute()
    
    extracted_vars = result.get('extracted_variables', {})
    shared_variables.update(extracted_vars)  # 保存到共享变量池
```

### 认证类型继承

动态Token会继承全局Token的认证类型配置：
- 全局Token配置：`auth_type = 'bearer'`
- 动态Token使用：`Bearer <动态Token值>`

如果没有全局Token配置，默认使用`Bearer`类型。

## 问题解答

### Q1: 全局Token会影响测试套件吗？

**A:** 不会！优化后，测试套件中的动态Token优先级更高，会自动覆盖全局Token。

### Q2: 需要手动配置headers_override吗？

**A:** 不需要！只要配置好登录用例的变量提取器，后续接口会自动使用动态Token。

### Q3: 单独执行接口时还能用全局Token吗？

**A:** 可以！单独执行时没有动态Token，会自动使用全局Token。

### Q4: 如何禁用全局Token？

**A:** 将全局Token设置为未启用（is_active=False），或者删除全局Token配置。

### Q5: 动态Token过期怎么办？

**A:** 测试套件每次执行都会先执行登录用例，获取最新的Token，不会有过期问题。

## 总结

这次优化实现了**智能Token管理**：
- 🎯 单独执行：便捷（全局Token）
- 🎯 套件执行：准确（动态Token）
- 🎯 零配置：简单（自动选择）

**真正实现了"零配置，自动应用"的设计理念！** 🚀


