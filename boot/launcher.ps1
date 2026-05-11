<#
.SYNOPSIS
    GA 桌面启动器：切换快捷方式图标并重启配置中启用的组件。
#>
param(
    [string]$IconFolder = "$PSScriptRoot\icons",
    [string]$ShortcutName = '启动GA'
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

Write-LauncherLog '====== Launcher 启动 ======'
Write-Host ''
Write-Host '══════════════════════════════════════' -ForegroundColor DarkCyan
Write-Host '  GA 桌面启动器 · 随机图标模式' -ForegroundColor Cyan
Write-Host '══════════════════════════════════════' -ForegroundColor DarkCyan
Write-Host ''

$pick = Select-GAIcon -IconDir $IconFolder
if ($pick) {
    if (Set-GAShortcutIcon -ShortcutPath $shortcutPath -IconPath $pick.FullName -LogPath $logFile) {
        Write-LauncherLog "图标已切换: $($pick.Name)"
        Write-Host "本次图标: $($pick.Name)" -ForegroundColor Magenta
    }
} else {
    Write-LauncherLog "未找到 .ico 文件在 $IconFolder" -Level 'WARN'
}

Write-LauncherLog '重启 GA...'
Write-Host ''
Write-Host '=== 重启 GA 中... ===' -ForegroundColor Green
$startScript = Join-Path $ctx.BootDir 'start.ps1'
& $startScript -Restart 2>&1 | ForEach-Object { Write-Host $_ }
Write-LauncherLog "start.ps1 -Restart 退出码: $LASTEXITCODE"

$exclude = ''
if ($pick) { $exclude = $pick.Name }
$nextPick = Select-GAIcon -IconDir $IconFolder -ExcludeName $exclude
if ($nextPick) {
    if (Set-GAShortcutIcon -ShortcutPath $shortcutPath -IconPath $nextPick.FullName -LogPath $logFile) {
        Write-LauncherLog "下次图标已预设: $($nextPick.Name)"
        Write-Host ''
        Write-Host "下次点击将显示: $($nextPick.Name)" -ForegroundColor Magenta
    }
}

Write-LauncherLog '====== Launcher 完成 ======'
Write-Host ''
Write-Host 'GA 重启完成。按 Enter 关闭...' -ForegroundColor Green
Read-Host
