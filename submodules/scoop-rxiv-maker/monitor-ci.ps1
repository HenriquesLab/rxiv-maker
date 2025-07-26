#Requires -Version 5.1

<#
.SYNOPSIS
    CI Monitoring Script for scoop-rxiv-maker
.DESCRIPTION
    Monitors GitHub Actions workflow runs and provides real-time status updates
.PARAMETER Watch
    Enable continuous monitoring mode
.PARAMETER Once
    Show status once and exit
.PARAMETER Interactive
    Enable interactive mode (cancel hanging jobs)
.PARAMETER RefreshInterval
    Refresh interval in seconds (default: 30)
.PARAMETER MaxRuntime
    Maximum runtime in seconds before considering a job hanging (default: 3600)
.EXAMPLE
    .\monitor-ci.ps1
    Monitor continuously with default settings

.EXAMPLE
    .\monitor-ci.ps1 -Once
    Show current status and exit

.EXAMPLE
    .\monitor-ci.ps1 -Interactive
    Monitor with ability to cancel hanging jobs
#>

[CmdletBinding(DefaultParameterSetName = 'Watch')]
param(
    [Parameter(ParameterSetName = 'Watch')]
    [switch]$Watch,

    [Parameter(ParameterSetName = 'Once')]
    [switch]$Once,

    [Parameter()]
    [switch]$Interactive,

    [Parameter()]
    [int]$RefreshInterval = 30,

    [Parameter()]
    [int]$MaxRuntime = 3600
)

# Configuration
$script:RepoName = "scoop-rxiv-maker"
$script:WorkflowName = "Test Formula"

# Color definitions
$script:Colors = @{
    Red    = "`e[31m"
    Green  = "`e[32m"
    Yellow = "`e[33m"
    Blue   = "`e[34m"
    Cyan   = "`e[36m"
    Reset  = "`e[0m"
}

# Function to print colored output
function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )

    $color = switch ($Status) {
        "SUCCESS" { $Colors.Green }
        "FAILURE" { $Colors.Red }
        "PENDING" { $Colors.Yellow }
        "INFO"    { $Colors.Blue }
        "RUNNING" { $Colors.Cyan }
        default   { $Colors.Reset }
    }

    Write-Host "${color}[$Status]$($Colors.Reset) $Message"
}

# Function to format duration
function Format-Duration {
    param([int]$Seconds)

    $hours = [math]::Floor($Seconds / 3600)
    $minutes = [math]::Floor(($Seconds % 3600) / 60)
    $secs = $Seconds % 60

    if ($hours -gt 0) {
        return "{0}h {1:D2}m {2:D2}s" -f $hours, $minutes, $secs
    } elseif ($minutes -gt 0) {
        return "{0}m {1:D2}s" -f $minutes, $secs
    } else {
        return "{0}s" -f $secs
    }
}

# Function to calculate runtime
function Get-Runtime {
    param([string]$StartTime)

    try {
        $start = [DateTime]::Parse($StartTime).ToUniversalTime()
        $runtime = ([DateTime]::UtcNow - $start).TotalSeconds
        return [int]$runtime
    } catch {
        return 0
    }
}

# Function to check if gh CLI is available
function Test-GHCLIAvailable {
    try {
        $null = gh --version 2>&1
        return $true
    } catch {
        Write-Status "FAILURE" "GitHub CLI (gh) is not installed or not in PATH"
        Write-Host "Please install GitHub CLI: https://cli.github.com/"
        return $false
    }
}

# Function to get workflow runs
function Get-WorkflowRuns {
    try {
        $runs = gh run list --repo "henriqueslab/$RepoName" --limit 10 --json status,conclusion,startedAt,displayTitle,workflowName,databaseId,url,createdAt,updatedAt 2>&1

        if ($LASTEXITCODE -ne 0) {
            Write-Status "FAILURE" "Failed to fetch workflow runs. Make sure you're authenticated with 'gh auth login'"
            return $null
        }

        return $runs | ConvertFrom-Json
    } catch {
        Write-Status "FAILURE" "Error parsing workflow data: $_"
        return $null
    }
}

# Function to get job details
function Get-JobDetails {
    param([string]$RunId)

    try {
        $jobs = gh run view $RunId --repo "henriqueslab/$RepoName" --json jobs 2>&1
        if ($LASTEXITCODE -eq 0) {
            return ($jobs | ConvertFrom-Json).jobs
        }
    } catch {
        Write-Verbose "Unable to fetch job details for run $RunId"
    }
    return $null
}

