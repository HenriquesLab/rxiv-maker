# Repository Safeguards System

This directory contains comprehensive safeguards to prevent repository corruption and content contamination between the main rxiv-maker repository and its submodules.

## 🚨 Problem Context

The rxiv-maker project uses Git submodules to manage related repositories:
- `submodules/homebrew-rxiv-maker`: Homebrew formula for package management
- `submodules/scoop-rxiv-maker`: Scoop manifest for Windows package management  
- `submodules/vscode-rxiv-maker`: VSCode extension for enhanced editing

**Previously experienced issues:**
- Incorrect submodule URLs pointing to wrong repositories
- Main repository Python files contaminating VSCode extension repository
- VSCode extension repository containing 79,000+ lines of wrong content
- Manual detection of corruption after the fact

## 🛡️ Multi-Layer Defense System

### Layer 1: Pre-Commit Hooks
**Automatic validation before any commit**

```bash
# Configured in .pre-commit-config.yaml
- validate-submodules        # Basic URL and structure validation
- check-repo-boundaries      # Deep content boundary validation
```

### Layer 2: Manual Validation Scripts
**On-demand validation for developers**

```bash
# Quick validation
./scripts/safeguards/validate-submodules.sh

# Deep boundary analysis  
python ./scripts/safeguards/check-repo-boundaries.py
```

### Layer 3: GitHub Actions CI/CD
**Continuous validation on every push/PR**

```yaml
# .github/workflows/repository-integrity.yml
- Runs on push to main/dev branches
- Runs on PRs affecting submodules
- Daily scheduled validation
- Manual dispatch with deep validation option
```

### Layer 4: Content Protection
**Preventive measures in .gitignore**

```gitignore
# Prevents accidental commits of wrong file types
/Formula/          # Homebrew files → only in homebrew submodule
/bucket/           # Scoop files → only in scoop submodule
/src/extension.ts  # VSCode files → only in vscode submodule
```

## 🔍 Validation Checks

### URL Validation
- ✅ Ensures `.gitmodules` contains correct repository URLs
- ✅ Detects case sensitivity issues (henriqueslab vs HenriquesLab)
- ✅ Validates submodule paths match expected structure

### Content Signature Validation
- ✅ **Homebrew**: Must have `Formula/rxiv-maker.rb`, no Python files
- ✅ **Scoop**: Must have `bucket/rxiv-maker.json`, valid JSON syntax
- ✅ **VSCode**: Must have `package.json` with VSCode engine, `src/extension.ts`

### Contamination Detection
- ✅ **Forward contamination**: Main repo files in submodules
- ✅ **Reverse contamination**: Submodule files in main repo  
- ✅ **Cross-contamination**: Files from one submodule in another

### Git Configuration Validation
- ✅ Submodule `.git` files point to correct gitdir locations
- ✅ Git modules directory structure is intact
- ✅ Submodule commit pointers are valid

## 🚀 Usage Guide

### For Developers

**Before making any submodule changes:**
```bash
# Run validation to ensure current state is clean
./scripts/safeguards/validate-submodules.sh
```

**When working with submodules:**
```bash
# Always use proper git submodule commands
git submodule update --init --recursive
git submodule add <url> <path>

# Never manually copy files between repositories
# Never change .gitmodules URLs without validation
```

**If validation fails:**
```bash
# Check the specific error messages
# Most common fixes:
git submodule sync                    # Fix URL mismatches
git submodule update --init --recursive  # Restore proper content
./scripts/safeguards/validate-submodules.sh  # Re-validate
```

### For Maintainers

**Emergency recovery procedures:**
```bash
# If submodule is completely corrupted
git rm --cached submodules/[name]
rm -rf submodules/[name]
git submodule add --force <correct-url> submodules/[name]

# Validate recovery
./scripts/safeguards/validate-submodules.sh
```

**Adding new submodules:**
1. Add validation rules to `validate-submodules.sh`
2. Update content signatures in `check-repo-boundaries.py`
3. Add URL validation in GitHub Actions workflow
4. Test with `./scripts/safeguards/validate-submodules.sh`

## 📋 Expected Repository Structures

