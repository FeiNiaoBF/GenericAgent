<#
.SYNOPSIS
    GA 桌面启动器 — 每次点击随机切换ちぃ图标，一键重启
.DESCRIPTION
    双击桌面"启动GA.lnk"即运行此脚本。
    1. 随机选取 icons/ 下一个 .ico 立即更新快捷方式图标
    2. 调用 start.ps1 -Restart 优雅重启所有bot
    3. 完成后再次随机选图标预设下次点击显示
#>
param(
    [string]$IconFolder = "$PSScriptRoot\icons"
)

# === 初始化 ===
$BootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "启动GA.lnk"
$LogDir = Join-Path $BootDir "logs"
$LogFile = Join-Path $LogDir ("launcher_{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# 强制 UTF-8 输出
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

function Write-Log {
    param([string]$Msg, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts [$Level] $Msg" | Add-Content -Path $LogFile -Encoding UTF8
}

function Update-ShortcutIcon {
    param([string]$IconFullPath)
    if (-not (Test-Path $ShortcutPath)) {
        Write-Log "快捷键不存在: $ShortcutPath" -Level "ERROR"
        Write-Host "快捷键不存在，请先运行 setup_shortcut.ps1" -ForegroundColor Red
        return $false
    }
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $sc = $WshShell.CreateShortcut($ShortcutPath)
        $sc.IconLocation = "$IconFullPath,0"
        $sc.Save()
        # 刷新图标缓存
        ie4uinit.exe -show 2>$null
        return $true
    } catch {
        Write-Log "图标更新失败: $_" -Level "ERROR"
        return $false
    }
}

function Get-RandomIcon {
    param([string]$Folder)
    if (-not (Test-Path $Folder)) {
        Write-Log "图标目录不存在: $Folder" -Level "ERROR"
        return $null
    }
    $icoFiles = Get-ChildItem $Folder -Filter "*.ico" -ErrorAction SilentlyContinue
    if ($icoFiles.Count -eq 0) {
        Write-Log "未找到 .ico 文件在 $Folder" -Level "WARN"
        return $null
    }
    return $icoFiles | Get-Random
}

# ============================================================
#  主流程
# ============================================================
Write-Log "====== Launcher 启动 ======"
Write-Host ""
Write-Host "══════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host "  🎲  GA 桌面启动器 · 随机图标模式" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host ""

# --- 第1步：随机选图标，立即更新快捷方式 ---
$pick = Get-RandomIcon -Folder $IconFolder
if ($pick) {
    if (Update-ShortcutIcon -IconFullPath $pick.FullName) {
        Write-Log "图标已切换: $($pick.Name)"
        Write-Host "🌸 本次图标: $($pick.Name)" -ForegroundColor Magenta
    }
}

# --- 第2步：重启bot（优雅停止→启动） ---
Write-Log "重启 GA..."
Write-Host ""
Write-Host "🔄 === 重启 GA 中... ===" -ForegroundColor Green
$startScript = Join-Path $BootDir "start.ps1"
& $startScript -Restart 2>&1 | ForEach-Object { Write-Host $_ }
Write-Log "start.ps1 -Restart 退出码: $LASTEXITCODE"

# --- 第3步：预设下次点击的随机图标 ---
$nextPick = Get-RandomIcon -Folder $IconFolder
if ($nextPick) {
    # 确保和本次不同（如果有多个图标）
    $iconCount = @(Get-ChildItem $IconFolder -Filter "*.ico" -ErrorAction SilentlyContinue).Count
    if ($pick -and $iconCount -gt 1) {
        while ($nextPick.Name -eq $pick.Name) {
            $nextPick = Get-RandomIcon -Folder $IconFolder
        }
    }
    if (Update-ShortcutIcon -IconFullPath $nextPick.FullName) {
        Write-Log "下次图标已预设: $($nextPick.Name)"
        Write-Host ""
        Write-Host "🎲 下次点击将显示: $($nextPick.Name)" -ForegroundColor Magenta
    }
}

Write-Log "====== Launcher 完成 ======"
Write-Host ""
Write-Host "✅ GA 重启完成！按任意键关闭..." -ForegroundColor Green
Read-Host
