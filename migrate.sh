#!/bin/bash

# BenchLink 数据库迁移脚本

echo "========================================="
echo "  BenchLink 数据库迁移脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -d "backend" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 进入后端目录
cd backend

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先创建虚拟环境${NC}"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查 Django 是否安装
if ! python -c "import django" 2>/dev/null; then
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -r requirements.txt -q
fi

echo -e "${YELLOW}开始数据库迁移...${NC}"
echo ""

# 创建迁移文件
echo -e "${YELLOW}1. 创建迁移文件...${NC}"
python manage.py makemigrations
if [ $? -ne 0 ]; then
    echo -e "${RED}创建迁移文件失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 迁移文件创建成功${NC}"
echo ""

# 执行迁移
echo -e "${YELLOW}2. 执行数据库迁移...${NC}"
python manage.py migrate
if [ $? -ne 0 ]; then
    echo -e "${RED}数据库迁移失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 数据库迁移成功${NC}"
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  迁移完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "提示: 如需重启服务，请运行 ./restart.sh"

