# Workflow Templates for rxiv-maker

This directory contains reusable workflow templates for coordinating actions across the rxiv-maker ecosystem.

## Available Templates

### 1. Submodule Sync Template (`submodule-sync.yml`)

**Purpose**: Synchronize submodules with changes from the main repository.

**Usage**: Copy this template to submodule repositories and customize as needed.

**Triggers**:
- `repository_dispatch` with type `sync-submodule`
- Manual workflow dispatch

**Key Features**:
- Automatic merging of main repository changes
- Validation of submodule state after sync
- Conditional downstream build triggers
- Comprehensive logging and status reporting

**Example Integration**:
```yaml
# In main repository workflow
- name: Trigger submodule sync
  run: |
    curl -X POST \
      -H "Authorization: token ${{ secrets.SYNC_TOKEN }}" \
      https://api.github.com/repos/org/submodule-repo/dispatches \
      -d '{
        "event_type": "sync-submodule",
        "client_payload": {
          "source_repo": "${{ github.repository }}",
          "source_commit": "${{ github.sha }}",
          "sync_type": "version_change",
          "version": "1.2.3"
        }
      }'
```

### 2. Cross-Repository Coordination Template (`cross-repo-coordination.yml`)

**Purpose**: Coordinate workflows across multiple repositories in the ecosystem.

**Usage**: Use as a reusable workflow in the main repository.

**Key Features**:
- Multi-repository dispatch coordination
- Enhanced payload with metadata
- Success/failure tracking across repositories
- Configurable completion waiting
- Detailed reporting and artifact storage

**Example Usage**:
```yaml
# In main repository workflow
jobs:
  coordinate-ecosystem:
    uses: ./.github/workflow-templates/cross-repo-coordination.yml
    with:
      target_repos: "org/docker-rxiv-maker,org/homebrew-rxiv-maker,org/scoop-rxiv-maker"
      action_type: "version-update"
      payload: '{"version": "1.2.3", "release_type": "minor"}'
      wait_for_completion: false
    secrets:
      COORDINATION_TOKEN: ${{ secrets.ECOSYSTEM_SYNC_TOKEN }}
```

## Best Practices

### Security Considerations

1. **Use Dedicated Tokens**: Create dedicated GitHub tokens with minimal required permissions for cross-repository coordination.

2. **Token Scoping**: 
   - `SYNC_TOKEN`: For submodule synchronization (needs `repo` scope for target repositories)
   - `COORDINATION_TOKEN`: For cross-repository coordination (needs `repo` scope for target repositories)

3. **Payload Validation**: Always validate payloads before processing to prevent injection attacks.

### Error Handling

1. **Graceful Degradation**: Workflows should continue even if some cross-repository actions fail.

2. **Retry Logic**: Implement retry logic for network-dependent operations.

3. **Comprehensive Logging**: Include detailed logging for debugging coordination issues.

### Performance Optimization

1. **Batching**: Group related operations when possible to reduce API calls.

2. **Parallel Execution**: Use parallel jobs for independent operations.

3. **Caching**: Cache dependencies and artifacts where appropriate.

## Customization Guidelines

### For Submodule Repositories

1. Copy `submodule-sync.yml` to `.github/workflows/` in the submodule repository.

2. Customize the validation section for repository-specific requirements:
```yaml
- name: Validate submodule state
  run: |
    # Add repository-specific validation logic
    if [ -f "custom-validation.sh" ]; then
      ./custom-validation.sh
    fi
```

3. Configure downstream triggers based on submodule purpose:
```yaml
- name: Trigger downstream builds
  run: |
    if [ "${{ steps.sync-info.outputs.sync_type }}" = "version_change" ]; then
      # Trigger Docker builds, package updates, etc.
      gh workflow run build-image.yml
    fi
```

### For Main Repository Integration

1. Add coordination calls to existing workflows:
```yaml
- name: Coordinate ecosystem updates
  uses: ./.github/workflow-templates/cross-repo-coordination.yml
  with:
    target_repos: ${{ env.ECOSYSTEM_REPOS }}
    action_type: ${{ github.event_name }}
    payload: ${{ toJson(github.event) }}
```

2. Set up environment variables for repository lists:
```yaml
env:
  ECOSYSTEM_REPOS: "org/docker-rxiv-maker,org/homebrew-rxiv-maker"
```

## Monitoring and Debugging

### Workflow Status Monitoring

1. **GitHub Actions Dashboard**: Monitor workflow status across all repositories.

2. **Custom Dashboards**: Create custom monitoring for ecosystem-wide status.

3. **Notification Integration**: Set up notifications for coordination failures.

### Common Issues

1. **Token Permissions**: Ensure tokens have appropriate scopes for target repositories.

2. **Repository Dispatch Limits**: Be aware of GitHub API rate limits for repository dispatches.

3. **Payload Size Limits**: Keep payloads under GitHub's size limits (256KB for repository_dispatch).

4. **Network Timeouts**: Implement appropriate timeouts for API calls.

## Migration Guide

### From Individual Workflows

1. **Identify Common Patterns**: Look for repeated coordination logic across workflows.

2. **Extract to Templates**: Move common patterns to reusable templates.

3. **Update Existing Workflows**: Replace inline coordination with template calls.

4. **Test Coordination**: Thoroughly test cross-repository coordination before production use.

### Version Compatibility

- Templates are designed to work with GitHub Actions runner versions 2.0+
- Uses stable action versions (e.g., `actions/checkout@v4`)
- Compatible with both public and private repositories

## Support

For issues with workflow templates:

1. Check the workflow logs for detailed error messages
2. Verify token permissions and scopes
3. Ensure target repositories have appropriate workflows configured
4. Review GitHub Actions documentation for API limits and restrictions

---

**Note**: These templates are part of the rxiv-maker ecosystem workflow refactoring initiative aimed at reducing redundancy and improving maintainability across repositories.