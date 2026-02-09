@echo off
chcp 65001 >nul
title PubMed Papers Feed
echo.
echo ========================================
echo   PubMed Papers Feed
echo   智能文献聚合与文案生成工具
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Python 已检测...

:: 检查依赖
echo [2/3] 检查依赖...
python -c "import fastapi, uvicorn, openai" >nul 2>&1
if errorlevel 1 (
    echo         正在安装依赖（首次运行需要）...
    pip install -r requirements.txt -q
)

:: 创建配置
echo [3/3] 准备配置文件...
if not exist "config.yaml" (
    copy config.yaml.example config.yaml
    echo         已创建默认配置，请编辑 config.yaml 填写 API Key
)

:: 启动
echo.
echo ========================================
echo   启动服务...                    
echo ========================================
echo.
echo 浏览器将自动打开 http://localhost:8000
echo 按 Ctrl+C 停止服务
echo.

timeout /t 2 /nobreak >nul
start http://localhost:8000
python main.py

pause
