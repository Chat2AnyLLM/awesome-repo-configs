#!/usr/bin/env python3
"""Remind contributors to use config files instead of editing README directly."""

import json
import os
import sys
import urllib.error
import urllib.request


API_URL = os.environ.get("GITHUB_API_URL", "https://api.github.com")
COMMENT_MARKER = "<!-- awesome-repo-configs-readme-reminder -->"
ROOT_README_PATHS_LOWERCASE = {"readme", "readme.md"}
CONTRIBUTING_URL = "https://github.com/Chat2AnyLLM/awesome-repo-configs/blob/main/CONTRIBUTING.md"
REPO_URL = "https://github.com/Chat2AnyLLM/awesome-repo-configs"


def api_request(path, token, method="GET", payload=None):
    url = path if path.startswith("http") else f"{API_URL}{path}"
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "awesome-repo-configs-readme-reminder",
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


def changed_readme_directly(changed_files):
    """Return True only for direct edits to the repository root README files."""
    return any(
        item.get("filename", "").strip("/").lower() in ROOT_README_PATHS_LOWERCASE for item in changed_files
    )


def build_comment():
    return "\n".join(
        [
            COMMENT_MARKER,
            "## README update reminder",
            "",
            "Thanks for the contribution.",
            "",
            "It looks like this pull request edits `README.md` directly.",
            "Please review the contribution guide and update the repo through a valid config file instead of using the README for repo additions:",
            f"- Contribution guide: {CONTRIBUTING_URL}",
            f"- Valid config reference: {REPO_URL}",
            "",
            "Use one of these files for repo updates:",
            "- `agent_repos.json`",
            "- `plugin_repos.json`",
            "- `skill_repos.json`",
        ]
    )


def upsert_comment(repository, pr_number, token, body):
    comments = paginated(f"/repos/{repository}/issues/{pr_number}/comments", token)
    existing = next((comment for comment in comments if COMMENT_MARKER in comment.get("body", "")), None)
    if existing:
        status, data = api_request(existing["url"], token, method="PATCH", payload={"body": body})
    else:
        status, data = api_request(
            f"/repos/{repository}/issues/{pr_number}/comments",
            token,
            method="POST",
            payload={"body": body},
        )
    if status >= 400:
        raise RuntimeError(data.get("message", "Unable to post PR comment"))


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]

    changed_files = paginated(f"/repos/{repository}/pulls/{pr_number}/files", token)
    if not changed_readme_directly(changed_files):
        print("No direct README changes detected.")
        return 0

    body = build_comment()
    upsert_comment(repository, pr_number, token, body)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
