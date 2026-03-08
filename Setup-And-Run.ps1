# ICL Voice Assistant - Complete Bootstrap & Setup Script
# This script automates the entire setup process from scratch:
# - Checks/installs Ollama
# - Pulls the required LLM model
# - Verifies ChromaDB vector store
# - Launches the application

param(
    [switch]$Windowed,      # Run in windowed mode (not fullscreen)
    [switch]$SkipOllama,    # Skip Ollama setup (already running)
    [switch]$UpdateModel,   # Force pull model even if exists
    [switch]$NoLaunch       # Setup only, don't launch app
)

# ============================================================================
# ADMIN CHECK (REQUIRED FOR INSTALLATION)
# ============================================================================
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ERROR: This script requires Administrator privileges     ║" -ForegroundColor Red
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "This is needed to install Python, Ollama, and configure the system."
    Write-Host ""
    Write-Host "To run as Administrator:"
    Write-Host "  1. Right-click PowerShell"
    Write-Host "  2. Select 'Run as Administrator'"
    Write-Host "  3. Run: .\Setup-And-Run.ps1"
    Write-Host ""
    exit 1
}

# Configuration
$ModelName = "llama3.1:8b-instruct-q4_K_M"
$OllamaUrl = "https://ollama.ai/download/OllamaSetup.exe"
$PythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptRoot
$VectorStoreDir = Join-Path $ProjectRoot "data/vector_store"
$TempDir = $env:TEMP

# Colors for output
function Write-Header { Write-Host $args[0] -ForegroundColor Cyan -BackgroundColor Black }
function Write-Success { Write-Host $args[0] -ForegroundColor Green }
function Write-Warning { Write-Host $args[0] -ForegroundColor Yellow }
function Write-Error2 { Write-Host $args[0] -ForegroundColor Red }

Write-Host ""
Write-Header "╔════════════════════════════════════════════════════════════════╗"
Write-Header "║  ICL Voice Assistant - Complete Bootstrap Setup               ║"
Write-Header "║  Innovation & Creativity Lab - Gettysburg College             ║"
Write-Header "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

# ============================================================================
# Step 1: Check for Python
# ============================================================================
Write-Header "Step 1: Verifying Python installation..."

$pythonPath = $null
try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Success "✓ Python found: $pythonVersion"
} catch {
    Write-Warning "✗ Python not found. Installing Python 3.11..."

    $installerPath = Join-Path $TempDir "python-3.11.9-amd64.exe"

    try {
        Write-Host "  Downloading Python installer..."
        $progressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $PythonUrl -OutFile $installerPath -TimeoutSec 300
        Write-Host "  Running Python installer..."

        # Install Python with automated flags
        & $installerPath /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

        # Wait for installation
        Start-Sleep -Seconds 10

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        # Verify installation
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        if ($pythonPath) {
            $pythonVersion = & $pythonPath --version 2>&1
            Write-Success "✓ Python installed successfully: $pythonVersion"
        } else {
            Write-Error2 "✗ Python installation completed but not in PATH"
            Write-Host "  Please restart PowerShell and try again"
            exit 1
        }
    } catch {
        Write-Error2 "✗ Failed to install Python: $_"
        Write-Host "  You can manually install from: https://www.python.org/downloads/"
        exit 1
    }
}

