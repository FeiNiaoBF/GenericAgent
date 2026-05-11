function Initialize-GABootConsole {
    try {
        $utf8 = [System.Text.UTF8Encoding]::new($false)
        [Console]::InputEncoding = $utf8
        [Console]::OutputEncoding = $utf8
        $script:OutputEncoding = $utf8
        $global:OutputEncoding = $utf8
        $PSDefaultParameterValues['*:Encoding'] = 'utf8'
    } catch {}
}

function Get-GADefaultShortcutName {
    return ([string]::Concat([char]0x542F, [char]0x52A8, 'GA'))
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
                Write-Host "$time Warn log write failed: $($_.Exception.Message)" -ForegroundColor Yellow
                $script:GALogWriteWarnings[$Path] = $true
            }
        }
    }

    if (-not $NoConsole) { Write-Host $line }
}

function Get-GAShortcutPath {
    param([string]$ShortcutName = '')
    if ([string]::IsNullOrWhiteSpace($ShortcutName)) {
        $ShortcutName = Get-GADefaultShortcutName
    }
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

function Get-GAPowerShellPath {
    foreach ($name in @('pwsh.exe', 'powershell.exe')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw 'PowerShell executable not found'
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
        if ($LogPath) { Write-GALog -Path $LogPath -Message "Shortcut not found: $ShortcutPath" -Level 'ERROR' -NoConsole }
        Write-Host 'Shortcut not found. Run setup_shortcut.ps1 first.' -ForegroundColor Red
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
        if ($LogPath) { Write-GALog -Path $LogPath -Message "Icon update failed: $_" -Level 'ERROR' -NoConsole }
        return $false
    }
}

function New-GADesktopShortcut {
    param(
        [string]$ShortcutName = '',
        [string]$IconPath,
        [string]$BootDir = (Get-GABootContext).BootDir
    )
    if ([string]::IsNullOrWhiteSpace($ShortcutName)) {
        $ShortcutName = Get-GADefaultShortcutName
    }
    $wtPath = Get-GAWindowsTerminalPath
    if (-not $wtPath) { throw 'Windows Terminal not found (wt.exe)' }

    $launcherPath = Join-Path $BootDir 'launcher.ps1'
    if (-not (Test-Path $launcherPath -PathType Leaf)) {
        throw "launcher.ps1 not found: $launcherPath"
    }

    $shortcutPath = Get-GAShortcutPath -ShortcutName $ShortcutName
    $psPath = Get-GAPowerShellPath
    $cmdPath = $env:ComSpec
    if (-not $cmdPath) { $cmdPath = Join-Path $env:SystemRoot 'System32\cmd.exe' }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $cmdPath
    $shortcut.Arguments = "/d /c start `"`" `"%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe`" -d `"$BootDir`" `"$psPath`" -NoLogo -NoExit -ExecutionPolicy Bypass -File `"$launcherPath`""
    $shortcut.WorkingDirectory = $BootDir
    $shortcut.IconLocation = "$IconPath,0"
    $shortcut.WindowStyle = 1
    $shortcut.Description = 'Start GenericAgent desktop launcher'
    $shortcut.Save()
    return $shortcutPath
}
