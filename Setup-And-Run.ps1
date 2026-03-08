# ICL Voice Assistant - Setup & Run Script
# Installs prerequisites (Python, Ollama, model) then delegates to Start-Kiosk.ps1
# Compatible with Windows PowerShell 5.1+

param(
    [switch]$Windowed,      # Pass -Windowed to Start-Kiosk.ps1
    [switch]$SkipOllama,    # Skip Ollama setup
    [switch]$UpdateModel,   # Force re-pull model
    [switch]$NoLaunch       # Setup only, don't launch
)

# ============================================================================
# Helpers
# ============================================================================
function Write-Header  { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host $msg -ForegroundColor Red }

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-InUserProfiles {
    param([string]$RelativePath)
    $found = $null
    $roots = @($env:USERPROFILE)
    Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $roots += $_.FullName
    }
    foreach ($root in $roots) {
        $candidate = Join-Path $root $RelativePath
        if (Test-Path $candidate) { $found = $candidate; break }
    }
    return $found
}

function Find-Ollama {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return Find-InUserProfiles "AppData\Local\Programs\Ollama\ollama.exe"
}

function Test-OllamaPort {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 11434)
        $connected = $tcp.Connected
        $tcp.Close()
        return $connected
    } catch { return $false }
}

# ============================================================================
# Admin check
# ============================================================================
if (-not (Test-Administrator)) {
    Write-Err "ERROR: This script requires Administrator privileges."
    Write-Host "  Right-click PowerShell -> Run as Administrator -> .\Setup-And-Run.ps1"
    exit 1
}

# Configuration
$ScriptRoot     = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot    = $ScriptRoot
$ModelName      = "llama3.1:8b-instruct-q4_K_M"
$OllamaUrl      = "https://ollama.ai/download/OllamaSetup.exe"
$VenvDir        = Join-Path $ProjectRoot ".venv"
$VenvPython     = Join-Path $VenvDir "Scripts\python.exe"

Write-Host ""
Write-Header "=== ICL Voice Assistant - Setup ==="
Write-Host ""

# ============================================================================
# Step 1: Find Python
# ============================================================================
Write-Header "Step 1: Finding Python..."

$pythonPath = $null
$candidates = New-Object System.Collections.Generic.List[string]

$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) { $candidates.Add($pyCmd.Source) }

$roots = @($env:USERPROFILE)
Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object { $roots += $_.FullName }
foreach ($root in $roots) {
    $base = "$root\AppData\Local\Programs\Python"
    if (Test-Path $base) {
        Get-ChildItem $base -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $candidates.Add("$($_.FullName)\python.exe")
        }
    }
}

foreach ($ver in @("313","312","311","310","39")) {
    $candidates.Add("C:\Python$ver\python.exe")
    $candidates.Add("C:\Program Files\Python$ver\python.exe")
}

Get-Command python -All -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Source -notmatch "WindowsApps") { $candidates.Add($_.Source) }
}

foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python \d+\.\d+") { $pythonPath = $candidate; break }
    }
}

if ($pythonPath) {
    Write-Success "[OK] Python found: $(& $pythonPath --version 2>&1)"
    Write-Success "     Path: $pythonPath"
} else {
    Write-Err "[!!] Python not found."
    Write-Host "     Install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
}

