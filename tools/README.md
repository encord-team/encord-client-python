# Docstring Quality Linter

Checks Python docstrings for proper Sphinx role usage, consistent formatting, and cross-references.

## What It Checks

- ✅ Sphinx roles (`:class:`, `:meth:`, `:func:`, `:attr:`) in docstrings
- ✅ Section header formatting (`Args:` not `**Args**`)
- ✅ Spelling consistency (`AuthorizationError` not `AuthorisationError`)
- ✅ Exception cross-references in Raises sections
- ✅ Class cross-references throughout docstrings

## Quick Start

### Run Manually

Check a single file:
```bash
python tools/docstring_linter.py --check --config tools/docstring_linter_config.json --files encord/user_client.py
```

Check a single file with detailed output (shows all issues with file locations):
```bash
python tools/docstring_linter.py --check --config tools/docstring_linter_config.json --files encord/user_client.py --verbose
```

Check all SDK files:
```bash
python tools/docstring_linter.py --check --config tools/docstring_linter_config.json --sdk-path encord/
```

Check all SDK files with detailed output:
```bash
python tools/docstring_linter.py --check --config tools/docstring_linter_config.json --sdk-path encord/ --verbose
```

Auto-fix safe issues (section headers, spelling):
```bash
python tools/docstring_linter.py --fix --config tools/docstring_linter_config.json --sdk-path encord/
```

### Pre-commit Hook

The linter is integrated into the pre-commit hooks. It will automatically check your docstrings before commit.

**Current mode:** Check only (warnings will block commits)

To run pre-commit hooks manually:
```bash
pre-commit run --all-files
```

To run just the docstring linter:
```bash
pre-commit run docstring-linter --all-files
```

## Configuration Options

### Option 1: Strict Mode (Current - Blocks on Warnings)

Blocks commits if any warnings are found. Good for enforcing high quality.

```yaml
# In .pre-commit-config.yaml
- id: docstring-linter
  entry: python tools/docstring_linter.py --check --config tools/docstring_linter_config.json --files
```

### Option 2: Relaxed Mode (Warn Only)

Only blocks commits on errors, not warnings. Good for gradual adoption.

To enable, edit `.pre-commit-config.yaml`:

```yaml
# In .pre-commit-config.yaml
- id: docstring-linter
  entry: python tools/docstring_linter.py --check --config tools/docstring_linter_config.json --files
  # Add this to make warnings not block:
  verbose: true
  # Or skip for now and only run manually
```

Or temporarily disable:
```yaml
- id: docstring-linter
  # Comment out to disable:
  # entry: python tools/docstring_linter.py ...
```

### Option 3: Auto-fix Mode

Automatically fixes safe issues on commit. **Use with caution!**

```yaml
- id: docstring-linter
  entry: python tools/docstring_linter.py --fix --config tools/docstring_linter_config.json --files
```

## Issue Severity Levels

- **Error** (exit 1): Critical issues like parse errors - must fix
- **Warning** (exit 1): Important issues - should fix
  - Unlinked exceptions
  - Invalid section headers
  - Spelling inconsistencies
- **Info** (exit 0): Nice to have improvements
  - Unlinked class references
  - Missing cross-references

## Recommended Workflow

### For New Code

Write docstrings with proper Sphinx roles from the start:

```python
def get_dataset(self, dataset_hash: str) -> Dataset:
    """Get a dataset by hash.

    Args:
        dataset_hash: The unique identifier for the dataset.

    Returns:
        :class:`~encord.dataset.Dataset`: The dataset instance.

    Raises:
        :class:`~encord.exceptions.AuthorizationError`: If API key is invalid.
        :class:`~encord.exceptions.ResourceNotFoundError`: If dataset not found.
    """
```

### For Existing Code

When modifying a file with warnings, fix the docstrings in that file:

1. Run linter with verbose output: `python tools/docstring_linter.py --check --files your_file.py --verbose`
2. Review issues grouped by type with file locations and suggested fixes
3. Apply fixes manually or use `--fix` for auto-fixable issues
4. Verify: `python tools/docstring_linter.py --check --files your_file.py`

**What does `--verbose` show?**
- Issues grouped by type (same grouping as the summary)
- File paths and line numbers in clickable format (`file.py:123`)
- Suggested fixes for each issue
- Function/method names where issues occur

Example verbose output:
```
unlinked_exception (15):
----------------------------------------------------------------------
encord/client.py:123: ⚠ [get_dataset] Exception "AuthenticationError" should use :class: role
  "AuthenticationError" → ":class:`~encord.exceptions.AuthenticationError`"
encord/project.py:456: ⚠ [create_project] Exception "ResourceNotFoundError" should use :class: role
  ...

unlinked_class (8):
----------------------------------------------------------------------
encord/user_client.py:182: ℹ [get_dataset] Class "Dataset" could use :class: role
  "Dataset" → ":class:`~encord.dataset.Dataset`"
  ...
```

## Skip Hook for Specific Commit

If you need to commit despite warnings:

```bash
git commit --no-verify -m "Your message"
```

**Use sparingly!** Better to fix the issues.

## Configuring the Linter

Edit `tools/docstring_linter_config.json` to:

- Add new SDK classes to detect
- Add new exception types
- Change auto-fix rules
- Modify ignore patterns

Example:
```json
{
  "sdk_package_name": "encord",
  "sdk_classes": [
    "LabelRowV2",
    "Dataset",
    "YourNewClass"  // Add here
  ],
  "exceptions": [
    "AuthorizationError",
    "YourNewException"  // Add here
  ]
}
```

## Generating Reports

Generate a JSON report of all issues:

```bash
python tools/docstring_linter.py \
  --check \
  --config tools/docstring_linter_config.json \
  --sdk-path encord/ \
  --report issues.json
```

## Command Line Options

Run with `--help` for full options:
```bash
python tools/docstring_linter.py --help
```

Common options:
- `--check` - Check only, don't modify files (dry run)
- `--fix` - Automatically fix issues where possible
- `--verbose` or `-v` - Show detailed output with all issues grouped by type
- `--files FILE [FILE ...]` - Check specific files
- `--sdk-path PATH` - Check all Python files in a directory
- `--report FILE.json` - Save results as JSON report
- `--config FILE.json` - Use custom configuration file

## Questions?

See the full documentation in the `encord-docs-mint` repository:
- Comprehensive style guide
- Before/after examples
- Complete setup instructions
