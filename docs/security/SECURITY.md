# Security Documentation for Rxiv-Maker

## Overview

This document outlines the security measures, best practices, and vulnerability mitigation strategies implemented in rxiv-maker to protect against common security threats.

## Security Architecture

### Defense in Depth

Rxiv-maker implements multiple layers of security controls:

1. **Input Validation** - All user inputs are validated and sanitized
2. **Path Security** - Comprehensive path traversal prevention
3. **Access Control** - Strict permission validation
4. **Monitoring** - Real-time security event monitoring
5. **Integrity Checking** - File and data integrity verification

## Vulnerability Protections

### 1. Path Traversal Prevention

**Threat**: Attackers attempting to access files outside intended directories using `../` or similar patterns.

**Mitigations**:
- Path component validation rejecting dangerous patterns
- Absolute path resolution and validation
- Base directory containment enforcement
- Symlink attack prevention

```python
# Example of secure path handling
from rxiv_maker.utils.secure_cache_utils import get_secure_cache_dir

# This will raise SecurityError if path contains traversal attempts
cache_dir = get_secure_cache_dir("safe_subfolder")  # ✓ Safe
cache_dir = get_secure_cache_dir("../etc/passwd")  # ✗ Blocked
```

### 2. TOCTOU Race Condition Prevention

**Threat**: Time-of-check-time-of-use vulnerabilities where file state changes between validation and use.

**Mitigations**:
- Atomic file operations using temporary files and rename
- File locking where supported
- Checksum verification after operations
- Transaction-like patterns for multi-step operations

### 3. Symlink Attack Protection

**Threat**: Malicious symlinks redirecting operations to unintended targets.

**Mitigations**:
- Symlink detection and validation
- Refusing to follow symlinks during migration
- Real path resolution and validation
- Symlink target containment checks

### 4. Disk Space Exhaustion Prevention

**Threat**: Denial of service through filling disk space.

**Mitigations**:
- File size limits (MAX_FILE_SIZE_MB = 100MB)
- Cache size limits (MAX_CACHE_SIZE_MB = 1000MB)
- Pre-operation disk space checks
- Quota enforcement

### 5. Input Validation & Sanitization

**Threat**: Injection attacks through malicious input.

**Mitigations**:
- Comprehensive input validation
- Special character filtering
- Command injection prevention
- URL validation for external resources

## Security Monitoring

### Real-time Monitoring

The security monitoring system tracks:
- Path traversal attempts
- Symlink attacks
- Permission violations
- Disk exhaustion attempts
- Suspicious patterns
- Rate limit violations

### Security Events

Events are classified by severity:
- **CRITICAL**: Immediate action required
- **HIGH**: Potential security breach
- **MEDIUM**: Security concern
- **LOW**: Informational
- **INFO**: Audit trail

### Alerting

Critical and high-severity events trigger immediate alerts through:
- Application logs
- Security log files
- Console warnings
- Optional webhook notifications

## Best Practices for Users

### 1. File Permissions

Ensure proper permissions on sensitive directories:
```bash
# Cache directory should not be world-writable
chmod 755 ~/.cache/rxiv-maker
```

### 2. Regular Updates

Keep rxiv-maker updated to receive security patches:
```bash
pip install --upgrade rxiv-maker
```

### 3. Monitoring Logs

Regularly review security logs:
```bash
# Check security events
cat ~/.rxiv-maker/security/security_*.log | jq '.'
```

### 4. Validate External Content

When using external resources:
- Only use trusted DOI providers
- Verify HTTPS connections
- Check file integrity after downloads

## Security Configuration

### Environment Variables

```bash
# Set maximum cache size (MB)
export RXIV_MAX_CACHE_SIZE=500

# Set security log directory
export RXIV_SECURITY_LOG_DIR=/var/log/rxiv-maker

# Enable verbose security logging
export RXIV_SECURITY_VERBOSE=1
```

### Configuration File

```yaml
# .rxiv.yml
security:
  max_file_size_mb: 50
  max_cache_size_mb: 500
  enable_monitoring: true
  alert_threshold: HIGH
  blocked_patterns:
    - "../../etc"
    - "/etc/passwd"
  allowed_domains:
    - doi.org
    - crossref.org
    - arxiv.org
```

## Incident Response

### If You Detect a Security Issue

1. **Stop the operation** immediately
2. **Review security logs** for details
3. **Check file integrity** of important files
4. **Report the issue** to the maintainers
5. **Clean affected cache** if necessary

### Reporting Security Vulnerabilities

Please report security vulnerabilities responsibly:

1. **DO NOT** create public GitHub issues for security vulnerabilities
2. Email security concerns to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)

## Security Audit Checklist

Regular security audits should verify:

- [ ] Path traversal protections are active
- [ ] Symlink validation is working
- [ ] File size limits are enforced
- [ ] Cache size limits are respected
- [ ] Permissions are correctly set
- [ ] Security monitoring is active
- [ ] Logs are being generated
- [ ] No sensitive data in logs
- [ ] Dependencies are up to date
- [ ] No known vulnerabilities in dependencies

## Compliance

Rxiv-maker's security measures help with compliance for:

- **OWASP Top 10** - Protection against common web vulnerabilities
- **CWE Top 25** - Mitigation of dangerous software weaknesses
- **GDPR** - Data protection through secure handling
- **Academic Standards** - Maintaining research data integrity

## Security Tools Integration

### Static Analysis

Run security analysis with:
```bash
# Bandit for Python security issues
bandit -r src/

# Safety for dependency vulnerabilities
safety check

# Semgrep for pattern-based analysis
semgrep --config=auto src/
```

### Runtime Monitoring

```python
from rxiv_maker.security.monitor import get_security_monitor

# Get security report
monitor = get_security_monitor()
report = monitor.get_security_report()
print(f"Total security events: {report['summary']['total_events']}")
print(f"Blocked attempts: {report['summary']['blocked_attempts']}")
```

## Updates and Patches

Security updates are released as:
- **Critical**: Immediate patch releases (x.x.1)
- **High**: Next minor release (x.1.0)
- **Medium/Low**: Next major release (1.0.0)

Subscribe to security advisories:
- GitHub repository watch for releases
- PyPI release notifications
- Security mailing list (if available)

## Contact

For security concerns, contact:
- Email: [security contact]
- GPG Key: [if available]

## Acknowledgments

We thank the security researchers and users who have helped improve rxiv-maker's security through responsible disclosure and feedback.