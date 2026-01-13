# TODO Prevention Policy

## Overview

RPM-EE enforces a **no-TODO policy** in committed code. All TODOs, FIXMEs, and similar markers must be converted to GitHub issues before committing.

## Rationale

TODOs in code:
- ❌ Get lost and forgotten
- ❌ Lack context and priority
- ❌ Don't have assignees or deadlines
- ❌ Can't be tracked or measured
- ❌ Clutter the codebase

GitHub issues:
- ✅ Tracked and visible
- ✅ Can be assigned and prioritized
- ✅ Support discussion and context
- ✅ Link to specific code locations
- ✅ Generate project metrics

## Blocked Patterns

The following comment patterns are **blocked** by pre-commit hooks:

```python
# TODO: This will fail
# FIXME: This will fail
# XXX: This will fail
# HACK: This will fail
# OPTIMIZE: This will fail
# REVIEW: This will fail
# REFACTOR: This will fail
# DEPRECATED: This will fail
# BUG: This will fail
# PERF: This will fail
```

## What to Do Instead

### ✅ Create a GitHub Issue

Instead of:
```python
def process_data(data):
    # TODO: Add input validation
    # FIXME: Handle edge case for empty data
    return transform(data)
```

Do this:
```python
def process_data(data):
    # See issue #123: Input validation needed
    # See issue #124: Handle empty data edge case
    return transform(data)
```

Then create issues:
- **Issue #123**: "Add input validation to process_data()"
- **Issue #124**: "Handle empty data edge case in process_data()"

### Creating Good Issues

```markdown
**Title:** Add input validation to process_data()

**Description:**
The `process_data()` function in `src/data_processor.py` needs input 
validation to handle:
- None values
- Empty lists
- Invalid data types

**Location:** `src/data_processor.py:42`
**Priority:** Medium
**Labels:** enhancement, data-processing
```

## Exceptions

### Allowed: Issue References

```python
# Issue #456: This is allowed
# Related to #789: Also allowed
# Blocked by #101: Allowed
```

### Allowed: Non-Action Comments

```python
# Note: This function is performance-critical
# Warning: Do not modify without benchmarking
# Important: Maintains compatibility with v1.0
```

### Temporary Bypass (Emergency Only)

If you **must** commit a TODO (emergency situations only):

```bash
# Skip the TODO check
SKIP=check-no-todos,ruff git commit -m "Emergency fix"
```

**⚠️ WARNING:** This should only be used in emergencies. The TODO must be converted to an issue immediately after.

## How It Works

### Two-Layer Detection

1. **Ruff (FIX rules)**
   - Detects: `TODO`, `FIXME`, `XXX`, `HACK`, `NOTE`
   - Fast, built-in
   - Part of regular linting

2. **Custom Grep Hook**
   - Detects: All patterns listed above
   - Backup to Ruff
   - More explicit error message

### Error Message

When you try to commit a TODO:

```
check-no-todos (prevent TODO/FIXME)..................Failed
❌ Found TODO/FIXME comments. Please create an issue instead.

src/presets.py:45:    # TODO: Add more presets
```

## Workflow Example

### Before Committing

1. **Write code with TODO**
   ```python
   def new_feature():
       # TODO: Implement caching
       return compute_expensive_operation()
   ```

2. **Create GitHub issue**
   - Go to GitHub → Issues → New Issue
   - Title: "Implement caching in new_feature()"
   - Description: Details about the caching strategy needed
   - Get issue number (e.g., #567)

3. **Replace TODO with issue reference**
   ```python
   def new_feature():
       # Issue #567: Implement caching
       return compute_expensive_operation()
   ```

4. **Commit successfully**
   ```bash
   git add src/feature.py
   git commit -m "Add new_feature (caching in #567)"
   ```

## Benefits

✅ **Trackable** - All improvements tracked in GitHub  
✅ **Prioritizable** - Issues can be labeled and prioritized  
✅ **Assignable** - Issues can be assigned to team members  
✅ **Discussable** - Issues support threaded discussions  
✅ **Measurable** - Project progress visible in issue metrics  
✅ **Linkable** - Issues link to PRs, commits, and code  

## Configuration

### Ruff Configuration

In `pyproject.toml`:
```toml
[tool.ruff.lint]
select = [
    "FIX",  # flake8-fixme (TODO, FIXME, XXX, HACK, NOTE)
    # ... other rules
]
```

### Pre-commit Hook

In `.pre-commit-config.yaml`:
```yaml
- id: check-no-todos
  name: check-no-todos (prevent TODO/FIXME)
  entry: bash -c 'if grep -rn --include="*.py" -E "(TODO|FIXME|XXX|HACK|...):" .; then echo "❌ Found TODO/FIXME comments. Please create an issue instead."; exit 1; fi'
  language: system
  types: [python]
```

## Testing

Test the TODO detection:

```bash
# Create test file with TODO
echo '# TODO: test' > /tmp/test_todo.py

# Run ruff check
ruff check --select FIX /tmp/test_todo.py

# Should output:
# FIX002 Line contains TODO, consider resolving the issue
```

## FAQs

**Q: What if I need to track something quickly?**  
A: Create a quick issue with minimal details. You can add more context later.

**Q: What about private notes to myself?**  
A: Use issue draft or personal notes outside the codebase.

**Q: What if the TODO is in documentation?**  
A: Same rule - create an issue for documentation improvements.

**Q: Can I use TODO in comments that aren't action items?**  
A: Yes, but only if not followed by a colon. `TODO` without `:` might pass, but better to use `Note:` or `See issue #N:` instead.

**Q: What about FIXME vs TODO?**  
A: Both are blocked. Use issues for both improvements and fixes.

## Alternative Approaches (If Needed)

If the no-TODO policy is too strict for your workflow, you can:

1. **Disable for specific files**
   ```toml
   # In pyproject.toml
   [tool.ruff.lint.per-file-ignores]
   "scripts/experimental.py" = ["FIX"]
   ```

2. **Use inline ignores (not recommended)**
   ```python
   # TODO: temporary  # noqa: FIX002
   ```

3. **Remove the hook entirely**
   ```bash
   # Comment out in .pre-commit-config.yaml
   # - id: check-no-todos
   ```

## Summary

🚫 **No TODOs in committed code**  
✅ **Create GitHub issues instead**  
📋 **Reference issues in comments**  
🔍 **Enforced by pre-commit hooks**  
⚠️ **Bypass only in emergencies**  

---

**Policy Effective:** January 13, 2026  
**Version:** v1.1  
**Enforcement:** Automated via pre-commit hooks
