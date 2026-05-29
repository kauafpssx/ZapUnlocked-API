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
    param([string]$Icon, [string]$Label)
    $ram = Get-RamPct
    $cpu = Get-CpuPct
    $py  = Get-PyVer
    $up  = Get-UpTime

    $tags = @(
        @{ text = "RAM ${ram}%";  color = "#8B3DFF" }
        @{ text = "CPU ${cpu}%";  color = "#A855F7" }
        @{ text = "PY ${py}";     color = "#C084FC" }
        @{ text = "UP ${up}";     color = "#6B7280" }
        @{ text = "${Icon} ${Label}"; color = "#8B3DFF" }
    )

    $items = @()
    foreach ($t in $tags) {
        $item = & gum style --border rounded --padding "0 1" --foreground $t.color $t.text
        $items += $item
    }

    & gum join --horizontal @items
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

function Write-Info  { & gum style --foreground "#A855F7" "  ◉ $args" }
function Write-Ok    { & gum style --foreground "#42C292" "  ✓ $args" }
function Write-Warn  { & gum style --foreground "#F59E0B" "  ⚠ $args" }
function Write-Err   { & gum style --foreground "#EF4444" "  ✖ $args" }
function Write-Step  { & gum style --foreground "#6B7280" "  · $args" }

function Show-Footer {
    param([string]$Message)
    Write-Host ""
    & gum style --foreground "#42C292" --border-foreground "#8B3DFF" --border rounded --align center --width 46 --padding "0 1" "✓ $Message  ($(Get-Elapsed))"
    Write-Host ""
}
