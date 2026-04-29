<#
.SYNOPSIS
停止所有GA bot — 独立停止脚本，非代理
用法:  cd boot && .\stop.ps1
#>
$BootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path (Join-Path $BootDir '..')
$ConfigPath = Join-Path $ProjectRoot "config\boot_config.json"
$LogPath = Join-Path $ProjectRoot "logs\boot.log"

# ---------- helper ----------
function Write-Log { param([string]$msg)
    $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$time $msg" | Out-File -FilePath $LogPath -Append -Encoding UTF8
    Write-Host "$time $msg"
}

function Get-RunningPids { param([string]$scriptName)
    $scriptName = $scriptName -replace '\.pyw?$',''
    # 优先用 Get-CimInstance (非Admin也能拿到CommandLine)
    $pids = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$scriptName*" } |
        Select-Object -ExpandProperty ProcessId
    if ($pids) { return $pids }
    # 回退: Get-Process
    Get-Process -Name "python*" -ErrorAction SilentlyContinue |
        Where-Object {
            try { $_.CommandLine -like "*$scriptName*" } catch { $false }
        } |
        Select-Object -ExpandProperty Id
}

function Stop-Bot { param([string]$scriptPath, [string]$botLabel, [string]$botKey)
    $pids = Get-RunningPids $scriptPath
    if ($pids.Count -eq 0) { Write-Log "  [$botLabel] 未运行" }
    else {
        # Signal graceful shutdown
        $shutdownFile = Join-Path $ProjectRoot "temp\.shutdown_$botKey"
        Set-Content -Path $shutdownFile -Value "shutdown" -Force
        Write-Log "  [$botLabel] 发送关闭信号..."
        # Wait for graceful shutdown (bot should notify user and exit)
        $waited = 0
        while ($waited -lt 8) {
            Start-Sleep -Seconds 1
            $waited++
            $remaining = Get-RunningPids $scriptPath
            if ($remaining.Count -eq 0) {
                Write-Log "  [$botLabel] 已优雅退出"
                return
            }
        }
        # Force kill remaining processes
        $finalPids = Get-RunningPids $scriptPath
        foreach ($pidVal in $finalPids) {
            try { Stop-Process -Id $pidVal -Force; Write-Log "  [$botLabel] 强制停止 PID=$pidVal" }
            catch { Write-Log "  [$botLabel] 停止失败 PID=$pidVal : $_" }
        }
    }
}

# ========== main ==========
Write-Log "=== Boot stop.ps1 (独立停止) ==="
Write-Log "  项目: $ProjectRoot"
Write-Log "  配置: $ConfigPath"

if (-not (Test-Path $ConfigPath)) {
    Write-Log "配置不存在: $ConfigPath, 无法获取bot列表"
    exit 1
}

$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Log "--- 停止所有GA bot ---"
foreach ($key in $cfg.bots.PSObject.Properties.Name) {
    $bot = $cfg.bots.$key
    $scriptPath = Join-Path $ProjectRoot $bot.entry
    Stop-Bot $scriptPath $bot.name $key
}
Write-Log "=== 已全部停止 ==="
