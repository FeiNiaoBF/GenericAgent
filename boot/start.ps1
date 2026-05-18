<#
.SYNOPSIS
GenericAgent boot launcher. Reads config/boot_config.json and manages enabled entries.
Usage:
  cd boot; .\start.ps1                     -> start enabled entries
  cd boot; .\start.ps1 -Bots "tg,fs"       -> enable specific entries, save config, and start them
  cd boot; .\start.ps1 -SelectedKeys "gui,tg" -> start selected entries once without changing config
  cd boot; .\start.ps1 -Restart            -> stop then start
  cd boot; .\start.ps1 -Stop               -> stop all entries
  cd boot; .\start.ps1 -Status             -> show status
  cd boot; .\start.ps1 -SetupAutoStart     -> install Windows startup entry
  cd boot; .\start.ps1 -RemoveAutoStart    -> remove Windows startup entry
#>
param(
    [string]$Bots = "",
    [string]$SelectedKeys = "",
    [switch]$UseSelectedKeys,
    [switch]$Restart,
    [switch]$Stop,
    [switch]$Status,
    [switch]$SetupAutoStart,
    [switch]$RemoveAutoStart
)

. (Join-Path $PSScriptRoot 'common.ps1')
Initialize-GABootConsole

$ctx = Get-GABootContext
$BootDir = $ctx.BootDir
$ProjectRoot = $ctx.ProjectRoot
$ConfigPath = $ctx.ConfigPath
$LogPath = $ctx.RootLogPath

# ---------- helper ----------
function Write-Log { param([string]$msg)
    Write-GALog -Path $LogPath -Message $msg
}

function Get-RunningPids { param([string]$scriptName)
    $scriptName = $scriptName -replace '\.pyw?$',''
    $pids = @()
    try {
        $pids = @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" -ErrorAction Stop |
            Where-Object { $_.CommandLine -like "*$scriptName*" } |
            Select-Object -ExpandProperty ProcessId)
    } catch {
        $pids = @()
    }
    if ($pids) { return $pids }
    try {
        return @(Get-Process -Name "python*" -ErrorAction Stop |
            Where-Object {
                try { $_.CommandLine -like "*$scriptName*" } catch { $false }
            } |
            Select-Object -ExpandProperty Id)
    } catch {
        return @()
    }
}

