#!/bin/bash

# BenchLink 项目停止脚本

echo "========================================="
echo "  停止 BenchLink 服务"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 停止后端服务（端口8000）
BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PID" ]; then
    echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null
    sleep 1
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
    sleep 1
    # 如果还在运行，强制杀死
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill -9 $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}前端服务已停止${NC}"
else
    echo -e "${GREEN}前端服务未运行${NC}"
fi

echo ""
echo -e "${GREEN}所有服务已停止${NC}"





