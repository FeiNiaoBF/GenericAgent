<#
.SYNOPSIS
GenericAgent 一键重启脚本 — 先优雅停止所有bot，再按配置启动
用法:
  cd boot; .\restart.ps1                     -> 停止所有→启动已启用的bot
  cd boot; .\restart.ps1 -Bots "tg,fs"       -> 停止所有→仅启动指定bot
  cd boot; .\restart.ps1 -SkipStop           -> 不停止，仅启动（等效 start.ps1）
  cd boot; .\restart.ps1 -StopOnly           -> 仅停止，不启动（等效 stop.ps1）
#>
param(
    [string]$Bots = "",
    [switch]$SkipStop,
    [switch]$StopOnly
)

$BootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$StopScript = Join-Path $BootDir "stop.ps1"
$StartScript = Join-Path $BootDir "start.ps1"

# ---------- helper ----------
function Show-Popup { param([string]$title, [string]$message, [int]$timeout = 5)
    try {
        $wshell = New-Object -ComObject Wscript.Shell
        $wshell.Popup($message, $timeout, $title, 0x40) | Out-Null
    } catch {
        Write-Host "[Popup] $title : $message" -ForegroundColor Cyan
    }
}

if (-not $StopOnly) { Show-Popup "GenericAgent · 重启中" "正在重启所有 Bot，请稍候..." 3 }

$ErrorActionPreference = "Stop"

# ====== Stop phase ======
if (-not $SkipStop) {
    Write-Host ""
    Write-Host "========== [restart] 第1步: 停止所有bot ==========" -ForegroundColor Yellow
    if (Test-Path $StopScript) {
        & $StopScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[restart] stop.ps1 返回非零 ($LASTEXITCODE), 继续尝试启动..." -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "[restart] 错误: 找不到 stop.ps1 ($StopScript)" -ForegroundColor Red
        exit 1
    }
    Write-Host "[restart] 停止完成, 稍等2秒..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

# ====== Start phase ======
if (-not $StopOnly) {
    Write-Host "========== [restart] 第2步: 启动bot ==========" -ForegroundColor Yellow
    if (Test-Path $StartScript) {
        $args = @()
        if ($Bots) { $args += "-Bots"; $args += $Bots }
        & $StartScript @args
    } else {
        Write-Host "[restart] 错误: 找不到 start.ps1 ($StartScript)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[restart] StopOnly 模式, 跳过启动." -ForegroundColor Gray
}

Write-Host "========== [restart] 完成 ==========" -ForegroundColor Green