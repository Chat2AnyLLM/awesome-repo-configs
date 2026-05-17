#!/usr/bin/env python3
"""Review PR changes to Claude repo config files."""

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CONFIG_FILES = {
    "agent_repos.json": "agent",
    "plugin_repos.json": "plugin",
    "skill_repos.json": "skill",
}
COMMENT_MARKER = "<!-- awesome-repo-configs-pr-review -->"
API_URL = os.environ.get("GITHUB_API_URL", "https://api.github.com")
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
MARKETPLACE_MANIFEST = ".claude-plugin/marketplace.json"


class DuplicateKeyError(ValueError):
    """Raised when JSON contains duplicate object keys."""


def parse_json_strict(text):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyError(f"duplicate key: {key}")
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=reject_duplicates)


def normalize_relative_path(value, field_name):
    if value is None:
        return "", []
    if not isinstance(value, str) or not value.strip():
        return "", [f"`{field_name}` must be a non-empty string when provided."]

    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.strip("/")

    if normalized.startswith("/") or ".." in normalized.split("/"):
        return "", [f"`{field_name}` must be a safe relative path."]
    return normalized, []


def join_path(prefix, suffix):
    return f"{prefix}/{suffix}" if prefix else suffix


def is_nested_skill_file(path, skills_root):
    prefix = f"{skills_root}/" if skills_root else ""
    if not path.startswith(prefix) or not path.endswith("/SKILL.md"):
        return False
    relative_path = path[len(prefix) :]
    return relative_path.count("/") == 1


def entry_repo_fields(config_file, entry):
    if CONFIG_FILES[config_file] == "plugin":
        return entry.get("repoOwner"), entry.get("repoName"), entry.get("repoBranch")
    return entry.get("owner"), entry.get("name"), entry.get("branch")


def validate_entry_schema(config_file, key, entry):
    errors = []
    warnings = []
    kind = CONFIG_FILES[config_file]

    if not isinstance(entry, dict):
        return [f"`{key}` must be an object."], warnings

    if kind == "plugin":
        required_strings = ["name", "description", "type", "repoOwner", "repoName"]
        for field in required_strings:
            if not isinstance(entry.get(field), str) or not entry.get(field).strip():
                errors.append(f"`{key}.{field}` must be a non-empty string.")
        if "repoBranch" in entry and (
            not isinstance(entry.get("repoBranch"), str) or not entry.get("repoBranch").strip()
        ):
            errors.append(f"`{key}.repoBranch` must be a non-empty string when provided.")
        if "pluginPath" in entry:
            _, path_errors = normalize_relative_path(entry.get("pluginPath"), "pluginPath")
            errors.extend(f"`{key}` {error}" for error in path_errors)
        aliases = entry.get("aliases")
        if aliases is not None and (
            not isinstance(aliases, list) or not all(isinstance(alias, str) and alias.strip() for alias in aliases)
        ):
            errors.append(f"`{key}.aliases` must be a list of non-empty strings when provided.")
    else:
        required_strings = ["owner", "name", "branch"]
        for field in required_strings:
            if not isinstance(entry.get(field), str) or not entry.get(field).strip():
                errors.append(f"`{key}.{field}` must be a non-empty string.")
        path_field = "agentsPath" if kind == "agent" else "skillsPath"
        if path_field in entry:
            _, path_errors = normalize_relative_path(entry.get(path_field), path_field)
            errors.extend(f"`{key}` {error}" for error in path_errors)

    if not isinstance(entry.get("enabled"), bool):
        errors.append(f"`{key}.enabled` must be a boolean.")

    owner, repo, _ = entry_repo_fields(config_file, entry)
    if isinstance(owner, str) and isinstance(repo, str) and key != f"{owner}/{repo}":
        warnings.append(f"`{key}` does not match `{owner}/{repo}`. Consider renaming the entry key to `{owner}/{repo}` for consistency.")

    return errors, warnings


def assess_plugin_standard(entry, tree_paths):
    errors = []
    warnings = []
    plugin_path, path_errors = normalize_relative_path(entry.get("pluginPath"), "pluginPath")
    errors.extend(path_errors)

    manifest_name = MARKETPLACE_MANIFEST if entry.get("type") == "marketplace" else PLUGIN_MANIFEST
    manifest_suffix = f"/{manifest_name}"
    manifests = {path.removesuffix(manifest_suffix) for path in tree_paths if path.endswith(manifest_suffix)}
    if manifest_name in tree_paths:
        manifests.add("")

    if plugin_path:
        if join_path(plugin_path, manifest_name) not in tree_paths:
            errors.append(f"Claude Code plugins require `{manifest_name}` at the configured `pluginPath`.")
            return errors, warnings
        roots = [plugin_path]
    else:
        roots = sorted(manifests)
        if not roots:
            errors.append(f"No Claude Code plugin manifest found. Expected `{manifest_name}` under the plugin root.")
            return errors, warnings

    for root in roots:
        has_component = any(
            path.startswith(join_path(root, "commands/")) and path.endswith(".md")
            or path.startswith(join_path(root, "agents/")) and path.endswith(".md")
            or is_nested_skill_file(path, join_path(root, "skills"))
            or path == join_path(root, "hooks/hooks.json")
            or path == join_path(root, ".mcp.json")
            for path in tree_paths
        )
        if not has_component:
            warnings.append(f"Plugin root `{root or '.'}` has a manifest but no standard commands, agents, skills, hooks, or MCP config.")

    return errors, warnings