function Stop-Bot { param([string]$scriptPath, [string]$botLabel, [string]$botKey = "")
    $pids = Get-RunningPids $scriptPath
    if ($pids.Count -eq 0) { Write-Log "  [$botLabel] not running" }
    else {
        # Signal graceful shutdown
        if ($botKey) {
            $shutdownFile = Join-Path $ProjectRoot "temp\.shutdown_$botKey"
            $shutdownDir = Split-Path $shutdownFile
            if (-not (Test-Path $shutdownDir)) { New-Item -ItemType Directory -Path $shutdownDir -Force | Out-Null }
            Set-Content -Path $shutdownFile -Value "shutdown" -Force
            Write-Log "  [$botLabel] shutdown signal sent..."
            $waited = 0
            while ($waited -lt 8) {
                Start-Sleep -Seconds 1
                $waited++
                $remaining = Get-RunningPids $scriptPath
                if ($remaining.Count -eq 0) { Write-Log "  [$botLabel] exited cleanly"; return }
            }
            Write-Log "  [$botLabel] graceful shutdown timed out; forcing stop"
        }
        foreach ($pidVal in (Get-RunningPids $scriptPath)) {
            try { Stop-Process -Id $pidVal -Force; Write-Log "  [$botLabel] force stopped PID=$pidVal" }
            catch { Write-Log "  [$botLabel] stop failed PID=$pidVal : $_" }
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
                try { Stop-Process -Id $sp -Force; Write-Log "  [$botLabel] removed stale PID=$sp ($($botCfg.also_check))" }
                catch { Write-Log "  [$botLabel] stale cleanup failed PID=$sp : $_" }
            }
            Start-Sleep -Milliseconds 500
        }
    }
    $existingPids = Get-RunningPids $scriptPath
    if ($existingPids.Count -gt 0) {
        Write-Log "  [$botLabel] already running PID=$($existingPids -join ','); skipped"
        return $existingPids
    }
    if (-not (Test-Path $scriptPath)) {
        Write-Log "  [$botLabel] error: script not found $scriptPath"
        return @()
    }
    if ($botCfg.console) {
        # Console mode: use python.exe + new console window (for TUI bots)
        $pythonExe = $pythonwPath -replace 'pythonw\.exe$', 'python.exe'
        if (-not (Test-Path $pythonExe)) { $pythonExe = 'python' }
        # Collect env vars to pass
        $envToSet = @{}
        if ($botCfg.notify_chat_id) { $envToSet["GA_NOTIFY_CHAT_ID"] = $botCfg.notify_chat_id }
        if ($botCfg.notify_chat_type) { $envToSet["GA_NOTIFY_CHAT_TYPE"] = $botCfg.notify_chat_type }
        $shutdownFile = Join-Path $ProjectRoot "temp\.shutdown_$botKey"
        $shutdownDir = Split-Path $shutdownFile
        if (-not (Test-Path $shutdownDir)) { New-Item -ItemType Directory -Path $shutdownDir -Force | Out-Null }
        $envToSet["GA_SHUTDOWN_FILE"] = $shutdownFile
        if (Test-Path $shutdownFile) { Remove-Item $shutdownFile -Force }
        # Save originals, apply to current process (inherited by child)
        $origEnv = @{}
        foreach ($k in $envToSet.Keys) { $origEnv[$k] = [Environment]::GetEnvironmentVariable($k, "Process") }
        foreach ($k in $envToSet.Keys) { [Environment]::SetEnvironmentVariable($k, $envToSet[$k], "Process") }
        # Launch in a new console window
        $p = Start-Process -FilePath $pythonExe -ArgumentList "`"$scriptPath`"" -WorkingDirectory $ProjectRoot -WindowStyle Normal -PassThru
        # Restore originals
        foreach ($k in $origEnv.Keys) { [Environment]::SetEnvironmentVariable($k, $origEnv[$k], "Process") }
    } else {
        # No-console mode: use pythonw.exe (background GUI bots)
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $pythonwPath
        $psi.Arguments = "`"$scriptPath`""
        $psi.WorkingDirectory = $ProjectRoot
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false
        if ($botCfg.notify_chat_id) { $psi.EnvironmentVariables["GA_NOTIFY_CHAT_ID"] = $botCfg.notify_chat_id }
        if ($botCfg.notify_chat_type) { $psi.EnvironmentVariables["GA_NOTIFY_CHAT_TYPE"] = $botCfg.notify_chat_type }
        $shutdownFile = Join-Path $ProjectRoot "temp\.shutdown_$botKey"
        $shutdownDir = Split-Path $shutdownFile
        if (-not (Test-Path $shutdownDir)) { New-Item -ItemType Directory -Path $shutdownDir -Force | Out-Null }
        $psi.EnvironmentVariables["GA_SHUTDOWN_FILE"] = $shutdownFile
        if (Test-Path $shutdownFile) { Remove-Item $shutdownFile -Force }
        $p = [System.Diagnostics.Process]::Start($psi)
    }
    Start-Sleep -Milliseconds 3000
    if ($p.HasExited) {
        Write-Log "  [$botLabel] start failed (exited immediately)"
        return @()
    }
    Write-Log "  [$botLabel] OK PID=$($p.Id)"
    return @($p.Id)
}

function Stop-AllBots {
    param($cfg)
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        $bot = $cfg.bots.$key
        Stop-Bot (Resolve-GAPath $bot.entry) $bot.name $key
    }
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
        $expanded = [Environment]::ExpandEnvironmentVariables(
            $ExecutionContext.InvokeCommand.ExpandString($c)
        )
        $candidatePaths = @()
        if ([System.IO.Path]::IsPathRooted($expanded)) {
            $candidatePaths += $expanded
        } elseif (($expanded -match '[\\/]') -or $expanded.StartsWith(".")) {
            $candidatePaths += (Join-Path $ProjectRoot $expanded)
        }
        $candidatePaths += $expanded

        foreach ($candidate in ($candidatePaths | Select-Object -Unique)) {
            if (Test-Path $candidate -PathType Leaf) {
                return (Resolve-Path $candidate).Path
            }
            $exe = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($exe) { return $exe.Source }
        }
    }
    $found = where.exe pythonw 2>$null | Select-Object -First 1
    if ($found) { return $found.Trim() }
    Write-Log "error: pythonw.exe not found"
    exit 1
}

