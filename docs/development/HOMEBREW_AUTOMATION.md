# Homebrew Automation Setup

This document explains how the automated Homebrew formula updates work and how to set them up.

## 🎯 Overview

The `homebrew-auto-update.yml` workflow automatically updates the Homebrew formula in the `homebrew-rxiv-maker` repository whenever a new release is published in the main `rxiv-maker` repository.

## 🔐 Authentication Setup

### Required Secret: `HOMEBREW_UPDATE_TOKEN`

This is a GitHub Fine-Grained Personal Access Token that allows the automation to:
- Read the homebrew-rxiv-maker repository
- Create branches and pull requests
- Update formula files

### Token Configuration

**Repository Access:**
- Target: `HenriquesLab/homebrew-rxiv-maker`

**Required Permissions:**
- **Contents**: Read and write (to update formula file)
- **Metadata**: Read (basic repository access)
- **Pull requests**: Write (to create automated PRs)
- **Issues**: Write (optional, for linking)

### Security Best Practices

1. **Fine-Grained Tokens**: Use fine-grained tokens instead of classic tokens
2. **Minimal Scope**: Only grant access to the homebrew-rxiv-maker repository
3. **Regular Rotation**: Set 1-year expiration and rotate before expiry
4. **Monitor Usage**: Review token usage in GitHub settings periodically

## 🚀 How It Works

### Workflow Trigger
```yaml
on:
  release:
    types: [published]
```

### Automation Steps

1. **Extract Release Info**: Gets version and download URL from the release
2. **Calculate SHA256**: Downloads tarball and calculates hash
3. **Update Formula**: Updates URL and SHA256 in `Formula/rxiv-maker.rb`
4. **Create PR**: Opens pull request with the changes
5. **Auto-merge**: *(Future enhancement)* Could auto-merge if tests pass

### Generated PR Example

```markdown
## 📦 Automatic Formula Update

This PR automatically updates the rxiv-maker Homebrew formula to version **v1.5.0**.

### 🔄 Changes Made
- ✅ Updated release URL to: `https://github.com/HenriquesLab/rxiv-maker/archive/refs/tags/v1.5.0.tar.gz`
- ✅ Updated SHA256 hash to: `abc123...`

### 🧪 Testing
After merging, the formula can be tested with:
```bash
brew tap HenriquesLab/rxiv-maker  
brew install rxiv-maker
rxiv --version
```
```

## 🧪 Testing

### Test Token Permissions
```bash
# Export your token (don't commit this!)
export HOMEBREW_UPDATE_TOKEN="your_token_here"

# Run validation script
./scripts/test-homebrew-token.sh
```

### Test Full Workflow
1. Create a test release in the main repository
2. Monitor the GitHub Actions workflow
3. Verify PR creation in homebrew-rxiv-maker
4. Test the updated formula

## 🔧 Troubleshooting

### Common Issues

**Token Permission Errors:**
- Verify token has correct repository access
- Check that permissions include Contents (write) and Pull requests (write)
- Ensure token hasn't expired

**SHA256 Calculation Fails:**
- Check if release tarball is publicly accessible
- Verify GitHub release was published successfully
- Look for network issues in Actions logs

**PR Creation Fails:**
- Ensure homebrew-rxiv-maker repository exists and is accessible
- Check if a branch with the same name already exists
- Verify GitHub CLI authentication in workflow

### Workflow Logs

Check the Actions tab in the main rxiv-maker repository:
- Navigate to: `https://github.com/HenriquesLab/rxiv-maker/actions`
- Look for "Auto-update Homebrew Formula" workflow runs
- Review individual step logs for detailed error messages

## 🔄 Maintenance

### Token Rotation
1. Create new fine-grained token with same permissions
2. Update `HOMEBREW_UPDATE_TOKEN` secret in repository settings  
3. Test with next release
4. Revoke old token

### Workflow Updates
- Keep workflow file in sync with formula structure changes
- Update token permissions if new features require additional access
- Monitor for GitHub API changes that might affect automation

## 📞 Support

If you encounter issues with the automation:

1. **Check Logs**: Review GitHub Actions workflow logs
2. **Verify Token**: Use test script to validate token permissions
3. **Manual Fallback**: Update formula manually if automation fails
4. **Report Issues**: Create issue in main rxiv-maker repository with logs

The automation is designed to fail gracefully - if it doesn't work, the release process continues normally and the formula can be updated manually.