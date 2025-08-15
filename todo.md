# 📝 RXIV-MAKER TODO LIST

**Last Updated**: 2025-08-14
**Current Branch**: dev

---

## ⚠️ IMMEDIATE ACTION REQUIRED

### **Before Merging to Main**:
- [ ] **Fix NotImplementedError bombs** in bibliography_cache.py (lines 387, 403, 414)
- [ ] **Stage and commit 55 modified files** currently in git status
- [ ] **Run full test suite** with coverage check: `nox -s "test(test_type='full')"`
- [ ] **Update version** in pyproject.toml
- [ ] **Create PR** with comprehensive changelog

### **Critical Technical Debt**:
- [ ] **15+ silent exception handlers** swallowing errors without logging
- [ ] **17 skipped tests** that need to be fixed or removed
- [ ] **3 placeholder functions** that will crash if called

---

## 🚧 ACTIVE DEVELOPMENT - IN PROGRESS

### 🔄 **CI/CD Pipeline Improvements**
- [ ] **Remove deprecated workflows** after confirming new ones are stable (30 days)
- [ ] **Fix container-engines.yml** - Currently reduced, needs restoration of full test matrix

### 📦 **Docker & Container Improvements**
- [ ] **Add Podman-specific optimizations** to build process
- [ ] **Document Podman usage** in user guides
- [ ] **Add container engine auto-detection** for seamless switching

### 🧪 **Testing Infrastructure**
- [ ] **Convert `test-binary.sh`** to Python-based pytest module
- [ ] **Add integration tests** for new container engine support
- [ ] **Implement smoke tests** for quick validation

### 📚 **Documentation Updates**
- [ ] **Update README.md** - Consolidate quickstart sections
- [ ] **Create Podman guide** - Document Podman as Docker alternative
- [ ] **Update installation docs** - Reflect new unified setup command
- [ ] **Add troubleshooting guide** - Common issues and solutions
- [ ] **Document new test structure** - Explain parametrized test sessions
- [ ] **Add architecture docs** - Explain refactored engine architecture
- [ ] **Create plugin development guide** - For future extensibility

---

## 🔮 FUTURE ENHANCEMENTS - PLANNED

### 🚀 **Release & Distribution**
- [ ] **Test automated PR creation** on next release
- [ ] **Migrate tap testing** to main repository
- [ ] **Deprecate manual update process** in tap repository
- [ ] **APT Repository** (Future Sprint):
    - [ ] Create `debian/` directory with packaging files
    - [ ] Implement `.deb` package build process
    - [ ] Set up GPG signing for repository
    - [ ] Create `publish-apt.yml` workflow
    - [ ] Host repository on `apt-repo` branch

### 💻 **Advanced Features**
- [ ] **Inline Code Execution**:
    - [ ] Design markdown syntax for code blocks
    - [ ] Create code execution engine
    - [ ] Implement Python code runner
    - [ ] Implement R code runner
    - [ ] Add security sandboxing
    - [ ] Create example manuscripts with dynamic content
- [ ] **Google Colab Integration**:
    - [ ] Create Podman-based Colab notebook
    - [ ] Add Playwright automation for testing
    - [ ] Document Colab-specific setup
    - [ ] Test with real manuscripts

---

## 🐛 BUGS & ISSUES TO ADDRESS

### 🔴 **High Priority Bugs**
- [ ] **NotImplementedError in bibliography_cache.py**:
    - [ ] Implement actual parsing logic (line 387)
    - [ ] Implement actual validation logic (line 403)
    - [ ] Implement actual analysis logic (line 414)

### 🟠 **Medium Priority Issues**
- [ ] **Deprecated Functions**:
    - [ ] Remove deprecated `rxiv install-deps` command redirect
    - [ ] Remove deprecated `rxiv bibliography validate` redirect
    - [ ] Clean up deprecation warnings in engine modules
- [ ] **Code Quality - Empty Exception Handlers**:
    - [ ] Fix empty `pass` in exception handlers in multiple files
    - [ ] Complete stub implementations in platform installers
    - [ ] Add proper logging for all silent exception handlers
- [ ] **Skipped Tests**:
    - [ ] Fix skipped DOI validator tests
    - [ ] Enable container engine tests
    - [ ] Fix cross-platform optimization tests
    - [ ] Enable system package manager tests

### 🟡 **Low Priority Improvements**
- [ ] **Logging Enhancements**:
    - [ ] Implement consistent `rich` logging across all modules
    - [ ] Add progress bars for long-running operations
    - [ ] Improve error message clarity
    - [ ] Remove hardcoded DEBUG references and use proper log levels
- [ ] **Performance Optimizations**:
    - [ ] Profile slow test cases and optimize
    - [ ] Implement caching for repeated operations
    - [ ] Optimize Docker build times
    - [ ] Add parallel processing for figure generation
- [ ] **Code Cleanup**:
    - [ ] Remove XXSUBNOTEPROTECTEDXX placeholder system
    - [ ] Clean up LaTeX multi-pass comments
    - [ ] Standardize error handling patterns
- [ ] **Cache Migration Follow-ups**:
    - [ ] Remove legacy cache references
    - [ ] Add cache statistics reporting
    - [ ] Implement cache pruning strategy
    - [ ] Add cache integrity checks
