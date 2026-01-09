# Migration Cleanup Rollback Procedures

## Overview

This document provides step-by-step procedures to rollback the migration cleanup changes if needed. All deleted files have been backed up and can be restored.

## Backup Locations

All deleted files are stored in the following backup directory:
```
chunkana/.backup/migration-cleanup/
```

### Backed Up Files

1. **Migration Documents:**
   - `MIGRATION_GUIDE.md` → `.backup/migration-cleanup/MIGRATION_GUIDE.md`
   - `BASELINE.md` → `.backup/migration-cleanup/BASELINE.md`

2. **Test Configuration Files:**
   - `plugin_config_keys.json` → `.backup/migration-cleanup/plugin_config_keys.json`
   - `plugin_tool_params.json` → `.backup/migration-cleanup/plugin_tool_params.json`

3. **Test Files (available in git history):**
   - `tests/test_dify_bug_fix_integration.py`
   - `tests/integration/test_dify_plugin_integration.py`
   - `tests/integration/test_dify_hierarchical_integration.py`
   - `tests/baseline/test_config_parity.py`
   - `tests/baseline/golden_dify_style/` directory

## Rollback Procedures

### Option 1: Full Rollback Using Git (Recommended)

If you need to completely undo all cleanup changes:

```bash
# 1. Check current git status
git status

# 2. Find the commit before cleanup started
git log --oneline -10

# 3. Reset to the commit before cleanup (replace COMMIT_HASH)
git reset --hard COMMIT_HASH

# 4. Verify rollback
git status
make test
```

### Option 2: Selective File Restoration

If you only need to restore specific files:

#### Restore Migration Documents

```bash
# Restore MIGRATION_GUIDE.md
cp .backup/migration-cleanup/MIGRATION_GUIDE.md ./MIGRATION_GUIDE.md

# Restore BASELINE.md
cp .backup/migration-cleanup/BASELINE.md ./BASELINE.md
```

#### Restore Test Configuration Files

```bash
# Restore plugin config files
cp .backup/migration-cleanup/plugin_config_keys.json tests/baseline/
cp .backup/migration-cleanup/plugin_tool_params.json tests/baseline/
```

#### Restore Deleted Test Files from Git

```bash
# Restore specific test files from git history
git checkout HEAD~N -- tests/test_dify_bug_fix_integration.py
git checkout HEAD~N -- tests/integration/test_dify_plugin_integration.py
git checkout HEAD~N -- tests/integration/test_dify_hierarchical_integration.py
git checkout HEAD~N -- tests/baseline/test_config_parity.py

# Restore golden_dify_style directory
git checkout HEAD~N -- tests/baseline/golden_dify_style/

# Note: Replace N with the number of commits to go back
```

### Option 3: Revert Specific Changes

If you need to revert only certain modifications:

#### Revert Documentation Changes

```bash
# Revert README.md changes
git checkout HEAD~N -- README.md

# Revert other documentation files
git checkout HEAD~N -- docs/TODO_DOCUMENTATION.md
git checkout HEAD~N -- docs/migration/parity_matrix.md
```

#### Revert Code Comment Changes

```bash
# Revert formatter changes
git checkout HEAD~N -- src/chunkana/renderers/formatters.py

# Revert test file changes
git checkout HEAD~N -- tests/baseline/test_renderer_compatibility.py
git checkout HEAD~N -- tests/baseline/test_canonical.py
```

## Verification After Rollback

After performing any rollback operation, verify the system integrity:

### 1. Check File Existence

```bash
# Verify key files exist
ls -la MIGRATION_GUIDE.md BASELINE.md
ls -la tests/baseline/plugin_config_keys.json
ls -la tests/baseline/golden_dify_style/
```

### 2. Run Tests

```bash
# Run full test suite
make test

# Or run specific test categories
make test-cov  # with coverage
```

### 3. Check Documentation Links

```bash
# Search for broken references
grep -r "MIGRATION_GUIDE.md" docs/
grep -r "BASELINE.md" docs/
```

## Rollback Validation Checklist

After rollback, ensure:

- [ ] All expected files are restored
- [ ] Tests pass without errors
- [ ] Documentation links work correctly
- [ ] No broken references remain
- [ ] Git status is clean (if using git rollback)

## Troubleshooting

### Issue: Tests Still Fail After Rollback

**Solution:**
1. Ensure all test files are restored
2. Check that baseline data files exist
3. Verify git submodules are up to date
4. Clear test cache: `rm -rf .pytest_cache/`

### Issue: Documentation Links Still Broken

**Solution:**
1. Verify all referenced files are restored
2. Check file paths are correct
3. Ensure no partial rollback occurred

### Issue: Git Conflicts During Rollback

**Solution:**
```bash
# If conflicts occur during git operations
git status
git reset --hard HEAD  # Discard local changes
# Then retry rollback procedure
```

## Emergency Contacts

If rollback procedures fail or cause issues:

1. **Check Git History:** Use `git reflog` to find previous states
2. **Backup Verification:** Ensure `.backup/migration-cleanup/` directory is intact
3. **Fresh Clone:** As last resort, clone repository from remote and apply necessary changes

## Notes

- **Backup Retention:** Keep `.backup/migration-cleanup/` directory until you're certain rollback won't be needed
- **Git History:** All changes are tracked in git, providing additional rollback options
- **Testing:** Always run full test suite after any rollback operation
- **Documentation:** Update this document if rollback procedures change

## Rollback Testing

To test rollback procedures without affecting the main codebase:

```bash
# Create test branch
git checkout -b test-rollback

# Perform rollback operations
# ... follow procedures above ...

# Verify results
make test

# If successful, apply to main branch
git checkout main
# ... repeat rollback procedures ...

# Clean up test branch
git branch -D test-rollback
```

This ensures rollback procedures work correctly before applying them to the main codebase.