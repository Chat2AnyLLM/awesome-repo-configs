# Contributing

Please do not update `README.md` directly to add a repo entry.

`awesome-repo-configs` is the central configuration hub for the Chat2AnyLLM `awesome-*` family. The Claude catalog generators consume their repo lists here; the prompt and MCP configurations are indices for external tooling.

To submit a valid config update for https://github.com/Chat2AnyLLM/awesome-repo-configs, update the appropriate JSON file instead:

- `agent_repos.json` — Claude Code agents (repos exposing `agents/*.md`)
- `plugin_repos.json` — Claude Code plugins & marketplaces (repos with `.claude-plugin/plugin.json` or `.claude-plugin/marketplace.json`)
- `skill_repos.json` — Claude Code skills (repos with `SKILL.md` layouts)
- `instruction_repos.json` — Instruction / docs repos consumed by code-agent-manager (e.g. `anthropics/claude-code`)
- `prompt_repos.json` — Prompt collections consumed by `awesome-prompts` (e.g. `Chat2AnyLLM/awesome-prompts` `dist/prompts.json`)
- `mcp_server_repos.json` — MCP server source repository index for external tooling
- `related_lists.json` — related lists and directories shown by `awesome-claude-skills`

Before opening or updating your pull request:

1. Add or update the correct entry in the matching config file.
2. Follow the existing schema used by nearby entries so the config stays valid. The standard schema is:
   ```json
   {
     "owner/name": {
       "owner": "owner",
       "name": "name",
       "branch": "main",
       "enabled": true
     }
   }
   ```
   Optional fields by file:
   - `agent_repos.json`: `agentsPath`, `catalogFile`
   - `plugin_repos.json`: uses `repoOwner`/`repoName`/`repoBranch` instead of `owner`/`name`/`branch`, plus `type`, `description`, `pluginPath`, `aliases`, `catalogFile`
   - `skill_repos.json`: `skillsPath`, `catalogFile`
   - `instruction_repos.json`, `prompt_repos.json`: `catalogFile`
    - `mcp_server_repos.json`: `serverName`, `subPath`, `note`
   Related lists use a separate schema and can point to websites as well as repositories:
   ```json
   {
     "example": {
       "name": "Example",
       "url": "https://example.com",
       "description": "A related directory.",
       "enabled": true
     }
   }
   ```
3. Run:

   ```bash
   python3 tests/test_json_validation.py
   python3 tests/test_pr_review_config.py
   python3 tests/test_readme_pr_reminder.py
   ```

README changes can still accompany a config update when needed, but repository additions should be made through the JSON config files above.
