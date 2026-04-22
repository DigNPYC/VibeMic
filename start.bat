@echo off
chcp 65001 >nul
echo ==========================================
echo  vibe搭子 - 电脑端服务端
echo ==========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [信息] 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo [信息] 正在检查依赖...
pip install -q -r requirements.txt

REM 启动程序
echo [信息] 启动服务端...
echo.
python main.py

pause
