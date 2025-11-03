# 自动化测试平台 - Token 认证使用说明

## 概述

在自动化测试平台中，为被测接口配置 Token 认证有几种方式：

1. **全局 Token 配置（推荐）** - 在配置管理页面设置全局 Token，所有未配置认证的接口自动使用
2. **接口级别配置** - 在接口定义时配置认证信息（优先级高于全局 Token）
3. **环境级别配置** - 在环境配置中设置公共请求头和变量
4. **动态 Token 获取** - 通过前置脚本登录获取 Token

## 优先级说明

认证信息的优先级（从高到低）：
1. **接口配置的认证** - 如果接口配置了 `auth_type`，优先使用接口配置
2. **全局 Token** - 如果接口未配置认证，自动使用全局 Token（如果已启用）
3. **环境变量/用例变量** - 在接口认证配置中使用 `${variable}` 时从变量中获取

**重要：如果接口配置了认证，全局 Token 不会生效，需要清空接口的认证配置才能使用全局 Token。**

## 认证方式

### 1. Bearer Token 认证

适用于大多数现代 API，格式：`Authorization: Bearer <token>`

**配置方式：**
```json
{
  "auth_type": "bearer",
  "auth_config": {
    "token": "your-token-here"
  }
}
```

**使用变量：**
```json
{
  "auth_type": "bearer",
  "auth_config": {
    "token": "${token}"
  }
}
```
Token 可以从环境变量、用例变量或前置脚本中获取。

### 2. Django REST Framework Token 认证

适用于 Django REST Framework，格式：`Authorization: Token <token>`

**配置方式：**
```json
{
  "auth_type": "drf_token",
  "auth_config": {
    "token": "your-token-here"
  }
}
```

### 3. Basic Auth 认证

传统的用户名密码认证

**配置方式：**
```json
{
  "auth_type": "basic",
  "auth_config": {
    "username": "user",
    "password": "pass"
  }
}
```

### 4. 自定义 Header Token

通过自定义 Header 传递 Token

**配置方式：**
```json
{
  "auth_type": "header",
  "auth_config": {
    "header_name": "Authorization",
    "format": "Bearer",
    "token": "${token}"
  }
}
```

## 全局 Token 使用（最简单的方式）

### 优势

✅ **无需为每个接口单独配置** - 配置一次，所有接口自动使用  
✅ **统一管理** - 集中管理所有 Token，方便更新和维护  
✅ **自动应用** - 接口执行时自动应用，无需额外操作

### 使用步骤

#### 1. 创建全局 Token

1. 访问 **配置管理** 页面
2. 切换到 **全局 Token** 标签
3. 点击 **新建 Token** 按钮
4. 填写信息：
   - **Token 名称**：如 "API Token"、"登录 Token"
   - **认证类型**：选择 Bearer Token、DRF Token 或自定义 Header
   - **Token 值**：输入实际的 Token 值
   - **是否启用**：勾选后才会自动应用
   - **设为默认 Token**：如果有多个 Token，可以选择一个默认的

#### 2. 使用全局 Token

**无需任何额外配置！**

- 创建接口时，**不配置** `auth_type` 和 `auth_config`
- 执行测试用例时，系统会自动使用全局 Token
- 如果接口已经配置了认证，全局 Token 不会覆盖

#### 3. 示例场景

**场景 A：所有接口使用同一个 Token**

1. 创建全局 Token：
   - 名称：`生产环境 API Token`
   - 认证类型：`Bearer Token`
   - Token 值：`your-production-token-here`
   - ✅ 启用
   - ✅ 设为默认

2. 创建接口时：
   - 不填写 "认证类型"
   - 不填写 "认证配置"
   - 直接保存

3. 执行测试用例时：
   - 系统自动在所有请求头中添加：`Authorization: Bearer your-production-token-here`

**场景 B：不同接口使用不同 Token**

1. 创建多个全局 Token：
   - Token A：`用户服务 Token`（设为默认）
   - Token B：`订单服务 Token`

2. 对于需要使用默认 Token 的接口：
   - 不配置认证，自动使用 Token A

3. 对于需要使用特定 Token 的接口：
   - 在接口的认证配置中手动指定，或
   - 在环境变量中配置不同的 Token 值

