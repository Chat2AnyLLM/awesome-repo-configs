#!/usr/bin/env python3
"""Unit tests for PR config review helpers."""

import importlib.util
import pathlib
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / ".github" / "scripts" / "review_pr_config.py"
SPEC = importlib.util.spec_from_file_location("review_pr_config", SCRIPT_PATH)
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)


class ReviewPrConfigTests(unittest.TestCase):
    def test_parse_json_strict_rejects_duplicate_keys(self):
        with self.assertRaises(REVIEW.DuplicateKeyError):
            REVIEW.parse_json_strict('{"repo": {"enabled": true}, "repo": {"enabled": false}}')

    def test_plugin_standard_requires_manifest_at_plugin_path(self):
        entry = {"pluginPath": "plugins/example"}
        errors, warnings = REVIEW.assess_plugin_standard(entry, {"plugins/example/commands/review.md"})
        self.assertIn("Claude Code plugins require `.claude-plugin/plugin.json`", errors[0])
        self.assertEqual([], warnings)

    def test_plugin_standard_accepts_manifest_and_components(self):
        entry = {"pluginPath": "plugins/example"}
        errors, warnings = REVIEW.assess_plugin_standard(
            entry,
            {
                "plugins/example/.claude-plugin/plugin.json",
                "plugins/example/skills/review/SKILL.md",
            },
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_skill_standard_accepts_nested_skill(self):
        entry = {"skillsPath": "skills"}
        errors, warnings = REVIEW.assess_skill_standard(entry, {"skills/review/SKILL.md"})
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_agent_schema_requires_boolean_enabled(self):
        errors, warnings = REVIEW.validate_entry_schema(
            "agent_repos.json",
            "owner/name",
            {"owner": "owner", "name": "name", "branch": "main", "enabled": "yes"},
        )
        self.assertIn("`owner/name.enabled` must be a boolean.", errors)
        self.assertEqual([], warnings)


if __name__ == "__main__":
    unittest.main()