### Main Repository (`rxiv-maker`)
```
Required:
├── pyproject.toml
├── Makefile  
├── src/rxiv_maker/
└── submodules/

Forbidden:
├── Formula/          # Belongs in homebrew submodule
├── bucket/           # Belongs in scoop submodule
├── src/extension.ts  # Belongs in vscode submodule
└── *.tmLanguage.json # Belongs in vscode submodule
```

### Homebrew Submodule (`homebrew-rxiv-maker`)
```
Required:
└── Formula/
    └── rxiv-maker.rb

Forbidden:
├── *.py              # Python files
├── src/rxiv_maker/   # Main repo structure
└── package.json      # VSCode/Node.js files
```

### Scoop Submodule (`scoop-rxiv-maker`)
```
Required:
└── bucket/
    └── rxiv-maker.json

Forbidden:
├── *.py              # Python files
├── src/rxiv_maker/   # Main repo structure
└── *.rb              # Ruby files
```

### VSCode Submodule (`vscode-rxiv-maker`)
```
Required:
├── package.json      # With "engines": {"vscode": "..."}
├── src/extension.ts
└── syntaxes/*.tmLanguage.json

Forbidden:
├── pyproject.toml    # Python project files
├── Makefile          # Main repo build files
├── src/rxiv_maker/   # Main repo source
└── Formula/          # Homebrew files
```

## 🧪 Testing and Development

### Running Tests Locally
```bash
# Test current repository state
./scripts/safeguards/validate-submodules.sh
python ./scripts/safeguards/check-repo-boundaries.py

# Test pre-commit hooks
pre-commit run validate-submodules --all-files
pre-commit run check-repo-boundaries --all-files
```

### Simulating Corruption (for testing)
```bash
# WARNING: Only for testing in disposable branches!

# Simulate URL corruption
sed -i 's/henriqueslab/WRONG/' .gitmodules

# Simulate file contamination
touch submodules/homebrew-rxiv-maker/contamination.py

# Run validation to see safeguards work
./scripts/safeguards/validate-submodules.sh  # Should fail
```

## 🔧 Configuration Files

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
- id: validate-submodules
  entry: scripts/safeguards/validate-submodules.sh
  files: ^(\.gitmodules|submodules/.*)$
  
- id: check-repo-boundaries  
  entry: python scripts/safeguards/check-repo-boundaries.py
  files: ^(\.gitmodules|submodules/.*|src/.*|pyproject\.toml|Makefile)$
```

### GitHub Actions Workflow
```yaml
# .github/workflows/repository-integrity.yml
on:
  push: [main, dev]
  pull_request: [main, dev] 
  schedule: [cron: '0 2 * * *']  # Daily at 2 AM UTC
```

## 📞 Support and Troubleshooting

### Common Error Messages

**"Submodule has incorrect URL"**
```bash
# Fix: Update .gitmodules and sync
git config -f .gitmodules submodule.path.url <correct-url>
git submodule sync path
```

**"Missing required file/directory"**
```bash
# Fix: Ensure submodule is properly initialized
git submodule update --init --recursive path
```

**"Contaminated with wrong file types"**
```bash
# Fix: Remove contaminating files and commit
cd submodules/name
git rm contaminating-file.py
git commit -m "Remove contamination"
cd ../..
git add submodules/name
git commit -m "Update submodule to remove contamination"
```

### Getting Help

1. **Check validation output**: Error messages are designed to be actionable
2. **Review this documentation**: Most issues are covered above
3. **Run manual validation**: Use scripts to get detailed error information
4. **Contact maintainers**: If validation passes but issues persist

## 🔮 Future Enhancements

Planned improvements to the safeguard system:

- **Automated recovery**: Scripts that can automatically fix common corruption patterns  
- **Slack/email alerts**: Notifications when CI detects repository integrity issues
- **Visual dashboard**: Web interface showing repository health status
- **Backup snapshots**: Automated backups of known-good submodule states
- **Policy enforcement**: Prevent merging PRs that fail integrity validation

---

**Remember**: These safeguards are your first line of defense against repository corruption. When in doubt, run the validation scripts! 🛡️