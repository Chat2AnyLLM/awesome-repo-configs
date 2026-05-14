# Contributing

Please do not update `README.md` directly to add a repo entry.

To submit a valid config update for https://github.com/Chat2AnyLLM/awesome-repo-configs, update the appropriate JSON file instead:

- `agent_repos.json`
- `plugin_repos.json`
- `skill_repos.json`

Before opening or updating your pull request:

1. Add or update the correct entry in the matching config file.
2. Follow the existing schema used by nearby entries so the config stays valid.
3. Run:

   ```bash
   python3 tests/test_json_validation.py
   python3 tests/test_pr_review_config.py
   python3 tests/test_readme_pr_reminder.py
   ```

README changes can still accompany a config update when needed, but repository additions should be made through the JSON config files above.
