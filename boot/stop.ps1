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

function Show-Popup { param([string]$title, [string]$message, [int]$timeout = 5)
    try {
        $wshell = New-Object -ComObject Wscript.Shell
        $wshell.Popup($message, $timeout, $title, 0x40) | Out-Null
    } catch {
        Write-Host "[Popup] $title : $message" -ForegroundColor Cyan
    }
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
    if ($pids.Count -eq 0) { Write-Log "  [$botLabel] 未运行"; return @{name=$botLabel; status="not_running"} }
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
                return @{name=$botLabel; status="graceful"}
            }
        }
        # Force kill remaining processes
        $finalPids = Get-RunningPids $scriptPath
        foreach ($pidVal in $finalPids) {
            $proc = Get-Process -Id $pidVal -ErrorAction SilentlyContinue
            if ($proc) {
                try {
                    Stop-Process -Id $pidVal -Force -ErrorAction Stop
                    Write-Log "  [$botLabel] 强制停止 PID=$pidVal"
                }
                catch { Write-Log "  [$botLabel] 停止失败 PID=$pidVal : $_" }
            } else {
                Write-Log "  [$botLabel] PID=$pidVal 已自行退出"
            }
        }
        return @{name=$botLabel; status="forced"}
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
$stopResults = @()
foreach ($key in $cfg.bots.PSObject.Properties.Name) {
    $bot = $cfg.bots.$key
    $scriptPath = Join-Path $ProjectRoot $bot.entry
    $result = Stop-Bot $scriptPath $bot.name $key
    $stopResults += $result
}
Write-Log "=== 已全部停止 ==="

# --- 弹窗提示 ---
$graceful = ($stopResults | Where-Object { $_.status -eq "graceful" }).Count
$forced = ($stopResults | Where-Object { $_.status -eq "forced" }).Count
$notRunning = ($stopResults | Where-Object { $_.status -eq "not_running" }).Count
$msgLines = @()
if ($graceful -gt 0) { $msgLines += "🟢 优雅退出: $graceful 个" }
if ($forced -gt 0) { $msgLines += "🟡 强制停止: $forced 个" }
if ($notRunning -gt 0) { $msgLines += "⚪ 原本未运行: $notRunning 个" }
$popupMsg = "所有 Bot 已停止`r`n" + ($msgLines -join "`r`n")
Show-Popup "GenericAgent · 关闭完成" $popupMsg 5
