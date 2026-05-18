<#
.SYNOPSIS
    GenericAgent desktop launcher.
#>
param(
    [string]$IconFolder = "$PSScriptRoot\icons",
    [string]$ShortcutName = ''
)

. (Join-Path $PSScriptRoot 'common.ps1')
Initialize-GABootConsole

$ctx = Get-GABootContext
$shortcutPath = Get-GAShortcutPath -ShortcutName $ShortcutName
$logFile = Join-Path $ctx.LauncherLogDir ("launcher_{0}.log" -f (Get-Date -Format 'yyyy-MM-dd'))

function Write-LauncherLog {
    param([string]$Message, [string]$Level = 'INFO')
    Write-GALog -Path $logFile -Message $Message -Level $Level -NoConsole
}

Write-LauncherLog '====== Launcher started ======'
Write-Host ''
Write-Host '======================================' -ForegroundColor DarkCyan
Write-Host '  GA desktop launcher - random icon' -ForegroundColor Cyan
Write-Host '======================================' -ForegroundColor DarkCyan
Write-Host ''

$pick = Select-GAIcon -IconDir $IconFolder
if ($pick) {
    if (Set-GAShortcutIcon -ShortcutPath $shortcutPath -IconPath $pick.FullName -LogPath $logFile) {
        Write-LauncherLog "Icon switched: $($pick.Name)"
        Write-Host "Current icon: $($pick.Name)" -ForegroundColor Magenta
    }
} else {
    Write-LauncherLog "No .ico files found in $IconFolder" -Level 'WARN'
}

Write-LauncherLog 'Opening frontend selector...'
$selectorScript = Join-Path $ctx.BootDir 'select_frontends.pyw'
$selectedKeys = ''
if (Test-Path $selectorScript -PathType Leaf) {
    try {
        $selectedKeys = (& python $selectorScript 2>$null)
        $selectorExitCode = $LASTEXITCODE
        if ($selectorExitCode -ne 0) {
            Write-LauncherLog "Frontend selection cancelled or failed (exit=$selectorExitCode)." -Level 'WARN'
            Write-Host ''
            Write-Host 'Frontend selection cancelled. GA was not restarted.' -ForegroundColor Yellow
            Write-LauncherLog '====== Launcher finished ======'
            exit 0
        }
        $selectedKeys = ([string]$selectedKeys).Trim()
        Write-LauncherLog "Frontend selection: $selectedKeys"
    } catch {
        Write-LauncherLog "Frontend selector failed: $_" -Level 'ERROR'
        Write-Host ''
        Write-Host "Frontend selector failed: $_" -ForegroundColor Red
        Write-LauncherLog '====== Launcher finished ======'
        exit 1
    }
} else {
    Write-LauncherLog "Frontend selector not found: $selectorScript" -Level 'ERROR'
    Write-Host ''
    Write-Host "Frontend selector not found: $selectorScript" -ForegroundColor Red
    Write-LauncherLog '====== Launcher finished ======'
    exit 1
}

Write-LauncherLog 'Restarting GA...'
Write-Host ''
Write-Host '=== Restarting GA... ===' -ForegroundColor Green
$startScript = Join-Path $ctx.BootDir 'start.ps1'
& $startScript -Restart -UseSelectedKeys -SelectedKeys $selectedKeys 2>&1 | ForEach-Object { Write-Host $_ }
Write-LauncherLog "start.ps1 -Restart -UseSelectedKeys -SelectedKeys '$selectedKeys' exit code: $LASTEXITCODE"

$exclude = ''
if ($pick) { $exclude = $pick.Name }
$nextPick = Select-GAIcon -IconDir $IconFolder -ExcludeName $exclude
if ($nextPick) {
    if (Set-GAShortcutIcon -ShortcutPath $shortcutPath -IconPath $nextPick.FullName -LogPath $logFile) {
        Write-LauncherLog "Next icon preset: $($nextPick.Name)"
        Write-Host ''
        Write-Host "Next click will show: $($nextPick.Name)" -ForegroundColor Magenta
    }
}

Write-LauncherLog '====== Launcher finished ======'
Write-Host ''
Write-Host 'GA restart complete. Press Enter to close...' -ForegroundColor Green
Read-Host