# ---------- load / write config ----------
function Get-Config {
    if (-not (Test-Path $ConfigPath)) {
        $examplePath = $ctx.ConfigExamplePath
        if (Test-Path $examplePath) {
            Copy-Item $examplePath $ConfigPath -Force
            Write-Log "config missing; created from example: $ConfigPath"
            Write-Log "please edit $ConfigPath before starting"
            exit 0
        }
        Write-Log "config missing: $ConfigPath (no example template); cannot start"
        exit 1
    }
    $cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    return $cfg
}

function Write-Config { param($cfg)
    $cfg | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigPath -Encoding UTF8
}

function Invoke-BootNotification {
    param([string]$OkList, [string]$FailList)
    $pythonExe = Resolve-GAPath ".venv\Scripts\python.exe" $ProjectRoot
    if (-not (Test-Path $pythonExe -PathType Leaf)) { $pythonExe = 'python' }
    $notifyScript = Join-Path $PSScriptRoot 'notify_boot.py'
    if (-not (Test-Path $notifyScript -PathType Leaf)) {
        Write-Log "  [notify] skipped: notify_boot.py not found"
        return
    }

    try {
        $output = & $pythonExe $notifyScript "--ok=$OkList" "--fail=$FailList" 2>&1
        foreach ($line in $output) {
            if ($line) { Write-Log "  [notify] $line" }
        }
    } catch {
        Write-Log "  [notify] failed: $_"
    }
}

# ========== main ==========
$pythonwPath = Resolve-Pythonw
$cfg = Get-Config

Write-Log "=== Boot start.ps1 ==="
Write-Log "  project: $ProjectRoot"
Write-Log "  Python: $pythonwPath"
Write-Log "  config: $ConfigPath"

# --- RemoveAutoStart ---
if ($RemoveAutoStart) {
    $vbsPath = $ctx.StartupVbsPath
    if (Test-Path $vbsPath) {
        Remove-Item $vbsPath -Force
        Write-Log "OK removed startup entry"
    } else { Write-Log "startup entry is not installed" }
    exit 0
}

