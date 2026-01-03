# Tests

This directory contains automated tests for the JSON configuration files in this repository.

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