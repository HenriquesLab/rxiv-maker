# test-rxiv-commands.ps1
# Test helper script for rxiv CLI commands

param(
    [string]$TestDir = "$env:TEMP\rxiv-test-$([System.Guid]::NewGuid().ToString('N').Substring(0,8))",
    [switch]$KeepTestDir,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

function Write-TestResult {
    param([string]$Message, [string]$Status = "INFO")

    $color = switch ($Status) {
        "OK" { "Green" }
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "INFO" { "Cyan" }
        "TEST" { "Magenta" }
        default { "White" }
    }

    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Test-Command {
    param(
        [string]$Command,
        [string]$Description,
        [int[]]$ExpectedExitCodes = @(0)
    )

    Write-TestResult "Testing: $Description" "TEST"
    if ($Verbose) {
        Write-TestResult "  Command: $Command" "INFO"
    }

    try {
        $output = Invoke-Expression $Command 2>&1
        $exitCode = $LASTEXITCODE

        if ($ExpectedExitCodes -contains $exitCode) {
            Write-TestResult "  [OK] Exit code: $exitCode" "OK"
            if ($Verbose -and $output) {
                Write-Host "  Output: $output"
            }
            return $true
        }
        else {
            Write-TestResult "  [FAIL] Exit code: $exitCode (expected: $($ExpectedExitCodes -join ','))" "ERROR"
            if ($output) {
                Write-Host "  Output: $output"
            }
            return $false
        }
    }
    catch {
        Write-TestResult "  [FAIL] Exception: $_" "ERROR"
        return $false
    }
}

function Initialize-TestEnvironment {
    Write-TestResult "Initializing test environment..." "INFO"

    # Create test directory
    if (Test-Path $TestDir) {
        Remove-Item $TestDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TestDir -Force | Out-Null
    Write-TestResult "  Test directory: $TestDir" "INFO"

    # Change to test directory
    Push-Location $TestDir

    return $true
}

function Cleanup-TestEnvironment {
    Write-TestResult "Cleaning up test environment..." "INFO"

    # Return to original directory
    Pop-Location

    # Remove test directory unless asked to keep it
    if (-not $KeepTestDir -and (Test-Path $TestDir)) {
        Remove-Item $TestDir -Recurse -Force
        Write-TestResult "  Test directory removed" "OK"
    }
    elseif ($KeepTestDir) {
        Write-TestResult "  Test directory kept at: $TestDir" "INFO"
    }
}

# Main test execution
try {
    Write-TestResult "Running rxiv CLI command tests..." "INFO"
    Write-Host ""

    # Initialize environment
    if (-not (Initialize-TestEnvironment)) {
        exit 1
    }

    $testResults = @()

    # Basic commands
    Write-TestResult "=== Basic Commands ===" "INFO"
    $testResults += Test-Command "rxiv --version" "Version check"
    $testResults += Test-Command "rxiv --help" "Help command"

    # Configuration commands
    Write-TestResult "`n=== Configuration Commands ===" "INFO"
    $testResults += Test-Command "rxiv config show" "Show configuration"

    # Version command variations
    Write-TestResult "`n=== Version Commands ===" "INFO"
    $testResults += Test-Command "rxiv version" "Version command"
    $testResults += Test-Command "rxiv version --detailed" "Detailed version"

    # Help for subcommands
    Write-TestResult "`n=== Subcommand Help ===" "INFO"
    $testResults += Test-Command "rxiv init --help" "Init help"
    $testResults += Test-Command "rxiv pdf --help" "PDF help"
    $testResults += Test-Command "rxiv validate --help" "Validate help"
    $testResults += Test-Command "rxiv clean --help" "Clean help"
    $testResults += Test-Command "rxiv figures --help" "Figures help"
    $testResults += Test-Command "rxiv bibliography --help" "Bibliography help"

    # Manuscript initialization
    Write-TestResult "`n=== Manuscript Operations ===" "INFO"
    $testResults += Test-Command "rxiv init test-manuscript" "Initialize manuscript"

    # Check if manuscript was created
    if (Test-Path "test-manuscript") {
        Push-Location "test-manuscript"

        # Check required files
        $requiredFiles = @("00_CONFIG.yml", "01_MAIN.md", "02_SUPPLEMENTARY_INFO.md", "03_REFERENCES.bib")
        $filesExist = $true

        foreach ($file in $requiredFiles) {
            if (Test-Path $file) {
                Write-TestResult "  File exists: $file" "OK"
            }
            else {
                Write-TestResult "  File missing: $file" "ERROR"
                $filesExist = $false
            }
        }

        if ($filesExist) {
            # Test validation (may fail without LaTeX)
            $testResults += Test-Command "rxiv validate --no-doi" "Validate manuscript (no DOI)" @(0, 1)
        }

        Pop-Location
    }
    else {
        Write-TestResult "  Manuscript directory not created" "WARN"
    }

    # Test error handling
    Write-TestResult "`n=== Error Handling ===" "INFO"
    $testResults += Test-Command "rxiv nonexistent-command" "Invalid command" @(2)

    # Summary
    Write-Host ""
    Write-TestResult "=== Test Summary ===" "INFO"
    $passed = ($testResults | Where-Object { $_ -eq $true }).Count
    $failed = ($testResults | Where-Object { $_ -eq $false }).Count
    $total = $testResults.Count

    Write-TestResult "  Total tests: $total" "INFO"
    Write-TestResult "  Passed: $passed" "OK"
    if ($failed -gt 0) {
        Write-TestResult "  Failed: $failed" "ERROR"
    }

    Write-Host ""
    if ($failed -eq 0) {
        Write-TestResult "All tests passed!" "OK"
        $exitCode = 0
    }
    else {
        Write-TestResult "$failed test(s) failed" "ERROR"
        $exitCode = 1
    }
}
catch {
    Write-TestResult "Test execution failed: $_" "ERROR"
    $exitCode = 2
}
finally {
    # Cleanup
    Cleanup-TestEnvironment
}

exit $exitCode
