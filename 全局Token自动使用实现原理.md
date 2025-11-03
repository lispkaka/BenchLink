# 全局 Token 自动使用实现原理

## 核心设计思想

**"零配置，自动应用"** - 通过智能检测机制，当接口未配置认证时，自动从全局配置中获取 Token 并应用。

## 实现架构

### 1. 执行流程

```
执行测试用例
    ↓
execute() 方法
    ↓
_build_auth() 构建认证信息
    ↓
检查接口配置？
    ├─ 已配置 auth_type → 使用接口配置
    └─ 未配置 → 检查全局 Token
        ├─ 有全局 Token → 自动应用 ✅
        └─ 无全局 Token → 不添加认证
    ↓
_build_headers() 构建请求头
    ↓
添加认证到请求头
    ↓
发送 HTTP 请求
```

### 2. 关键技术实现

#### A. 智能 Token 获取机制

```python
def _get_global_token(self) -> Optional[GlobalToken]:
    """
    获取全局 Token
    优先级策略：
    1. 优先使用标记为"默认"的 Token
    2. 如果没有默认 Token，使用第一个启用的 Token
    """
    try:
        # 第一步：查找默认 Token（优先级最高）
        default_token = GlobalToken.objects.filter(
            is_active=True,      # 必须启用
            is_default=True      # 标记为默认
        ).first()
        
        if default_token:
            return default_token
        
        # 第二步：如果没有默认 Token，获取第一个启用的 Token
        active_token = GlobalToken.objects.filter(
            is_active=True
        ).first()
        
        return active_token
    except Exception:
        return None
```

**设计亮点：**
- ✅ 支持多个 Token 同时存在
- ✅ 通过"默认"标记实现智能选择
- ✅ 异常处理确保系统稳定性

#### B. 优先级控制逻辑

```python
def _build_auth(self) -> Optional[Any]:
    """
    构建认证信息的核心逻辑
    实现了清晰的分层优先级
    """
    # ========== 第一优先级：接口配置的认证 ==========
    if self.api.auth_type:  # 如果接口配置了认证类型
        # 使用接口配置的认证（支持多种类型）
        # ... 处理接口配置的认证 ...
        return auth_from_api_config
    
    # ========== 第二优先级：全局 Token ==========
    # 只有接口未配置认证时，才会执行到这里
    global_token = self._get_global_token()
    if global_token:
        # 1. 获取 Token 值
        token_value = global_token.token
        
        # 2. 合并全局 Token 的变量到执行器变量中
        #    这样 Token 值中的 ${variable} 可以被替换
        if global_token.variables:
            for key, value in global_token.variables.items():
                if key not in self.variables:
                    self.variables[key] = value
        
        # 3. 替换 Token 值中的变量
        token_value = self._replace_variables(token_value)
        
        # 4. 根据全局 Token 的认证类型返回不同格式
        if global_token.auth_type == 'bearer':
            return ('Bearer', token_value)
        elif global_token.auth_type == 'drf_token':
            return ('Token', token_value)
        elif global_token.auth_type == 'header':
            # Header 类型在 _build_headers 中处理
            return None
    
    # ========== 第三优先级：无认证 ==========
    return None
```

**设计亮点：**
- ✅ 清晰的优先级控制，接口配置永远优先
- ✅ 支持变量替换，Token 值可以使用 `${variable}` 动态获取
- ✅ 多种认证类型支持（Bearer、DRF Token、自定义 Header）

#### C. 认证信息注入到请求头

