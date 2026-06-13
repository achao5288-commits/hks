@echo off
chcp 65001 >nul
REM ============================================================
REM Windows 启动脚本 - Workflow Automation Platform
REM ============================================================
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"

echo ============================================
echo   拖拽式工作流自动化平台 - 启动中...
echo ============================================

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)
echo [OK] Python 已找到

REM Check Node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js
    pause
    exit /b 1
)
echo [OK] Node.js 已找到

REM Initialize database
echo.
echo [1/3] 初始化数据库...
cd /d "%BACKEND_DIR%"
python -c "from models import create_tables; create_tables(); print('  数据库已就绪')"

REM Initialize demo data
echo.
echo [2/3] 初始化演示数据...
python "%PROJECT_DIR%\scripts\demo_data.py"

REM Start backend
echo.
echo [3/3] 启动服务...
echo   启动后端 (http://localhost:8000)...
start "Workflow Backend" cmd /c "cd /d "%BACKEND_DIR%" && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Start frontend
echo   启动前端 (http://localhost:5173)...
start "Workflow Frontend" cmd /c "cd /d "%FRONTEND_DIR%" && npx vite --port 5173"

timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   ✅ 服务启动完成!
echo ============================================
echo   前端界面:  http://localhost:5173
echo   后端API:   http://localhost:8000/api
echo   API文档:   http://localhost:8000/docs
echo   演示页面:  http://localhost:5173/demo-news.html
echo ============================================
echo.
echo   关闭此窗口或各服务窗口即可停止
echo.

pause
