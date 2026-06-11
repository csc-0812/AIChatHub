# ============================================
# AIChatHub Docker 一键部署脚本 (Windows PowerShell)
# 用法: .\scripts\deploy.ps1
# ============================================

$ErrorActionPreference = "Stop"

$ComposeFile = "docker/docker-compose.yml"
$DockerCompose = "docker compose -f $ComposeFile"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AIChatHub Docker 本地部署脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ---------- 1. 环境检查 ----------
Write-Host "[1/5] 检查 Docker 环境..." -ForegroundColor Yellow

$dockerVersion = docker --version 2>$null
if (-not $dockerVersion) {
    Write-Host "❌ Docker 未安装，请先安装 Docker Desktop" -ForegroundColor Red
    Write-Host "   下载地址: https://docs.docker.com/desktop/setup/install/windows-install/" -ForegroundColor Red
    exit 1
}

$composeVersion = docker compose version 2>$null
if (-not $composeVersion) {
    Write-Host "❌ Docker Compose 不可用" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ $dockerVersion" -ForegroundColor Green
Write-Host "  ✓ $composeVersion" -ForegroundColor Green
Write-Host ""

# ---------- 2. 环境变量 ----------
Write-Host "[2/5] 加载环境变量..." -ForegroundColor Yellow

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "  ✓ 已加载 .env 文件" -ForegroundColor Green
}
else {
    Write-Host "  ⚠ 未找到 .env 文件，使用 docker-compose.yml 中的默认值" -ForegroundColor Yellow
}
Write-Host ""

# ---------- 3. 构建镜像 ----------
Write-Host "[3/5] 构建 Docker 镜像..." -ForegroundColor Yellow
Invoke-Expression "$DockerCompose build --parallel"
Write-Host ""

# ---------- 4. 启动服务 ----------
Write-Host "[4/5] 启动服务..." -ForegroundColor Yellow
Invoke-Expression "$DockerCompose up -d"
Write-Host ""

# ---------- 5. 等待就绪 ----------
Write-Host "[5/5] 等待服务就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "📊 服务状态:" -ForegroundColor Cyan
Invoke-Expression "$DockerCompose ps"
Write-Host ""

# 检查后端健康
Write-Host "🔍 检查后端健康状态..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  ✓ 后端服务正常" -ForegroundColor Green
}
catch {
    Write-Host "  ⚠ 后端服务可能尚未就绪，请稍后检查" -ForegroundColor Yellow
}

$frontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ✅ 部署完成!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  前端访问:  http://localhost:$frontendPort" -ForegroundColor White
Write-Host "  后端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "  API 文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  健康检查:  http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "  常用命令:" -ForegroundColor White
Write-Host "    查看日志:    $DockerCompose logs -f [backend|frontend|redis]" -ForegroundColor Gray
Write-Host "    停止服务:    $DockerCompose down" -ForegroundColor Gray
Write-Host "    重启服务:    $DockerCompose restart" -ForegroundColor Gray
Write-Host "    重新构建:    $DockerCompose up -d --build" -ForegroundColor Gray
Write-Host "    进入后端容器: $DockerCompose exec backend sh" -ForegroundColor Gray
Write-Host ""
Write-Host "  创建超级管理员（首次使用）:" -ForegroundColor White
Write-Host "    $DockerCompose exec backend uv run python scripts/make_super_admin.py" -ForegroundColor Gray
Write-Host ""
