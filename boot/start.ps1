<#
.SYNOPSIS
GenericAgent Boot 统一启动器 — 从 config/boot_config.json 读取配置，管理所有bot
用法:
  cd boot; .\start.ps1                     -> 按配置启动已启用的bot
  cd boot; .\start.ps1 -Bots "tg,fs"       -> 启动指定bot并保存配置
  cd boot; .\start.ps1 -Restart            -> 重启(优雅停止→启动)
  cd boot; .\start.ps1 -Stop               -> 优雅停止所有bot
  cd boot; .\start.ps1 -Status             -> 查看运行状态 
  cd boot; .\start.ps1 -SetupAutoStart     -> 安装开机自启动
  cd boot; .\start.ps1 -RemoveAutoStart    -> 移除开机自启动
#>
param(
    [string]$Bots = "",
    [switch]$Restart,
    [switch]$Stop,
    [switch]$Status,
    [switch]$SetupAutoStart,
    [switch]$RemoveAutoStart
)

$BootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path (Join-Path $BootDir '..')
$ConfigPath = Join-Path $ProjectRoot "config\boot_config.json"
$LogPath = Join-Path $ProjectRoot "logs\boot.log"
$LogDir = Split-Path $LogPath
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

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
    # 回退: Get-Process (Admin可能需要)
    Get-Process -Name "python*" -ErrorAction SilentlyContinue |
        Where-Object {
            try { $_.CommandLine -like "*$scriptName*" } catch { $false }
        } |
        Select-Object -ExpandProperty Id
}

function Stop-Bot { param([string]$scriptPath, [string]$botLabel, [string]$botKey = "")
    $pids = Get-RunningPids $scriptPath
    if ($pids.Count -eq 0) { Write-Log "  [$botLabel] 未运行" }
    else {
        # Signal graceful shutdown
        if ($botKey) {
            $shutdownFile = Join-Path $ProjectRoot "temp\.shutdown_$botKey"
            Set-Content -Path $shutdownFile -Value "shutdown" -Force
            Write-Log "  [$botLabel] 发送关闭信号..."
            $waited = 0
            while ($waited -lt 8) {
                Start-Sleep -Seconds 1
                $waited++
                $remaining = Get-RunningPids $scriptPath
                if ($remaining.Count -eq 0) { Write-Log "  [$botLabel] 已优雅退出"; return }
            }
            Write-Log "  [$botLabel] 优雅关闭超时, 强制停止"
        }
        foreach ($pidVal in (Get-RunningPids $scriptPath)) {
            try { Stop-Process -Id $pidVal -Force; Write-Log "  [$botLabel] 强制停止 PID=$pidVal" }
            catch { Write-Log "  [$botLabel] 停止失败 PID=$pidVal : $_" }
        }
    }
}

