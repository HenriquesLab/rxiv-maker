# test-python-env.ps1
# Test helper script for Python environment validation in Scoop

param(
    [string]$Action = "test",
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
        default { "White" }
    }

    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Test-PythonInstallation {
    Write-TestResult "Testing Python installation..." "INFO"

    try {
        $pythonVersion = python --version 2>&1
        Write-TestResult "Python found: $pythonVersion" "OK"
        return $true
    }
    catch {
        Write-TestResult "Python not found in PATH" "ERROR"
        return $false
    }
}

function Test-PipInstallation {
    Write-TestResult "Testing pip installation..." "INFO"

    try {
        $pipVersion = python -m pip --version 2>&1
        Write-TestResult "Pip found: $pipVersion" "OK"
        return $true
    }
    catch {
        Write-TestResult "Pip not found or not working" "ERROR"
        return $false
    }
}

function Test-RxivMakerModule {
    Write-TestResult "Testing rxiv-maker Python module..." "INFO"

    try {
        $result = python -c "import rxiv_maker; print(f'rxiv-maker version: {rxiv_maker.__version__}')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-TestResult $result "OK"
            return $true
        }
        else {
            Write-TestResult "Failed to import rxiv_maker module" "ERROR"
            return $false
        }
    }
    catch {
        Write-TestResult "Error testing rxiv_maker module: $_" "ERROR"
        return $false
    }
}

function Test-RxivCommand {
    Write-TestResult "Testing rxiv CLI command..." "INFO"

    try {
        $rxivPath = Get-Command rxiv -ErrorAction Stop
        Write-TestResult "rxiv command found at: $($rxivPath.Source)" "OK"

        $version = rxiv --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-TestResult "rxiv version: $version" "OK"
            return $true
        }
        else {
            Write-TestResult "rxiv command failed with exit code: $LASTEXITCODE" "ERROR"
            return $false
        }
    }
    catch {
        Write-TestResult "rxiv command not found in PATH" "ERROR"
        return $false
    }
}

function Test-Dependencies {
    Write-TestResult "Testing Python dependencies..." "INFO"

    $dependencies = @(
        "click",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "seaborn",
        "PIL",
        "pypdf",
        "yaml",
        "crossref_commons",
        "rich",
        "rich_click"
    )

    $failed = @()

    foreach ($dep in $dependencies) {
        try {
            $importName = if ($dep -eq "PIL") { "PIL" }
                         elseif ($dep -eq "yaml") { "yaml" }
                         else { $dep }

            python -c "import $importName" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                if ($Verbose) {
                    Write-TestResult "  + $dep" "OK"
                }
            }
            else {
                $failed += $dep
                Write-TestResult "  - $dep" "ERROR"
            }
        }
        catch {
            $failed += $dep
            Write-TestResult "  - $dep (exception)" "ERROR"
        }
    }

    if ($failed.Count -eq 0) {
        Write-TestResult "All dependencies installed correctly" "OK"
        return $true
    }
    else {
        Write-TestResult "Missing dependencies: $($failed -join ', ')" "ERROR"
        return $false
    }
}

function Test-PathConfiguration {
    Write-TestResult "Testing PATH configuration..." "INFO"

    # Check if Python scripts directory is in PATH
    $pythonScripts = python -c "import site; print(site.USER_BASE + '\\Scripts')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pythonScripts = $pythonScripts.Trim()
        if ($env:PATH -like "*$pythonScripts*") {
            Write-TestResult "Python scripts directory in PATH: $pythonScripts" "OK"
            return $true
        }
        else {
            Write-TestResult "Python scripts directory NOT in PATH: $pythonScripts" "WARN"
            Write-TestResult "You may need to add it manually or restart your shell" "INFO"
            return $false
        }
    }
    else {
        Write-TestResult "Could not determine Python scripts directory" "WARN"
        return $false
    }
}

# Main execution
switch ($Action) {
    "test" {
        Write-TestResult "Running rxiv-maker environment tests..." "INFO"
        Write-Host ""

        $results = @{
            Python = Test-PythonInstallation
            Pip = Test-PipInstallation
            Module = Test-RxivMakerModule
            Command = Test-RxivCommand
            Dependencies = Test-Dependencies
            Path = Test-PathConfiguration
        }

        Write-Host ""
        Write-TestResult "Test Summary:" "INFO"
        $passed = 0
        $failed = 0

        foreach ($test in $results.GetEnumerator()) {
            if ($test.Value) {
                Write-TestResult "  $($test.Key): PASSED" "OK"
                $passed++
            }
            else {
                Write-TestResult "  $($test.Key): FAILED" "ERROR"
                $failed++
            }
        }

        Write-Host ""
        if ($failed -eq 0) {
            Write-TestResult "All tests passed!" "OK"
            exit 0
        }
        else {
            Write-TestResult "$failed test(s) failed" "ERROR"
            exit 1
        }
    }

    "check-python" {
        if (Test-PythonInstallation) { exit 0 } else { exit 1 }
    }

    "check-module" {
        if (Test-RxivMakerModule) { exit 0 } else { exit 1 }
    }

    "check-command" {
        if (Test-RxivCommand) { exit 0 } else { exit 1 }
    }

    default {
        Write-TestResult "Unknown action: $Action" "ERROR"
        Write-TestResult "Valid actions: test, check-python, check-module, check-command" "INFO"
        exit 1
    }
}
