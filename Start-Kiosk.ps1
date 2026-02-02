# ICL Voice Assistant Kiosk Auto-Start Script (PowerShell)
# This script provides robust auto-restart functionality with logging.

param(
    [switch]$Windowed,
    [switch]$NoRag,
    [int]$MaxRestarts = 10,
    [int]$RestartDelaySeconds = 5,
    [int]$ResetCounterAfterMinutes = 60
)

# Configuration
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptRoot ".venv\Scripts\python.exe"
$LaunchScript = Join-Path $ScriptRoot "scripts\launch_kiosk.py"
$LogDir = Join-Path $ScriptRoot "logs"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Log file with date
$LogFile = Join-Path $LogDir "autostart_$(Get-Date -Format 'yyyyMMdd').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

function Start-Kiosk {
    param([string[]]$Arguments)
    
    $process = Start-Process -FilePath $VenvPython `
        -ArgumentList (@($LaunchScript) + $Arguments) `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput (Join-Path $LogDir "kiosk_stdout.log") `
        -RedirectStandardError (Join-Path $LogDir "kiosk_stderr.log")
    
    return $process
}

# Main execution
Write-Log "=== ICL Voice Assistant Auto-Start Script ===" 
Write-Log "Python: $VenvPython"
Write-Log "Script: $LaunchScript"
Write-Log "Max Restarts: $MaxRestarts"

# Build arguments
$KioskArgs = @()
if ($Windowed) { $KioskArgs += "--windowed" }
if ($NoRag) { $KioskArgs += "--no-rag" }

$RestartCount = 0
$LastRestartTime = Get-Date

try {
    while ($true) {
        # Reset counter if enough time has passed
        $TimeSinceLastRestart = (Get-Date) - $LastRestartTime
        if ($TimeSinceLastRestart.TotalMinutes -gt $ResetCounterAfterMinutes -and $RestartCount -gt 0) {
            Write-Log "Resetting restart counter (stable for $ResetCounterAfterMinutes minutes)"
            $RestartCount = 0
        }
        
        # Check if we've hit the restart limit
        if ($RestartCount -ge $MaxRestarts) {
            Write-Log "ERROR: Maximum restart limit reached ($MaxRestarts)" "ERROR"
            Write-Log "Waiting 5 minutes before resetting..." "WARN"
            Start-Sleep -Seconds 300
            $RestartCount = 0
        }
        
        Write-Log "Starting kiosk (attempt: $($RestartCount + 1)/$MaxRestarts)..."
        
        # Start the kiosk
        $process = Start-Kiosk -Arguments $KioskArgs
        
        # Wait for the process to exit
        $process.WaitForExit()
        $ExitCode = $process.ExitCode
        
        Write-Log "Kiosk exited with code: $ExitCode"
        
        # Handle exit codes
        switch ($ExitCode) {
            0 {
                Write-Log "Clean exit. Stopping auto-restart."
                exit 0
            }
            2 {
                Write-Log "Requested shutdown. Stopping auto-restart."
                exit 0
            }
            default {
                $RestartCount++
                $LastRestartTime = Get-Date
                Write-Log "Crash detected. Restarting in $RestartDelaySeconds seconds..." "WARN"
                Start-Sleep -Seconds $RestartDelaySeconds
            }
        }
    }
}
catch {
    Write-Log "Fatal error in auto-start script: $_" "ERROR"
    exit 1
}
finally {
    Write-Log "=== Auto-start script ended ==="
}
