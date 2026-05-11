function Initialize-GABootConsole {
    try {
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        $PSDefaultParameterValues['*:Encoding'] = 'utf8'
    } catch {}
}

function Get-GABootContext {
    $bootDir = $PSScriptRoot
    $projectRoot = (Resolve-Path (Join-Path $bootDir '..')).Path
    [pscustomobject]@{
        BootDir = $bootDir
        ProjectRoot = $projectRoot
        ConfigPath = Join-Path $projectRoot 'config\boot_config.json'
        ConfigExamplePath = Join-Path $projectRoot 'config\boot_config.example.json'
        RootLogPath = Join-Path $projectRoot 'logs\boot.log'
        IconDir = Join-Path $bootDir 'icons'
        LauncherLogDir = Join-Path $bootDir 'logs'
        StartupVbsPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\GenericAgent.vbs'
    }
}

function Resolve-GAPath {
    param(
        [string]$PathValue,
        [string]$ProjectRoot = (Get-GABootContext).ProjectRoot
    )
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $null }
    $expanded = [Environment]::ExpandEnvironmentVariables(
        $ExecutionContext.InvokeCommand.ExpandString($PathValue)
    )
    if ([System.IO.Path]::IsPathRooted($expanded)) { return $expanded }
    return Join-Path $ProjectRoot $expanded
}

function Write-GALog {
    param(
        [string]$Path,
        [string]$Message,
        [string]$Level = '',
        [switch]$NoConsole
    )
    $time = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    if ([string]::IsNullOrWhiteSpace($Level)) {
        $line = "$time $Message"
    } else {
        $line = "$time [$Level] $Message"
    }

    if ($Path) {
        try {
            $dir = Split-Path $Path
            if ($dir -and -not (Test-Path $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
            }
            Add-Content -Path $Path -Value $line -Encoding UTF8 -ErrorAction Stop
        } catch {
            if (-not $script:GALogWriteWarnings) { $script:GALogWriteWarnings = @{} }
            if (-not $script:GALogWriteWarnings.ContainsKey($Path)) {
                Write-Host "$time Warn 日志写入失败: $($_.Exception.Message)" -ForegroundColor Yellow
                $script:GALogWriteWarnings[$Path] = $true
            }
        }
    }

    if (-not $NoConsole) { Write-Host $line }
}

function Get-GAShortcutPath {
    param([string]$ShortcutName = '启动GA')
    $desktop = [Environment]::GetFolderPath('Desktop')
    return Join-Path $desktop "$ShortcutName.lnk"
}

function Get-GAWindowsTerminalPath {
    $candidate = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\wt.exe'
    if (Test-Path $candidate -PathType Leaf) { return $candidate }
    $cmd = Get-Command wt.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Get-GAIconFiles {
    param([string]$IconDir)
    if (-not (Test-Path $IconDir)) { return @() }
    return @(Get-ChildItem $IconDir -Filter '*.ico' -File -ErrorAction SilentlyContinue)
}

function Select-GAIcon {
    param(
        [string]$IconDir,
        [string]$IconName = '',
        [string]$ExcludeName = ''
    )
    $icons = Get-GAIconFiles -IconDir $IconDir
    if ($icons.Count -eq 0) { return $null }

    if (-not [string]::IsNullOrWhiteSpace($IconName)) {
        $named = Join-Path $IconDir $IconName
        if (Test-Path $named -PathType Leaf) { return Get-Item $named }
    }

    $pool = $icons
    if ($ExcludeName -and $icons.Count -gt 1) {
        $pool = @($icons | Where-Object { $_.Name -ne $ExcludeName })
    }
    return $pool | Get-Random
}

function Update-GAIconCache {
    try { ie4uinit.exe -show 2>$null } catch {}
}

function Set-GAShortcutIcon {
    param(
        [string]$ShortcutPath,
        [string]$IconPath,
        [string]$LogPath = ''
    )
    if (-not (Test-Path $ShortcutPath)) {
        if ($LogPath) { Write-GALog -Path $LogPath -Message "快捷键不存在: $ShortcutPath" -Level 'ERROR' -NoConsole }
        Write-Host '快捷键不存在，请先运行 setup_shortcut.ps1' -ForegroundColor Red
        return $false
    }
    try {
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($ShortcutPath)
        $shortcut.IconLocation = "$IconPath,0"
        $shortcut.Save()
        Update-GAIconCache
        return $true
    } catch {
        if ($LogPath) { Write-GALog -Path $LogPath -Message "图标更新失败: $_" -Level 'ERROR' -NoConsole }
        return $false
    }
}

function New-GADesktopShortcut {
    param(
        [string]$ShortcutName,
        [string]$IconPath,
        [string]$BootDir = (Get-GABootContext).BootDir
    )
    $wtPath = Get-GAWindowsTerminalPath
    if (-not $wtPath) { throw '未找到 Windows Terminal (wt.exe)' }

    $launcherPath = Join-Path $BootDir 'launcher.ps1'
    if (-not (Test-Path $launcherPath -PathType Leaf)) {
        throw "launcher.ps1 不存在: $launcherPath"
    }

    $shortcutPath = Get-GAShortcutPath -ShortcutName $ShortcutName
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $wtPath
    $shortcut.Arguments = "-d `"$BootDir`" powershell -NoExit -ExecutionPolicy Bypass -Command `"& .\launcher.ps1`""
    $shortcut.WorkingDirectory = $BootDir
    $shortcut.IconLocation = "$IconPath,0"
    $shortcut.WindowStyle = 1
    $shortcut.Description = '启动 GenericAgent 桌面启动器'
    $shortcut.Save()
    return $shortcutPath
}
