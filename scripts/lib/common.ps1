# ZapUnlocked API — Common UI Library for Windows
# Provides reusable UI components via Gum.
# Source this file in PowerShell scripts.

$script:StartTime = Get-Date

function Get-Elapsed {
    $diff = (Get-Date) - $script:StartTime
    if ($diff.TotalMinutes -ge 1) {
        return "$([math]::Floor($diff.TotalMinutes))m$($diff.Seconds)s"
    }
    return "$($diff.Seconds)s"
}

function Get-RamPct {
    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        return [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize * 100)
    } catch { return "?" }
}

function Get-CpuPct {
    try {
        $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop
        return $cpu.LoadPercentage
    } catch { return "?" }
}

function Get-PyVer {
    try {
        $v = & python --version 2>&1
        if ($v -match '\d+\.\d+\.\d+') { return $matches[0] }
    } catch {}
    try {
        $v = & python3 --version 2>&1
        if ($v -match '\d+\.\d+\.\d+') { return $matches[0] }
    } catch {}
    return "N/A"
}

function Get-UpTime {
    return Get-Elapsed
}

function Show-Banner {
    $P = @{ForegroundColor = "DarkMagenta" }
    Write-Host ""
    Write-Host "███████╗ █████╗ ██████╗ ██╗   ██╗███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗        █████╗ ██████╗ ██╗" @P
    Write-Host "╚══███╔╝██╔══██╗██╔══██╗██║   ██║████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██║" @P
    Write-Host "  ███╔╝ ███████║██████╔╝██║   ██║██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ █████╗  ██║  ██║█████╗███████║██████╔╝██║" @P
    Write-Host " ███╔╝  ██╔══██║██╔═══╝ ██║   ██║██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██║  ██║╚════╝██╔══██║██╔═══╝ ██║" @P
    Write-Host "███████╗██║  ██║██║     ╚██████╔╝██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██████╔╝      ██║  ██║██║     ██║" @P
    Write-Host "╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝       ╚═╝  ╚═╝╚═╝     ╚═╝" @P
    Write-Host ""
}

function Show-Tags {
    param([string]$Icon, [string]$Label, [string]$OsLabel = "")
    $py  = Get-PyVer

    $items = @()
    $items += & gum style --border rounded --padding "0 1" --foreground "#C084FC" "PY ${py}"
    $items += "  "
    $items += & gum style --border rounded --padding "0 1" --foreground "#8B3DFF" --bold "${Icon} ${Label}"
    if ($OsLabel) {
        $items += "  "
        $items += & gum style --border rounded --padding "0 1" --foreground "#8B3DFF" "$OsLabel"
    }

    & gum join --horizontal @items
}

# ── Header state (for in-place refresh) ──────────────────────────────
$script:HeaderIcon = ""
$script:HeaderLabel = ""
$script:HeaderOs = ""

function Init-Header {
    param([string]$Icon, [string]$Label, [string]$OsLabel = "")
    $script:HeaderIcon = $Icon
    $script:HeaderLabel = $Label
    $script:HeaderOs = $OsLabel
}

function Refresh-Header {
    $py  = Get-PyVer

    $items = @()
    $items += & gum style --border rounded --padding "0 1" --foreground "#C084FC" "PY ${py}"
    $items += "  "
    $items += & gum style --border rounded --padding "0 1" --foreground "#8B3DFF" --bold "${script:HeaderIcon} ${script:HeaderLabel}"
    if ($script:HeaderOs) {
        $items += "  "
        $items += & gum style --border rounded --padding "0 1" --foreground "#8B3DFF" "$($script:HeaderOs)"
    }

    Write-Host -NoNewline "`e[5A`e[J"
    & gum join --horizontal @items
    Show-Sep
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
    Write-Host ""
    & gum style --foreground "#42C292" --border-foreground "#8B3DFF" --border rounded --align center --width 46 --padding "0 1" "✓ $Message  ($(Get-Elapsed))"
    Write-Host ""
}