#### 4. 全局 Token 的变量支持

全局 Token 的 Token 值也支持变量替换：

**示例：使用环境变量**
1. 在全局 Token 中设置：`Token 值 = ${api_token}`
2. 在环境配置的 `variables` 中设置：
```json
{
  "api_token": "actual-token-value"
}
```

这样不同环境可以使用不同的 Token，但全局 Token 配置保持不变。

## 动态 Token 获取

### 方式一：前置脚本获取 Token

在测试用例的 **前置脚本** 中登录并提取 Token：

**示例：登录接口获取 Token**

1. **创建登录测试用例**（用于获取 Token）
   - 接口：POST `/api/login`
   - 请求体：`{"username": "test", "password": "123456"}`
   - 响应体：`{"token": "abc123...", "user": {...}}`

2. **配置变量提取器**（在用例的 `variables.extractors` 中）：
```json
{
  "extractors": {
    "token": "$.token",
    "user_id": "$.user.id"
  }
}
```

3. **在被测接口中使用 Token**
   - 在接口配置中设置：
   ```json
   {
     "auth_type": "bearer",
     "auth_config": {
       "token": "${token}"
     }
   }
   ```

### 方式二：环境变量中配置

在环境配置的 `variables` 中设置 Token：

```json
{
  "variables": {
    "token": "your-static-token",
    "base_url": "https://api.example.com"
  }
}
```

然后在接口配置中使用 `${token}`。

### 方式三：用例变量中配置

在测试用例的 `variables` 中设置：

```json
{
  "variables": {
    "token": "your-token",
    "user_id": "123"
  }
}
```

## 完整示例：登录后调用接口

### 步骤 1：创建登录接口

**接口定义：**
- 名称：用户登录
- URL：`/api/users/login`
- 方法：POST
- 请求体：
```json
{
  "username": "testuser",
  "password": "testpass"
}
```

### 步骤 2：创建登录测试用例

**用例配置：**
- 名称：获取登录 Token
- 关联接口：选择上面的登录接口
- 变量提取器（在 `variables.extractors` 中）：
```json
{
  "extractors": {
    "token": "$.token",
    "refresh_token": "$.refresh_token"
  }
}
```

### 步骤 3：创建需要认证的接口

**接口定义：**
- 名称：获取用户信息
- URL：`/api/users/me`
- 方法：GET
- 认证配置：
```json
{
  "auth_type": "bearer",
  "auth_config": {
    "token": "${token}"
  }
}
```

### 步骤 4：创建测试套件（TestSuite）

在测试套件中按顺序执行：
1. 先执行"获取登录 Token"用例
2. 再执行"获取用户信息"用例

这样第二个用例就能自动使用第一个用例提取的 Token。

## 常见问题

### Q: Token 过期怎么办？

A: 可以在前置脚本中检查 Token 是否过期，如果过期则重新登录获取新的 Token。

**前置脚本示例：**
```python
# 检查 token 是否过期（示例，需要根据实际情况调整）
token = get_variable('token')
if not token:
    # Token 不存在，需要登录
    # 这里可以通过执行登录接口获取 token
    set_variable('token', 'new-token-from-login')
```

### Q: 如何在请求头中直接添加 Token？

A: 使用 `headers_override` 或环境的 `headers` 配置：

```json
{
  "headers": {
    "Authorization": "Bearer ${token}",
    "X-Api-Key": "${api_key}"
  }
}
```

### Q: 多个接口需要不同的 Token 怎么办？

A: 可以在不同的环境配置中设置不同的 Token，或使用不同的变量名（如 `token1`, `token2`）。

## 变量优先级

变量查找顺序（从高到低）：
1. 执行器动态变量（`executor.variables`）- 参数化数据、前置脚本设置的变量
2. 用例变量（`testcase.variables`）
3. 环境变量（`environment.variables`）

如果在多个地方定义了同名变量，优先级高的会覆盖优先级低的。

## Token 自动查找

如果 `auth_config` 中没有配置 `token`，系统会自动尝试从变量中获取：
1. `token`
2. `access_token`

这样可以简化配置，只需要在变量中设置 token，接口会自动使用。

