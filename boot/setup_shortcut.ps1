<#
.SYNOPSIS
    创建/更新桌面"启动GA"快捷方式
.DESCRIPTION
    快捷方式指向 Windows Terminal (wt.exe)，天然支持 UTF-8。
    每次双击 → 运行 launcher.ps1 → 随机图标 + 停止/启动 GA。
.NOTES
    运行: cd boot; .\setup_shortcut.ps1
    或:   cd boot; .\setup_shortcut.ps1 -Icon "chi (5).ico"
#>
param(
    [string]$Icon = "",          # 指定初始图标文件名（可选，留空则随机）
    [string]$ShortcutName = "启动GA"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$BootDir = $PSScriptRoot
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"
$IconDir = Join-Path $BootDir "icons"

Write-Host ""
Write-Host "══════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host "  🔧 GA 桌面快捷键设置" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host ""

# --- 检查 wt.exe 可用性 ---
$wtPath = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\wt.exe"
if (-not (Test-Path $wtPath)) {
    Write-Host "❌ 未找到 Windows Terminal (wt.exe)" -ForegroundColor Red
    Write-Host "   请从 Microsoft Store 安装 Windows Terminal" -ForegroundColor Yellow
    Write-Host "   或运行: winget install Microsoft.WindowsTerminal" -ForegroundColor Yellow
    exit 1
}

# --- 验证图标目录 ---
if (-not (Test-Path $IconDir)) {
    Write-Host "❌ 图标目录不存在: $IconDir" -ForegroundColor Red
    exit 1
}

$icoFiles = Get-ChildItem $IconDir -Filter "*.ico" -ErrorAction SilentlyContinue
if ($icoFiles.Count -eq 0) {
    Write-Host "❌ 未找到 .ico 图标文件" -ForegroundColor Red
    exit 1
}

# --- 选定图标 ---
if ($Icon -ne "" -and (Test-Path (Join-Path $IconDir $Icon))) {
    $selectedIco = Join-Path $IconDir $Icon
    Write-Host "📌 使用指定图标: $Icon" -ForegroundColor Green
} else {
    $selectedIco = ($icoFiles | Get-Random).FullName
    Write-Host "🎲 随机初始图标: $(Split-Path $selectedIco -Leaf)" -ForegroundColor Magenta
}

# --- 验证 launcher.ps1 ---
$launcherPath = Join-Path $BootDir "launcher.ps1"
if (-not (Test-Path $launcherPath)) {
    Write-Host "❌ launcher.ps1 不存在: $launcherPath" -ForegroundColor Red
    exit 1
}

# --- 创建快捷键 ---
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $sc = $WshShell.CreateShortcut($ShortcutPath)
    
    # 使用 Windows Terminal (原生 UTF-8 支持)
    $sc.TargetPath = $wtPath
    $sc.Arguments = "-d `"$BootDir`" powershell -NoExit -ExecutionPolicy Bypass -Command `"& .\launcher.ps1`""
    $sc.WorkingDirectory = $BootDir
    $sc.IconLocation = "$selectedIco,0"
    $sc.WindowStyle = 1  # Normal
    $sc.Description = "启动 GenericAgent · ちぃ桌面启动器"
    $sc.Save()
    
    Write-Host ""
    Write-Host "✅ 桌面快捷键已创建: $ShortcutPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 快捷键配置:" -ForegroundColor Gray
    Write-Host "   目标:  Windows Terminal (wt.exe)" -ForegroundColor Gray
    Write-Host "   脚本:  launcher.ps1 (UTF-8 BOM)" -ForegroundColor Gray
    Write-Host "   图标:  $(Split-Path $selectedIco -Leaf) (随机池: $($icoFiles.Count) 个)" -ForegroundColor Gray
    Write-Host "   功能:  双击 → 随机图标 + 停止GA → 启动GA → 预设下次图标" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🎲 双击桌面 '启动GA' 即可使用！" -ForegroundColor Cyan
    Write-Host "   每次点击都会显示不同的ちぃ图标哦~" -ForegroundColor DarkCyan
} catch {
    Write-Host "❌ 创建快捷键失败: $_" -ForegroundColor Red
    exit 1
}