function Start-Bot { param([string]$scriptPath, [string]$botLabel, [string]$botKey, $cfg, [string]$pythonwPath)
    # Check bot_script (also_check) for stale processes from old configs
    $botCfg = $cfg.bots.$botKey
    if ($botCfg.also_check) {
        $stalePids = Get-RunningPids $botCfg.also_check
        if ($stalePids.Count -gt 0) {
            foreach ($sp in $stalePids) {
                try { Stop-Process -Id $sp -Force; Write-Log "  [$botLabel] 清理旧进程 PID=$sp ($($botCfg.also_check))" }
                catch { Write-Log "  [$botLabel] 清理旧进程失败 PID=$sp : $_" }
            }
            Start-Sleep -Milliseconds 500
        }
    }
    $existingPids = Get-RunningPids $scriptPath
    if ($existingPids.Count -gt 0) {
        Write-Log "  [$botLabel] 已在运行 PID=$($existingPids -join ',') 跳过"
        return $existingPids
    }
    if (-not (Test-Path $scriptPath)) {
        Write-Log "  [$botLabel] 错误: 脚本不存在 $scriptPath"
        return @()
    }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pythonwPath
    $psi.Arguments = "`"$scriptPath`""
    $psi.WorkingDirectory = $ProjectRoot
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    # Pass notification config via env vars
    if ($botCfg.notify_chat_id) {
        $psi.EnvironmentVariables["GA_NOTIFY_CHAT_ID"] = $botCfg.notify_chat_id
    }
    if ($botCfg.notify_chat_type) {
        $psi.EnvironmentVariables["GA_NOTIFY_CHAT_TYPE"] = $botCfg.notify_chat_type
    }
    $shutdownFile = Join-Path $ProjectRoot "temp\.shutdown_$botKey"
    $psi.EnvironmentVariables["GA_SHUTDOWN_FILE"] = $shutdownFile
    # Clean any stale shutdown file
    if (Test-Path $shutdownFile) { Remove-Item $shutdownFile -Force }
    $p = [System.Diagnostics.Process]::Start($psi)
    Start-Sleep -Milliseconds 3000
    $p.Refresh()
    if ($p.HasExited) {
        Write-Log "  [$botLabel] 启动失败 (立即退出)"
        return @()
    }
    Write-Log "  [$botLabel] OK PID=$($p.Id)"
    return @($p.Id)
}

# ---------- resolve pythonw ----------
function Resolve-Pythonw {
    $cfgPythonw = $null
    if (Test-Path $ConfigPath) {
        try {
            $cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $cfgPythonw = $cfg.pythonw
        } catch {}
    }
    $candidates = @()
    if ($cfgPythonw) { $candidates += $cfgPythonw }
    $candidates += "pythonw.exe"
    foreach ($c in $candidates) {
        $resolved = $ExecutionContext.InvokeCommand.ExpandString($c)
        $exe = Get-Command $resolved -ErrorAction SilentlyContinue
        if ($exe) { return $exe.Source }
    }
    $found = where.exe pythonw 2>$null | Select-Object -First 1
    if ($found) { return $found.Trim() }
    Write-Log "错误: 找不到 pythonw.exe"
    exit 1
}

# ---------- load / write config ----------
function Get-Config {
    if (-not (Test-Path $ConfigPath)) {
        $examplePath = Join-Path $ProjectRoot "config\boot_config.example.json"
        if (Test-Path $examplePath) {
            Copy-Item $examplePath $ConfigPath -Force
            Write-Log "配置不存在, 已从 example 创建: $ConfigPath"
            Write-Log "请编辑 $ConfigPath 填入实际配置后再启动"
            exit 0
        }
        Write-Log "配置不存在: $ConfigPath (也无 example 模板), 无法启动"
        exit 1
    }
    $cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    return $cfg
}

function Write-Config { param($cfg)
    $cfg | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigPath -Encoding UTF8
}

# ========== main ==========
$pythonwPath = Resolve-Pythonw
$cfg = Get-Config

Write-Log "=== Boot start.ps1 ==="
Write-Log "  项目: $ProjectRoot"
Write-Log "  Python: $pythonwPath"
Write-Log "  配置: $ConfigPath"

# --- RemoveAutoStart ---
if ($RemoveAutoStart) {
    $vbsPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\GenericAgent.vbs"
    if (Test-Path $vbsPath) {
        Remove-Item $vbsPath -Force
        Write-Log "OK 已移除开机自启动"
    } else { Write-Log "开机自启动尚未安装" }
    exit 0
}

# --- SetupAutoStart ---
if ($SetupAutoStart) {
    $vbsPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\GenericAgent.vbs"
    $psCall = "powershell.exe -ExecutionPolicy Bypass -File `"$BootDir\start.ps1`""
    $vbsContent = "Set WshShell = CreateObject(""WScript.Shell"")`r`n" +
                  "WshShell.Run ""$psCall "", 0, False"
    Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII
    Write-Log "OK 开机自启动已安装 -> $vbsPath"
    exit 0
}

# --- Status ---
if ($Status) {
    Write-Host ""
    Write-Host "========== GenericAgent Boot 运行状态 =========="
    Write-Host "配置: $ConfigPath"
    $autoStart = Test-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\GenericAgent.vbs"
    Write-Host "开机自启动: $(if($autoStart){'Y'}else{'N'})"
    Write-Host ""
    Write-Host "Bot                     状态   PID"
    Write-Host "----------------------------------------"
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        $bot = $cfg.bots.$key
        $name = $bot.name
        $scriptPath = Join-Path $ProjectRoot $bot.entry
        $pids = Get-RunningPids $scriptPath
        if ($pids.Count -gt 0) { $st = "运行中" } else { $st = "已停止" }
        $pidStr = if ($pids.Count -gt 0) { "$($pids -join ',')" } else { "-" }
        Write-Host ("{0,-25} {1,-6} {2}" -f $name, $st, $pidStr)
    }
    Write-Host "----------------------------------------"
    Write-Host ""
    exit 0
}

