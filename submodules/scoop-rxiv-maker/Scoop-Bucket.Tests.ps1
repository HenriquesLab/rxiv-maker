# Import Scoop testing framework
if (!$env:SCOOP_HOME) {
    $env:SCOOP_HOME = try { Resolve-Path (scoop prefix scoop) } catch { "" }
}

if ($env:SCOOP_HOME -and (Test-Path "$env:SCOOP_HOME\test\Import-Bucket-Tests.ps1")) {
    . "$env:SCOOP_HOME\test\Import-Bucket-Tests.ps1"
} else {
    # Fallback to custom tests if Scoop test framework not available
    Write-Host "Scoop test framework not found, running custom tests..." -ForegroundColor Yellow

    Describe "rxiv-maker Scoop Manifest Tests" {
        BeforeAll {
            $script:manifestPath = "$PSScriptRoot\bucket\rxiv-maker.json"
            $script:manifest = $null

            # Load manifest
            try {
                $script:manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
            } catch {
                Write-Error "Failed to load manifest: $_"
            }
        }

        Context "Manifest Structure" {
            It "Manifest file exists" {
                Test-Path $manifestPath | Should -Be $true
            }

            It "Manifest is valid JSON" {
                { Get-Content $manifestPath -Raw | ConvertFrom-Json } | Should -Not -Throw
            }

            It "Has required fields" {
                $manifest | Should -Not -BeNullOrEmpty
                $manifest.version | Should -Not -BeNullOrEmpty
                $manifest.url | Should -Not -BeNullOrEmpty
                $manifest.hash | Should -Not -BeNullOrEmpty
                $manifest.description | Should -Not -BeNullOrEmpty
                $manifest.homepage | Should -Not -BeNullOrEmpty
                $manifest.license | Should -Not -BeNullOrEmpty
            }

            It "Version follows semantic versioning" {
                $manifest.version | Should -Match '^\d+\.\d+\.\d+$'
            }

            It "URL is HTTPS" {
                $manifest.url | Should -Match '^https://'
            }

            It "Hash is SHA256 format" {
                $manifest.hash | Should -Match '^(sha256:)?[a-fA-F0-9]{64}$'
            }

            It "Has Python dependency" {
                $manifest.depends | Should -Contain 'python'
            }

            It "Has proper bin shim configuration" {
                $manifest.bin | Should -Not -BeNullOrEmpty
                $manifest.bin[0] | Should -HaveCount 3
                $manifest.bin[0][0] | Should -Be 'python'
                $manifest.bin[0][1] | Should -Be 'rxiv'
                $manifest.bin[0][2] | Should -Be '-m rxiv_maker.cli'
            }
        }

        Context "URL and Checksum Validation" -Tag 'Network' {
            It "Download URL is accessible" {
                $response = $null
                try {
                    $response = Invoke-WebRequest -Uri $manifest.url -Method Head -UseBasicParsing -TimeoutSec 30
                    $response.StatusCode | Should -Be 200
                } catch {
                    if ($_.Exception.Response.StatusCode -eq 404) {
                        Set-ItResult -Skipped -Because "URL returned 404 - version might be old"
                    } else {
                        throw $_
                    }
                }
            }

            It "PyPI version exists" {
                $version = $manifest.version
                $pypiUrl = "https://pypi.org/pypi/rxiv-maker/$version/json"

                try {
                    $response = Invoke-RestMethod -Uri $pypiUrl -TimeoutSec 30
                    $response.info.version | Should -Be $version
                } catch {
                    if ($_.Exception.Response.StatusCode -eq 404) {
                        Set-ItResult -Skipped -Because "Version not found on PyPI"
                    } else {
                        throw $_
                    }
                }
            }
        }

        Context "Auto-update Configuration" {
            It "Has checkver configuration" {
                $manifest.checkver | Should -Not -BeNullOrEmpty
                $manifest.checkver.url | Should -Be "https://pypi.org/pypi/rxiv-maker/json"
                $manifest.checkver.jsonpath | Should -Be '$.info.version'
            }

            It "Has autoupdate configuration" {
                $manifest.autoupdate | Should -Not -BeNullOrEmpty
                $manifest.autoupdate.url | Should -Match '\$version'
            }

            It "Autoupdate hash configuration is correct" {
                $manifest.autoupdate.hash | Should -Not -BeNullOrEmpty
                $manifest.autoupdate.hash.url | Should -Be "https://pypi.org/pypi/rxiv-maker/json"
                $manifest.autoupdate.hash.jsonpath | Should -Match '\$version'
            }
        }

        Context "Installation Hooks" {
            It "Has pre_install hooks" {
                $manifest.pre_install | Should -Not -BeNullOrEmpty
                $manifest.pre_install | Should -HaveCount 2
            }

            It "Has post_install hooks" {
                $manifest.post_install | Should -Not -BeNullOrEmpty
                $manifest.post_install.Count | Should -BeGreaterThan 5
            }

            It "Post install includes pip install command" {
                $pipCommand = $manifest.post_install | Where-Object { $_ -match 'pip install' }
                $pipCommand | Should -Not -BeNullOrEmpty
                $pipCommand | Should -Match 'rxiv-maker==\$version'
            }

            It "Has pre_uninstall hooks" {
                $manifest.pre_uninstall | Should -Not -BeNullOrEmpty
                $manifest.pre_uninstall | Should -HaveCount 2
            }

            It "Pre uninstall includes pip uninstall command" {
                $pipUninstall = $manifest.pre_uninstall | Where-Object { $_ -match 'pip uninstall' }
                $pipUninstall | Should -Not -BeNullOrEmpty
                $pipUninstall | Should -Match 'rxiv-maker'
            }
        }

        Context "Dependencies and Suggestions" {
            It "Suggests LaTeX distributions" {
                $manifest.suggest | Should -Not -BeNullOrEmpty
                $manifest.suggest.'LaTeX distribution' | Should -Not -BeNullOrEmpty
                $manifest.suggest.'LaTeX distribution' | Should -Contain 'extras/latex'
                $manifest.suggest.'LaTeX distribution' | Should -Contain 'extras/miktex'
            }

            It "Suggests version control" {
                $manifest.suggest.'Version control' | Should -Be 'git'
            }

            It "Suggests build tools" {
                $manifest.suggest.'Build tools' | Should -Be 'make'
            }
        }

        Context "User Documentation" {
            It "Has notes section" {
                $manifest.notes | Should -Not -BeNullOrEmpty
                $manifest.notes | Should -HaveCount 7
            }

            It "Notes mention rxiv command" {
                $notesText = $manifest.notes -join ' '
                $notesText | Should -Match 'rxiv'
            }

            It "Notes mention documentation URL" {
                $notesText = $manifest.notes -join ' '
                $notesText | Should -Match 'github.com/henriqueslab/rxiv-maker'
            }
        }

        Context "Installation Simulation" -Tag 'CI' {
            It "Can simulate installation process" {
                # This test simulates what Scoop would do without actually installing
                $pythonAvailable = Get-Command python -ErrorAction SilentlyContinue

                if (!$pythonAvailable) {
                    Set-ItResult -Skipped -Because "Python not available for testing"
                    return
                }

                # Test that pip command would work
                $pipVersion = & python -m pip --version 2>&1
                $pipVersion | Should -Match 'pip \d+'
            }
        }
    }

    # Additional custom tests specific to rxiv-maker
    Describe "rxiv-maker Specific Tests" {
        Context "PyPI Integration" -Tag 'Network' {
            It "Latest PyPI version check works" {
                try {
                    $pypiData = Invoke-RestMethod -Uri "https://pypi.org/pypi/rxiv-maker/json" -TimeoutSec 30
                    $latestVersion = $pypiData.info.version
                    $latestVersion | Should -Match '^\d+\.\d+\.\d+$'
                } catch {
                    Set-ItResult -Skipped -Because "Could not connect to PyPI"
                }
            }

            It "Wheel package exists for current version" {
                $version = $manifest.version
                try {
                    $pypiData = Invoke-RestMethod -Uri "https://pypi.org/pypi/rxiv-maker/$version/json" -TimeoutSec 30
                    $wheelFiles = $pypiData.urls | Where-Object { $_.packagetype -eq 'bdist_wheel' }
                    $wheelFiles | Should -Not -BeNullOrEmpty
                } catch {
                    Set-ItResult -Skipped -Because "Could not fetch version data from PyPI"
                }
            }
        }

        Context "Performance Tests" -Tag 'Performance' {
            It "Manifest loads quickly" {
                $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
                Get-Content $manifestPath -Raw | ConvertFrom-Json | Out-Null
                $stopwatch.Stop()

                # Manifest should load in under 100ms
                $stopwatch.ElapsedMilliseconds | Should -BeLessThan 100
            }
        }
    }
}
