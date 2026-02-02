# ICL Voice Assistant - Windows Task Scheduler Setup
# Run this script as Administrator to configure auto-start on boot.

param(
    [switch]$Uninstall,
    [switch]$Windowed,
    [string]$User = $env:USERNAME
)

$TaskName = "ICL Voice Assistant Kiosk"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $ScriptRoot "Start-Kiosk.ps1"

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check for admin rights
if (-not (Test-Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

if ($Uninstall) {
    Write-Host "Removing scheduled task: $TaskName" -ForegroundColor Yellow
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Task removed successfully." -ForegroundColor Green
    } else {
        Write-Host "Task not found." -ForegroundColor Yellow
    }
    exit 0
}

Write-Host "=== ICL Voice Assistant Auto-Start Setup ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will create a Windows Scheduled Task to start the kiosk"
Write-Host "automatically when the user '$User' logs in."
Write-Host ""

# Build the PowerShell arguments
$PsArgs = @("-ExecutionPolicy", "Bypass", "-File", "`"$StartScript`"")
if ($Windowed) {
    $PsArgs += "-Windowed"
}

$Arguments = $PsArgs -join " "

# Create the scheduled task
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $Arguments `
    -WorkingDirectory $ScriptRoot

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $User

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $User `
    -LogonType Interactive `
    -RunLevel Limited

# Remove existing task if present
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Register the new task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Starts the ICL Voice Assistant kiosk at user logon" | Out-Null
    
    Write-Host ""
    Write-Host "SUCCESS: Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The kiosk will automatically start when '$User' logs in."
    Write-Host ""
    Write-Host "To test now, run:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To remove this task, run:" -ForegroundColor Cyan
    Write-Host "  .\Setup-AutoStart.ps1 -Uninstall"
    Write-Host ""
}
catch {
    Write-Host "ERROR: Failed to create scheduled task." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
