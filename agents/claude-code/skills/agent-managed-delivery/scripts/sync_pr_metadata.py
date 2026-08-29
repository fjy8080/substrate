#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MetadataError(RuntimeError):
    pass


FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
HIDDEN_LINE = re.compile(
    r"(?m)^[ \t]*<!--[ \t]*(?:base:[^\s>]+|commits:[0-9]+|files:[0-9]+)"
    r"[ \t]*-->[ \t]*(?:\r?\n)?"
)
VISIBLE_PATTERNS = {
    "base": re.compile(r"(?m)^(?P<prefix>[ \t]*-[ \t]*Base:[ \t]*`)[^`\r\n]*(?P<suffix>`[ \t]*)$"),
    "commits": re.compile(
        r"(?m)^(?P<prefix>[ \t]*-[ \t]*Commits:[ \t]*`)[^`\r\n]*(?P<suffix>`[ \t]*)$"
    ),
    "files": re.compile(
        r"(?m)^(?P<prefix>[ \t]*-[ \t]*Files changed:[ \t]*`)[^`\r\n]*(?P<suffix>`[ \t]*)$"
    ),
    "head": re.compile(
        r"(?m)^(?P<prefix>[ \t]*-[ \t]*\[[ xX]\][ \t]*核验的是当前最新提交"
        r"（HEAD SHA）：[ \t]*`)(?:待填写|[0-9a-fA-F]{7,40})(?P<suffix>`[ \t]*)$"
    ),
}


@dataclass(frozen=True)
class PullSnapshot:
    state: str
    head: str
    base: str
    commits: int
    files: int
    body: str

    @property
    def signature(self) -> tuple[str, str, int, int]:
        return (self.head, self.base, self.commits, self.files)


def run(arguments: list[str], *, cwd: Path | None = None, stdin: str | None = None) -> str:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise MetadataError(result.stderr.strip() or f"{' '.join(arguments)} failed")
    return result.stdout


def repository_root() -> Path:
    value = run(["git", "rev-parse", "--show-toplevel"]).strip()
    if not value:
        raise MetadataError("Run inside the Git repository that owns the pull request.")
    return Path(value).resolve()


def current_repository(root: Path) -> str:
    value = run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        cwd=root,
    ).strip()
    if not value:
        raise MetadataError("Cannot resolve the current GitHub repository.")
    return value


def gh_json(arguments: list[str], *, cwd: Path, payload: dict[str, Any] | None = None) -> Any:
    command = ["gh", "api", *arguments]
    stdin = None
    if payload is not None:
        command.extend(["--input", "-"])
        stdin = json.dumps(payload, ensure_ascii=False)
    raw = run(command, cwd=cwd, stdin=stdin)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MetadataError(f"GitHub returned invalid JSON: {exc}") from exc


