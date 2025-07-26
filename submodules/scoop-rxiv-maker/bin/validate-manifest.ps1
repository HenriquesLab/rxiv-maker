#Requires -Version 5.1

<#
.SYNOPSIS
    Validate rxiv-maker Scoop manifest locally
.DESCRIPTION
    Validates the rxiv-maker.json manifest file including JSON syntax, required fields,
    and network connectivity to download URLs.
.PARAMETER ManifestPath
    Path to the manifest file (default: bucket/rxiv-maker.json)
.PARAMETER SkipNetwork
    Skip network-based tests (URL verification)
.EXAMPLE
    .\bin\validate-manifest.ps1
    Validate manifest with all tests

.EXAMPLE
    .\bin\validate-manifest.ps1 -SkipNetwork
    Validate manifest structure only, skip network tests
#>

param(
    [String] $ManifestPath = "$PSScriptRoot/../bucket/rxiv-maker.json",
    [Switch] $SkipNetwork
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "🔍 Scoop Manifest Validator" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Check if manifest file exists
if (!(Test-Path $ManifestPath)) {
    Write-Host "❌ Manifest file not found: $ManifestPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Manifest file found: $ManifestPath" -ForegroundColor Green

# Test JSON syntax
Write-Host "`n📝 Testing JSON syntax..." -ForegroundColor Yellow
try {
    $manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
    Write-Host "✅ JSON syntax is valid" -ForegroundColor Green
} catch {
    Write-Host "❌ JSON syntax error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Validate required fields
Write-Host "`n🔍 Validating required fields..." -ForegroundColor Yellow
$requiredFields = @('version', 'url', 'hash', 'description', 'homepage', 'license')
$missingFields = @()

foreach ($field in $requiredFields) {
    if (!$manifest.$field) {
        $missingFields += $field
    }
}

if ($missingFields.Count -gt 0) {
    Write-Host "❌ Missing required fields: $($missingFields -join ', ')" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ All required fields present" -ForegroundColor Green
}

# Validate field formats
Write-Host "`n✏️ Validating field formats..." -ForegroundColor Yellow

# Version format
if ($manifest.version -match '^\d+\.\d+\.\d+$') {
    Write-Host "✅ Version format is valid: $($manifest.version)" -ForegroundColor Green
} else {
    Write-Host "❌ Invalid version format: $($manifest.version)" -ForegroundColor Red
    exit 1
}

# URL format
if ($manifest.url -match '^https://') {
    Write-Host "✅ URL format is valid (HTTPS)" -ForegroundColor Green
} else {
    Write-Host "❌ URL must be HTTPS: $($manifest.url)" -ForegroundColor Red
    exit 1
}

# Hash format
if ($manifest.hash -match '^(sha256:)?[a-fA-F0-9]{64}$') {
    Write-Host "✅ Hash format is valid (SHA256)" -ForegroundColor Green
} else {
    Write-Host "❌ Invalid hash format: $($manifest.hash)" -ForegroundColor Red
    exit 1
}

# Dependencies
if ($manifest.depends -contains 'python') {
    Write-Host "✅ Python dependency is present" -ForegroundColor Green
} else {
    Write-Host "❌ Missing Python dependency" -ForegroundColor Red
    exit 1
}

# Binary shim configuration
if ($manifest.bin -and $manifest.bin[0] -and $manifest.bin[0].Count -eq 3) {
    Write-Host "✅ Binary shim configuration is valid" -ForegroundColor Green
} else {
    Write-Host "❌ Invalid binary shim configuration" -ForegroundColor Red
    exit 1
}

# Network tests (if not skipped)
if (!$SkipNetwork) {
    Write-Host "`n🌐 Testing network connectivity..." -ForegroundColor Yellow

    # Test download URL
    Write-Host "Testing download URL: $($manifest.url)"
    try {
        $response = Invoke-WebRequest -Uri $manifest.url -Method Head -UseBasicParsing -TimeoutSec 30
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Download URL is accessible" -ForegroundColor Green
        } else {
            Write-Host "❌ Download URL returned status: $($response.StatusCode)" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Download URL test failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }

    # Test PyPI version
    Write-Host "Testing PyPI version: $($manifest.version)"
    try {
        $pypiUrl = "https://pypi.org/pypi/rxiv-maker/$($manifest.version)/json"
        $response = Invoke-RestMethod -Uri $pypiUrl -TimeoutSec 30
        if ($response.info.version -eq $manifest.version) {
            Write-Host "✅ Version exists on PyPI" -ForegroundColor Green
        } else {
            Write-Host "❌ Version mismatch on PyPI" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ PyPI version test failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }

    # Test autoupdate URL pattern
    if ($manifest.autoupdate -and $manifest.autoupdate.url) {
        Write-Host "Testing autoupdate URL pattern..."
        try {
            $autoupdateUrl = $manifest.autoupdate.url -replace '\$version', $manifest.version
            $response = Invoke-WebRequest -Uri $autoupdateUrl -Method Head -UseBasicParsing -TimeoutSec 30
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Autoupdate URL pattern is valid" -ForegroundColor Green
            } else {
                Write-Host "❌ Autoupdate URL returned status: $($response.StatusCode)" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "❌ Autoupdate URL test failed: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "`n🌐 Network tests skipped" -ForegroundColor Yellow
}

# Display manifest summary
Write-Host "`n📋 Manifest Summary:" -ForegroundColor Cyan
Write-Host "  Version: $($manifest.version)" -ForegroundColor Gray
Write-Host "  Description: $($manifest.description)" -ForegroundColor Gray
Write-Host "  Homepage: $($manifest.homepage)" -ForegroundColor Gray
Write-Host "  License: $($manifest.license)" -ForegroundColor Gray
Write-Host "  Download URL: $($manifest.url)" -ForegroundColor Gray
Write-Host "  Hash: $($manifest.hash)" -ForegroundColor Gray

Write-Host "`n✅ Manifest validation completed successfully!" -ForegroundColor Green
exit 0
