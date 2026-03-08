# ICL Voice Assistant - Complete Bootstrap & Setup Script
# Compatible with Windows PowerShell 5.1+
# Checks/installs Python, Ollama, pulls the LLM model, and launches the app.

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
    Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
    Write-Host ""
    Write-Host "To run as Administrator:"
    Write-Host "  1. Right-click PowerShell"
    Write-Host "  2. Select 'Run as Administrator'"
    Write-Host "  3. Run: .\Setup-And-Run.ps1"
    Write-Host ""
    exit 1
}

# Configuration
$ModelName    = "llama3.1:8b-instruct-q4_K_M"
$OllamaUrl    = "https://ollama.ai/download/OllamaSetup.exe"
$PythonUrl    = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$ScriptRoot   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot  = $ScriptRoot
$VectorStoreDir = Join-Path $ProjectRoot "data\vector_store"
$TempDir      = $env:TEMP

function Write-Header  { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host $msg -ForegroundColor Red }

Write-Host ""
Write-Header "=== ICL Voice Assistant - Complete Bootstrap Setup ==="
Write-Host ""

# ============================================================================
# Step 1: Find Python (skipping the Microsoft Store stub)
# ============================================================================
Write-Header "Step 1: Verifying Python installation..."

$pythonPath = $null
$candidates = New-Object System.Collections.Generic.List[string]

# 1. py launcher (most reliable on Windows, works even when run as admin)
$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) { $candidates.Add($pyCmd.Source) }

# 2. Scan all user profiles for Python installs
#    NOTE: $env:LOCALAPPDATA changes when running as Admin, so we use
#    $env:USERPROFILE and also scan C:\Users\* to find real user installs
$userRoots = @($env:USERPROFILE)
Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $userRoots += $_.FullName
}

foreach ($userRoot in $userRoots) {
    $pythonBase = "$userRoot\AppData\Local\Programs\Python"
    if (Test-Path $pythonBase) {
        Get-ChildItem $pythonBase -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $candidates.Add("$($_.FullName)\python.exe")
        }
    }
}

# 3. System-wide installs
foreach ($ver in @("313","312","311","310","39")) {
    $candidates.Add("C:\Python$ver\python.exe")
    $candidates.Add("C:\Program Files\Python$ver\python.exe")
}

# 4. Any python in PATH that isn't the WindowsApps stub
$allPython = Get-Command python -All -ErrorAction SilentlyContinue
if ($allPython) {
    foreach ($cmd in $allPython) {
        if ($cmd.Source -notmatch "WindowsApps") {
            $candidates.Add($cmd.Source)
        }
    }
}

foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python \d+\.\d+") {
            $pythonPath = $candidate
            break
        }
    }
}

if ($pythonPath) {
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Success "[OK] Python found: $pythonVersion"
    Write-Success "     Path: $pythonPath"
} else {
    Write-Warn "[!!] Python not found. Installing Python 3.11..."
    $installerPath = Join-Path $TempDir "python-3.11.9-amd64.exe"
    try {
        Write-Host "     Downloading Python installer..."
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $PythonUrl -OutFile $installerPath -TimeoutSec 300
        Write-Host "     Running installer..."
        & $installerPath /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
        Start-Sleep -Seconds 10

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path","User")

        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        if ($pythonPath) {
            Write-Success "[OK] Python installed: $(& $pythonPath --version 2>&1)"
        } else {
            Write-Err "[!!] Python installed but not found in PATH. Restart PowerShell and retry."
            exit 1
        }
    } catch {
        Write-Err "[!!] Failed to install Python: $_"
        exit 1
    }
}

