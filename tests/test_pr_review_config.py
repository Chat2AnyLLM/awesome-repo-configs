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

    def test_marketplace_plugin_standard_accepts_marketplace_manifest(self):
        entry = {"pluginPath": "plugins/example", "type": "marketplace"}
        errors, warnings = REVIEW.assess_plugin_standard(
            entry,
            {
                "plugins/example/.claude-plugin/marketplace.json",
                "plugins/example/skills/review/SKILL.md",
            },
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_standard_plugin_still_requires_plugin_manifest(self):
        entry = {"pluginPath": "plugins/example", "type": "plugin"}
        errors, warnings = REVIEW.assess_plugin_standard(
            entry,
            {"plugins/example/.claude-plugin/marketplace.json"},
        )
        self.assertIn("Claude Code plugins require `.claude-plugin/plugin.json`", errors[0])
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

    def test_instruction_schema_accepts_minimal_entry(self):
        errors, warnings = REVIEW.validate_entry_schema(
            "instruction_repos.json",
            "anthropics/claude-code",
            {"owner": "anthropics", "name": "claude-code", "branch": "main", "enabled": True},
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_prompt_schema_accepts_catalog_file(self):
        errors, warnings = REVIEW.validate_entry_schema(
            "prompt_repos.json",
            "Chat2AnyLLM/awesome-prompts",
            {
                "owner": "Chat2AnyLLM",
                "name": "awesome-prompts",
                "branch": "master",
                "enabled": True,
                "catalogFile": "dist/prompts.json",
            },
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_mcp_server_schema_accepts_sub_path_and_server_name(self):
        errors, warnings = REVIEW.validate_entry_schema(
            "mcp_server_repos.json",
            "modelcontextprotocol/servers",
            {
                "owner": "modelcontextprotocol",
                "name": "servers",
                "branch": "main",
                "enabled": True,
                "serverName": "fetch",
                "subPath": "src/fetch",
            },
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_mcp_server_schema_rejects_bad_sub_path(self):
        errors, _ = REVIEW.validate_entry_schema(
            "mcp_server_repos.json",
            "x/y",
            {"owner": "x", "name": "y", "branch": "main", "enabled": True, "subPath": "../escape"},
        )
        self.assertTrue(any("subPath" in e for e in errors))

    def test_assess_claude_standard_skips_non_claude_kinds(self):
        for config_file in ("instruction_repos.json", "prompt_repos.json", "mcp_server_repos.json"):
            errors, warnings = REVIEW.assess_claude_standard(config_file, {}, set())
            self.assertEqual([], errors, f"{config_file} should have no errors")
            self.assertEqual([], warnings, f"{config_file} should have no warnings")


if __name__ == "__main__":
    unittest.main()
