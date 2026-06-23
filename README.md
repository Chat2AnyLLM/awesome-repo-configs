# awesome-repo-configs

Central configuration hub for the **Chat2AnyLLM `awesome-*` family**. This repo is the single source of truth for repo lists that the downstream Claude-Code aggregators consume directly.

| File | Consumed by | Description |
|---|---|---|
| `agent_repos.json` | `awesome-claude-agents`, `code-agent-manager` | Claude Code agent repos |
| `plugin_repos.json` | `awesome-claude-plugins`, `code-agent-manager` | Claude Code plugin & marketplace repos |
| `skill_repos.json` | `awesome-claude-skills`, `code-agent-manager` | Claude Code skill repos |
| `instruction_repos.json` | `code-agent-manager` | Instruction / docs repos |
| `prompt_repos.json` | `code-agent-manager` | Pointer to the canonical prompt collection (`Chat2AnyLLM/awesome-prompts` `dist/prompts.json`) |
| `mcp_server_repos.json` | external tooling / discovery | Registry index of MCP server source repos derived from `awesome-mcp-servers` |

Downstream Claude-Code repos (`awesome-claude-{agents,plugins,skills}`) pull these JSON files directly from `main` via raw.githubusercontent.com and treat this repo as their **only** source. A push to `main` here fan-out-dispatches a `config-updated` event to each of those repos so they regenerate their README / aggregate output.

`awesome-prompts` and `awesome-mcp-servers` keep their own build pipelines (they aggregate non-repo data sources such as CSVs, markdown lists, and hand-curated server JSONs); the `prompt_repos.json` and `mcp_server_repos.json` files here are indices for external consumers, not inputs to those repos' builds.

## Adding or updating a repo

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Do not edit `README.md` to add entries — update the JSON.

## Local validation

```bash
python3 tests/test_json_validation.py
python3 tests/test_pr_review_config.py
python3 tests/test_readme_pr_reminder.py
```
