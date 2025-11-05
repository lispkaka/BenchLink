# 全局Token使用指南（优化版）

## 🎯 快速开始

### 1. 配置全局Token（用于快速调试）

**操作步骤：**
1. 进入**设置** → **全局Token**
2. 点击**新建Token**
3. 填写配置：
   - **Token名称**：例如"默认Token"
   - **认证类型**：选择`Bearer Token`
   - **Token值**：粘贴你的Token
   - ✅ 勾选**是否启用**
   - ✅ 勾选**设为默认Token**
4. 保存

**结果：** 所有未配置认证的接口将自动使用这个Token ✨

### 2. 配置登录用例（用于测试套件）

**操作步骤：**
1. 创建或编辑登录接口的测试用例
2. 在用例的**变量配置**中添加提取器：
```json
{
  "extractors": {
    "token": "$.data.accessToken"
  }
}
```
3. 保存

**说明：** `$.data.accessToken`是JSON路径，根据你的登录接口响应结构调整

### 3. 创建测试套件

**操作步骤：**
1. 创建测试套件，例如"用户管理流程"
2. 添加测试用例，按执行顺序：
   - **第1个用例**：登录接口（会提取token）
   - **第2个用例**：获取用户信息
   - **第3个用例**：更新用户信息
   - ...更多用例
3. 保存

**重要：** 所有接口都不需要配置认证，系统会自动处理！

## 📋 使用场景

### 场景A：单独调试接口

**适用：** 快速测试单个接口

**步骤：**
1. 配置全局Token（一次配置，永久使用）
2. 在接口列表中点击"执行"按钮

**效果：**
- ✅ 自动使用全局Token
- ✅ 无需任何额外配置
- ✅ 适合开发调试

**示例：**
```
接口：获取用户信息
auth_type: 未配置
↓
系统自动添加：
Authorization: Bearer <全局Token>
```

### 场景B：执行测试套件

**适用：** 完整流程测试、持续集成

**步骤：**
1. 配置登录用例的变量提取器（一次配置）
2. 在测试套件中执行

**效果：**
- ✅ 登录接口提取最新Token
- ✅ 后续接口自动使用最新Token
- ✅ Token永远不会过期
- ✅ 适合正式测试

**示例：**
```
测试套件：用户管理流程
├── 1. 登录 → 提取token（动态）
├── 2. 获取用户信息 → 使用动态token ✅
├── 3. 更新用户信息 → 使用动态token ✅
└── 4. 退出登录 → 使用动态token ✅
```

## 🔄 Token优先级（重要）

系统自动按以下优先级选择Token：

```
1. 接口配置的auth_type（最高优先级）
   ↓ 如果接口未配置认证
2. 动态Token（从测试套件中登录接口提取）
   ↓ 如果没有动态Token
3. 全局Token（配置管理中设置的）
   ↓ 如果没有全局Token
4. 无认证
```

### 优先级示例

**情况1：单独执行接口**
```
variables['token'] = 不存在
↓
使用全局Token
```

**情况2：测试套件执行**
```
登录用例提取：variables['token'] = 新Token（动态）
↓
后续用例使用：动态Token（优先级更高）
```

**情况3：接口明确配置了认证**
```
接口auth_type = 'bearer'
↓
使用接口配置的认证（忽略全局Token和动态Token）
```

## ✅ 最佳实践

### 1. 全局Token的用途

**推荐用法：** 开发调试、快速测试
- ✅ 方便：单独执行接口时自动使用
- ✅ 简单：配置一次，处处使用
- ❌ 注意：Token可能过期，需要手动更新

**配置建议：**
```
Token名称：开发环境Token
认证类型：Bearer Token
是否启用：✅
设为默认：✅
```

### 2. 测试套件的用途

**推荐用法：** 完整流程测试、自动化测试
- ✅ 可靠：每次执行都获取最新Token
- ✅ 真实：模拟真实用户流程
- ✅ 自动：无需手动更新Token

**配置建议：**
```
第一个用例：登录
variables:
  extractors:
    token: $.data.accessToken
    user_id: $.data.userId

后续用例：无需配置认证，自动使用动态Token
```

### 3. 混合使用策略

**开发阶段：**
- 配置全局Token
- 快速调试单个接口

**测试阶段：**
- 创建测试套件
- 包含登录用例
- 执行完整流程

**持续集成：**
- 只使用测试套件
- 可以禁用全局Token
- 保证测试准确性

## 🔧 常见配置

### 登录接口响应格式与提取器配置

#### 格式1：嵌套在data中
```json
{
  "code": 200,
  "data": {
    "accessToken": "eyJhbGc...",
    "userId": 12345
  }
}
```
**提取器配置：**
```json
{
  "extractors": {
    "token": "$.data.accessToken",
    "user_id": "$.data.userId"
  }
}
```