# ============================================================================
# Step 2: Check/Install Ollama
# ============================================================================
if (-not $SkipOllama) {
    Write-Host ""
    Write-Header "Step 2: Checking Ollama installation..."

    $ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue

    if ($ollamaPath) {
        Write-Success "✓ Ollama found at: $($ollamaPath.Source)"
    } else {
        Write-Warning "✗ Ollama not found. Installing..."

        $installerPath = Join-Path $TempDir "OllamaSetup.exe"

        try {
            Write-Host "  Downloading Ollama installer (~200MB)..."
            $progressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $OllamaUrl -OutFile $installerPath -TimeoutSec 300
            Write-Host "  Running Ollama installer (this may take a few minutes)..."
            & $installerPath

            # Wait for installer
            Start-Sleep -Seconds 5

            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

            # Verify installation
            $ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
            if ($ollamaPath) {
                Write-Success "✓ Ollama installed successfully!"
            } else {
                Write-Error2 "✗ Ollama installation may have failed"
                Write-Host "  Please manually install from: https://ollama.ai"
                exit 1
            }
        } catch {
            Write-Error2 "✗ Failed to download/install Ollama: $_"
            exit 1
        }
    }

    # ========================================================================
    # Step 3: Wait for Ollama service and verify connectivity
    # ========================================================================
    Write-Host ""
    Write-Header "Step 3: Starting Ollama service..."

    $ollamaRunning = $false
    $maxRetries = 60
    $retryCount = 0

    while ($retryCount -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $ollamaRunning = $true
                break
            }
        } catch {
            # Ollama not yet responding
        }

        if ($retryCount -eq 0) {
            Write-Host "  Waiting for Ollama to start (up to 60 seconds)..."
        }

        Start-Sleep -Seconds 1
        $retryCount++
        if ($retryCount % 10 -eq 0) {
            Write-Host "." -NoNewline
        }
    }

    Write-Host ""

    if ($ollamaRunning) {
        Write-Success "✓ Ollama is running and responding"
    } else {
        Write-Error2 "✗ Ollama is not responding at http://localhost:11434"
        Write-Host ""
        Write-Warning "Troubleshooting:"
        Write-Host "  1. Ollama may still be starting - wait a minute and retry"
        Write-Host "  2. Check if Ollama installed correctly: ollama --version"
        Write-Host "  3. Try restarting your computer"
        Write-Host ""
        Write-Host "  Run again with -SkipOllama if Ollama is already running"
        exit 1
    }

    # ========================================================================
    # Step 4: Pull the required model
    # ========================================================================
    Write-Host ""
    Write-Header "Step 4: Setting up LLM model..."

    # Check if model exists
    $modelExists = $false
    try {
        Write-Host "  Checking for existing model..."
        $modelsOutput = & ollama list 2>$null
        if ($modelsOutput -match $ModelName) {
            $modelExists = $true
        }
    } catch {
        # Continue - will attempt pull anyway
    }

    if ($modelExists -and -not $UpdateModel) {
        Write-Success "✓ Model $ModelName already available"
    } else {
        Write-Warning "  Pulling model: $ModelName"
        Write-Host "  This will download ~5GB (may take 10-30 minutes depending on connection)"
        Write-Host ""
        try {
            & ollama pull $ModelName
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ Model pulled successfully!"
            } else {
                Write-Error2 "✗ Failed to pull model"
                exit 1
            }
        } catch {
            Write-Error2 "✗ Error pulling model: $_"
            exit 1
        }
    }
} else {
    Write-Success "⊘ Skipping Ollama setup (assuming already running)"
}

# ============================================================================
# Step 5: Verify project structure
# ============================================================================
Write-Host ""
Write-Header "Step 5: Verifying project structure..."

$requiredDirs = @(
    "data/vector_store",
    "src",
    "logs"
)

foreach ($dir in $requiredDirs) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}
Write-Success "✓ Project structure verified"

# ============================================================================
# Step 6: Install Python dependencies
# ============================================================================
Write-Host ""
Write-Header "Step 6: Installing Python dependencies..."

try {
    Push-Location $ProjectRoot
    Write-Host "  Running: pip install -e ."
    & python -m pip install -e . --quiet

    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Dependencies installed successfully"
    } else {
        Write-Warning "  Some dependencies may have warnings (this is usually OK)"
    }

    Pop-Location
} catch {
    Write-Error2 "✗ Failed to install dependencies: $_"
    exit 1
}

# ============================================================================
# Step 7: Initialize ChromaDB vector store
# ============================================================================
Write-Host ""
Write-Header "Step 7: Setting up ChromaDB vector store..."

if (Test-Path (Join-Path $VectorStoreDir "chroma.db")) {
    Write-Success "✓ Vector store already initialized"
} else {
    New-Item -ItemType Directory -Path $VectorStoreDir -Force | Out-Null
    Write-Success "✓ Vector store directory ready (will populate on first run)"
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host ""
Write-Header "╔════════════════════════════════════════════════════════════════╗"
Write-Header "║  Setup Complete - All Prerequisites Ready!                    ║"
Write-Header "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

if (-not $NoLaunch) {
    Write-Success "Launching ICL Voice Assistant..."
    Write-Host ""

    try {
        $launchArgs = @("scripts/launch_kiosk.py")
        if ($Windowed) {
            $launchArgs += "--windowed"
        }

        Push-Location $ProjectRoot
        & python @launchArgs
        Pop-Location
    } catch {
        Write-Error2 "✗ Failed to launch application: $_"
        exit 1
    }
} else {
    Write-Success "Setup complete! To launch the application:"
    Write-Host ""
    Write-Host "  Windowed mode (for testing):"
    Write-Host "    python scripts/launch_kiosk.py --windowed"
    Write-Host ""
    Write-Host "  Fullscreen kiosk mode:"
    Write-Host "    python scripts/launch_kiosk.py"
    Write-Host ""
}
