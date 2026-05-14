# Tests

This directory contains automated tests for the JSON configuration files and PR review helpers in this repository.

## test_json_validation.py

Validates the JSON configuration files (`agent_repos.json`, `plugin_repos.json`, `skill_repos.json`) for:

1. **JSON Syntax**: Ensures all files contain valid JSON
2. **No Duplicates**: Checks that there are no duplicate keys in the JSON objects

### Running Tests Locally

```bash
python3 tests/test_json_validation.py
```

### CI/CD Integration

The validation is automatically run in GitHub Actions as part of the `notify-other-repos.yml` workflow. The workflow will fail if any JSON file has syntax errors or duplicate entries, preventing invalid configurations from being deployed.

## test_pr_review_config.py

Validates helper logic used by the incoming PR review workflow for:

1. **Strict JSON Parsing**: Ensures duplicate keys are rejected
2. **Claude Standards**: Checks plugin, skill, and agent path validation helpers
3. **Schema Checks**: Confirms submitted repo entries use expected field types

### Running Tests Locally

```bash
python3 tests/test_pr_review_config.py
```

## test_readme_pr_reminder.py

Validates helper logic used by the README reminder workflow for:

1. **README Detection**: Checks that direct root README edits are detected
2. **Comment Content**: Confirms the reminder links contributors to the contribution guide and valid config repo

### Running Tests Locally

```bash
python3 tests/test_readme_pr_reminder.py
```
