@echo off
REM PM Digital Employee - 本地开发启动脚本 (Windows)
REM 一键启动本地开发环境

echo ===========================================
echo   PM数字员工系统 - 本地开发启动脚本 (Windows)
echo ===========================================

REM 检查Python环境
echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境，使用系统Python环境
)

REM 检查依赖
echo 检查依赖...

REM 检查必需的包
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未安装fastapi
    set MISSING_DEPS=YES
)

python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未安装uvicorn
    set MISSING_DEPS=YES
)

python -c "import sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未安装sqlalchemy
    set MISSING_DEPS=YES
)

if "%MISSING_DEPS%"=="YES" (
    if exist "requirements.txt" (
        echo 尝试安装 requirements.txt 中的依赖...
        pip install -r requirements.txt
    ) else (
        echo 未找到 requirements.txt 文件
    )
)

REM 检查环境变量文件
if not exist ".env" (
    if exist ".env.example" (
        echo 复制环境变量配置模板...
        copy .env.example .env
        echo 请编辑 .env 文件以配置飞书参数
    ) else (
        echo 警告: 未找到 .env 和 .env.example 文件
    )
)

REM 检查并创建必要目录
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads

echo 启动PM数字员工系统...

REM 检查uvicorn并启动
python -c "import uvicorn" >nul 2>&1
if not errorlevel 1 (
    echo 使用uvicorn启动服务...
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo uvicorn未安装，尝试直接运行...
    python -m app.main
)

echo 服务已启动!
echo 访问 http://localhost:8000 查看应用
echo 访问 http://localhost:8000/docs 查看API文档
pause