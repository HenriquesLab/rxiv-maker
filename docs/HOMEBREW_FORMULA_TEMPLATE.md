# Homebrew Formula Update Template

This template provides standardized documentation for Homebrew formula updates across HenriquesLab repositories.

## Template for CONTRIBUTING.md

Use this section in your CONTRIBUTING.md file:

```markdown
## Updating the Homebrew Formula

When releasing a new version, the Homebrew formula must be updated in the [`homebrew-formulas` repository](https://github.com/HenriquesLab/homebrew-formulas).

### Automated Workflow (Recommended)

\`\`\`bash
cd ../homebrew-formulas
just release PACKAGE_NAME  # Full workflow: update → test → commit → push
\`\`\`

This automatically:
- Fetches the latest version from PyPI
- Downloads and calculates SHA256 checksum
- Updates the formula file
- Tests the installation
- Commits with standardized message
- Pushes to remote

### Manual Workflow (Alternative)

If `just` is not available, you can update the formula manually:

#### 1. Get Package Information from PyPI

\`\`\`bash
VERSION=X.Y.Z  # Replace with new version
curl "https://pypi.org/pypi/PACKAGE_NAME/$VERSION/json" | \\
  jq -r '.urls[] | select(.packagetype=="sdist") | "URL: \\(.url)\\nSHA256: \\(.digests.sha256)"'
\`\`\`

#### 2. Update the Formula

Navigate to the homebrew-formulas repository and edit the formula:

\`\`\`bash
cd ../homebrew-formulas  # Use relative path from PACKAGE_NAME directory
\`\`\`

Edit `Formula/PACKAGE_NAME.rb`:
- Update the `url` line with the new URL
- Update the `sha256` line with the new hash

#### 3. Test Locally

\`\`\`bash
brew uninstall PACKAGE_NAME 2>/dev/null || true
brew install --build-from-source ./Formula/PACKAGE_NAME.rb
brew test PACKAGE_NAME
COMMAND_NAME --version  # Verify correct version
\`\`\`

#### 4. Audit the Formula

\`\`\`bash
brew audit --strict --online PACKAGE_NAME
\`\`\`

#### 5. Commit and Push

\`\`\`bash
git add Formula/PACKAGE_NAME.rb
git commit -m "PACKAGE_NAME: update to version $VERSION"
git push
\`\`\`

#### 6. Verify Installation

\`\`\`bash
brew uninstall PACKAGE_NAME
brew install henriqueslab/formulas/PACKAGE_NAME
COMMAND_NAME --version
\`\`\`

**Note:** The automated workflow using `just` is preferred for consistency and efficiency. See the [homebrew-formulas repository](https://github.com/HenriquesLab/homebrew-formulas) for additional utility commands like `just list`, `just check-updates`, and `just sha256`
```

## Template for CLAUDE.md

Include this section in your CLAUDE.md file:

```markdown
### Homebrew Formula Updates

PACKAGE_NAME is distributed via PyPI and Homebrew. After the PyPI release is live, update the Homebrew formula.

#### Homebrew Formula Location

The Homebrew formula is maintained in a separate repository located at `../homebrew-formulas`:
- **Repository**: `../homebrew-formulas/`
- **Formula file**: `Formula/PACKAGE_NAME.rb`
- **Automation**: Managed via justfile commands

#### Commands

After the PyPI release is live and verified at https://pypi.org/project/PACKAGE_NAME/:

\`\`\`bash
cd ../homebrew-formulas

# Option 1: Full automated release workflow (recommended)
# This will update, test, commit, and push in one command
just release PACKAGE_NAME

# Option 2: Manual step-by-step workflow
just update PACKAGE_NAME           # Updates to latest PyPI version
just test PACKAGE_NAME             # Tests the formula installation
just commit PACKAGE_NAME VERSION   # Commits with standardized message
git push                           # Push to remote

# Utility commands
just list                          # List all formulas with current versions
just check-updates                 # Check for available PyPI updates
just sha256 PACKAGE_NAME VERSION   # Get SHA256 for a specific version
\`\`\`

#### Workflow Notes

- **Always verify PyPI first**: The formula update pulls package info from PyPI, so the release must be live
- **Automatic metadata**: The `just update` command automatically fetches the version, download URL, and SHA256 checksum from PyPI
- **Full automation**: The `just release` command runs the complete workflow: update → test → commit → push
- **Standardized commits**: Formula updates use consistent commit message format
- **Testing**: The `just test` command uninstalls and reinstalls the formula to verify it works correctly
```

## Customization Guide

When using this template for a new package:

### Required Replacements

1. **PACKAGE_NAME**: Replace with the PyPI package name (e.g., `rxiv-maker`, `taskrepo`, `folder2md4llms`)
2. **COMMAND_NAME**: Replace with the CLI command (e.g., `rxiv`, `tsk`, `folder2md`)

### Optional Additions

Depending on your package, you may want to add:

1. **Verification commands**: Additional commands to verify installation (e.g., `rxiv check-installation`)
2. **Platform-specific notes**: If there are macOS/Linux differences
3. **Dependencies**: If the formula has special dependencies to note

## Examples

### rxiv-maker
```bash
PACKAGE_NAME=rxiv-maker
COMMAND_NAME=rxiv
```

### TaskRepo
```bash
PACKAGE_NAME=taskrepo
COMMAND_NAME=tsk
```

### folder2md4llms
```bash
PACKAGE_NAME=folder2md4llms
COMMAND_NAME=folder2md
```

## Consistency Checklist

When adding Homebrew documentation to a repository, ensure:

- [ ] Use `just release PACKAGE_NAME` as the primary recommended method
- [ ] Show automated workflow first, manual workflow second
- [ ] Use `VERSION=X.Y.Z` as placeholder (not hardcoded version)
- [ ] Use `../homebrew-formulas` relative path (not hardcoded absolute path)
- [ ] Reference `homebrew-formulas` repository for utility commands
- [ ] Include note about automated workflow being preferred
- [ ] Link to https://github.com/HenriquesLab/homebrew-formulas
- [ ] Document both CONTRIBUTING.md and CLAUDE.md (if CLAUDE.md exists)

## Related Documentation

- **homebrew-formulas repository**: https://github.com/HenriquesLab/homebrew-formulas
- **Just command runner**: https://github.com/casey/just
- **Homebrew formula documentation**: https://docs.brew.sh/Formula-Cookbook

## Maintenance

This template should be updated when:
- Homebrew formula automation workflow changes
- New utility commands are added to homebrew-formulas
- Common issues or best practices are identified

**Last updated:** 2026-02-02 (aligned with rxiv-maker PR #280, folder2md4llms PR #37, TaskRepo PR #12)