# ============================================================================
# Step 2: Check/Install Ollama
# ============================================================================
if (-not $SkipOllama) {
    Write-Host ""
    Write-Header "Step 2: Checking Ollama installation..."

    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue

    if ($ollamaCmd) {
        Write-Success "[OK] Ollama found: $($ollamaCmd.Source)"
    } else {
        Write-Warn "[!!] Ollama not found. Installing..."
        $installerPath = Join-Path $TempDir "OllamaSetup.exe"
        try {
            Write-Host "     Downloading Ollama installer (~200MB)..."
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $OllamaUrl -OutFile $installerPath -TimeoutSec 300
            Write-Host "     Running installer..."
            & $installerPath
            Start-Sleep -Seconds 10

            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path","User")

            $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
            if ($ollamaCmd) {
                Write-Success "[OK] Ollama installed!"
            } else {
                Write-Err "[!!] Ollama install may have failed. Try: https://ollama.ai"
                exit 1
            }
        } catch {
            Write-Err "[!!] Failed to install Ollama: $_"
            exit 1
        }
    }

    # ========================================================================
    # Step 3: Wait for Ollama service
    # ========================================================================
    Write-Host ""
    Write-Header "Step 3: Waiting for Ollama service..."

    $ollamaRunning = $false
    Write-Host "     Polling http://localhost:11434 (up to 60s)..."

    for ($i = 0; $i -lt 60; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $ollamaRunning = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
        if ($i % 10 -eq 9) { Write-Host "     Still waiting..." }
    }

    if ($ollamaRunning) {
        Write-Success "[OK] Ollama is running"
    } else {
        Write-Err "[!!] Ollama not responding after 60s."
        Write-Host "     Try restarting your PC and running again."
        Write-Host "     Or run with -SkipOllama if it is already running."
        exit 1
    }

    # ========================================================================
    # Step 4: Pull the model
    # ========================================================================
    Write-Host ""
    Write-Header "Step 4: Setting up LLM model..."

    $modelExists = $false
    try {
        $modelsOutput = & ollama list 2>&1
        if ($modelsOutput -match [regex]::Escape($ModelName)) { $modelExists = $true }
    } catch { }

    if ($modelExists -and -not $UpdateModel) {
        Write-Success "[OK] Model already available: $ModelName"
    } else {
        Write-Warn "     Pulling $ModelName (~5GB, may take 10-30 mins)..."
        & ollama pull $ModelName
        if ($LASTEXITCODE -eq 0) {
            Write-Success "[OK] Model ready!"
        } else {
            Write-Err "[!!] Failed to pull model."
            exit 1
        }
    }
} else {
    Write-Success "[--] Skipping Ollama setup"
}

# ============================================================================
# Step 5: Verify project structure
# ============================================================================
Write-Host ""
Write-Header "Step 5: Verifying project structure..."

foreach ($dir in @("data\vector_store", "logs")) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}
Write-Success "[OK] Project structure verified"

# ============================================================================
# Step 6: Install Python dependencies
# ============================================================================
Write-Host ""
Write-Header "Step 6: Installing Python dependencies..."

Push-Location $ProjectRoot
& $pythonPath -m pip install -e . --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Success "[OK] Dependencies installed"
} else {
    Write-Warn "[!!] pip returned a non-zero exit code (may still be OK)"
}
Pop-Location

# ============================================================================
# Step 7: ChromaDB vector store
# ============================================================================
Write-Host ""
Write-Header "Step 7: Checking ChromaDB vector store..."

if (Test-Path (Join-Path $VectorStoreDir "chroma.db")) {
    Write-Success "[OK] Vector store already exists"
} else {
    New-Item -ItemType Directory -Path $VectorStoreDir -Force | Out-Null
    Write-Success "[OK] Vector store directory created (populates on first run)"
}

# ============================================================================
# Done
# ============================================================================
Write-Host ""
Write-Header "=== Setup Complete - All Prerequisites Ready! ==="
Write-Host ""

if (-not $NoLaunch) {
    Write-Success "Launching ICL Voice Assistant..."
    Write-Host ""
    $launchArgs = @("scripts\launch_kiosk.py")
    if ($Windowed) { $launchArgs += "--windowed" }

    Push-Location $ProjectRoot
    & $pythonPath @launchArgs
    Pop-Location
} else {
    Write-Host "To launch manually:"
    Write-Host "  & '$pythonPath' scripts\launch_kiosk.py --windowed"
    Write-Host ""
}
