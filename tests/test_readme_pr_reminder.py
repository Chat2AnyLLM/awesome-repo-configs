#!/usr/bin/env python3
"""Unit tests for README PR reminder helpers."""

import importlib.util
import pathlib
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / ".github" / "scripts" / "remind_readme_contribution.py"
SPEC = importlib.util.spec_from_file_location("remind_readme_contribution", SCRIPT_PATH)
REMINDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REMINDER)


class ReadmePrReminderTests(unittest.TestCase):
    def test_detects_root_readme_change(self):
        self.assertTrue(REMINDER.changed_readme_directly([{"filename": "README.md"}]))

    def test_ignores_non_readme_changes(self):
        self.assertFalse(
            REMINDER.changed_readme_directly(
                [{"filename": "plugin_repos.json"}, {"filename": ".github/workflows/review-pr.yml"}]
            )
        )

    def test_build_comment_includes_guide_and_repo_links(self):
        comment = REMINDER.build_comment()
        self.assertIn("CONTRIBUTING.md", comment)
        self.assertIn("https://github.com/Chat2AnyLLM/awesome-repo-configs", comment)
        self.assertIn("agent_repos.json", comment)


if __name__ == "__main__":
    unittest.main()
