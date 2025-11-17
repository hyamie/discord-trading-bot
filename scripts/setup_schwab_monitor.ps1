# PowerShell Script to Setup Automated Schwab Token Monitoring
# This creates a Windows Task Scheduler task to check token expiry daily

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Test
)

$ProjectPath = "C:\ClaudeAgents\projects\discord-trading-bot"
$ScriptPath = "$ProjectPath\scripts\schwab_token_monitor.py"
$TaskName = "SchwabTokenMonitor"
$TaskDescription = "Daily check of Schwab API refresh token expiry"

function Install-MonitorTask {
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 69) -ForegroundColor Cyan
    Write-Host "Installing Schwab Token Monitor Task" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    # Check if Python is available
    try {
        $pythonVersion = & python --version 2>&1
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found! Please install Python first." -ForegroundColor Red
        exit 1
    }

    # Check if script exists
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "❌ Monitor script not found at: $ScriptPath" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Monitor script found" -ForegroundColor Green

    # Create the scheduled task action
    $action = New-ScheduledTaskAction `
        -Execute "python" `
        -Argument "`"$ScriptPath`"" `
        -WorkingDirectory $ProjectPath

    # Create trigger for daily at 9 AM
    $trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM

    # Create additional trigger for system startup (with 5 min delay)
    $startupTrigger = New-ScheduledTaskTrigger -AtStartup
    $startupTrigger.Delay = "PT5M"  # 5 minute delay after startup

    # Settings
    $settings = New-ScheduledTaskSettings `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    # Create principal (run as current user)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest

    # Unregister if exists
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Write-Host "🗑️  Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Register the task
    try {
        $task = Register-ScheduledTask `
            -TaskName $TaskName `
            -Description $TaskDescription `
            -Action $action `
            -Trigger @($trigger, $startupTrigger) `
            -Settings $settings `
            -Principal $principal

        Write-Host ""
        Write-Host "✅ Task created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Task Details:" -ForegroundColor Cyan
        Write-Host "   Name: $TaskName" -ForegroundColor White
        Write-Host "   Schedule: Daily at 9:00 AM + System startup" -ForegroundColor White
        Write-Host "   Script: $ScriptPath" -ForegroundColor White
        Write-Host ""
        Write-Host "🧪 Test the task:" -ForegroundColor Cyan
        Write-Host "   .\setup_schwab_monitor.ps1 -Test" -ForegroundColor White
        Write-Host ""
        Write-Host "📊 View task in Task Scheduler:" -ForegroundColor Cyan
        Write-Host "   taskschd.msc" -ForegroundColor White
        Write-Host ""

    } catch {
        Write-Host "❌ Failed to create task: $_" -ForegroundColor Red
        exit 1
    }
}

function Uninstall-MonitorTask {
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 69) -ForegroundColor Cyan
    Write-Host "Uninstalling Schwab Token Monitor Task" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Task removed successfully!" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  Task not found (already removed)" -ForegroundColor Yellow
    }
    Write-Host ""
}

function Test-MonitorTask {
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 69) -ForegroundColor Cyan
    Write-Host "Testing Schwab Token Monitor" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    # Check if task exists
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "❌ Task not installed! Run with -Install first." -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Task found" -ForegroundColor Green
    Write-Host ""
    Write-Host "Running monitor script manually..." -ForegroundColor Cyan
    Write-Host ""

    # Run the Python script
    Set-Location $ProjectPath
    & python $ScriptPath

    $exitCode = $LASTEXITCODE

    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "✅ Monitor ran successfully - Token is healthy" -ForegroundColor Green
    } elseif ($exitCode -eq 1) {
        Write-Host "⚠️  Monitor ran successfully - ACTION REQUIRED (token expiring/expired)" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Monitor failed with exit code: $exitCode" -ForegroundColor Red
    }
    Write-Host ""
}

# Main execution
if ($Install) {
    Install-MonitorTask
} elseif ($Uninstall) {
    Uninstall-MonitorTask
} elseif ($Test) {
    Test-MonitorTask
} else {
    Write-Host "Schwab Token Monitor - Setup Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\setup_schwab_monitor.ps1 -Install    # Install daily monitoring task" -ForegroundColor Yellow
    Write-Host "  .\setup_schwab_monitor.ps1 -Test       # Test the monitor script" -ForegroundColor Yellow
    Write-Host "  .\setup_schwab_monitor.ps1 -Uninstall  # Remove the scheduled task" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The task will run:" -ForegroundColor White
    Write-Host "  - Daily at 9:00 AM" -ForegroundColor Gray
    Write-Host "  - At system startup (after 5 min delay)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Exit codes:" -ForegroundColor White
    Write-Host "  0 = Token healthy (>1 day remaining)" -ForegroundColor Green
    Write-Host "  1 = Action required (token expiring/expired)" -ForegroundColor Yellow
    Write-Host ""
}