def assess_skill_standard(entry, tree_paths):
    errors = []
    warnings = []
    skills_path, path_errors = normalize_relative_path(entry.get("skillsPath"), "skillsPath")
    errors.extend(path_errors)

    if skills_path:
        direct_skill = join_path(skills_path, "SKILL.md")
        if direct_skill not in tree_paths and not any(is_nested_skill_file(path, skills_path) for path in tree_paths):
            errors.append("Claude Code skills require `SKILL.md` at `skillsPath` or in skill subdirectories.")
    else:
        skill_files = [path for path in tree_paths if path.endswith("SKILL.md")]
        if not skill_files:
            errors.append("No Claude Code skill found. Expected at least one `SKILL.md` file.")
        elif not any(path.startswith("skills/") or "/skills/" in path or path == "SKILL.md" for path in skill_files):
            warnings.append("Found `SKILL.md`, but the standard layout uses `skills/<skill-name>/SKILL.md`.")

    return errors, warnings


def assess_agent_standard(entry, tree_paths):
    errors = []
    warnings = []
    agents_path, path_errors = normalize_relative_path(entry.get("agentsPath"), "agentsPath")
    errors.extend(path_errors)

    if agents_path:
        has_agent = any(path.startswith(f"{agents_path}/") and path.endswith(".md") for path in tree_paths)
        if not has_agent:
            errors.append("No agent markdown files found under the configured `agentsPath`.")
    else:
        has_agent = any(
            (path.startswith("agents/") or path.startswith(".claude/agents/")) and path.endswith(".md")
            for path in tree_paths
        )
        if not has_agent:
            warnings.append("No standard `agents/*.md` or `.claude/agents/*.md` files found.")

    return errors, warnings


def assess_claude_standard(config_file, entry, tree_paths):
    kind = CONFIG_FILES[config_file]
    if kind == "plugin":
        return assess_plugin_standard(entry, tree_paths)
    if kind == "skill":
        return assess_skill_standard(entry, tree_paths)
    return assess_agent_standard(entry, tree_paths)


def api_request(path, token, method="GET", payload=None):
    url = path if path.startswith("http") else f"{API_URL}{path}"
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "awesome-repo-configs-pr-review",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"message": body}
        return error.code, parsed


def paginated(path, token):
    page = 1
    results = []
    while True:
        separator = "&" if "?" in path else "?"
        status, data = api_request(f"{path}{separator}per_page=100&page={page}", token)
        if status >= 400:
            raise RuntimeError(data.get("message", f"GitHub API error {status}"))
        if not data:
            return results
        results.extend(data)
        if len(data) < 100:
            return results
        page += 1


def get_file_text(repo, path, ref, token):
    quoted_path = urllib.parse.quote(path)
    quoted_ref = urllib.parse.quote(ref, safe="")
    status, data = api_request(f"/repos/{repo}/contents/{quoted_path}?ref={quoted_ref}", token)
    if status == 404:
        return None
    if status >= 400:
        raise RuntimeError(data.get("message", f"Unable to fetch {path}"))
    if data.get("encoding") != "base64":
        raise RuntimeError(f"Unexpected encoding for {path}")
    return base64.b64decode(data["content"]).decode("utf-8")


def get_tree_paths(owner, repo, ref, token):
    quoted_ref = urllib.parse.quote(ref, safe="")
    status, data = api_request(f"/repos/{owner}/{repo}/git/trees/{quoted_ref}?recursive=1", token)
    if status >= 400:
        return None, data.get("message", f"Unable to read repository tree for {owner}/{repo}@{ref}")
    if data.get("truncated"):
        return None, "Repository tree is too large for a complete Claude standard check."
    return {item["path"] for item in data.get("tree", []) if item.get("type") == "blob"}, None


def merge_pull_request(repository, pr_number, token):
    status, data = api_request(
        f"/repos/{repository}/pulls/{pr_number}/merge",
        token,
        method="PUT",
        payload={"merge_method": "merge"},
    )
    if status == 405:
        raise RuntimeError(data.get("message", "Pull request is not mergeable (conflicts, required checks, or branch protection rules may be blocking the merge)"))
    if status >= 400:
        raise RuntimeError(data.get("message", f"Unable to merge pull request: {status}"))


