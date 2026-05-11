<#
.SYNOPSIS
    创建或更新桌面“启动GA”快捷方式。
#>
param(
    [string]$Icon = '',
    [string]$ShortcutName = '启动GA'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
Initialize-GABootConsole

$ctx = Get-GABootContext
$iconDir = $ctx.IconDir

Write-Host ''
Write-Host '══════════════════════════════════════' -ForegroundColor DarkCyan
Write-Host '  GA 桌面快捷键设置' -ForegroundColor Cyan
Write-Host '══════════════════════════════════════' -ForegroundColor DarkCyan
Write-Host ''

$wtPath = Get-GAWindowsTerminalPath
if (-not $wtPath) {
    Write-Host '未找到 Windows Terminal (wt.exe)' -ForegroundColor Red
    Write-Host '请从 Microsoft Store 安装 Windows Terminal，或运行: winget install Microsoft.WindowsTerminal' -ForegroundColor Yellow
    exit 1
}

$icons = Get-GAIconFiles -IconDir $iconDir
if ($icons.Count -eq 0) {
    Write-Host "未找到 .ico 图标文件: $iconDir" -ForegroundColor Red
    exit 1
}

$selectedIcon = Select-GAIcon -IconDir $iconDir -IconName $Icon
if (-not $selectedIcon) {
    Write-Host "未找到可用图标: $iconDir" -ForegroundColor Red
    exit 1
}

if ($Icon -and $selectedIcon.Name -eq $Icon) {
    Write-Host "使用指定图标: $Icon" -ForegroundColor Green
} elseif ($Icon) {
    Write-Host "指定图标不存在，改用随机图标: $($selectedIcon.Name)" -ForegroundColor Yellow
} else {
    Write-Host "随机初始图标: $($selectedIcon.Name)" -ForegroundColor Magenta
}

try {
    $shortcutPath = New-GADesktopShortcut -ShortcutName $ShortcutName -IconPath $selectedIcon.FullName -BootDir $ctx.BootDir
    Write-Host ''
    Write-Host "桌面快捷键已创建: $shortcutPath" -ForegroundColor Green
    Write-Host ''
    Write-Host '快捷键配置:' -ForegroundColor Gray
    Write-Host "   目标:  Windows Terminal ($wtPath)" -ForegroundColor Gray
    Write-Host '   脚本:  launcher.ps1' -ForegroundColor Gray
    Write-Host "   图标:  $($selectedIcon.Name) (随机池: $($icons.Count) 个)" -ForegroundColor Gray
    Write-Host '   功能:  双击 -> 随机图标 -> 停止GA -> 启动GA -> 预设下次图标' -ForegroundColor Gray
    Write-Host ''
    Write-Host "双击桌面 '$ShortcutName' 即可使用。" -ForegroundColor Cyan
} catch {
    Write-Host "创建快捷键失败: $_" -ForegroundColor Red
    exit 1
}
