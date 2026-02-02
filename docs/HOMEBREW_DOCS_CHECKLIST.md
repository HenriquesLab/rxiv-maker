# Homebrew Documentation Review Checklist

Use this checklist when reviewing or adding Homebrew formula documentation to ensure consistency across HenriquesLab repositories.

## Quick Review Checklist

### CONTRIBUTING.md

- [ ] **Automated workflow first**: `just release PACKAGE_NAME` shown as recommended method
- [ ] **Manual workflow second**: Included as "Alternative" with clear heading
- [ ] **Version placeholder**: Uses `VERSION=X.Y.Z` (NOT hardcoded like `VERSION=1.18.4`)
- [ ] **Relative path**: Uses `../homebrew-formulas` (NOT `~/GitHub/homebrew-formulas`)
- [ ] **Repository link**: Includes link to https://github.com/HenriquesLab/homebrew-formulas
- [ ] **Utility commands note**: Mentions `just list`, `just check-updates`, `just sha256`
- [ ] **Preference note**: States automated workflow is "preferred for consistency and efficiency"

### CLAUDE.md (if present)

- [ ] **Homebrew section exists**: Documents the Homebrew formula update process
- [ ] **Automation documented**: Shows `just release PACKAGE_NAME` workflow
- [ ] **Commands listed**: Includes Option 1 (automated) and Option 2 (manual step-by-step)
- [ ] **Workflow notes**: Explains PyPI verification, automatic metadata, full automation
- [ ] **Consistent with CONTRIBUTING.md**: Both files reference the same workflow

### Common Issues to Check

#### 1. Hardcoded Versions
❌ **BAD:**
```bash
VERSION=1.18.4  # Replace with new version
```

✅ **GOOD:**
```bash
VERSION=X.Y.Z  # Replace with new version
```

#### 2. Absolute Paths
❌ **BAD:**
```bash
cd ~/GitHub/homebrew-formulas
```

✅ **GOOD:**
```bash
cd ../homebrew-formulas  # Use relative path from PACKAGE_NAME directory
```

#### 3. Manual-First Approach
❌ **BAD:**
```markdown
## Updating the Homebrew Formula

### 1. Get Package Information from PyPI
[manual steps...]
```

✅ **GOOD:**
```markdown
## Updating the Homebrew Formula

### Automated Workflow (Recommended)
[automated steps...]

### Manual Workflow (Alternative)
[manual steps...]
```

#### 4. Missing Context
❌ **BAD:**
```bash
just release PACKAGE_NAME
```

✅ **GOOD:**
```bash
cd ../homebrew-formulas
just release PACKAGE_NAME  # Full workflow: update → test → commit → push
```

With explanation of what it does automatically.

## Repository-Specific Checks

### Package Names
Verify correct package name mapping:
- **rxiv-maker** → CLI: `rxiv`
- **TaskRepo** → CLI: `tsk`
- **folder2md4llms** → CLI: `folder2md`

### Verification Commands
Check if package-specific verification is included where applicable:
- rxiv-maker: `rxiv check-installation` (optional)
- TaskRepo: `tsk --version`
- folder2md4llms: `folder2md --version`

## Before Committing

1. **Test template substitution**: Ensure PACKAGE_NAME and COMMAND_NAME are correctly replaced
2. **Check links**: Verify all repository links are valid
3. **Validate formatting**: Ensure code blocks and markdown formatting are correct
4. **Cross-reference**: Compare with rxiv-maker, folder2md4llms, or TaskRepo for consistency

## After PR Merge

1. **Update template**: If new patterns emerge, update HOMEBREW_FORMULA_TEMPLATE.md
2. **Document in checklist**: Add new common issues to this checklist
3. **Cross-repository sync**: Consider if other repos need the same update

## Automated Review Indicators

These patterns indicate potential issues:

```bash
# Pattern detection for automated reviews
grep -n "VERSION=[0-9]" CONTRIBUTING.md           # Hardcoded version
grep -n "~/GitHub/homebrew" CONTRIBUTING.md       # Absolute path
grep -n "^### 1\." CONTRIBUTING.md                # Manual-first approach (missing automated section)
```

## Related PRs

Template established and applied in:
- **rxiv-maker**: PR #280
- **folder2md4llms**: PR #37
- **TaskRepo**: PR #12

## Template Location

Standard template: `docs/HOMEBREW_FORMULA_TEMPLATE.md`

---

**Last updated:** 2026-02-02