# Function to display run status
function Show-RunStatus {
    param(
        [PSCustomObject]$Run,
        [switch]$InteractiveMode
    )

    $status = $Run.status
    $conclusion = $Run.conclusion
    $title = $Run.displayTitle
    $workflow = $Run.workflowName
    $runId = $Run.databaseId
    $url = $Run.url
    $startTime = $Run.startedAt

    # Calculate runtime
    $runtime = if ($startTime) { Get-Runtime $startTime } else { 0 }

    # Status indicator
    switch ($status) {
        "in_progress" {
            if ($runtime -gt $MaxRuntime) {
                Write-Status "FAILURE" "🔴 HANGING - $workflow"
            } else {
                Write-Status "RUNNING" "🔵 RUNNING - $workflow"
            }
        }
        "completed" {
            switch ($conclusion) {
                "success" { Write-Status "SUCCESS" "✅ SUCCESS - $workflow" }
                "failure" { Write-Status "FAILURE" "❌ FAILED - $workflow" }
                "cancelled" { Write-Status "PENDING" "⚠️  CANCELLED - $workflow" }
                default { Write-Status "INFO" "⚪ $conclusion - $workflow" }
            }
        }
        "queued" { Write-Status "PENDING" "⏳ QUEUED - $workflow" }
        default { Write-Status "INFO" "⚪ $status - $workflow" }
    }

    # Run details
    Write-Host "   ID: $runId"
    Write-Host "   Title: $title"
    Write-Host "   Runtime: $(Format-Duration $runtime)"
    Write-Host "   URL: $url"

    # Job details for running jobs
    if ($status -eq "in_progress") {
        Write-Host "   Jobs:"

        $jobs = Get-JobDetails -RunId $runId
        if ($jobs) {
            foreach ($job in $jobs) {
                $jobStatus = switch ($job.status) {
                    "in_progress" { "🔵 $($job.name) (running)" }
                    "completed" {
                        switch ($job.conclusion) {
                            "success" { "✅ $($job.name)" }
                            "failure" { "❌ $($job.name)" }
                            default { "⚪ $($job.name) ($($job.conclusion))" }
                        }
                    }
                    "queued" { "⏳ $($job.name) (queued)" }
                    default { "⚪ $($job.name) ($($job.status))" }
                }
                Write-Host "     $jobStatus"
            }
        }

        # Check if job should be cancelled
        if ($InteractiveMode -and $runtime -gt $MaxRuntime) {
            Write-Host ""
            $response = Read-Host "Cancel this hanging job? (y/n)"
            if ($response -eq 'y') {
                gh run cancel $runId --repo "henriqueslab/$RepoName"
                Write-Status "INFO" "✓ Cancelled job $runId"
            }
        }
    }

    Write-Host ""
}

# Function to show summary
function Show-Summary {
    param([array]$Runs)

    if (-not $Runs) { return }

    $totalRuns = $Runs.Count
    $runningRuns = @($Runs | Where-Object { $_.status -eq "in_progress" }).Count
    $queuedRuns = @($Runs | Where-Object { $_.status -eq "queued" }).Count
    $successRuns = @($Runs | Where-Object { $_.status -eq "completed" -and $_.conclusion -eq "success" }).Count
    $failedRuns = @($Runs | Where-Object { $_.status -eq "completed" -and $_.conclusion -eq "failure" }).Count

    Write-Host ("=" * 70)
    Write-Host "CI MONITORING SUMMARY - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host ("=" * 70)
    Write-Host "🔵 Running: $runningRuns  |  ⏳ Queued: $queuedRuns  |  ✅ Success: $successRuns  |  ❌ Failed: $failedRuns"
    Write-Host "Total runs shown: $totalRuns"
    Write-Host ("=" * 70)
    Write-Host ""
}

# Function to monitor continuously
function Start-ContinuousMonitoring {
    param([switch]$InteractiveMode)

    while ($true) {
        Clear-Host

        $runs = Get-WorkflowRuns
        if ($runs) {
            Show-Summary -Runs $runs

            foreach ($run in $runs) {
                Show-RunStatus -Run $run -InteractiveMode:$InteractiveMode
            }
        }

        if ($InteractiveMode) {
            Write-Host "Press Ctrl+C to exit, or wait ${RefreshInterval}s for refresh..."
        } else {
            Write-Host "Refreshing in ${RefreshInterval}s... (Press Ctrl+C to exit)"
        }

        Start-Sleep -Seconds $RefreshInterval
    }
}

