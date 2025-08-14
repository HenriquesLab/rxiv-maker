# 📝 RXIV-MAKER TASK TRACKER

**Last Updated**: 2025-08-14  
**Format Version**: 2.0 (Multi-Agent Coordination)  
**Active Sprint**: Pre-Merge Quality Gates  
**Current Branch**: dev (49 files modified)

---

## 🚨 CRITICAL - Immediate Action Required

### RXIV-001: Stage and commit modified files
- **Status**: ready
- **Priority**: critical
- **Category**: version_control
- **Estimated**: 10 minutes
- **Description**: Stage and commit 55 modified files currently in git status
- **Acceptance Criteria**:
  - All modified files reviewed for quality
  - Meaningful commit message created
  - No sensitive data accidentally included
- **Command**: `git add -A && git commit -m "feat: major dev branch consolidation"`

### RXIV-002: Run full test suite
- **Status**: ready
- **Priority**: critical
- **Category**: testing
- **Estimated**: 10 minutes
- **Dependencies**: [RXIV-001]
- **Description**: Execute complete test suite with coverage check
- **Acceptance Criteria**:
  - All tests pass
  - Coverage >= 85% (enforced minimum)
  - No new test failures introduced
- **Command**: `nox -s "test(test_type='full')"`

### RXIV-003: Update version number
- **Status**: ready
- **Priority**: critical
- **Category**: release_prep
- **Estimated**: 2 minutes
- **Dependencies**: [RXIV-002]
- **Location**: pyproject.toml
- **Description**: Increment version for new release
- **Current Version**: 1.5.1
- **Target Version**: 1.5.2 or 1.6.0 (depending on changes)

### RXIV-004: Create comprehensive PR
- **Status**: blocked
- **Priority**: critical
- **Category**: release_prep
- **Blocked By**: [RXIV-001, RXIV-002, RXIV-003]
- **Estimated**: 30 minutes
- **Description**: Create PR documenting all dev branch changes
- **Key Changes to Document**:
  - Engine architecture refactoring
  - Docker/Podman workflow consolidation (9 → 3 workflows)
  - Container engine abstraction improvements
  - Test coverage improvements (126+ new tests)
  - Security enhancements
  - Dependency updates

---

## 🔥 HIGH PRIORITY - Bug Fixes

### RXIV-005: Fix silent exception handlers
- **Status**: ready
- **Priority**: high
- **Category**: bug_fix
- **Estimated**: 2 hours
- **Description**: Add proper logging to 15+ empty exception handlers
- **Locations**:
  ```
  generate_figures.py:160 - Cache update failure
  cache_management.py:235 - ValueError/TypeError
  engines/factory.py:128 - Engine detection failure
  docker/manager.py:262,570,838,898 - Multiple failures
  security/scanner.py:691 - Exception ignored
  ```
- **Acceptance Criteria**:
  - All empty `pass` statements replaced with logging
  - Error context preserved for debugging
  - No silent failures in production

### RXIV-006: Fix skipped tests
- **Status**: ready
- **Priority**: high
- **Category**: testing
- **Estimated**: 3 hours
- **Description**: Enable or fix 17 currently skipped tests
- **Test Categories**:
  - DOI validator tests (test_doi_validator.py)
  - Container engine tests (test_container_engines.py)
  - Cross-platform tests (test_cross_platform_optimizations.py)
  - Package manager tests (test_package_managers.py)
- **Acceptance Criteria**:
  - All tests either fixed or removed with justification
  - No reduction in overall coverage
  - Clear documentation for any permanently skipped tests

### RXIV-007: Remove hardcoded DEBUG references
- **Status**: ready
- **Priority**: medium
- **Category**: code_quality
- **Estimated**: 1 hour
- **Description**: Replace hardcoded DEBUG with proper log levels
- **Locations**:
  ```
  validate_manuscript.py:581
  fix_bibliography.py:581
  pdf_validator.py:477
  logging_config.py:74,86,221
  ```
- **Acceptance Criteria**:
  - All hardcoded DEBUG replaced with configurable levels
  - Logging configuration centralized
  - Debug mode controllable via environment variable

---

## 🎯 HIGH PRIORITY - Test Coverage

### RXIV-008: Improve build_manager.py coverage
- **Status**: ready
- **Priority**: high
- **Category**: test_coverage
- **Current Coverage**: 27%
- **Target Coverage**: 90%
- **Estimated**: 3 hours
- **Location**: src/rxiv_maker/engine/build_manager.py
- **Acceptance Criteria**:
  - Comprehensive unit tests for all public methods
  - Mock external dependencies
  - Test both success and failure paths

### RXIV-009: Improve platform.py coverage
- **Status**: ready
- **Priority**: high
- **Category**: test_coverage
- **Current Coverage**: 24%
- **Target Coverage**: 90%
- **Estimated**: 2 hours
- **Location**: src/rxiv_maker/utils/platform.py
- **Acceptance Criteria**:
  - Cross-platform tests (Windows/Unix)
  - Mock subprocess calls
  - Test error handling

### RXIV-010: Improve file_helpers.py coverage
- **Status**: ready
- **Priority**: high
- **Category**: test_coverage
- **Current Coverage**: 20%
- **Target Coverage**: 90%
- **Estimated**: 2 hours
- **Location**: src/rxiv_maker/utils/file_helpers.py

---

## 🚧 IN PROGRESS - Active Development