```python
def execute(self) -> Dict[str, Any]:
    """执行测试用例的主流程"""
    # 1. 构建 URL、Headers、Params、Body 等
    url = self._build_url()
    headers = self._build_headers()
    params = ...
    body = ...
    
    # 2. 构建认证信息（关键步骤）
    auth = self._build_auth()  # 这里会调用上面的逻辑
    
    # 3. 将认证信息注入到请求头
    if auth:
        if isinstance(auth, tuple) and len(auth) == 2:
            if auth[0] == 'Bearer':
                # Bearer Token: Authorization: Bearer <token>
                headers['Authorization'] = f'Bearer {auth[1]}'
            elif auth[0] == 'Token':
                # DRF Token: Authorization: Token <token>
                headers['Authorization'] = f'Token {auth[1]}'
            else:
                # Basic Auth 使用 requests 的 auth 参数
                request_kwargs['auth'] = auth
    
    # 4. 处理全局 Token 的 Header 类型
    if not self.api.auth_type:  # 只有接口未配置认证时才处理
        global_token = self._get_global_token()
        if global_token and global_token.auth_type == 'header':
            # 自定义 Header 格式
            headers[header_name] = f'{format} {token}'
    
    # 5. 发送 HTTP 请求
    response = session.request(method=method, url=url, headers=headers, ...)
```

## 技术优势

### 1. 零侵入设计
- ✅ 接口模型无需修改
- ✅ 现有接口无需重新配置
- ✅ 向后兼容，不影响已有功能

### 2. 智能降级
```
接口配置了认证 → 使用接口配置
    ↓
接口未配置认证 → 自动使用全局 Token
    ↓
全局 Token 不存在 → 不添加认证（正常请求）
```

### 3. 变量系统集成
- 全局 Token 的 Token 值支持 `${variable}` 变量
- 可以从环境变量、用例变量中获取动态值
- 实现了 Token 的动态化配置

### 4. 多 Token 管理
- 支持创建多个全局 Token
- 通过"默认"标记控制优先级
- 支持启用/停用，灵活控制

## 使用场景示例

### 场景 1：所有接口使用同一个 Token

**配置：**
1. 创建全局 Token：`生产环境 Token`，设为默认并启用

**执行：**
- 接口 A（未配置认证）→ 自动使用全局 Token ✅
- 接口 B（未配置认证）→ 自动使用全局 Token ✅
- 接口 C（已配置认证）→ 使用接口配置的认证 ✅

### 场景 2：不同环境使用不同 Token

**配置：**
1. 全局 Token：`Token 值 = ${env_token}`（使用变量）
2. 环境 A：`variables = {"env_token": "token-for-env-a"}`
3. 环境 B：`variables = {"env_token": "token-for-env-b"}`

**执行：**
- 在环境 A 执行 → 使用 `token-for-env-a`
- 在环境 B 执行 → 使用 `token-for-env-b`

### 场景 3：混合使用

**配置：**
- 全局 Token：`通用 API Token`（默认）
- 接口 A：未配置认证 → 使用全局 Token
- 接口 B：配置了特殊认证 → 使用接口配置

## 实现细节

### 数据库查询优化

```python
# 使用 Django ORM 的 first() 方法，只查询一条记录
# 查询会自动添加 LIMIT 1，性能优化
default_token = GlobalToken.objects.filter(
    is_active=True,
    is_default=True
).first()  # 只返回第一条，不加载所有数据
```

### 变量替换机制

```python
def _replace_variables(self, text: str) -> str:
    """
    变量替换支持多层优先级：
    1. executor.variables（执行器动态变量）
    2. testcase.variables（用例变量）
    3. environment.variables（环境变量）
    """
    # 合并所有变量源
    all_vars = {}
    if self.environment:
        all_vars.update(self.environment.variables or {})
    all_vars.update(self.testcase.variables or {})
    all_vars.update(self.variables or {})  # 执行器变量优先级最高
    
    # 使用正则表达式替换 ${variable}
    return re.sub(r'\$\{(\w+)\}', lambda m: str(all_vars.get(m.group(1), m.group(0))), text)
```

### 异常处理

```python
try:
    # 尝试获取全局 Token
    global_token = self._get_global_token()
except Exception:
    # 即使数据库查询失败，也不影响测试执行
    # 只是不使用全局 Token，继续正常流程
    return None
```

## 总结

全局 Token 自动使用机制的核心在于：

1. **智能检测** - 自动判断接口是否配置了认证
2. **优雅降级** - 多层级的优先级控制
3. **零配置** - 用户无需为每个接口单独配置
4. **灵活性** - 支持多种认证类型和变量替换
5. **稳定性** - 完善的异常处理，不影响现有功能

这是一个典型的"约定优于配置"（Convention over Configuration）设计模式的应用！

