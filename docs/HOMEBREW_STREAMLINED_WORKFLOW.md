# Streamlined Homebrew Workflow Guide

This document explains the new hybrid Homebrew workflow that can operate in two modes: traditional PR-based updates and streamlined direct-push updates.

## 🎯 Overview

The enhanced workflow supports two operational modes:

1. **🚀 Direct Push Mode (Streamlined)**: Automatically validates and pushes formula updates directly to main
2. **📋 PR Mode (Traditional)**: Creates pull requests for manual review (legacy behavior)

## 🔄 Workflow Modes

### Direct Push Mode (Recommended)
- **Speed**: ~5 minutes from release to homebrew availability
- **Validation**: Comprehensive pre-commit testing and validation
- **Safety**: Automatic rollback on failure
- **User Experience**: Immediate access to new releases

### PR Mode (Legacy)
- **Speed**: Hours to days (requires manual review)
- **Validation**: Post-merge testing
- **Safety**: Manual review process
- **User Experience**: Delayed access pending PR merge

## 🚀 Enabling Direct Push Mode

### Method 1: Repository Variable (Recommended)
Set the repository variable `HOMEBREW_DIRECT_PUSH` to `true`:

1. Go to Settings → Secrets and variables → Actions
2. Click "Variables" tab
3. Add variable: `HOMEBREW_DIRECT_PUSH` = `true`

### Method 2: Manual Workflow Dispatch
1. Go to Actions → Auto-update Homebrew Formula
2. Click "Run workflow"
3. Check "Use direct push instead of PR workflow"
4. Enter tag name (e.g., `v1.5.0`)
5. Run workflow

### Method 3: Environment Variable (Testing)
For testing, set environment variable in workflow file:
```yaml
env:
  USE_DIRECT_PUSH: 'true'
```

## 🛡️ Safety Features

### Pre-Commit Validation
- **Ruby syntax check**: Ensures formula is syntactically valid
- **Brew audit**: Validates formula structure and dependencies
- **Tarball verification**: Confirms download integrity and accessibility
- **Installation test**: Verifies formula installs and runs correctly
- **Version validation**: Confirms installed version matches expected

### Rollback Protection
- **Backup creation**: Stores commit reference before changes
- **Automatic rollback**: Reverts to previous state on any failure
- **Force push recovery**: Restores repository to working state
- **Comprehensive logging**: Full audit trail for debugging

### Monitoring & Alerting
- **Step-by-step reporting**: Clear status at each validation stage
- **Failure notifications**: Immediate alerts on issues
- **Success confirmation**: Verification of successful updates
- **Unified summary**: Mode-aware status reporting

## 📊 Comparison

| Feature | Direct Push Mode | PR Mode |
|---------|------------------|---------|
| **Time to Release** | ~5 minutes | Hours/days |
| **Manual Intervention** | None | Required |
| **Validation** | Pre-commit | Post-merge |
| **Rollback** | Automatic | Manual |
| **Testing** | Comprehensive | Basic |
| **User Access** | Immediate | Delayed |
| **Complexity** | Simple | Complex |

## 🧪 Testing the Workflow

### Test with Feature Flag
1. Enable direct push mode via repository variable
2. Create a test release or use manual workflow dispatch
3. Monitor workflow execution in Actions tab
4. Verify formula update in homebrew repository
5. Test installation: `brew install HenriquesLab/rxiv-maker/rxiv-maker`

### Validation Steps
The workflow performs these validation steps in direct push mode:

```bash
# 1. Syntax validation
ruby -c Formula/rxiv-maker.rb

# 2. Formula audit
brew audit --strict --online Formula/rxiv-maker.rb

# 3. Installation test
brew install --build-from-source Formula/rxiv-maker.rb

# 4. Version verification
rxiv --version | grep "expected_version"

# 5. Cleanup
brew uninstall rxiv-maker
```

## 🔧 Troubleshooting

### Common Issues

**Validation Failures:**
- Check formula syntax and brew audit output
- Verify tarball is accessible and SHA256 matches
- Ensure all dependencies are available

**Push Failures:**
- Confirm token has write permissions to homebrew repository
- Check for conflicts with concurrent updates
- Review backup and rollback logs

**Installation Test Failures:**
- Verify formula dependencies
- Check build requirements
- Review installation logs

### Monitoring Workflow Execution

Check these locations for detailed information:
- **Actions Tab**: Real-time workflow execution
- **Step Summary**: Unified status and next steps
- **Workflow Logs**: Detailed step-by-step output
- **Repository History**: Commit history in homebrew repo

## 🔐 Security Considerations

### Token Permissions
The workflow requires these permissions for direct push mode:
- **Contents**: Write (to update formula and push commits)
- **Metadata**: Read (basic repository access)

**Removed permissions** (no longer needed):
- **Pull requests**: Write
- **Issues**: Write

### Safety Measures
- All changes are atomic (single commit)
- Comprehensive validation before any push
- Automatic rollback on failure
- Full audit trail and logging
- No secrets or sensitive data exposure

## 📈 Migration Timeline

### Phase 1: Parallel Operation (Recommended)
- Keep both modes available
- Test direct push mode with minor releases
- Collect performance and reliability metrics
- Train team on new workflow

### Phase 2: Primary Mode Switch
- Make direct push mode the default
- Use PR mode only for special cases
- Document lessons learned
- Update team procedures

### Phase 3: Full Migration (Optional)
- Remove PR mode entirely
- Simplify workflow configuration
- Update all documentation
- Archive legacy workflow

## 📞 Support and Feedback

### Getting Help
- **GitHub Issues**: Technical problems with the workflow
- **Discussions**: Questions about workflow configuration
- **Documentation**: Updates to this guide based on experience

### Reporting Issues
Include this information when reporting workflow issues:
- Workflow mode used (direct push or PR)
- Release version being processed
- Link to failed workflow run
- Error messages from logs
- Expected vs actual behavior

## 🎉 Benefits Summary

**For Users:**
- Immediate access to new releases via Homebrew
- Faster bug fixes and feature availability
- More reliable installation experience

**For Maintainers:**
- Reduced manual intervention
- Simplified release process
- Better automation and monitoring
- Faster feedback on issues

**For the Project:**
- Improved user experience
- Reduced maintenance overhead
- More predictable release pipeline
- Better reliability and testing

---

This streamlined workflow represents a significant improvement in the release pipeline while maintaining the safety and reliability that users expect.