def pull_snapshot(root: Path, repo: str, number: int) -> PullSnapshot:
    value = gh_json([f"repos/{repo}/pulls/{number}"], cwd=root)
    try:
        return PullSnapshot(
            state=str(value["state"]),
            head=str(value["head"]["sha"]),
            base=str(value["base"]["ref"]),
            commits=int(value["commits"]),
            files=int(value["changed_files"]),
            body=str(value.get("body") or ""),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MetadataError("GitHub pull request payload is missing required metadata.") from exc


def replace_visible(body: str, field: str, value: str) -> str:
    pattern = VISIBLE_PATTERNS[field]
    matches = list(pattern.finditer(body))
    if len(matches) > 1:
        raise MetadataError(f"PR body has ambiguous duplicate visible {field} metadata fields.")
    if not matches:
        return body
    return pattern.sub(lambda match: f"{match.group('prefix')}{value}{match.group('suffix')}", body)


def canonical_body(body: str, snapshot: PullSnapshot) -> str:
    marker_block = (
        f"<!-- base:{snapshot.base} -->\n"
        f"<!-- commits:{snapshot.commits} -->\n"
        f"<!-- files:{snapshot.files} -->\n"
    )
    first = True

    def replace_hidden(_: re.Match[str]) -> str:
        nonlocal first
        if first:
            first = False
            return marker_block
        return ""

    updated = HIDDEN_LINE.sub(replace_hidden, body)
    if first:
        updated = f"{updated.rstrip()}\n\n{marker_block}" if updated.strip() else marker_block
    updated = replace_visible(updated, "base", snapshot.base)
    updated = replace_visible(updated, "commits", str(snapshot.commits))
    updated = replace_visible(updated, "files", str(snapshot.files))
    updated = replace_visible(updated, "head", snapshot.head)
    return updated


def static_projection(body: str) -> str:
    value = HIDDEN_LINE.sub("", body)
    for field, pattern in VISIBLE_PATTERNS.items():
        value = pattern.sub(
            lambda match, name=field: f"{match.group('prefix')}<{name}>{match.group('suffix')}",
            value,
        )
    return value.rstrip()


def stable_snapshot(
    root: Path,
    repo: str,
    number: int,
    expected_head: str,
    timeout: float,
    interval: float,
) -> PullSnapshot:
    deadline = time.monotonic() + timeout
    previous: tuple[str, str, int, int] | None = None
    stable_count = 0
    last: PullSnapshot | None = None
    while time.monotonic() <= deadline:
        last = pull_snapshot(root, repo, number)
        if last.state != "open":
            raise MetadataError(f"PR #{number} is {last.state}, not open.")
        if last.head == expected_head:
            if last.signature == previous:
                stable_count += 1
            else:
                previous = last.signature
                stable_count = 1
            if stable_count >= 2:
                return last
        time.sleep(interval)
    observed = last.head if last is not None else "unavailable"
    raise MetadataError(
        f"Timed out waiting for PR #{number} metadata at expected head {expected_head}; "
        f"last observed head was {observed}."
    )


def result_payload(status: str, repo: str, number: int, snapshot: PullSnapshot) -> dict[str, Any]:
    return {
        "status": status,
        "repository": repo,
        "pull_request": number,
        "head_sha": snapshot.head,
        "base": snapshot.base,
        "commits": snapshot.commits,
        "files": snapshot.files,
        "body_sha256": hashlib.sha256(snapshot.body.encode("utf-8")).hexdigest(),
    }


def synchronize(args: argparse.Namespace) -> dict[str, Any]:
    root = repository_root()
    repo = current_repository(root)
    if args.repo.casefold() != repo.casefold():
        raise MetadataError(f"Requested repository {args.repo} does not match current repository {repo}.")
    expected_head = args.expected_head.lower()
    for attempt in range(1, 4):
        before = stable_snapshot(root, repo, args.pr, expected_head, args.timeout, args.interval)
        if args.required_base and before.base != args.required_base:
            raise MetadataError(
                f"PR #{args.pr} targets {before.base}, required base is {args.required_base}."
            )
        expected_body = canonical_body(before.body, before)
        if static_projection(before.body) != static_projection(expected_body):
            raise MetadataError("Refusing to change non-metadata PR body content.")
        if before.body == expected_body:
            return result_payload("IN_SYNC", repo, args.pr, before)
        if not args.apply:
            payload = result_payload("DRIFT", repo, args.pr, before)
            payload["would_update"] = True
            return payload
        gh_json(
            ["--method", "PATCH", f"repos/{repo}/pulls/{args.pr}"],
            cwd=root,
            payload={"body": expected_body},
        )
        after = pull_snapshot(root, repo, args.pr)
        if after.signature != before.signature:
            if attempt < 3:
                continue
            raise MetadataError("PR head/base/statistics changed concurrently during metadata update.")
        if after.body != expected_body:
            raise MetadataError("GitHub PR body read-back does not match the requested metadata update.")
        if static_projection(before.body) != static_projection(after.body):
            raise MetadataError("PR body narrative changed during metadata synchronization.")
        return result_payload("UPDATED", repo, args.pr, after)
    raise MetadataError("Could not synchronize PR metadata after concurrent updates.")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Synchronize repository-required base/commits/files PR body metadata."
    )
    value.add_argument("--repo", required=True, help="Exact OWNER/REPO assertion")
    value.add_argument("--pr", required=True, type=int)
    value.add_argument("--expected-head", required=True)
    value.add_argument("--required-base")
    value.add_argument("--apply", action="store_true", help="Patch and verify the PR body")
    value.add_argument("--timeout", type=float, default=30.0)
    value.add_argument("--interval", type=float, default=1.0)
    return value


def main() -> int:
    args = parser().parse_args()
    if args.pr <= 0:
        print("error: PR number must be positive", file=sys.stderr)
        return 2
    if not FULL_SHA.fullmatch(args.expected_head):
        print("error: --expected-head must be a full 40-character SHA", file=sys.stderr)
        return 2
    if args.timeout <= 0 or args.timeout > 120 or args.interval <= 0:
        print("error: timeout must be in (0, 120] and interval must be positive", file=sys.stderr)
        return 2
    try:
        payload = synchronize(args)
    except MetadataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
