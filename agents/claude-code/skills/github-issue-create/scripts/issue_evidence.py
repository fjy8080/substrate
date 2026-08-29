#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit


class EvidenceError(RuntimeError):
    pass


ISSUE_REFERENCE = re.compile(r"(?<![\w/])#(?P<number>[1-9][0-9]*)\b")
COMMAND_TIMEOUT_SECONDS = 60
MAX_PULL_FILES = 3000
MAX_PULL_COMMITS = 250
MAX_PULL_WORKERS = 4
MAX_OPEN_PULLS = 40


def run(arguments: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise EvidenceError(
            f"Command timed out after {COMMAND_TIMEOUT_SECONDS}s: {arguments[0]}"
        ) from exc
    except OSError as exc:
        raise EvidenceError(f"Cannot execute {arguments[0]}: {exc}") from exc


def git(root: Path, *arguments: str, allow_failure: bool = False) -> str:
    result = run(["git", *arguments], cwd=root)
    if result.returncode and not allow_failure:
        raise EvidenceError(result.stderr.strip() or f"git {' '.join(arguments)} failed")
    return result.stdout.strip()


def gh_json(arguments: list[str], *, allow_not_found: bool = False) -> Any:
    result = run(["gh", *arguments])
    if result.returncode:
        if allow_not_found and "HTTP 404" in result.stderr:
            return None
        raise EvidenceError(result.stderr.strip() or f"gh {' '.join(arguments)} failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"GitHub returned invalid JSON: {exc}") from exc


def paginated_rest(endpoint: str, *, headers: list[str] | None = None) -> list[dict[str, Any]]:
    arguments = ["api", "--paginate", "--slurp", endpoint]
    for header in headers or []:
        arguments.extend(["-H", header])
    pages = gh_json(arguments)
    if not isinstance(pages, list):
        raise EvidenceError(f"Expected paginated list from {endpoint}")
    items: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, list):
            raise EvidenceError(f"Expected array page from {endpoint}")
        for index, item in enumerate(page):
            if not isinstance(item, dict):
                raise EvidenceError(
                    f"Expected object item at {endpoint} page item {index}, got {type(item).__name__}"
                )
            items.append(item)
    return items


def repository_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"])
    if result.returncode:
        raise EvidenceError("Run issue_evidence.py inside the current Git repository.")
    return Path(result.stdout.strip()).resolve()


def actor(user: Any) -> dict[str, Any]:
    if not isinstance(user, dict):
        return {"login": None, "node_id": None}
    return {"login": user.get("login"), "node_id": user.get("node_id") or user.get("id")}


def extract_issue_numbers(text: Any) -> list[int]:
    if not isinstance(text, str):
        return []
    return sorted({int(match.group("number")) for match in ISSUE_REFERENCE.finditer(text)})


def normalize_issue(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": item.get("number"),
        "url": item.get("html_url"),
        "title": item.get("title"),
        "state": item.get("state"),
        "state_reason": item.get("state_reason"),
        "is_pull_request": isinstance(item.get("pull_request"), dict),
        "author": actor(item.get("user")),
        "author_association": item.get("author_association"),
        "labels": [label.get("name") for label in item.get("labels") or [] if isinstance(label, dict)],
        "assignees": [actor(value) for value in item.get("assignees") or []],
        "milestone": (item.get("milestone") or {}).get("title"),
        "locked": item.get("locked"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "closed_at": item.get("closed_at"),
        "body": item.get("body") or "",
    }


def normalize_pull(item: dict[str, Any]) -> dict[str, Any]:
    text = f"{item.get('title') or ''}\n{item.get('body') or ''}"
    return {
        "number": item.get("number"),
        "url": item.get("html_url"),
        "title": item.get("title"),
        "body": item.get("body") or "",
        "state": item.get("state"),
        "draft": item.get("draft"),
        "author": actor(item.get("user")),
        "base": {
            "ref": (item.get("base") or {}).get("ref"),
            "sha": (item.get("base") or {}).get("sha"),
        },
        "head": {
            "ref": (item.get("head") or {}).get("ref"),
            "sha": (item.get("head") or {}).get("sha"),
            "repo": ((item.get("head") or {}).get("repo") or {}).get("full_name"),
        },
        "issue_references": extract_issue_numbers(text),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def normalize_pull_file(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item.get("filename"), str) or not item["filename"].strip():
        raise EvidenceError("Pull file entry is missing filename.")
    return {
        "path": item.get("filename"),
        "previous_path": item.get("previous_filename"),
        "status": item.get("status"),
        "additions": item.get("additions"),
        "deletions": item.get("deletions"),
        "changes": item.get("changes"),
    }


def normalize_review(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("id") is None or not isinstance(item.get("state"), str):
        raise EvidenceError("Pull review entry is missing id/state.")
    return {
        "id": item.get("id"),
        "node_id": item.get("node_id"),
        "url": item.get("html_url"),
        "author": actor(item.get("user")),
        "author_association": item.get("author_association"),
        "state": item.get("state"),
        "commit_id": item.get("commit_id"),
        "submitted_at": item.get("submitted_at"),
        "body": item.get("body") or "",
    }


def normalize_inline_comment(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item.get("path"), str) or not item["path"].strip():
        raise EvidenceError("Inline review comment is missing path.")
    return {
        **normalize_comment(item),
        "path": item.get("path"),
        "line": item.get("line"),
        "original_line": item.get("original_line"),
        "side": item.get("side"),
        "commit_id": item.get("commit_id"),
        "in_reply_to_id": item.get("in_reply_to_id"),
    }


def normalize_pull_commit(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item.get("sha"), str) or not item["sha"].strip():
        raise EvidenceError("Pull commit entry is missing SHA.")
    commit = item.get("commit") or {}
    commit_author = commit.get("author") or {}
    commit_committer = commit.get("committer") or {}
    message = str(commit.get("message") or "")
    return {
        "sha": item.get("sha"),
        "author": actor(item.get("author")),
        "committer": actor(item.get("committer")),
        "authored_at": commit_author.get("date"),
        "committed_at": commit_committer.get("date"),
        "message_headline": message.splitlines()[0] if message else "",
        "parent_shas": [
            parent.get("sha") for parent in item.get("parents") or [] if isinstance(parent, dict)
        ],
    }


def normalize_comment(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("id") is None:
        raise EvidenceError("Issue/PR comment entry is missing id.")
    return {
        "id": item.get("id"),
        "node_id": item.get("node_id"),
        "url": item.get("html_url"),
        "author": actor(item.get("user")),
        "author_association": item.get("author_association"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "body": item.get("body") or "",
    }


def normalize_timeline(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": item.get("event"),
        "actor": actor(item.get("actor")),
        "created_at": item.get("created_at") or item.get("submitted_at"),
        "commit_id": item.get("commit_id") or item.get("sha"),
        "label": (item.get("label") or {}).get("name"),
        "assignee": actor(item.get("assignee")),
        "assigner": actor(item.get("assigner")),
        "source": item.get("source"),
    }


def parse_worktrees(raw: str) -> list[dict[str, Any]]:
    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in [*raw.splitlines(), ""]:
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, separator, value = line.partition(" ")
        current[key] = value if separator else True
    return worktrees


def redact_remote_url(value: str) -> str:
    if "://" not in value:
        return value
    parsed = urlsplit(value)
    hostname = parsed.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parsed.scheme, hostname, parsed.path, "", ""))


def remote_heads(root: Path, name: str) -> dict[str, Any]:
    result = run(["git", "ls-remote", "--heads", name], cwd=root)
    if result.returncode:
        return {"query_ok": False, "heads": []}
    heads: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        sha, separator, ref = line.partition("\t")
        if not separator or not ref.startswith("refs/heads/"):
            continue
        heads.append({"branch": ref.removeprefix("refs/heads/"), "sha": sha})
    return {"query_ok": True, "heads": heads}


def remote_matches_repo(remote: dict[str, Any], repo: str) -> bool:
    suffixes = (repo.casefold(), f"{repo.casefold()}.git")
    return any(
        str(remote.get(key) or "").casefold().rstrip("/").endswith(suffixes)
        for key in ("fetch_url", "push_url")
    )


def repository_remote_completeness(
    local: dict[str, Any], repo: str, target_base: str
) -> tuple[list[dict[str, Any]], bool]:
    matching = [
        remote for remote in local.get("remotes", []) if remote_matches_repo(remote, repo)
    ]
    complete = bool(matching) and all(
        remote.get("heads_query_ok") is True for remote in matching
    ) and any(
        any(head.get("branch") == target_base for head in remote.get("heads", []))
        for remote in matching
    )
    return matching, complete


def worktree_status(item: dict[str, Any]) -> dict[str, Any]:
    path = item.get("worktree")
    if not isinstance(path, str) or item.get("bare"):
        return {**item, "status_query_ok": False, "dirty": None}
    result = run(["git", "status", "--short", "--branch"], cwd=Path(path))
    if result.returncode:
        return {**item, "status_query_ok": False, "dirty": None}
    lines = result.stdout.splitlines()
    return {
        **item,
        "status_query_ok": True,
        "dirty": any(line and not line.startswith("## ") for line in lines),
        "status_short_branch": result.stdout.strip(),
    }


def local_repository(root: Path) -> dict[str, Any]:
    remotes: list[dict[str, str]] = []
    for name in git(root, "remote").splitlines():
        if not name:
            continue
        heads = remote_heads(root, name)
        remotes.append(
            {
                "name": name,
                "fetch_url": redact_remote_url(git(root, "remote", "get-url", name)),
                "push_url": redact_remote_url(git(root, "remote", "get-url", "--push", name)),
                "heads_query_ok": heads["query_ok"],
                "heads": heads["heads"],
            }
        )
    worktrees = parse_worktrees(git(root, "worktree", "list", "--porcelain"))
    return {
        "root": str(root),
        "branch": git(root, "branch", "--show-current"),
        "head_sha": git(root, "rev-parse", "HEAD"),
        "status_short_branch": git(root, "status", "--short", "--branch"),
        "remotes": remotes,
        "worktrees": [worktree_status(item) for item in worktrees],
    }


def repo_view(root: Path) -> dict[str, Any]:
    result = run(
        ["gh", "repo", "view", "--json", "nameWithOwner,url,defaultBranchRef"],
        cwd=root,
    )
    if result.returncode:
        raise EvidenceError(result.stderr.strip() or "Cannot resolve the current GitHub repository.")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"Cannot parse current repository identity: {exc}") from exc
    return {
        "name_with_owner": value.get("nameWithOwner"),
        "url": value.get("url"),
        "default_branch": (value.get("defaultBranchRef") or {}).get("name"),
    }


def issue_detail(repo: str, number: int) -> dict[str, Any]:
    raw = gh_json(["api", f"repos/{repo}/issues/{number}"])
    if not isinstance(raw, dict):
        raise EvidenceError(f"Issue #{number} detail is not an object.")
    issue = normalize_issue(raw)
    comments = paginated_rest(f"repos/{repo}/issues/{number}/comments?per_page=100")
    timeline = paginated_rest(
        f"repos/{repo}/issues/{number}/timeline?per_page=100",
        headers=["Accept: application/vnd.github+json"],
    )
    issue["comments"] = [normalize_comment(item) for item in comments]
    issue["timeline"] = [normalize_timeline(item) for item in timeline]
    after = gh_json(["api", f"repos/{repo}/issues/{number}"])
    if not isinstance(after, dict) or issue_fingerprint(raw) != issue_fingerprint(after):
        raise EvidenceError(f"Issue #{number} changed during detail capture; rerun.")
    return issue


def issue_fingerprint(item: dict[str, Any]) -> tuple[Any, ...]:
    normalized = normalize_issue(item)
    return (
        normalized.get("number"),
        normalized.get("state"),
        normalized.get("state_reason"),
        normalized.get("title"),
        normalized.get("body"),
        normalized.get("updated_at"),
        tuple(sorted(str(value) for value in normalized.get("labels", []))),
        tuple(
            sorted(
                (str(value.get("node_id")), str(value.get("login")))
                for value in normalized.get("assignees", [])
            )
        ),
        normalized.get("milestone"),
    )


def issue_inventory_fingerprint(items: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return sorted((issue_fingerprint(item) for item in items), key=lambda value: int(value[0] or 0))


def label_inventory_fingerprint(items: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    return sorted(
        (
            str(item.get("name") or ""),
            str(item.get("description") or ""),
            str(item.get("color") or ""),
        )
        for item in items
    )


def local_snapshot_fingerprint(local: dict[str, Any]) -> str:
    payload = {
        "branch": local.get("branch"),
        "head_sha": local.get("head_sha"),
        "status_short_branch": local.get("status_short_branch"),
        "remotes": sorted(
            local.get("remotes", []), key=lambda value: str(value.get("name") or "")
        ),
        "worktrees": sorted(
            local.get("worktrees", []), key=lambda value: str(value.get("worktree") or "")
        ),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pull_detail(repo: str, item: dict[str, Any]) -> dict[str, Any]:
    listed_pull = normalize_pull(item)
    number = listed_pull.get("number")
    if not isinstance(number, int) or number <= 0:
        raise EvidenceError("Open pull request is missing a valid number.")
    before = gh_json(["api", f"repos/{repo}/pulls/{number}"])
    if not isinstance(before, dict):
        raise EvidenceError(f"Pull request #{number} detail is not an object.")
    if pull_fingerprint(item) != pull_fingerprint(before):
        raise EvidenceError(f"Pull request #{number} changed after the open-PR inventory snapshot.")
    expected_files = before.get("changed_files")
    expected_commits = before.get("commits")
    if not isinstance(expected_files, int) or expected_files < 0:
        raise EvidenceError(f"Pull request #{number} is missing changed_files count.")
    if not isinstance(expected_commits, int) or expected_commits < 0:
        raise EvidenceError(f"Pull request #{number} is missing commits count.")
    if expected_files > MAX_PULL_FILES:
        raise EvidenceError(
            f"Pull request #{number} has {expected_files} files, above REST proof limit {MAX_PULL_FILES}."
        )
    if expected_commits > MAX_PULL_COMMITS:
        raise EvidenceError(
            f"Pull request #{number} has {expected_commits} commits, above REST proof limit {MAX_PULL_COMMITS}."
        )
    files = paginated_rest(f"repos/{repo}/pulls/{number}/files?per_page=100")
    reviews = paginated_rest(f"repos/{repo}/pulls/{number}/reviews?per_page=100")
    conversation = paginated_rest(f"repos/{repo}/issues/{number}/comments?per_page=100")
    inline = paginated_rest(f"repos/{repo}/pulls/{number}/comments?per_page=100")
    commits = paginated_rest(f"repos/{repo}/pulls/{number}/commits?per_page=100")
    after = gh_json(["api", f"repos/{repo}/pulls/{number}"])
    if not isinstance(after, dict) or pull_fingerprint(before) != pull_fingerprint(after):
        raise EvidenceError(f"Pull request #{number} head/base/state changed during detail capture.")
    if after.get("changed_files") != expected_files or after.get("commits") != expected_commits:
        raise EvidenceError(f"Pull request #{number} counts changed during detail capture.")
    if len(files) != expected_files:
        raise EvidenceError(
            f"Pull request #{number} file evidence incomplete: expected {expected_files}, got {len(files)}."
        )
    if len(commits) != expected_commits:
        raise EvidenceError(
            f"Pull request #{number} commit evidence incomplete: expected {expected_commits}, got {len(commits)}."
        )
    pull = normalize_pull(before)
    pull.update(
        {
            "files": [normalize_pull_file(value) for value in files],
            "reviews": [normalize_review(value) for value in reviews],
            "conversation_comments": [normalize_comment(value) for value in conversation],
            "inline_comments": [normalize_inline_comment(value) for value in inline],
            "commits": [normalize_pull_commit(value) for value in commits],
            "expected_changed_files": expected_files,
            "expected_commits": expected_commits,
            "detail_completeness": {
                "files_paginated": True,
                "reviews_paginated": True,
                "conversation_comments_paginated": True,
                "inline_comments_paginated": True,
                "commits_paginated": True,
            },
        }
    )
    return pull


def pull_fingerprint(item: dict[str, Any]) -> tuple[Any, ...]:
    normalized = normalize_pull(item)
    return (
        normalized.get("number"),
        normalized.get("state"),
        normalized.get("draft"),
        normalized.get("title"),
        normalized.get("body"),
        normalized.get("updated_at"),
        normalized["base"].get("ref"),
        normalized["base"].get("sha"),
        normalized["head"].get("ref"),
        normalized["head"].get("sha"),
        normalized["head"].get("repo"),
    )


def pull_inventory_fingerprint(items: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return sorted((pull_fingerprint(item) for item in items), key=lambda value: int(value[0] or 0))


def collect_pull_details(repo: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        return []
    if len(items) > MAX_OPEN_PULLS:
        raise EvidenceError(
            f"Repository has {len(items)} open PRs, above bounded snapshot limit {MAX_OPEN_PULLS}."
        )
    workers = min(MAX_PULL_WORKERS, len(items))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda item: pull_detail(repo, item), items))


def build_snapshot(
    requested_repo: str | None,
    issue_numbers: list[int],
    target_base: str,
) -> dict[str, Any]:
    started_at = datetime.now(UTC).isoformat()
    root = repository_root()
    view = repo_view(root)
    repo = str(view.get("name_with_owner") or "")
    if not repo:
        raise EvidenceError("Current GitHub repository identity is empty.")
    if requested_repo and requested_repo.casefold() != repo.casefold():
        raise EvidenceError(
            f"Requested repository {requested_repo} does not match current repository {repo}."
        )

    local = local_repository(root)
    authenticated = actor(gh_json(["api", "user"]))
    encoded_base = quote(target_base, safe="")
    target_branch = gh_json(
        ["api", f"repos/{repo}/branches/{encoded_base}"],
        allow_not_found=True,
    )
    open_pull_raw = paginated_rest(f"repos/{repo}/pulls?state=open&per_page=100")
    open_pulls = collect_pull_details(repo, open_pull_raw)
    open_issue_raw = paginated_rest(f"repos/{repo}/issues?state=open&per_page=100")
    open_issues = [
        normalize_issue(item)
        for item in open_issue_raw
        if not isinstance(item.get("pull_request"), dict)
    ]
    labels = paginated_rest(f"repos/{repo}/labels?per_page=100")
    requested_issues = [issue_detail(repo, number) for number in sorted(set(issue_numbers))]
    related_pulls: dict[str, list[dict[str, Any]]] = {}
    for number in sorted(set(issue_numbers)):
        related_pulls[str(number)] = [
            pull for pull in open_pulls if number in pull.get("issue_references", [])
        ]
    open_pull_raw_after = paginated_rest(f"repos/{repo}/pulls?state=open&per_page=100")
    if pull_inventory_fingerprint(open_pull_raw) != pull_inventory_fingerprint(open_pull_raw_after):
        raise EvidenceError("Open pull-request inventory changed during snapshot capture; rerun.")
    target_branch_after = gh_json(
        ["api", f"repos/{repo}/branches/{encoded_base}"],
        allow_not_found=True,
    )
    if ((target_branch or {}).get("commit") or {}).get("sha") != (
        ((target_branch_after or {}).get("commit") or {}).get("sha")
    ):
        raise EvidenceError(f"Target branch {target_base} changed during snapshot capture; rerun.")
    open_issue_raw_after = paginated_rest(f"repos/{repo}/issues?state=open&per_page=100")
    open_issues_after = [
        item for item in open_issue_raw_after if not isinstance(item.get("pull_request"), dict)
    ]
    if issue_inventory_fingerprint(
        [item for item in open_issue_raw if not isinstance(item.get("pull_request"), dict)]
    ) != issue_inventory_fingerprint(open_issues_after):
        raise EvidenceError("Open Issue inventory changed during snapshot capture; rerun.")
    labels_after = paginated_rest(f"repos/{repo}/labels?per_page=100")
    if label_inventory_fingerprint(labels) != label_inventory_fingerprint(labels_after):
        raise EvidenceError("Repository labels changed during snapshot capture; rerun.")
    local_after = local_repository(root)
    if local_snapshot_fingerprint(local) != local_snapshot_fingerprint(local_after):
        raise EvidenceError("Local worktree/remote state changed during snapshot capture; rerun.")
    matching_remotes, remote_branch_complete = repository_remote_completeness(
        local, repo, target_base
    )
    all_remote_heads_complete = bool(local["remotes"]) and all(
        remote.get("heads_query_ok") is True for remote in local["remotes"]
    )
    remote_branch_complete = remote_branch_complete and all_remote_heads_complete

    return {
        "snapshot_version": 2,
        "capture_started_at": started_at,
        "captured_at": datetime.now(UTC).isoformat(),
        "authenticated_actor": authenticated,
        "repository": view,
        "local": local,
        "target_base": {
            "name": target_base,
            "exists": isinstance(target_branch, dict),
            "sha": ((target_branch or {}).get("commit") or {}).get("sha"),
            "protected": target_branch.get("protected") if isinstance(target_branch, dict) else None,
        },
        "open_pull_requests": open_pulls,
        "open_issues": open_issues,
        "available_labels": [
            {
                "name": item.get("name"),
                "description": item.get("description"),
                "color": item.get("color"),
            }
            for item in labels
        ],
        "requested_issues": requested_issues,
        "related_open_pulls": related_pulls,
        "completeness": {
            "open_pull_requests_paginated": True,
            "open_pull_files_paginated": True,
            "open_pull_reviews_paginated": True,
            "open_pull_conversation_comments_paginated": True,
            "open_pull_inline_comments_paginated": True,
            "open_pull_commits_paginated": True,
            "open_pull_inventory_stable": True,
            "target_base_stable": True,
            "open_issue_inventory_stable": True,
            "labels_stable": True,
            "local_and_remote_state_stable": True,
            "snapshot_consistent": True,
            "open_issues_paginated": True,
            "labels_paginated": True,
            "requested_issue_comments_paginated": True,
            "requested_issue_timeline_paginated": True,
            "repository_remote_present": bool(matching_remotes),
            "remote_branch_heads_complete": remote_branch_complete,
            "worktree_status_complete": all(
                worktree.get("status_query_ok") is True for worktree in local["worktrees"]
            ),
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Capture current repository, Issue, PR, branch, and worktree evidence."
    )
    result.add_argument("--repo", help="Optional OWNER/NAME assertion for the current repository")
    result.add_argument("--issue", type=int, action="append", default=[])
    result.add_argument("--target-base", default="develop")
    result.add_argument("--compact", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    if any(number <= 0 for number in args.issue):
        print("error: issue numbers must be positive", file=sys.stderr)
        return 2
    try:
        snapshot = build_snapshot(args.repo, args.issue, args.target_base)
    except EvidenceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            snapshot,
            ensure_ascii=False,
            indent=None if args.compact else 2,
            separators=(",", ":") if args.compact else None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
