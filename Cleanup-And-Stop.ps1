# ICL Voice Assistant - Cleanup & Stop Script
# Stops Ollama, kills running processes, and cleans up resources

param(
    [switch]$Force         # Force kill without prompting
)

# Colors
function Write-Header { Write-Host $args[0] -ForegroundColor Cyan -BackgroundColor Black }
function Write-Success { Write-Host $args[0] -ForegroundColor Green }
function Write-Warning { Write-Host $args[0] -ForegroundColor Yellow }
function Write-Error2 { Write-Host $args[0] -ForegroundColor Red }

Write-Host ""
Write-Header "╔════════════════════════════════════════════════════════════════╗"
Write-Header "║  ICL Voice Assistant - Cleanup & Stop                          ║"
Write-Header "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

# ============================================================================
# Step 1: Stop Ollama service
# ============================================================================
Write-Header "Step 1: Stopping Ollama service..."

$ollamaProcesses = Get-Process -Name "ollama" -ErrorAction SilentlyContinue

if ($ollamaProcesses) {
    Write-Warning "  Found Ollama process(es) running..."

    if (-not $Force) {
        Write-Host "  Attempting graceful shutdown..."
    }

    try {
        # Try graceful shutdown first
        $ollamaProcesses | Stop-Process -ErrorAction SilentlyContinue -WarningAction SilentlyContinue
        Start-Sleep -Seconds 2

        # Check if still running
        $stillRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue

        if ($stillRunning) {
            Write-Warning "  Graceful shutdown didn't work. Force killing..."
            $stillRunning | Stop-Process -Force -ErrorAction SilentlyContinue
        }

        Write-Success "✓ Ollama stopped"
    } catch {
        Write-Error2 "✗ Failed to stop Ollama: $_"
    }
} else {
    Write-Success "✓ Ollama not running"
}

# ============================================================================
# Step 2: Kill any Python processes running the kiosk
# ============================================================================
Write-Header ""
Write-Header "Step 2: Stopping ICL Voice Assistant processes..."

$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "launch_kiosk|src/main"
}

if ($pythonProcesses) {
    Write-Warning "  Found application process(es) running..."

    try {
        $pythonProcesses | Stop-Process -ErrorAction SilentlyContinue -WarningAction SilentlyContinue
        Start-Sleep -Seconds 1

        # Force kill if still running
        $stillRunning = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -match "launch_kiosk|src/main"
        }

        if ($stillRunning) {
            $stillRunning | Stop-Process -Force -ErrorAction SilentlyContinue
        }

        Write-Success "✓ Application processes stopped"
    } catch {
        Write-Error2 "✗ Failed to stop application: $_"
    }
} else {
    Write-Success "✓ No application processes running"
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
Write-Host "  python scripts/launch_kiosk.py --windowed"
Write-Host ""
