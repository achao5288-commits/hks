#!/bin/bash
# ============================================================
# 一键启动脚本 - Workflow Automation Platform
# 同时启动前端(Vite)、后端(FastAPI)、Electron窗口
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DESKTOP_DIR="$PROJECT_DIR/desktop"

BACKEND_PORT=8000
FRONTEND_PORT=5173

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  拖拽式工作流自动化平台 - 启动中...${NC}"
echo -e "${CYAN}============================================${NC}"

# ---- Check prerequisites ----
echo -e "\n${YELLOW}[1/5] 检查运行环境...${NC}"

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python (需要 3.10+)${NC}"
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo -e "  Python: $($PYTHON --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js (需要 18+)${NC}"
    exit 1
fi
echo -e "  Node.js: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: 未找到 npm${NC}"
    exit 1
fi
echo -e "  npm: $(npm --version)"

# ---- Port check ----
echo -e "\n${YELLOW}[2/5] 检查端口占用...${NC}"

check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        if lsof -i :$port -t &> /dev/null; then
            echo -e "  ${RED}端口 ${port} 已被占用${NC}"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -ano 2>/dev/null | grep -q ":$port "; then
            echo -e "  ${RED}端口 ${port} 已被占用${NC}"
            return 1
        fi
    fi
    echo -e "  ${GREEN}端口 ${port} 可用${NC}"
    return 0
}

ORIGINAL_PORT=$BACKEND_PORT
while ! check_port $BACKEND_PORT; do
    BACKEND_PORT=$((BACKEND_PORT + 1))
    if [ $((BACKEND_PORT - ORIGINAL_PORT)) -gt 10 ]; then
        echo -e "${RED}无法找到可用端口 (8000-8010)${NC}"
        exit 1
    fi
    echo -e "  ${YELLOW}尝试端口: ${BACKEND_PORT}${NC}"
done

check_port $FRONTEND_PORT || true

# ---- Install dependencies ----
echo -e "\n${YELLOW}[3/5] 安装依赖...${NC}"

# Python dependencies
echo -e "  安装 Python 依赖..."
cd "$BACKEND_DIR"
$PYTHON -m pip install -r requirements.txt -q 2>&1 | tail -1
echo -e "  ${GREEN}Python 依赖已就绪${NC}"

# Frontend dependencies
echo -e "  安装前端依赖..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    npm install --silent
    echo -e "  ${GREEN}前端依赖已安装${NC}"
else
    echo -e "  ${GREEN}前端依赖已就绪${NC}"
fi

# ---- Initialize database ----
echo -e "\n${YELLOW}[4/5] 初始化数据库...${NC}"
cd "$BACKEND_DIR"
$PYTHON -c "from models import create_tables; create_tables(); print('  数据库表已创建')"
echo -e "  ${GREEN}数据库已就绪${NC}"

# ---- Start services ----
echo -e "\n${YELLOW}[5/5] 启动服务...${NC}"

# Start backend
echo -e "  启动后端服务 (端口 ${BACKEND_PORT})..."
cd "$BACKEND_DIR"
$PYTHON -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
BACKEND_PID=$!
echo -e "  ${GREEN}后端已启动 (PID: ${BACKEND_PID})${NC}"

# Start frontend
echo -e "  启动前端开发服务器 (端口 ${FRONTEND_PORT})..."
cd "$FRONTEND_DIR"
npx vite --port $FRONTEND_PORT &
FRONTEND_PID=$!
echo -e "  ${GREEN}前端已启动 (PID: ${FRONTEND_PID})${NC}"

# Wait for services
sleep 3

# ---- Summary ----
echo -e "\n${CYAN}============================================${NC}"
echo -e "${GREEN}  ✅ 服务已启动!${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  前端界面:  ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  后端API:   ${CYAN}http://localhost:${BACKEND_PORT}/api${NC}"
echo -e "  API文档:   ${CYAN}http://localhost:${BACKEND_PORT}/docs${NC}"
echo -e "  演示页面:  ${CYAN}http://localhost:${FRONTEND_PORT}/demo-news.html${NC}"
echo -e ""
echo -e "  ${YELLOW}按 Ctrl+C 停止所有服务${NC}"

# Cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
wait
