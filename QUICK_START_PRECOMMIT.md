# Quick Start: Pre-commit Hooks

Get the RPM-EE pre-commit hooks running in 3 minutes.

## 1. Install (One-time setup)

```bash
# Install pre-commit
pip install pre-commit

# Install development tools (optional, auto-installed on first run)
pip install -r requirements-dev.txt

# Install git hooks
pre-commit install
```

**That's it!** Hooks will now run automatically on every commit.

## 2. Test Your Setup

```bash
# Run all hooks manually to verify
pre-commit run --all-files
```

Expected output:
```
black....................................................................Passed
isort....................................................................Passed
ruff.....................................................................Passed
mypy.....................................................................Passed
detect-secrets...........................................................Passed
bandit...................................................................Passed
...
```

## 3. Make a Commit

```bash
# Edit a file
vim src/presets.py

# Stage changes
git add src/presets.py

# Commit (hooks run automatically)
git commit -m "Update clinical preset"
```

### If hooks fail:

1. **Auto-fixed** (black, isort): Just re-add and commit
   ```bash
   git add src/presets.py
   git commit -m "Update clinical preset"
   ```

2. **Linting errors** (ruff, mypy): Fix manually and re-commit
   ```bash
   # Fix the issues
   vim src/presets.py
   
   # Try again
   git add src/presets.py
   git commit -m "Update clinical preset"
   ```

## Common Commands

| What | Command |
|------|---------|
| Run all hooks | `pre-commit run --all-files` |
| Run one hook | `pre-commit run black --all-files` |
| Update hooks | `pre-commit autoupdate` |
| Skip hooks (emergency) | `git commit --no-verify -m "message"` |
| Clear cache | `pre-commit clean` |

## What Gets Checked

✅ Python formatting (black, isort)  
✅ Code quality (ruff, mypy)  
✅ Security (detect-secrets, bandit)  
✅ File validation (YAML, JSON, Markdown)  
✅ Clinical presets validation  
✅ Experiment configs  

## Troubleshooting

### "Hook failed" on commit
- Read the error message
- Fix the issue or let auto-formatters fix it
- Re-add files: `git add .`
- Try committing again

### Hooks are slow
```bash
# Skip slow hooks temporarily
SKIP=mypy git commit -m "message"
```

### Need help
See `docs/PRE_COMMIT_SETUP.md` for detailed guide.

## Pro Tips

💡 Run `pre-commit run --all-files` before pushing  
💡 Commit often (smaller commits = faster checks)  
💡 Let formatters do their job (don't fight black)  
💡 Fix linting errors - they catch real bugs  
💡 Update hooks monthly: `pre-commit autoupdate`  

---

**Ready to code!** Your commits will now be automatically checked for quality, security, and consistency.

For full documentation, see:
- `docs/PRE_COMMIT_SETUP.md` - Complete guide
- `PRE_COMMIT_SUMMARY.md` - Implementation details
