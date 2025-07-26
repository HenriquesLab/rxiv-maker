#Requires -Version 5.1
#Requires -Modules @{ ModuleName = 'BuildHelpers'; ModuleVersion = '2.0.1' }
#Requires -Modules @{ ModuleName = 'Pester'; ModuleVersion = '5.2.0' }

<#
.SYNOPSIS
    Test runner for scoop-rxiv-maker bucket
.DESCRIPTION
    Runs Pester tests for the Scoop bucket, including manifest validation and installation tests
.PARAMETER TestPath
    Path to the test file or directory to run
.PARAMETER PassThru
    Return Pester result object
.PARAMETER CI
    Running in CI environment (enables additional output)
.EXAMPLE
    .\bin\test.ps1
    Run all tests

.EXAMPLE
    .\bin\test.ps1 -TestPath "Scoop-Bucket.Tests.ps1"
    Run specific test file
#>

param(
    [String] $TestPath = "$PSScriptRoot/..",
    [Switch] $PassThru,
    [Switch] $CI
)

# Strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "🧪 Scoop rxiv-maker Bucket Test Runner" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if running in CI
if ($env:CI -eq 'true' -or $CI) {
    Write-Host "Running in CI mode" -ForegroundColor Yellow
    $VerbosityLevel = 'Detailed'
} else {
    Write-Host "Running in local mode" -ForegroundColor Green
    $VerbosityLevel = 'Normal'
}

# Verify Scoop is installed
try {
    $scoopPath = Get-Command scoop -ErrorAction Stop
    Write-Host "✅ Scoop found at: $($scoopPath.Source)" -ForegroundColor Green
} catch {
    Write-Host "❌ Scoop is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Scoop first: https://scoop.sh" -ForegroundColor Yellow
    exit 1
}

# Set Scoop environment if not set
if (!$env:SCOOP_HOME) {
    try {
        $env:SCOOP_HOME = Resolve-Path (scoop prefix scoop)
        Write-Host "✅ SCOOP_HOME set to: $env:SCOOP_HOME" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Could not determine SCOOP_HOME, some tests may fail" -ForegroundColor Yellow
    }
}

# Display environment information
Write-Host "`nEnvironment Information:" -ForegroundColor Cyan
Write-Host "  PowerShell Version: $($PSVersionTable.PSVersion)" -ForegroundColor Gray
Write-Host "  OS: $($PSVersionTable.OS)" -ForegroundColor Gray
Write-Host "  Scoop Version: $(scoop --version)" -ForegroundColor Gray
if ($env:SCOOP_HOME) {
    Write-Host "  SCOOP_HOME: $env:SCOOP_HOME" -ForegroundColor Gray
}

# Install required modules if not present
$requiredModules = @(
    @{ Name = 'BuildHelpers'; Version = '2.0.1' }
    @{ Name = 'Pester'; Version = '5.2.0' }
)

foreach ($module in $requiredModules) {
    if (!(Get-Module -ListAvailable -Name $module.Name | Where-Object { $_.Version -ge $module.Version })) {
        Write-Host "Installing $($module.Name) v$($module.Version)..." -ForegroundColor Yellow
        Install-Module -Name $module.Name -MinimumVersion $module.Version -Force -Scope CurrentUser
    }
}

# Import modules
Import-Module BuildHelpers -MinimumVersion 2.0.1
Import-Module Pester -MinimumVersion 5.2.0

# Configure Pester
$pesterConfig = New-PesterConfiguration -Hashtable @{
    Run = @{
        Path = $TestPath
        PassThru = $true
    }
    Filter = @{
        ExcludeTag = if ($CI -or $env:CI) { @() } else { @('CI') }
    }
    Output = @{
        Verbosity = $VerbosityLevel
    }
    TestResult = @{
        Enabled = $true
        OutputFormat = 'NUnitXml'
        OutputPath = "$PSScriptRoot/../test-results.xml"
    }
    CodeCoverage = @{
        Enabled = $false  # Not applicable for manifest testing
    }
}

# Add test data to environment
$env:SCOOP_TEST_BUCKET = "$PSScriptRoot/.."
$env:SCOOP_TEST_MANIFEST = "$PSScriptRoot/../bucket/rxiv-maker.json"

Write-Host "`nRunning tests from: $TestPath" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Run tests
$testResult = Invoke-Pester -Configuration $pesterConfig

# Display summary
Write-Host "`nTest Summary:" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
Write-Host "Total Tests: $($testResult.TotalCount)" -ForegroundColor Gray
Write-Host "Passed: $($testResult.PassedCount)" -ForegroundColor Green
Write-Host "Failed: $($testResult.FailedCount)" -ForegroundColor Red
Write-Host "Skipped: $($testResult.SkippedCount)" -ForegroundColor Yellow

if ($testResult.FailedCount -gt 0) {
    Write-Host "`n❌ Tests failed!" -ForegroundColor Red

    # Display failed tests
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    foreach ($test in $testResult.Failed) {
        Write-Host "  - $($test.ExpandedPath)" -ForegroundColor Red
        if ($test.ErrorRecord) {
            Write-Host "    Error: $($test.ErrorRecord.Exception.Message)" -ForegroundColor DarkRed
        }
    }

    if ($PassThru) {
        return $testResult
    }
    exit $testResult.FailedCount
} else {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    if ($PassThru) {
        return $testResult
    }
    exit 0
}
