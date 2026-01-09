# Plugin-Specific Code Refactoring Roadmap

## Overview

This document provides a step-by-step plan for removing the remaining plugin-specific code from the chunkana library. The primary target is the `render_dify_style()` function, which is the last remnant of plugin-specific naming in the codebase.

## Current State Analysis

### Plugin-Specific Code Inventory

**Function: `render_dify_style()`**
- **Location**: `src/chunkana/renderers/formatters.py` (lines 37-85)
- **Size**: 49 lines
- **Complexity**: Medium
- **Dependencies**: 
  - `chunkana.types.Chunk`
  - Standard library only
- **Usage Locations**:
  - `src/chunkana/__init__.py` (export)
  - `tests/unit/test_renderers.py` (tests)
  - `tests/property/test_renderers.py` (property tests)
  - `tests/baseline/test_renderer_compatibility.py` (baseline tests)

## Refactoring Strategy

### Phase 1: Function Renaming (Priority: High)

**Objective**: Rename `render_dify_style()` to a generic name that reflects its actual functionality.

**Proposed New Name**: `render_with_metadata()`
- Accurately describes the function's behavior
- Generic and plugin-agnostic
- Maintains semantic clarity

**Effort Estimate**: 2-3 hours
**Risk Level**: Low
**Breaking Change**: Yes (requires version bump)

### Phase 2: Backward Compatibility (Priority: High)

**Objective**: Maintain backward compatibility during transition period.

**Implementation**:
```python
# In src/chunkana/renderers/formatters.py
def render_with_metadata(chunks: list[Chunk]) -> list[str]:
    """Render chunks with embedded metadata for enhanced retrieval."""
    # Current implementation

# Deprecated alias for backward compatibility
def render_dify_style(chunks: list[Chunk]) -> list[str]:
    """
    Deprecated: Use render_with_metadata() instead.
    
    This function will be removed in v3.0.0.
    """
    import warnings
    warnings.warn(
        "render_dify_style() is deprecated. Use render_with_metadata() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return render_with_metadata(chunks)
```

**Effort Estimate**: 1 hour
**Risk Level**: Very Low

### Phase 3: Export Updates (Priority: High)

**Objective**: Update public exports to use new function name.

**Files to Update**:
- `src/chunkana/__init__.py`

**Implementation**:
```python
# Update exports
from .renderers.formatters import (
    render_with_metadata,
    render_dify_style,  # Keep for backward compatibility
    # ... other exports
)

# Update __all__ list
__all__ = [
    "render_with_metadata",
    "render_dify_style",  # Deprecated
    # ... other exports
]
```

**Effort Estimate**: 30 minutes
**Risk Level**: Low

### Phase 4: Test Updates (Priority: Medium)

**Objective**: Update all tests to use new function name.

**Files to Update**:
- `tests/unit/test_renderers.py`
- `tests/property/test_renderers.py`
- `tests/baseline/test_renderer_compatibility.py`

**Strategy**:
1. Update import statements
2. Update function calls
3. Update test names and docstrings
4. Add deprecation warning tests

**Effort Estimate**: 1-2 hours
**Risk Level**: Low

### Phase 5: Documentation Updates (Priority: Medium)

**Objective**: Update all documentation to reference new function name.

**Files to Update**:
- `README.md`
- `docs/api/parameter-mapping.md`
- `docs/api/compatibility.md`
- `docs/examples/advanced-usage.md`
- Any other documentation files

**Effort Estimate**: 1 hour
**Risk Level**: Very Low

### Phase 6: Deprecation Removal (Priority: Low)

**Objective**: Remove deprecated function in next major version.

**Timeline**: Next major version release (v3.0.0)
**Implementation**:
- Remove `render_dify_style()` function
- Remove from exports
- Update changelog with breaking change notice

**Effort Estimate**: 30 minutes
**Risk Level**: Medium (breaking change)

## Implementation Timeline

### Immediate (v2.x.x patch release)
- [ ] Phase 1: Function Renaming
- [ ] Phase 2: Backward Compatibility
- [ ] Phase 3: Export Updates

### Short-term (v2.x.x minor release)
- [ ] Phase 4: Test Updates
- [ ] Phase 5: Documentation Updates

### Long-term (v3.0.0 major release)
- [ ] Phase 6: Deprecation Removal

## Risk Mitigation

### Testing Strategy
1. **Unit Tests**: Verify both old and new function names work identically
2. **Integration Tests**: Ensure no breaking changes in public API
3. **Deprecation Tests**: Verify warning messages are displayed correctly
4. **Backward Compatibility Tests**: Ensure existing code continues to work

### Rollback Plan
1. **Git Tags**: Tag each phase for easy rollback
2. **Feature Flags**: Use feature flags for gradual rollout if needed
3. **Documentation**: Maintain clear rollback procedures

### Communication Plan
1. **Changelog**: Document all changes with clear migration instructions
2. **Deprecation Notices**: Provide clear timeline for removal
3. **Migration Guide**: Create simple migration guide for users

## Success Criteria

### Phase Completion Criteria
- [ ] All tests pass with new function name
- [ ] Backward compatibility maintained
- [ ] No breaking changes in patch/minor releases
- [ ] Clear deprecation warnings displayed
- [ ] Documentation updated and consistent

### Final Success Criteria
- [ ] Zero plugin-specific naming in codebase
- [ ] All functionality preserved
- [ ] Clean, generic API surface
- [ ] Comprehensive test coverage maintained
- [ ] Clear migration path for users

## Effort Summary

| Phase | Effort | Risk | Priority |
|-------|--------|------|----------|
| 1. Function Renaming | 2-3 hours | Low | High |
| 2. Backward Compatibility | 1 hour | Very Low | High |
| 3. Export Updates | 30 min | Low | High |
| 4. Test Updates | 1-2 hours | Low | Medium |
| 5. Documentation Updates | 1 hour | Very Low | Medium |
| 6. Deprecation Removal | 30 min | Medium | Low |

**Total Effort**: 6-8 hours
**Total Timeline**: 2-3 releases over 3-6 months

## Conclusion

This refactoring roadmap provides a safe, incremental approach to removing the last plugin-specific code from chunkana. The strategy prioritizes backward compatibility and minimizes risk while achieving the goal of a completely generic, plugin-agnostic codebase.

The phased approach allows for careful testing and validation at each step, ensuring that the library maintains its functionality while improving its API design and reducing cognitive overhead for future contributors.