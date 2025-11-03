#!/bin/bash

# BenchLink 项目重启脚本

echo "========================================="
echo "  BenchLink 项目重启脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 停止现有服务
echo -e "${YELLOW}停止现有服务...${NC}"

# 停止后端服务（端口8000）
BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PID" ]; then
    echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null
    sleep 2
    # 如果还在运行，强制杀死
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill -9 $BACKEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}后端服务已停止${NC}"
else
    echo -e "${GREEN}后端服务未运行${NC}"
fi

# 停止前端服务（端口5173）
FRONTEND_PID=$(lsof -ti:5173 2>/dev/null)
if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
    kill $FRONTEND_PID 2>/dev/null
    sleep 2
    # 如果还在运行，强制杀死
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill -9 $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}前端服务已停止${NC}"
else
    echo -e "${GREEN}前端服务未运行${NC}"
fi

echo ""
echo -e "${YELLOW}等待3秒后启动服务...${NC}"
sleep 3
echo ""

# 启动后端服务
echo -e "${YELLOW}启动后端服务...${NC}"
cd backend

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先创建虚拟环境${NC}"
    exit 1
fi

source venv/bin/activate

# 检查依赖是否安装
if ! python -c "import django" 2>/dev/null; then
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -r requirements.txt -q
fi

# 确保日志目录存在
mkdir -p ../logs

# 启动服务
# 先尝试使用自定义命令（允许数据库连接失败），如果失败则使用标准命令
if python manage.py runserver_nodb --help > /dev/null 2>&1; then
    echo -e "${YELLOW}使用自定义启动命令（允许数据库连接失败）...${NC}"
    python manage.py runserver_nodb 0.0.0.0:8000 > ../logs/backend.log 2>&1 &
else
    echo -e "${YELLOW}使用标准启动命令...${NC}"
    # 使用标准命令，但如果数据库连接失败会启动失败
    python manage.py runserver 0.0.0.0:8000 > ../logs/backend.log 2>&1 &
fi
BACKEND_PID=$!

# 等待服务启动（最多等待10秒）
echo -e "${YELLOW}等待后端服务启动...${NC}"
BACKEND_STARTED=false
for i in {1..20}; do
    sleep 0.5
    if kill -0 $BACKEND_PID 2>/dev/null; then
        if lsof -ti:8000 > /dev/null 2>&1; then
            echo -e "${GREEN}后端服务已启动 (PID: $BACKEND_PID)${NC}"
            echo -e "${GREEN}后端地址: http://127.0.0.1:8000${NC}"
            echo -e "${GREEN}日志文件: logs/backend.log${NC}"
            BACKEND_STARTED=true
            break
        fi
    else
        echo -e "${RED}后端服务进程已退出！${NC}"
        echo -e "${YELLOW}最后20行日志:${NC}"
        tail -20 ../logs/backend.log
        break
    fi
done

if [ "$BACKEND_STARTED" = false ]; then
    echo -e "${RED}警告: 后端服务可能未成功启动，请检查日志: logs/backend.log${NC}"
    echo -e "${YELLOW}最后20行日志:${NC}"
    tail -20 ../logs/backend.log
fi

cd ..

echo ""

# 启动前端服务
echo -e "${YELLOW}启动前端服务...${NC}"
cd frontend

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm use 18 > /dev/null 2>&1
    npm install > ../logs/frontend.log 2>&1
fi

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 18 > /dev/null 2>&1

npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# 等待前端服务启动（最多等待10秒）
echo -e "${YELLOW}等待前端服务启动...${NC}"
FRONTEND_STARTED=false
for i in {1..20}; do
    sleep 0.5
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        if lsof -ti:5173 > /dev/null 2>&1; then
            echo -e "${GREEN}前端服务已启动 (PID: $FRONTEND_PID)${NC}"
            echo -e "${GREEN}前端地址: http://localhost:5173${NC}"
            echo -e "${GREEN}日志文件: logs/frontend.log${NC}"
            FRONTEND_STARTED=true
            break
        fi
    else
        echo -e "${RED}前端服务进程已退出！${NC}"
        echo -e "${YELLOW}最后20行日志:${NC}"
        tail -20 ../logs/frontend.log
        break
    fi
done

if [ "$FRONTEND_STARTED" = false ]; then
    echo -e "${RED}警告: 前端服务可能未成功启动，请检查日志: logs/frontend.log${NC}"
    echo -e "${YELLOW}最后20行日志:${NC}"
    tail -20 ../logs/frontend.log
fi

cd ..

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  所有服务已启动完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "查看日志："
echo "  后端: tail -f logs/backend.log"
echo "  前端: tail -f logs/frontend.log"
echo ""
echo "停止服务："
echo "  后端: kill $BACKEND_PID"
echo "  前端: kill $FRONTEND_PID"
echo "  或运行: ./stop.sh"