# ============================================================================
# Step 2: Find/Install Ollama
# ============================================================================
if (-not $SkipOllama) {
    Write-Host ""
    Write-Header "Step 2: Checking Ollama..."

    $ollamaExe = Find-Ollama

    # Verify it works
    if ($ollamaExe) {
        $ollamaWorks = $false
        try {
            $verOutput = & $ollamaExe --version 2>&1
            if ($verOutput -match "ollama") { $ollamaWorks = $true }
        } catch { }

        if ($ollamaWorks) {
            Write-Success "[OK] Ollama found: $ollamaExe ($verOutput)"
        } else {
            Write-Warn "[!!] Ollama exe broken - reinstalling..."
            $ollamaDir = Split-Path $ollamaExe -Parent
            Remove-Item -Path $ollamaDir -Recurse -Force -ErrorAction SilentlyContinue
            $ollamaExe = $null
        }
    }

    if (-not $ollamaExe) {
        Write-Warn "[!!] Ollama not found. Downloading..."
        $installerPath = Join-Path $env:TEMP "OllamaSetup.exe"
        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $OllamaUrl -OutFile $installerPath -TimeoutSec 300
            Write-Host "     Running installer - click through the setup window..."

            $installerProc = Start-Process -FilePath $installerPath -PassThru
            Write-Host "     Waiting for installer to complete (up to 5 minutes)..."
            $installerProc | Wait-Process -Timeout 300 -ErrorAction SilentlyContinue

            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path","User")
            $ollamaExe = Find-Ollama

            if ($ollamaExe) {
                Write-Success "[OK] Ollama installed: $ollamaExe"
            } else {
                Write-Err "[!!] Ollama not detected. Install manually: https://ollama.ai"
                exit 1
            }
        } catch {
            Write-Err "[!!] Failed to download Ollama: $_"
            exit 1
        }
    }

    # ========================================================================
    # Step 3: Start Ollama server
    # ========================================================================
    Write-Host ""
    Write-Header "Step 3: Starting Ollama server..."

    if (Test-OllamaPort) {
        Write-Success "[OK] Ollama server already running (port 11434)"
    } else {
        Write-Host "     Launching 'ollama serve'..."
        Start-Process -FilePath $ollamaExe -ArgumentList "serve"
        Write-Host "     Waiting for server (up to 30s)..."

        $ollamaRunning = $false
        for ($i = 0; $i -lt 30; $i++) {
            if (Test-OllamaPort) { $ollamaRunning = $true; break }
            Start-Sleep -Seconds 1
            if ($i % 10 -eq 9) { Write-Host "     Still waiting..." }
        }

        if ($ollamaRunning) {
            Write-Success "[OK] Ollama server is running"
        } else {
            Write-Err "[!!] Ollama server not responding after 30s."
            exit 1
        }
    }

    # ========================================================================
    # Step 4: Pull model
    # ========================================================================
    Write-Host ""
    Write-Header "Step 4: Checking LLM model..."

    $modelExists = $false
    try {
        $modelsOutput = & $ollamaExe list 2>&1
        if ($modelsOutput -match [regex]::Escape($ModelName)) { $modelExists = $true }
    } catch { }

    if ($modelExists -and -not $UpdateModel) {
        Write-Success "[OK] Model ready: $ModelName"
    } else {
        Write-Warn "     Pulling $ModelName (~5GB, may take 10-30 mins)..."
        & $ollamaExe pull $ModelName
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
# Step 5: Create virtual environment & install dependencies
# ============================================================================
Write-Host ""
Write-Header "Step 5: Setting up Python environment..."

if (Test-Path $VenvPython) {
    Write-Success "[OK] Virtual environment exists: $VenvDir"
} else {
    Write-Host "     Creating virtual environment..."
    & $pythonPath -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Err "[!!] Failed to create virtual environment."
        exit 1
    }
    Write-Success "[OK] Virtual environment created"
}

Write-Host "     Installing dependencies (this may take a few minutes)..."
Push-Location $ProjectRoot
& $VenvPython -m pip install -e . --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "[OK] Dependencies installed"
} else {
    Write-Warn "[!!] pip returned non-zero (may still be OK)"
}
Pop-Location

# ============================================================================
# Step 6: Verify project structure
# ============================================================================
Write-Host ""
Write-Header "Step 6: Verifying project structure..."

foreach ($dir in @("data\vector_store", "logs")) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}
Write-Success "[OK] Project structure verified"

# ============================================================================
# Done - hand off to Start-Kiosk.ps1
# ============================================================================
Write-Host ""
Write-Header "=== Setup Complete ==="
Write-Host ""

if (-not $NoLaunch) {
    $startKiosk = Join-Path $ProjectRoot "Start-Kiosk.ps1"
    if (Test-Path $startKiosk) {
        Write-Success "Handing off to Start-Kiosk.ps1..."
        Write-Host ""
        $kioskArgs = @{}
        if ($Windowed) { $kioskArgs["Windowed"] = $true }
        & $startKiosk @kioskArgs
    } else {
        Write-Err "Start-Kiosk.ps1 not found. Launch manually:"
        Write-Host "  & '$VenvPython' scripts\launch_kiosk.py --windowed"
    }
} else {
    Write-Success "Setup complete. To launch:"
    Write-Host "  .\Start-Kiosk.ps1 -Windowed"
    Write-Host ""
}