# --- Restart: stop all first ---
if ($Restart) {
    Write-Log "--- 重启模式: 停止所有bot ---"
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        $bot = $cfg.bots.$key
        $scriptPath = Join-Path $ProjectRoot $bot.entry
        Stop-Bot $scriptPath $bot.name $key
    }
    Start-Sleep -Seconds 1
    Write-Log "--- 重启模式: 启动bot ---"
}

# --- Stop: graceful stop all ---
if ($Stop) {
    Write-Log "--- 停止模式: 优雅停止所有bot ---"
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        $bot = $cfg.bots.$key
        $scriptPath = Join-Path $ProjectRoot $bot.entry
        Stop-Bot $scriptPath $bot.name $key
    }
    Write-Log "--- 停止完成 ---"
    exit 0
}

# --- determine which bots to start ---
$botKeys = @()
if ($Bots) {
    $botList = $Bots -split ',' | ForEach-Object { $_.Trim().ToLower() }
    foreach ($key in $cfg.bots.PSObject.Properties.Name) { $cfg.bots.$key.enabled = $false }
    $unknown = @()
    foreach ($b in $botList) {
        if ($cfg.bots.$b) { $cfg.bots.$b.enabled = $true; $botKeys += $b }
        else { $unknown += $b }
    }
    if ($unknown.Count -gt 0) { Write-Log "  Warn 未知bot: $($unknown -join ',') (可用: $($cfg.bots.PSObject.Properties.Name -join ', '))" }
    Write-Config $cfg
    Write-Log "OK 配置已更新: 启用bot = $Bots"
} else {
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        if ($cfg.bots.$key.enabled) { $botKeys += $key }
    }
}

if ($botKeys.Count -eq 0) {
    Write-Log "没有需要启动的bot (配置中未启用任何bot, 可用 -Bots 指定)"
    exit 0
}

# --- start ---
Write-Log "--- 启动bot ---"
$started = @()
foreach ($key in $botKeys) {
    $bot = $cfg.bots.$key
    $scriptPath = Join-Path $ProjectRoot $bot.entry
    Write-Log "  启动 $($bot.name) ($($bot.entry)) ..."
    $pids = Start-Bot $scriptPath $bot.name $key $cfg $pythonwPath
    if ($pids.Count -gt 0) { $started += @{key=$key; name=$bot.name} }
}

# --- verify ---
Write-Log "--- 状态验证 ---"
$startedOk = @()
$startedFail = @()
foreach ($s in $started) {
    $bot = $cfg.bots.$($s.key)
    $scriptPath = Join-Path $ProjectRoot $bot.entry
    $pids = Get-RunningPids $scriptPath
    if ($pids.Count -gt 0) { Write-Log "  [OK] $($s.name) 运行中 PID=$($pids -join ',')"; $startedOk += $s.name }
    else { Write-Log "  [X] $($s.name) 已退出"; $allOk = $false; $startedFail += $s.name }
}
if ($allOk) { Write-Log "=== OK 全部启动成功 ===" }
else { Write-Log "=== Warn 部分启动失败, 请检查日志 ===" }

# --- Bot 通知 (替代弹窗) ---
$okList = if ($startedOk.Count -gt 0) { $startedOk -join ', ' } else { '' }
$failList = if ($startedFail.Count -gt 0) { $startedFail -join ', ' } else { '' }
$pythonExe = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) { $pythonExe = 'python' }
$notifyScript = Join-Path $PSScriptRoot 'notify_boot.py'
& $pythonExe $notifyScript -Ok $okList -Fail $failList *>> $bootLog

# 开机自启提示 (不再静默安装)
$vbsPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\GenericAgent.vbs"
if (Test-Path $vbsPath) {
    Write-Log "  (开机自启: 已配置)"
} else {
    Write-Log "  (提示: 如需开机自启, 手动将 start.ps1 快捷方式放入启动目录: $env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\)"
}
