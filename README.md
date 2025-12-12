# BenchLink - 接口测试平台

一个基于 Django + Vue3 的现代化接口测试平台，提供接口管理、测试用例管理、自动化测试执行和定时任务等功能。

## 功能特性

- ✅ **项目管理** - 支持多项目隔离管理
- ✅ **接口管理** - 完整的接口CRUD和调试功能
- ✅ **环境管理** - 支持多环境配置（开发、测试、生产等）
- ✅ **测试用例** - 支持前置/后置脚本和断言规则
- ✅ **测试套件** - 批量组织和管理测试用例
- ✅ **执行记录** - 完整的测试执行历史和结果查看
- ✅ **定时任务** - 基于Cron表达式的定时测试执行
- ✅ **用户权限** - 基于Token的用户认证和权限管理

## 技术栈

### 后端
- Django 4.2
- Django REST Framework
- PostgreSQL
- Redis
- Celery (异步任务)

### 前端
- Vue 3
- Vue Router
- Pinia
- Element Plus
- Axios
- Vite

## 项目结构

```
BenchLink/
├── backend/          # Django 后端
├── frontend/         # Vue3 前端
├── docker/          # Docker 配置
└── README.md
```

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 初始化数据库
docker-compose -f docker/docker-compose.yml exec backend python manage.py migrate
docker-compose -f docker/docker-compose.yml exec backend python manage.py createsuperuser
```

访问：
- 前端：http://localhost
- 后端API：http://localhost:8000
- 管理后台：http://localhost:8000/admin

### 方式二：本地开发

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env  # 创建 .env 文件并配置

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：
- 前端：http://localhost:5173
- 后端API：http://localhost:8000

## 环境变量配置

在 `backend/` 目录下创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=benchlink
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## API 文档

启动后端服务后，访问：
- API 根路径：http://localhost:8000/api/
- Django Admin：http://localhost:8000/admin/

主要API端点：
- `/api/users/` - 用户管理
- `/api/projects/` - 项目管理
- `/api/environments/` - 环境管理
- `/api/apis/` - 接口管理
- `/api/testcases/` - 测试用例
- `/api/testsuites/` - 测试套件
- `/api/executions/` - 执行记录
- `/api/scheduler/` - 定时任务

## 开发计划

- [ ] 接口导入/导出（Postman、Swagger等格式）
- [ ] 测试报告生成（HTML、PDF）
- [ ] 数据Mock功能
- [ ] 性能测试支持
- [ ] 测试数据管理
- [ ] 更丰富的断言类型
- [ ] 团队协作功能
- [ ] 通知系统（邮件、钉钉、企业微信等）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！



# BenchLink
