# ZapUnlocked API — Common UI Library for Windows
# Provides reusable UI components via Gum.
# Source this file in PowerShell scripts.

# ── Fix encoding for gum (UTF-8) ──────────────────────────────────────
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

# ── Gum auto-install ──────────────────────────────────────────────────
$script:GumPath = "$env:USERPROFILE\.local\bin\gum.exe"
if (!(Get-Command gum -ErrorAction SilentlyContinue) -and !(Test-Path $script:GumPath)) {
    Write-Host "Installing gum..."
    $tmp = "$env:TEMP\gum_install"
    New-Item -ItemType Directory -Force -Path $tmp > $null
    try {
        $tag = (Invoke-WebRequest -Uri "https://api.github.com/repos/charmbracelet/gum/releases/latest" -UseBasicParsing | ConvertFrom-Json).tag_name
        $ver = $tag.TrimStart('v')
        $zip = "$tmp\gum.zip"
        Invoke-WebRequest -Uri "https://github.com/charmbracelet/gum/releases/download/$tag/gum_${ver}_Windows_x86_64.zip" -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath $tmp -Force
        New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.local\bin" > $null
        Move-Item -Path "$tmp\gum_${ver}_Windows_x86_64\gum.exe" -Destination $script:GumPath -Force
        [Environment]::SetEnvironmentVariable("Path", "$env:USERPROFILE\.local\bin;$env:Path", "User")
    } catch {
        Write-Host "[WARN] Failed to download gum. Install manually: winget install charmbracelet.gum"
    }
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
if (Test-Path $script:GumPath) {
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# ── Venv Python detection ─────────────────────────────────────────────
$script:VenvPython = ""
$script:PyVer = ""
function Set-VenvPython {
    $root = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..\..").Path } else { (Get-Location).Path }
    $vp = "$root\.venv\Scripts\python.exe"
    if (Test-Path $vp) {
        $script:VenvPython = $vp
        try {
            $v = & $script:VenvPython --version 2>&1
            if ($v -match '\d+\.\d+\.\d+') { $script:PyVer = $matches[0] }
        } catch {}
    }
    if (!$script:PyVer) {
        try {
            $v = & python --version 2>&1
            if ($v -match '\d+\.\d+\.\d+') { $script:PyVer = $matches[0] }
        } catch {}
    }
    if (!$script:PyVer) {
        try {
            $v = & python3 --version 2>&1
            if ($v -match '\d+\.\d+\.\d+') { $script:PyVer = $matches[0] }
        } catch {}
    }
    if (!$script:PyVer) { $script:PyVer = "N/A" }
}
Set-VenvPython

$script:StartTimeFile = "$env:TEMP\zap_start.txt"
if ((Test-Path $script:StartTimeFile) -and ((Get-Date) - (Get-Item $script:StartTimeFile).LastWriteTime).TotalMinutes -lt 5) {
    $script:StartTime = [DateTime]::Parse((Get-Content $script:StartTimeFile -Raw -ErrorAction SilentlyContinue).Trim())
} else {
    $script:StartTime = Get-Date
    $script:StartTime.ToString('o') | Set-Content $script:StartTimeFile -NoNewline
}

function Get-Elapsed {
    $diff = (Get-Date) - $script:StartTime
    if ($diff.TotalMinutes -ge 1) {
        return "$([math]::Floor($diff.TotalMinutes))m$($diff.Seconds)s"
    }
    return "$($diff.Seconds)s"
}

function Get-PyVer {
    return $script:PyVer
}

$script:Purple = "$([char]27)[38;2;139;61;255m"
$script:Reset  = "$([char]27)[0m"

function Show-Banner {
    Write-Host ""
    Write-Host "$($script:Purple)███████╗ █████╗ ██████╗ ██╗   ██╗███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗        █████╗ ██████╗ ██╗$($script:Reset)"
    Write-Host "$($script:Purple)╚══███╔╝██╔══██╗██╔══██╗██║   ██║████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██║$($script:Reset)"
    Write-Host "$($script:Purple)  ███╔╝ ███████║██████╔╝██║   ██║██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ █████╗  ██║  ██║█████╗███████║██████╔╝██║$($script:Reset)"
    Write-Host "$($script:Purple) ███╔╝  ██╔══██║██╔═══╝ ██║   ██║██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██║  ██║╚════╝██╔══██║██╔═══╝ ██║$($script:Reset)"
    Write-Host "$($script:Purple)███████╗██║  ██║██║     ╚██████╔╝██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██████╔╝      ██║  ██║██║     ██║$($script:Reset)"
    Write-Host "$($script:Purple)╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝       ╚═╝  ╚═╝╚═╝     ╚═╝$($script:Reset)"
    Write-Host ""
}

function Get-GumBlock {
    param([scriptblock]$Script)
    $r = & $Script @args
    if ($r -is [array]) { return $r -join "`n" }
    return $r
}

$script:IconMap = @{
    install = "⬇"
    run     = "▶"
    remove  = "✕"
    genenv  = "⚙"
}

function Show-Tags {
    param([string]$Task, [string]$OsLabel = "")
    $py  = Get-PyVer
    $icon = $script:IconMap[$Task]
    $label = $Task.ToUpper()

    $items = @()
    $items += Get-GumBlock { param($v) & gum style --border rounded --padding "0 1" --foreground "#C084FC" "PY $v" } $py
    $items += "  "
    $items += Get-GumBlock { param($i,$l) & gum style --border rounded --padding "0 1" --foreground "#8B3DFF" --bold "$i $l" } $icon $label
    if ($OsLabel) {
        $items += "  "
        $items += Get-GumBlock { param($o) & gum style --border rounded --padding "0 1" --foreground "#8B3DFF" "$o" } $OsLabel
    }

    & gum join --horizontal @items
}

$script:HeaderTask = ""
$script:HeaderOs = ""

function Init-Header {
    param([string]$Task, [string]$OsLabel = "")
    $script:HeaderTask = $Task
    $script:HeaderOs = $OsLabel
}

function Refresh-Header {
    # re-display header inline (no-op - deprecated)
}

function Show-Sep {
    $line = "─" * 68
    & gum style --foreground "#4B5563" $line
}

function Show-Task {
    param([string]$Label)
    Write-Host ""
    & gum style --foreground "#E9D5FF" --bold "  $Label"
}

function Write-Info  { Write-Host "  " -NoNewline; Write-Host "◉" -NoNewline -ForegroundColor DarkMagenta; Write-Host " $args" }
function Write-Ok    { Write-Host "  " -NoNewline; Write-Host "✓" -NoNewline -ForegroundColor Green; Write-Host " $args" }
function Write-Warn  { Write-Host "  " -NoNewline; Write-Host "⚠" -NoNewline -ForegroundColor Yellow; Write-Host " $args" }
function Write-Err   { Write-Host "  " -NoNewline; Write-Host "✖" -NoNewline -ForegroundColor Red; Write-Host " $args" }
function Write-Step  { Write-Host "  " -NoNewline; Write-Host "·" -NoNewline -ForegroundColor Gray; Write-Host " $args" }

function Show-Footer {
    param([string]$Message)
    Remove-Item $script:StartTimeFile -ErrorAction SilentlyContinue
    Write-Host ""
    & gum style --foreground "#42C292" --border-foreground "#8B3DFF" --border rounded --align center --width 46 --padding "0 1" "✓ $Message  ($(Get-Elapsed))"
    Write-Host ""
}