# Function to cancel hanging jobs in batch
function Stop-HangingJobs {
    $runs = Get-WorkflowRuns
    if (-not $runs) { return }

    $hangingJobs = $runs | Where-Object {
        $_.status -eq "in_progress" -and
        $_.startedAt -and
        (Get-Runtime $_.startedAt) -gt $MaxRuntime
    }

    if ($hangingJobs.Count -eq 0) {
        Write-Status "INFO" "No hanging jobs found"
        return
    }

    foreach ($job in $hangingJobs) {
        $runtime = Get-Runtime $job.startedAt
        Write-Status "PENDING" "Cancelling hanging job: $($job.displayTitle) (ID: $($job.databaseId), Runtime: $(Format-Duration $runtime))"

        gh run cancel $job.databaseId --repo "henriqueslab/$RepoName"

        if ($LASTEXITCODE -eq 0) {
            Write-Status "SUCCESS" "✓ Cancelled job $($job.databaseId)"
        } else {
            Write-Status "FAILURE" "Failed to cancel job $($job.databaseId)"
        }
    }
}

# Function to get workflow performance metrics
function Get-WorkflowMetrics {
    param([int]$Days = 7)

    Write-Status "INFO" "Getting performance metrics for the last $Days days..."

    # Get workflow runs for the specified period
    $runs = gh run list --repo "henriqueslab/$RepoName" --limit 100 --json status,conclusion,startedAt,updatedAt,createdAt 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Status "FAILURE" "Failed to fetch workflow runs for metrics"
        return
    }

    $runsData = $runs | ConvertFrom-Json

    # Filter runs from the last N days
    $cutoffDate = (Get-Date).AddDays(-$Days).ToUniversalTime()
    $recentRuns = $runsData | Where-Object {
        $_.createdAt -and ([DateTime]::Parse($_.createdAt).ToUniversalTime() -gt $cutoffDate)
    }

    if ($recentRuns.Count -eq 0) {
        Write-Status "INFO" "No runs found in the last $Days days"
        return
    }

    # Calculate metrics
    $totalRuns = $recentRuns.Count
    $successRuns = @($recentRuns | Where-Object { $_.conclusion -eq "success" }).Count
    $failureRuns = @($recentRuns | Where-Object { $_.conclusion -eq "failure" }).Count
    $cancelledRuns = @($recentRuns | Where-Object { $_.conclusion -eq "cancelled" }).Count
    $successRate = if ($totalRuns -gt 0) { [math]::Round(($successRuns / $totalRuns) * 100, 1) } else { 0 }

    # Calculate average duration for completed runs
    $completedRuns = $recentRuns | Where-Object {
        $_.status -eq "completed" -and $_.startedAt -and $_.updatedAt
    }

    $totalDuration = 0
    foreach ($run in $completedRuns) {
        $duration = Get-Runtime $run.startedAt
        $totalDuration += $duration
    }

    $avgDuration = if ($completedRuns.Count -gt 0) {
        [int]($totalDuration / $completedRuns.Count)
    } else { 0 }

    Write-Host ""
    Write-Host "📊 Metrics (last $Days days):"
    Write-Host "├── Total runs: $totalRuns"
    Write-Host "├── Success rate: ${successRate}%"
    Write-Host "├── Failures: $failureRuns"
    Write-Host "├── Cancelled: $cancelledRuns"
    Write-Host "└── Avg duration: $(Format-Duration $avgDuration)"
    Write-Host ""
}

# Main function
function Main {
    Write-Host "🧪 Scoop rxiv-maker CI Monitor" -ForegroundColor Cyan
    Write-Host ("=" * 30) -ForegroundColor Cyan
    Write-Host ""

    # Check if gh CLI is available
    if (-not (Test-GHCLIAvailable)) {
        exit 1
    }

    # Handle different modes
    if ($Once) {
        $runs = Get-WorkflowRuns
        if ($runs) {
            Show-Summary -Runs $runs
            foreach ($run in $runs) {
                Show-RunStatus -Run $run
            }

            # Show metrics
            Get-WorkflowMetrics -Days 7
        }
    } elseif ($PSCmdlet.ParameterSetName -eq "CancelHanging") {
        Stop-HangingJobs
    } else {
        # Default to watch mode
        Start-ContinuousMonitoring -InteractiveMode:$Interactive
    }
}

# Add cancel hanging parameter set
if ($PSBoundParameters.ContainsKey('CancelHanging')) {
    Stop-HangingJobs
    exit
}

# Show help if requested
if ($PSBoundParameters.ContainsKey('Help')) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit
}

# Run main function
Main
