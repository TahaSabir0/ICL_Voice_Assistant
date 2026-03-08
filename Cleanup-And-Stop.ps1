# ICL Voice Assistant - Cleanup & Stop Script
# Stops Ollama, kills running processes, and cleans up resources

param(
    [switch]$Force         # Force kill without prompting
)

# Colors
function Write-Header { Write-Host $args[0] -ForegroundColor Cyan -BackgroundColor Black }
function Write-Success { Write-Host $args[0] -ForegroundColor Green }
function Write-Warn   { Write-Host $args[0] -ForegroundColor Yellow }
function Write-Err    { Write-Host $args[0] -ForegroundColor Red }

Write-Host ""
Write-Header "╔════════════════════════════════════════════════════════════════╗"
Write-Header "║  ICL Voice Assistant - Cleanup & Stop                          ║"
Write-Header "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

# ============================================================================
# Step 1: Stop Ollama (process + tray app + service)
# ============================================================================
Write-Header "Step 1: Stopping Ollama..."

$ollamaStopped = $false

# Kill all Ollama-related processes (cli, tray app, server)
$ollamaProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -match "^ollama"
}

if ($ollamaProcesses) {
    Write-Warn "  Found Ollama process(es): $($ollamaProcesses.ProcessName -join ', ')"

    try {
        $ollamaProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2

        # Verify they're gone
        $stillRunning = Get-Process -ErrorAction SilentlyContinue | Where-Object {
            $_.ProcessName -match "^ollama"
        }

        if ($stillRunning) {
            Write-Warn "  Some processes persisted, force killing..."
            $stillRunning | Stop-Process -Force -ErrorAction SilentlyContinue
        }

        $ollamaStopped = $true
        Write-Success "✓ Ollama processes stopped"
    } catch {
        Write-Err "✗ Failed to stop Ollama: $_"
    }
} else {
    Write-Success "✓ Ollama not running"
}

# Also stop the Windows service if it exists
$ollamaSvc = Get-Service -Name "OllamaService" -ErrorAction SilentlyContinue
if ($ollamaSvc -and $ollamaSvc.Status -eq "Running") {
    Write-Warn "  Stopping Ollama Windows service..."
    try {
        Stop-Service -Name "OllamaService" -Force -ErrorAction Stop
        Write-Success "✓ Ollama service stopped"
    } catch {
        Write-Warn "  Could not stop service (may need Admin): $_"
    }
}

# ============================================================================
# Step 2: Kill Python processes running the kiosk
# ============================================================================
Write-Host ""
Write-Header "Step 2: Stopping ICL Voice Assistant processes..."

# Use WMI/CIM to get the actual command line — Get-Process.CommandLine
# is NOT available in Windows PowerShell 5.1
$kiosked = $false
try {
    $wmiProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction Stop
    $kioskProcesses = $wmiProcesses | Where-Object {
        $_.CommandLine -match "launch_kiosk|kiosk_app|src[/\\]main"
    }

    if ($kioskProcesses) {
        Write-Warn "  Found $($kioskProcesses.Count) kiosk process(es):"
        foreach ($proc in $kioskProcesses) {
            Write-Host "    PID $($proc.ProcessId): $($proc.CommandLine)"
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
        $kiosked = $true
        Write-Success "✓ Application processes stopped"
    } else {
        Write-Success "✓ No kiosk processes found"
    }
} catch {
    # Fallback: if CIM fails, kill all python processes with user confirmation
    Write-Warn "  Could not inspect command lines. Checking for any Python processes..."
    $allPython = Get-Process -Name "python" -ErrorAction SilentlyContinue

    if ($allPython) {
        Write-Warn "  Found $($allPython.Count) Python process(es)."

        if ($Force) {
            $allPython | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Success "✓ All Python processes stopped (forced)"
            $kiosked = $true
        } else {
            Write-Host "  Cannot determine which are kiosk processes."
            Write-Host "  Run with -Force to kill ALL Python processes,"
            Write-Host "  or close the kiosk window manually."
        }
    } else {
        Write-Success "✓ No Python processes running"
    }
}

# ============================================================================
# Step 3: Summary
# ============================================================================
Write-Host ""
Write-Header "╔════════════════════════════════════════════════════════════════╗"
Write-Header "║  Cleanup Complete                                              ║"
Write-Header "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Success "All ICL Voice Assistant processes have been stopped."
Write-Host ""
Write-Host "Ollama service note:"
Write-Host "  • Ollama was stopped but NOT uninstalled"
Write-Host "  • To fully remove Ollama: Control Panel → Uninstall a program"
Write-Host ""
Write-Host "To restart the application:"
Write-Host "  .\Setup-And-Run.ps1 -Windowed"
Write-Host ""