### RXIV-011: Fix container-engines.yml workflow
- **Status**: in_progress
- **Priority**: medium
- **Category**: ci_cd
- **Description**: Restore full test matrix for container engines
- **Current Issue**: Workflow reduced, needs full Docker + Podman matrix
- **Location**: .github/workflows/container-engines.yml

### RXIV-012: Complete Podman documentation
- **Status**: in_progress
- **Priority**: medium
- **Category**: documentation
- **Dependencies**: [RXIV-011]
- **Description**: Document Podman as Docker alternative
- **Deliverables**:
  - User guide for Podman setup
  - Migration guide from Docker
  - Troubleshooting section

---

## ⏸️ BLOCKED - Waiting on Dependencies

### RXIV-013: Test Homebrew automation
- **Status**: blocked
- **Priority**: medium
- **Category**: release_automation
- **Blocked By**: Next release event
- **Description**: Verify automated formula updates work correctly
- **Location**: .github/workflows/homebrew-auto-update.yml

### RXIV-014: Remove deprecated workflows
- **Status**: blocked
- **Priority**: low
- **Category**: cleanup
- **Blocked By**: 30-day stability period
- **Description**: Delete workflows in .github/workflows/deprecated/
- **Target Date**: 2025-02-14

---

## 📋 BACKLOG - Future Enhancements

### RXIV-015: Implement inline code execution
- **Status**: ready
- **Priority**: low
- **Category**: feature
- **Description**: Execute Python/R code in manuscripts
- **Epic**: Advanced manuscript features
- **Subtasks**:
  - Design markdown syntax for code blocks
  - Create secure execution engine
  - Implement sandboxing with containers
  - Add Python runner
  - Add R runner

### RXIV-016: Create APT repository
- **Status**: ready
- **Priority**: low
- **Category**: distribution
- **Description**: Official APT repository for Debian/Ubuntu
- **Subtasks**:
  - Create debian/ packaging files
  - Implement .deb build process
  - Set up GPG signing
  - Create publish-apt.yml workflow
  - Host on apt-repo branch

### RXIV-017: Podman Colab notebook
- **Status**: ready
- **Priority**: low
- **Category**: feature
- **Description**: Create Podman-based Google Colab notebook
- **Dependencies**: Playwright automation for testing

---

## ✅ COMPLETED - Last 7 Days

### RXIV-C001: CI Coverage Enforcement ✅
- **Completed**: 2025-08-14
- **Achievement**: Added 85% minimum coverage threshold to CI
- **Files Modified**: .github/workflows/ci.yml, noxfile.py

### RXIV-C002: UV Package Manager Migration ✅
- **Completed**: 2025-08-14
- **Achievement**: Complete migration to uv for faster dependency management
- **Impact**: 3x faster dependency installation

### RXIV-C003: Security Automation ✅
- **Completed**: 2025-08-14
- **Achievement**: Integrated pip-audit, safety, and bandit in CI
- **Impact**: Every PR automatically scanned for vulnerabilities

### RXIV-C004: Documentation Generation ✅
- **Completed**: 2025-08-14
- **Achievement**: Automated API documentation with CI validation
- **Impact**: Always up-to-date documentation

### RXIV-C005: Setup Environment Coverage ✅
- **Completed**: 2025-08-14
- **Achievement**: Improved from 0% to 95% coverage
- **Tests Added**: 47 comprehensive tests
- **Impact**: Critical module now thoroughly tested

---

## 📊 METRICS & TRACKING

### Test Coverage Progress
```
Module                        Before  After   Target
─────────────────────────────────────────────────
setup_environment.py          0%      95%     ✅
security/scanner.py           N/A     90%+    ✅
security/dependency_manager   N/A     90%+    ✅
CLI modules (overall)         0%      19%     🔄
build_manager.py             27%      27%     🎯
platform.py                  24%      24%     🎯
file_helpers.py              20%      20%     🎯
DOI validators               8-15%    8-15%   🎯
─────────────────────────────────────────────
Overall Coverage             ~10%     85%+    ✅
```

### Sprint Velocity
- **Tests Added This Sprint**: 126+
- **Files Modified**: 49
- **Lines Changed**: +2,061 / -2,383 (net -322)
- **Workflows Consolidated**: 9 → 3

### Quality Gates Status
- ✅ Coverage Enforcement: Active (85% minimum)
- ✅ Security Scanning: Active (pip-audit, safety, bandit)
- ✅ Documentation Generation: Active
- ✅ UV Package Manager: Migrated
- 🔄 Test Coverage Target: In Progress (Target: 90%)

---

## 🔧 Quick Commands

```bash
# Run tests
nox -s "test(test_type='fast')"   # Quick validation (~1 min)
nox -s "test(test_type='full')"   # Complete suite (~10 min)

# Check coverage
nox -s coverage

# Security scan
nox -s security

# Generate docs
nox -s docs

# Validate before merge
nox -s "test(test_type='full')" && nox -s security && nox -s coverage
```

---

## 📝 Notes for Agents

- **Priority Order**: Always work on critical → high → medium → low
- **Blocked Tasks**: Check dependencies before starting work
- **Test Pattern**: Use test_setup_environment.py as template
- **Commit Style**: Follow conventional commits (feat:, fix:, docs:, etc.)
- **Coverage Target**: Every new code must have >90% test coverage
- **Error Handling**: Never use empty except blocks - always log
- **Documentation**: Update docs for any public API changes