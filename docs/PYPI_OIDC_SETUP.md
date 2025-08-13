# PyPI OIDC Trusted Publisher Configuration

## Status
The simplified GitHub Actions release workflow (v1.4.23) is working correctly but requires PyPI OIDC configuration to publish packages.

## What's Working
✅ Package building and validation
✅ GitHub release creation with artifacts
✅ Release notes generation
✅ OIDC token exchange with GitHub

## What Needs Configuration
The PyPI publishing step failed with `invalid-publisher` error. This is expected - PyPI needs to be configured to trust this GitHub repository.

## Setup Instructions

### 1. Configure PyPI Trusted Publisher
1. Log into PyPI.org with the `rxiv-maker` package owner account
2. Navigate to the project settings: https://pypi.org/manage/project/rxiv-maker/settings/
3. Go to "Publishing" → "Add a new publisher"
4. Configure GitHub Actions publisher with these exact values:

```yaml
Owner: HenriquesLab
Repository: rxiv-maker
Workflow name: release-simple.yml
Environment name: pypi  # Important: must match workflow
```

### 2. Important Notes
- The environment name MUST be `pypi` to match the workflow configuration
- No API tokens are needed - OIDC eliminates the need for stored secrets
- The workflow will automatically use OIDC after PyPI configuration

### 3. Testing After Configuration
Once PyPI is configured, the next tag push will automatically:
1. Build the package
2. Create GitHub release
3. Publish to PyPI using OIDC (no tokens!)

## Workflow Claims (for debugging)
The workflow presents these OIDC claims to PyPI:
- `repository`: `HenriquesLab/rxiv-maker`
- `repository_owner`: `HenriquesLab`
- `environment`: `pypi`
- `workflow_ref`: `HenriquesLab/rxiv-maker/.github/workflows/release-simple.yml@refs/tags/vX.Y.Z`

## Security Benefits
- No stored API tokens that can be compromised
- Short-lived tokens (expires after job completion)
- Cryptographically verified publisher identity
- Audit trail of all publishing attempts

## Alternative: Fallback to API Token
If OIDC cannot be configured, add a PyPI API token as a repository secret:
1. Create token at https://pypi.org/manage/account/token/
2. Add as repository secret named `PYPI_API_TOKEN`
3. Modify workflow to use token-based authentication (not recommended)