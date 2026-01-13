# Pre-commit Hooks Setup Guide

This document explains how to set up and use the pre-commit hooks for RPM-EE.

## Prerequisites

- Python 3.10 or higher
- Git

## Installation

### 1. Install pre-commit

```bash
pip install pre-commit
```

### 2. Install the git hook scripts

```bash
cd /path/to/RPM-EE
pre-commit install
```

This will install the pre-commit hook into `.git/hooks/pre-commit`.

### 3. Install required tools

The pre-commit hooks will automatically install the necessary tools when first run, but you can also install them manually:

```bash
pip install black isort ruff mypy bandit pydocstyle pytest detect-secrets pyyaml
```

For non-Python tools (optional):

```bash
# Markdown linting
npm install -g markdownlint-cli

# YAML linting (if pip install doesn't include it)
pip install yamllint
```

## Usage

### Automatic (On Commit)

Pre-commit hooks run automatically when you `git commit`:

```bash
git add .
git commit -m "Your commit message"
# Hooks will run automatically
```

If any hook fails:
1. The commit will be blocked
2. Some hooks may auto-fix issues (e.g., black, isort)
3. Review changes with `git diff`
4. Re-add fixed files: `git add .`
5. Try committing again

### Manual (Run on All Files)

Run all hooks manually on all files:

```bash
pre-commit run --all-files
```

Run specific hook:

```bash
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

### Skip Hooks (Use Sparingly)

If you need to skip hooks (NOT recommended):

```bash
git commit --no-verify -m "Emergency commit"
```

## What Gets Checked

### 1. Code Formatting (Auto-fix)
- ✅ **Black** - Python code formatting
- ✅ **isort** - Import statement sorting
- ✅ **Ruff format** - Additional formatting

### 2. Code Quality (Linting)
- ✅ **Ruff** - Fast Python linter
- ✅ **Mypy** - Type checking
- ✅ **Pydocstyle** - Docstring style checking

### 3. Security
- ✅ **detect-secrets** - Prevent committing secrets
- ✅ **Bandit** - Security vulnerability scanning

### 4. File Validation
- ✅ **YAML** - Syntax and style validation
- ✅ **JSON** - Syntax validation
- ✅ **Markdown** - Linting and formatting

### 5. General Checks
- ✅ Large files (>5MB)
- ✅ Merge conflicts
- ✅ Trailing whitespace
- ✅ Line endings (LF)
- ✅ Python syntax errors
- ✅ Debug statements (pdb, etc.)

### 6. RPM-EE Specific
- ✅ Clinical presets validation
- ✅ Experiment config validation
- ✅ Documentation reference checking

## Hook Execution Order

Hooks run in this order (fast → slow):

1. **Fast checks** (syntax, file checks)
2. **Formatters** (black, isort, ruff-format)
3. **Linters** (ruff, mypy)
4. **Security** (detect-secrets, bandit)
5. **Project-specific** (preset validation, config checks)
6. **Tests** (optional, disabled by default)

## Configuration Files

- **`.pre-commit-config.yaml`** - Main pre-commit configuration
- **`pyproject.toml`** - Python tool configuration (black, ruff, mypy, pytest)
- **`.yamllint.yaml`** - YAML linting rules
- **`.markdownlint.json`** - Markdown linting rules
- **`.secrets.baseline`** - detect-secrets baseline

## Customization

### Disable Specific Hooks

Edit `.pre-commit-config.yaml` and comment out unwanted hooks:

```yaml
# - repo: https://github.com/psf/black
#   rev: 23.12.1
#   hooks:
#     - id: black
```

### Adjust Tool Settings

Edit `pyproject.toml` to customize tool behavior:

```toml
[tool.black]
line-length = 120  # Change from 100

[tool.ruff]
ignore = ["E501"]  # Add more rules to ignore
```

### Skip Hooks for Specific Files

Add patterns to exclude in `.pre-commit-config.yaml`:

```yaml
exclude: |
  (?x)^(
    .*\.pyc$|
    my_special_file\.py
  )$
```

## Troubleshooting

### Hook Installation Failed

```bash
# Reinstall pre-commit
pre-commit clean
pre-commit install
```

### Hook Takes Too Long

```bash
# Skip slow hooks temporarily
SKIP=mypy,pytest git commit -m "message"
```

### Update Hooks to Latest Versions

```bash
pre-commit autoupdate
```

### Clear Hook Cache

```bash
pre-commit clean
```

### Test Specific Hook

```bash
pre-commit try-repo . <hook-id>
```

## Bypassing Hooks (Emergency Only)

If you absolutely must commit without running hooks:

```bash
git commit --no-verify -m "Emergency fix"
```

**⚠️ WARNING:** Only use this in emergencies. Bypassing hooks can introduce:
- Formatting inconsistencies
- Security vulnerabilities
- Broken tests
- Invalid configurations

## CI/CD Integration

The same hooks should run in CI. Add to your CI config:

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - uses: pre-commit/action@v3.0.0
```

## Best Practices

1. **Commit Often** - Small commits are faster to check
2. **Run Manually First** - Use `pre-commit run --all-files` before committing large changes
3. **Keep Tools Updated** - Run `pre-commit autoupdate` monthly
4. **Don't Skip Hooks** - They catch issues early
5. **Review Auto-fixes** - Don't blindly commit formatter changes

## Getting Help

- Pre-commit docs: https://pre-commit.com/
- Tool-specific issues: Check individual tool documentation
- RPM-EE issues: See project README or open an issue

## Validation Scripts

### Test Preset Validation

```bash
python scripts/validate_presets.py
```

### Test Experiment Config Validation

```bash
python scripts/validate_experiment_config.py config/example.yaml
```

### Test Documentation References

```bash
python scripts/check_doc_references.py docs/**/*.md
```

## Status Check

Verify your setup:

```bash
# Check pre-commit is installed
pre-commit --version

# Check hooks are installed
ls -la .git/hooks/pre-commit

# Test hooks
pre-commit run --all-files
```

## Example Workflow

```bash
# 1. Make changes
vim src/presets.py

# 2. Stage changes
git add src/presets.py

# 3. Commit (hooks run automatically)
git commit -m "Add new clinical preset"

# 4. If hooks fail and auto-fix:
git add src/presets.py  # Re-add fixed files
git commit -m "Add new clinical preset"

# 5. Push
git push
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `pre-commit install` | Install hooks |
| `pre-commit run --all-files` | Run all hooks manually |
| `pre-commit run <hook>` | Run specific hook |
| `pre-commit autoupdate` | Update hook versions |
| `pre-commit clean` | Clear cache |
| `SKIP=<hook> git commit` | Skip specific hook |
| `git commit --no-verify` | Skip all hooks (emergency) |

---

**Last Updated:** January 13, 2026  
**Version:** v1.1