#### 格式2：在根级别
```json
{
  "code": 200,
  "token": "eyJhbGc...",
  "user": {
    "id": 12345
  }
}
```
**提取器配置：**
```json
{
  "extractors": {
    "token": "$.token",
    "user_id": "$.user.id"
  }
}
```

#### 格式3：不同的字段名
```json
{
  "success": true,
  "result": {
    "jwt": "eyJhbGc...",
    "refresh_token": "..."
  }
}
```
**提取器配置：**
```json
{
  "extractors": {
    "token": "$.result.jwt",
    "refresh_token": "$.result.refresh_token"
  }
}
```

## ❓ 常见问题

### Q1: 我配置了全局Token，为什么还返回401？

**A:** 可能的原因：
1. ✅ 检查全局Token是否**启用**
2. ✅ 检查Token是否**过期**（重新获取）
3. ✅ 检查接口是否需要**签名**（如X-Sign）

**解决方案：**
- 重新执行登录接口获取新Token
- 或执行测试套件（自动获取最新Token）

### Q2: 测试套件执行时，为什么所有接口都返回401？

**A:** 可能的原因：
1. ❌ 登录用例未配置变量提取器
2. ❌ 提取器的JSON路径不正确
3. ❌ 登录接口本身失败了

**排查步骤：**
1. 单独执行登录用例，查看响应
2. 检查variables配置中是否有extractors
3. 确认JSON路径与响应结构匹配

**正确配置示例：**
```json
{
  "extractors": {
    "token": "$.data.accessToken"
  }
}
```

### Q3: 如何知道使用的是全局Token还是动态Token？

**A:** 查看执行结果中的`extracted_variables`：

```json
{
  "extracted_variables": {
    "token": "eyJhbGc...",  // 这是当前使用的Token
    "_global_token_static": "..."  // 这是全局Token的值
  }
}
```

- 如果`token`与`_global_token_static`相同 → 使用全局Token
- 如果`token`与`_global_token_static`不同 → 使用动态Token

### Q4: 我不想用全局Token，只想用动态Token怎么办？

**A:** 两种方式：
1. **禁用全局Token**：在全局Token配置中取消勾选"是否启用"
2. **删除全局Token**：直接删除全局Token配置

**结果：** 只在测试套件执行时使用动态Token

### Q5: 接口需要签名（如X-Sign），怎么配置？

**A:** 在环境配置的**前置钩子**中生成签名：

```python
# 环境前置钩子示例
import hmac
import hashlib
import time
import uuid

# 生成签名所需的参数
x_time = str(int(time.time() * 1000))
x_nonce = str(uuid.uuid4())

# 计算签名
sign_str = f"METHOD:{method}PATH:{path}TIME:{x_time}NONCE:{x_nonce}"
x_sign = hmac.new(SECRET_KEY.encode(), sign_str.encode(), hashlib.sha256).hexdigest()

# 设置变量
set_variable('x_sign', x_sign)
set_variable('x_time', x_time)
set_variable('x_nonce', x_nonce)
```

然后在接口headers中使用：
```json
{
  "X-Sign": "${x_sign}",
  "X-Time": "${x_time}",
  "X-Nonce": "${x_nonce}"
}
```

### Q6: 多个环境怎么管理Token？

**A:** 推荐方案：

**方案1：多个全局Token**
- 创建多个全局Token，例如：
  - "测试环境Token"
  - "预发布环境Token"
  - "生产环境Token"
- 切换环境时，只启用对应的Token

**方案2：环境变量**
- 在不同环境配置中设置不同的Token变量
- 全局Token使用变量：`${env_token}`

**方案3：测试套件（推荐）**
- 每个环境创建单独的测试套件
- 都包含登录用例
- 自动获取对应环境的Token

## 📊 配置检查清单

### 单独执行接口
- [ ] 全局Token已创建
- [ ] 全局Token已启用
- [ ] 全局Token已设为默认
- [ ] 接口未配置auth_type
- [ ] Token未过期

### 测试套件执行
- [ ] 创建了登录测试用例
- [ ] 登录用例配置了变量提取器
- [ ] JSON路径与响应结构匹配
- [ ] 测试套件中登录用例排在第一位
- [ ] 后续接口未配置auth_type

## 🎉 总结

优化后的全局Token功能实现了：

1. **零配置**：接口不需要配置认证
2. **智能选择**：自动选择最合适的Token
3. **动态优先**：测试套件使用最新Token
4. **静态兜底**：单独执行使用全局Token
5. **灵活可控**：支持接口级别覆盖

**一句话总结：开发时用全局Token，测试时用动态Token，系统自动选择！** 🚀


