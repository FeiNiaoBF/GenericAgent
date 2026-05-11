<#
.SYNOPSIS
    Create or update the GenericAgent desktop shortcut.
#>
param(
    [string]$Icon = '',
    [string]$ShortcutName = ''
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Initialize-GABootConsole

$ctx = Get-GABootContext
$iconDir = $ctx.IconDir

Write-Host ''
Write-Host '======================================' -ForegroundColor DarkCyan
Write-Host '  GA desktop shortcut setup' -ForegroundColor Cyan
Write-Host '======================================' -ForegroundColor DarkCyan
Write-Host ''

$wtPath = Get-GAWindowsTerminalPath
if (-not $wtPath) {
    Write-Host 'Windows Terminal not found (wt.exe)' -ForegroundColor Red
    Write-Host 'Install Windows Terminal from Microsoft Store or run: winget install Microsoft.WindowsTerminal' -ForegroundColor Yellow
    exit 1
}

$icons = Get-GAIconFiles -IconDir $iconDir
if ($icons.Count -eq 0) {
    Write-Host "No .ico icon files found: $iconDir" -ForegroundColor Red
    exit 1
}

$selectedIcon = Select-GAIcon -IconDir $iconDir -IconName $Icon
if (-not $selectedIcon) {
    Write-Host "No usable icon found: $iconDir" -ForegroundColor Red
    exit 1
}

if ($Icon -and $selectedIcon.Name -eq $Icon) {
    Write-Host "Using requested icon: $Icon" -ForegroundColor Green
} elseif ($Icon) {
    Write-Host "Requested icon not found; using random icon: $($selectedIcon.Name)" -ForegroundColor Yellow
} else {
    Write-Host "Random initial icon: $($selectedIcon.Name)" -ForegroundColor Magenta
}

try {
    $shortcutPath = New-GADesktopShortcut -ShortcutName $ShortcutName -IconPath $selectedIcon.FullName -BootDir $ctx.BootDir
    Write-Host ''
    Write-Host "Desktop shortcut created: $shortcutPath" -ForegroundColor Green
    Write-Host ''
    Write-Host 'Shortcut config:' -ForegroundColor Gray
    Write-Host "   Target: cmd -> Windows Terminal ($wtPath)" -ForegroundColor Gray
    Write-Host '   Script: launcher.ps1' -ForegroundColor Gray
    Write-Host "   Icon:   $($selectedIcon.Name) (pool: $($icons.Count))" -ForegroundColor Gray
    Write-Host '   Flow:   double click -> random icon -> stop GA -> start GA -> preset next icon' -ForegroundColor Gray
    Write-Host ''
    if ([string]::IsNullOrWhiteSpace($ShortcutName)) { $ShortcutName = Get-GADefaultShortcutName }
    Write-Host "Double-click desktop shortcut '$ShortcutName' to start." -ForegroundColor Cyan
} catch {
    Write-Host "Shortcut creation failed: $_" -ForegroundColor Red
    exit 1
}