def comment_on_pr(repository, pr_number, token, body):
    comments = paginated(f"/repos/{repository}/issues/{pr_number}/comments", token)
    existing = next((comment for comment in comments if COMMENT_MARKER in comment.get("body", "")), None)
    if existing:
        status, data = api_request(existing["url"], token, method="PATCH", payload={"body": body})
    else:
        status, data = api_request(f"/repos/{repository}/issues/{pr_number}/comments", token, method="POST", payload={"body": body})
    if status >= 400:
        raise RuntimeError(data.get("message", "Unable to post PR comment"))


def changed_entries(base_data, head_data):
    changes = []
    for key, value in head_data.items():
        if base_data.get(key) != value:
            changes.append((key, value))
    return changes


def build_comment(errors, warnings, checked_entries, changed_config_files):
    result = "❌ Needs changes" if errors else "✅ Looks valid"
    lines = [
        COMMENT_MARKER,
        "## Automated PR review",
        "",
        "Thanks for the contribution — I will look at it ASAP.",
        "",
        f"**Result:** {result}",
        f"**Changed config files:** {', '.join(changed_config_files) if changed_config_files else 'none'}",
        f"**Changed entries checked:** {checked_entries}",
        "",
    ]
    if errors:
        lines.extend(["### Required fixes", *[f"- {error}" for error in errors], ""])
    if warnings:
        lines.extend(["### Review notes", *[f"- {warning}" for warning in warnings], ""])
    if not errors and not warnings:
        lines.append("No issues found in the submitted repo config changes.")
    return "\n".join(lines)


def review_pull_request(repository, pr_number, token):
    status, pr = api_request(f"/repos/{repository}/pulls/{pr_number}", token)
    if status >= 400:
        raise RuntimeError(pr.get("message", "Unable to read pull request"))

    changed_files = paginated(f"/repos/{repository}/pulls/{pr_number}/files", token)
    changed_config_files = [item["filename"] for item in changed_files if item["filename"] in CONFIG_FILES]
    errors = []
    warnings = []
    checked_entries = 0

    for config_file in changed_config_files:
        head_text = get_file_text(pr["head"]["repo"]["full_name"], config_file, pr["head"]["sha"], token)
        if head_text is None:
            warnings.append(f"`{config_file}` was deleted; no submitted repos to validate.")
            continue

        try:
            head_data = parse_json_strict(head_text)
        except (json.JSONDecodeError, DuplicateKeyError) as error:
            errors.append(f"`{config_file}` is not valid JSON: {error}")
            continue

        if not isinstance(head_data, dict):
            errors.append(f"`{config_file}` must contain a JSON object at the root.")
            continue

        base_text = get_file_text(repository, config_file, pr["base"]["sha"], token)
        try:
            base_data = parse_json_strict(base_text) if base_text else {}
        except (json.JSONDecodeError, DuplicateKeyError):
            base_data = {}

        for key, entry in changed_entries(base_data, head_data):
            checked_entries += 1
            schema_errors, schema_warnings = validate_entry_schema(config_file, key, entry)
            errors.extend(f"`{config_file}` {error}" for error in schema_errors)
            warnings.extend(f"`{config_file}` {warning}" for warning in schema_warnings)
            if schema_errors:
                continue

            owner, repo_name, branch = entry_repo_fields(config_file, entry)
            status, repo_info = api_request(f"/repos/{owner}/{repo_name}", token)
            if status >= 400:
                errors.append(f"`{config_file}` `{key}` points to an unavailable repository `{owner}/{repo_name}`.")
                continue

            branch_to_check = branch or repo_info.get("default_branch")
            status, branch_info = api_request(
                f"/repos/{owner}/{repo_name}/branches/{urllib.parse.quote(branch_to_check, safe='')}",
                token,
            )
            if status >= 400:
                errors.append(f"`{config_file}` `{key}` points to missing branch `{branch_to_check}`.")
                continue

            tree_paths, tree_error = get_tree_paths(owner, repo_name, branch_info["commit"]["sha"], token)
            if tree_error:
                warnings.append(f"`{config_file}` `{key}`: {tree_error}")
                continue

            standard_errors, standard_warnings = assess_claude_standard(config_file, entry, tree_paths)
            errors.extend(f"`{config_file}` `{key}`: {error}" for error in standard_errors)
            warnings.extend(f"`{config_file}` `{key}`: {warning}" for warning in standard_warnings)

    return errors, warnings, checked_entries, changed_config_files


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]

    errors, warnings, checked_entries, changed_config_files = review_pull_request(repository, pr_number, token)
    body = build_comment(errors, warnings, checked_entries, changed_config_files)
    comment_on_pr(repository, pr_number, token, body)
    print(body)
    if errors:
        return 1
    try:
        merge_pull_request(repository, pr_number, token)
        print("Pull request merged automatically.")
    except RuntimeError as exc:
        print(f"::warning::Auto-merge skipped: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
