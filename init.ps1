# Seedance 视频制作工具 - 开发环境初始化脚本
# 用法: powershell -ExecutionPolicy Bypass -File init.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Seedance 视频制作工具 - 环境初始化 ===" -ForegroundColor Cyan

# 1. 检查 Python
Write-Host "[1/4] 检查 Python 环境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

# 2. 安装依赖
Write-Host "[2/4] 安装 Python 依赖..." -ForegroundColor Yellow
python -c "
import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'], check=True)
print('依赖安装完成')
"

# 3. 创建数据目录
Write-Host "[3/4] 创建数据目录..." -ForegroundColor Yellow
$dirs = @("data\projects", "data\assets", "data\thumbnails")
foreach ($dir in $dirs) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  创建: $dir"
    }
}

# 4. 启动开发服务器
Write-Host "[4/4] 启动 Flask 开发服务器..." -ForegroundColor Yellow
Write-Host "  访问 http://localhost:5000" -ForegroundColor Green
python app.py