# --- SetupAutoStart ---
if ($SetupAutoStart) {
    $vbsPath = $ctx.StartupVbsPath
    $psCall = "powershell.exe -ExecutionPolicy Bypass -File `"$BootDir\start.ps1`""
    $vbsContent = "Set WshShell = CreateObject(""WScript.Shell"")`r`n" +
                  "WshShell.Run ""$psCall "", 0, False"
    Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII
    Write-Log "OK startup entry installed -> $vbsPath"
    exit 0
}

# --- Status ---
if ($Status) {
    Write-Host ""
    Write-Host "========== GenericAgent Boot status =========="
    Write-Host "config: $ConfigPath"
    $autoStart = Test-Path $ctx.StartupVbsPath
    Write-Host "startup entry: $(if($autoStart){'Y'}else{'N'})"
    Write-Host ""
    Write-Host "Bot                     Enabled Status PID"
    Write-Host "-----------------------------------------------"
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        $bot = $cfg.bots.$key
        $name = $bot.name
        $enabled = if ($bot.enabled) { "Y" } else { "N" }
        $scriptPath = Resolve-GAPath $bot.entry
        $pids = Get-RunningPids $scriptPath
        if ($pids.Count -gt 0) { $st = "running" } else { $st = "stopped" }
        $pidStr = if ($pids.Count -gt 0) { "$($pids -join ',')" } else { "-" }
        Write-Host ("{0,-25} {1,-6} {2,-6} {3}" -f $name, $enabled, $st, $pidStr)
    }
    Write-Host "-----------------------------------------------"
    Write-Host ""
    exit 0
}

# --- Restart: stop all first ---
if ($Restart) {
    Write-Log "--- restart mode: stopping all entries ---"
    Stop-AllBots $cfg
    Start-Sleep -Seconds 1
    Write-Log "--- restart mode: starting entries ---"
}

# --- Stop: graceful stop all ---
if ($Stop) {
    Write-Log "--- stop mode: stopping all entries ---"
    Stop-AllBots $cfg
    Write-Log "--- stop complete ---"
    exit 0
}

# --- determine which bots to start ---
$botKeys = @()
if ($UseSelectedKeys) {
    $selectedList = $SelectedKeys -split ',' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
    $unknown = @()
    foreach ($b in $selectedList) {
        if ($cfg.bots.$b) { $botKeys += $b }
        else { $unknown += $b }
    }
    if ($unknown.Count -gt 0) { Write-Log "  Warn unknown selected bot: $($unknown -join ',') (available: $($cfg.bots.PSObject.Properties.Name -join ', '))" }
    Write-Log "OK one-shot selected entries = $($botKeys -join ',')"
} elseif ($Bots) {
    $botList = $Bots -split ',' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
    foreach ($key in $cfg.bots.PSObject.Properties.Name) { $cfg.bots.$key.enabled = $false }
    $unknown = @()
    foreach ($b in $botList) {
        if ($cfg.bots.$b) { $cfg.bots.$b.enabled = $true; $botKeys += $b }
        else { $unknown += $b }
    }
    if ($unknown.Count -gt 0) { Write-Log "  Warn unknown bot: $($unknown -join ',') (available: $($cfg.bots.PSObject.Properties.Name -join ', '))" }
    Write-Config $cfg
    Write-Log "OK config updated: enabled entries = $Bots"
} else {
    foreach ($key in $cfg.bots.PSObject.Properties.Name) {
        if ($cfg.bots.$key.enabled) { $botKeys += $key }
    }
}

$botKeys = @($botKeys | Select-Object -Unique)
if ($botKeys.Count -eq 0) {
    Write-Log "no entries to start (none selected/enabled; use launcher window, -SelectedKeys, or -Bots)"
    exit 0
}

if (($botKeys -contains "gui") -and ($botKeys -contains "launch")) {
    $botKeys = @($botKeys | Where-Object { $_ -ne "launch" })
    Write-Log "  [GUI] gui already uses launch.pyw; skipped launch to avoid duplicate window"
}

# --- start ---
Write-Log "--- starting entries ---"
$started = @()
$startedFail = @()
$allOk = $true
foreach ($key in $botKeys) {
    $bot = $cfg.bots.$key
    $scriptPath = Resolve-GAPath $bot.entry
    Write-Log "  starting $($bot.name) ($($bot.entry)) ..."
    $pids = Start-Bot $scriptPath $bot.name $key $cfg $pythonwPath
    if ($pids.Count -gt 0) { $started += @{key=$key; name=$bot.name} }
    else { $startedFail += $bot.name; $allOk = $false }
}

# --- verify ---
Write-Log "--- status verification ---"
$startedOk = @()
foreach ($s in $started) {
    $bot = $cfg.bots.$($s.key)
    $scriptPath = Resolve-GAPath $bot.entry
    $pids = Get-RunningPids $scriptPath
    if ($pids.Count -gt 0) { Write-Log "  [OK] $($s.name) running PID=$($pids -join ',')"; $startedOk += $s.name }
    else { Write-Log "  [X] $($s.name) exited"; $allOk = $false; $startedFail += $s.name }
}
if ($allOk) { Write-Log "=== OK all entries started ===" }
else { Write-Log "=== Warn some entries failed; check logs ===" }

# --- bot notification ---
$okList = if ($startedOk.Count -gt 0) { $startedOk -join ', ' } else { '' }
$failList = if ($startedFail.Count -gt 0) { $startedFail -join ', ' } else { '' }
Invoke-BootNotification -OkList $okList -FailList $failList

# startup hint
$vbsPath = $ctx.StartupVbsPath
if (Test-Path $vbsPath) {
    Write-Log "  (startup entry: configured)"
} else {
    Write-Log "  (hint: for startup, place a start.ps1 shortcut in: $env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\)"
}
