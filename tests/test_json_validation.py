#!/usr/bin/env python3
"""
Test script to validate JSON configuration files.
Tests:
1. JSON syntax validation
2. Duplicate key detection
"""

import json
import sys
from pathlib import Path

def validate_json_file(file_path):
    """Validate JSON syntax and return parsed data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f"JSON syntax error: {e}"
    except Exception as e:
        return False, None, f"Error reading file: {e}"

def check_duplicates(data, file_path):
    """Check for duplicate keys in JSON object"""
    if not isinstance(data, dict):
        return False, "Root element must be a JSON object"

    keys = list(data.keys())
    unique_keys = set(keys)

    if len(keys) != len(unique_keys):
        duplicates = [key for key in unique_keys if keys.count(key) > 1]
        return False, f"Duplicate keys found: {duplicates}"

    return True, None

def main():
    """Main test function"""
    json_files = [
        'agent_repos.json',
        'plugin_repos.json',
        'skill_repos.json'
    ]

    all_valid = True
    results = []

    for json_file in json_files:
        file_path = Path(json_file)
        if not file_path.exists():
            results.append(f"❌ {json_file}: File not found")
            all_valid = False
            continue

        # Validate JSON syntax
        is_valid, data, error = validate_json_file(file_path)
        if not is_valid:
            results.append(f"❌ {json_file}: {error}")
            all_valid = False
            continue

        # Check for duplicates
        has_no_duplicates, dup_error = check_duplicates(data, file_path)
        if not has_no_duplicates:
            results.append(f"❌ {json_file}: {dup_error}")
            all_valid = False
            continue

        results.append(f"✅ {json_file}: Valid JSON, no duplicates")

    # Print results
    print("JSON Configuration Files Validation Results:")
    print("=" * 50)
    for result in results:
        print(result)

    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())