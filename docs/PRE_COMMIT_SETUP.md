# Pre-commit Hooks Setup

Comprehensive code quality, security, and consistency checks on every commit.

## Quick Setup (3 steps)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files  # Test
```

## What Gets Checked

✅ **Formatting** - Black, isort (auto-fix)  
✅ **Linting** - Ruff (30+ rule sets), pydocstyle  
✅ **Type checking** - mypy  
✅ **Security** - detect-secrets, bandit  
✅ **Files** - YAML, JSON, markdown validation  
✅ **Project** - Clinical presets, experiment configs  
✅ **Policy** - No TODOs (use GitHub issues)  

## Usage

**Automatic:**
```bash
git commit -m "Your message"  # Hooks run automatically
```

**Manual:**
```bash
pre-commit run --all-files     # Run all
pre-commit run black           # Run specific
```

**Emergency bypass (NOT recommended):**
```bash
git commit --no-verify -m "Emergency"
```

## TODO Prevention Policy

**❌ Blocked patterns:**
```python
# TODO: This will fail
# FIXME: This will fail  
# HACK, XXX, BUG, etc. - all blocked
```

**✅ Use GitHub issues instead:**
```python
# Issue #123: Add validation
# See #456 for details
```

**Why:** TODOs get lost, issues are tracked/assigned/prioritized.

**Enforcement:** 2-layer detection (Ruff FIX + grep hook)

## Configuration Files

- `.pre-commit-config.yaml` - Hook definitions
- `pyproject.toml` - Tool settings (black, ruff, mypy, pytest)
- `.yamllint.yaml` - YAML rules
- `.markdownlint.json` - Markdown rules

## Common Commands

| Command | Purpose |
|---------|---------|
| `pre-commit install` | Install hooks |
| `pre-commit run --all-files` | Run all manually |
| `pre-commit autoupdate` | Update hook versions |
| `pre-commit clean` | Clear cache |
| `SKIP=mypy git commit` | Skip specific hook |

## Troubleshooting

**Hook failed?**
1. Read error message
2. Fix issue (or let auto-fix run)
3. Re-add files: `git add .`
4. Try again

**Slow hooks?**
```bash
SKIP=mypy,pytest git commit -m "message"
```

**Update hooks:**
```bash
pre-commit autoupdate
```

## Hook Categories

### 1. Formatting (Auto-fix)
- Black (line-length: 100)
- isort (black profile)
- Ruff format

### 2. Linting
- Ruff (E,W,F,I,N,UP,B,A,C4,DTZ,T10,EM,ISC,PIE,PYI,RSE,RET,SIM,TID,ARG,PTH,PD,PGH,PL,TRY,NPY,RUF,FIX)
- Pydocstyle (NumPy convention)

### 3. Type Checking
- mypy (gradual typing)

### 4. Security
- detect-secrets (credential leaks)
- bandit (vulnerability scan)

### 5. File Validation
- yamllint, check-json, markdownlint

### 6. General
- Large files (>5MB), merge conflicts
- Trailing whitespace, line endings (LF)
- Python syntax, debug statements
- Executable permissions

### 7. RPM-EE Specific
- Clinical preset validation (`scripts/validate_presets.py`)
- Experiment config validation (`scripts/validate_experiment_config.py`)
- Documentation reference checking (`scripts/check_doc_references.py`)
- TODO prevention (Ruff FIX + grep)

## Example Workflow

```bash
# 1. Make changes
vim src/presets.py

# 2. Commit (hooks run automatically)
git commit -m "Update preset"

# 3. If hooks auto-fix:
git add src/presets.py
git commit -m "Update preset"
```

## Tool Configuration

**Black & Ruff:**
- Line length: 100
- Target: Python 3.10
- Compatible profiles

**Mypy:**
- Gradual typing
- Ignore missing imports

**Ruff rules:**
30+ categories including FIX (TODO detection)

**Excluded:**
`__pycache__/`, `.venv/`, `node_modules/`, `saved_logs/`, `results/`, `logs/`, `Users/`

## Validation Scripts

Test the validators:

```bash
python scripts/validate_presets.py
python scripts/validate_experiment_config.py config/example.yaml
python scripts/check_doc_references.py docs/*.md
```

## CI/CD Integration

Add to `.github/workflows/pre-commit.yml`:

```yaml
name: Pre-commit
on: [push, pull_request]
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - uses: pre-commit/action@v3.0.0
```

## Best Practices

1. Commit often (small commits = faster checks)
2. Run manually before pushing: `pre-commit run --all-files`
3. Don't skip hooks (they catch real issues)
4. Update monthly: `pre-commit autoupdate`
5. Create issues, not TODOs

---

**Version:** v1.1  
**Updated:** January 13, 2026
