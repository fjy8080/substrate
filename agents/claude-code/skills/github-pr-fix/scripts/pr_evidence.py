#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any


BODY_METADATA = {
    "base": re.compile(r"<!--[ \t]*base:([^\s>]+)[ \t]*-->"),
    "commits": re.compile(r"<!--[ \t]*commits:([0-9]+)[ \t]*-->"),
    "files": re.compile(r"<!--[ \t]*files:([0-9]+)[ \t]*-->"),
}


class EvidenceError(RuntimeError):
    pass


COMMAND_TIMEOUT_SECONDS = 60


def run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments,
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


COMMITS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      viewerCanUpdate
      commits(first: 100, after: $cursor) {
        nodes {
          commit {
            oid
            authors(first: 100) {
              nodes { name email user { login id } }
              pageInfo { hasNextPage }
            }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $cursor) {
        nodes {
          id
          path
          line
          originalLine
          isOutdated
          isResolved
          resolvedBy { login id }
          comments(first: 100) {
            nodes {
              id
              databaseId
              url
              body
              createdAt
              outdated
              author { login }
              replyTo { id databaseId }
            }
            pageInfo { hasNextPage }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


def gh_json(arguments: list[str]) -> Any:
    result = run(["gh", *arguments])
    if result.returncode:
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
                    f"Expected object item at {endpoint} page item {index}, "
                    f"got {type(item).__name__}"
                )
            items.append(item)
    return items


def graphql_page(
    query: str,
    owner: str,
    name: str,
    number: int,
    cursor: str | None,
) -> dict[str, Any]:
    arguments = [
        "api",
        "graphql",
        "-f",
        f"query={query}",
        "-F",
        f"owner={owner}",
        "-F",
        f"name={name}",
        "-F",
        f"number={number}",
    ]
    if cursor is not None:
        arguments.extend(["-f", f"cursor={cursor}"])
    result = gh_json(arguments)
    if not isinstance(result, dict) or result.get("errors"):
        raise EvidenceError(f"GraphQL query failed: {result.get('errors') if isinstance(result, dict) else result}")
    return result


def actor_from_rest(user: Any) -> dict[str, str | None]:
    if not isinstance(user, dict):
        return {"login": None, "node_id": None}
    return {"login": user.get("login"), "node_id": user.get("node_id")}


def actor_from_graphql(user: Any) -> dict[str, str | None]:
    if not isinstance(user, dict):
        return {"login": None, "node_id": None}
    return {"login": user.get("login"), "node_id": user.get("id")}


def same_actor(left: dict[str, Any], right: dict[str, Any]) -> bool | None:
    left_id = left.get("node_id")
    right_id = right.get("node_id")
    if left_id and right_id:
        return str(left_id) == str(right_id)
    left_login = left.get("login")
    right_login = right.get("login")
    if left_login and right_login:
        return str(left_login).casefold() == str(right_login).casefold()
    return None


def classify_pr_relation(authenticated: dict[str, Any], creator: dict[str, Any]) -> str:
    match = same_actor(authenticated, creator)
    if match is True:
        return "SELF_PR"
    if match is False:
        return "OTHER_PR"
    return "UNKNOWN_PR_RELATION"


def email_fingerprint(email: Any) -> str | None:
    if not isinstance(email, str) or not email.strip():
        return None
    return hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()[:12]


def fetch_commit_authors(
    owner: str,
    name: str,
    number: int,
) -> tuple[list[dict[str, Any]], bool, bool | None]:
    cursor: str | None = None
    records: list[dict[str, Any]] = []
    complete = True
    viewer_can_update: bool | None = None
    while True:
        result = graphql_page(COMMITS_QUERY, owner, name, number, cursor)
        pull_request = result["data"]["repository"]["pullRequest"]
        viewer_can_update = pull_request.get("viewerCanUpdate")
        connection = pull_request["commits"]
        for node in connection.get("nodes") or []:
            commit = node.get("commit") or {}
            authors = commit.get("authors") or {}
            if (authors.get("pageInfo") or {}).get("hasNextPage"):
                complete = False
            records.append(
                {
                    "oid": commit.get("oid"),
                    "authors": [
                        {
                            "name": author.get("name"),
                            "email_fingerprint": email_fingerprint(author.get("email")),
                            **actor_from_graphql(author.get("user")),
                        }
                        for author in authors.get("nodes") or []
                    ],
                }
            )
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise EvidenceError("Commit pagination reported another page without a cursor.")
    return records, complete, viewer_can_update


def contribution_evidence(
    authenticated: dict[str, Any],
    commit_records: list[dict[str, Any]],
    *,
    complete: bool,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for record in commit_records:
        for author in record.get("authors") or []:
            match = same_actor(authenticated, author)
            if match is True:
                matches.append({"commit_oid": record.get("oid"), "actor": author})
            elif match is None or not author.get("login"):
                unresolved.append(
                    {
                        "commit_oid": record.get("oid"),
                        "name": author.get("name"),
                        "email_fingerprint": author.get("email_fingerprint"),
                    }
                )
    if matches:
        status = "CONTRIBUTOR"
    elif not complete or unresolved:
        status = "UNKNOWN_CONTRIBUTION"
    else:
        status = "NON_CONTRIBUTOR"
    return {
        "status": status,
        "matching_commits": matches,
        "unresolved_authors": unresolved,
        "complete": complete,
    }


def classify_independence(pr_relation: str, contribution_status: str) -> str:
    if pr_relation == "SELF_PR":
        return "NON_INDEPENDENT_SELF"
    if pr_relation != "OTHER_PR":
        return "UNKNOWN_INDEPENDENCE"
    if contribution_status == "CONTRIBUTOR":
        return "NON_INDEPENDENT_CONTRIBUTOR"
    if contribution_status == "NON_CONTRIBUTOR":
        return "PROVISIONALLY_INDEPENDENT"
    return "UNKNOWN_INDEPENDENCE"


def publication_route(pr_relation: str) -> str:
    if pr_relation == "SELF_PR":
        return "ORDINARY_ISSUE_COMMENT"
    if pr_relation == "OTHER_PR":
        return "FORMAL_REVIEW"
    return "HOLD_FOR_USER"


def fetch_review_threads(owner: str, name: str, number: int) -> tuple[list[dict[str, Any]], bool]:
    cursor: str | None = None
    threads: list[dict[str, Any]] = []
    complete = True
    while True:
        result = graphql_page(THREADS_QUERY, owner, name, number, cursor)
        connection = result["data"]["repository"]["pullRequest"]["reviewThreads"]
        for node in connection.get("nodes") or []:
            comments = node.get("comments") or {}
            if (comments.get("pageInfo") or {}).get("hasNextPage"):
                complete = False
            threads.append(
                {
                    "node_id": node.get("id"),
                    "path": node.get("path"),
                    "line": node.get("line"),
                    "original_line": node.get("originalLine"),
                    "is_outdated": node.get("isOutdated"),
                    "is_resolved": node.get("isResolved"),
                    "resolved_by": actor_from_graphql(node.get("resolvedBy")),
                    "comments": [
                        {
                            "node_id": comment.get("id"),
                            "database_id": comment.get("databaseId"),
                            "url": comment.get("url"),
                            "body": comment.get("body"),
                            "created_at": comment.get("createdAt"),
                            "outdated": comment.get("outdated"),
                            "author": actor_from_graphql(comment.get("author")),
                            "reply_to": comment.get("replyTo"),
                        }
                        for comment in comments.get("nodes") or []
                    ],
                }
            )
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise EvidenceError("Review-thread pagination reported another page without a cursor.")
    return threads, complete


def normalize_review(review: dict[str, Any], head_sha: str) -> dict[str, Any]:
    return {
        "id": review.get("id"),
        "node_id": review.get("node_id"),
        "url": review.get("html_url"),
        "author": actor_from_rest(review.get("user")),
        "state": review.get("state"),
        "commit_id": review.get("commit_id"),
        "is_current_head": review.get("commit_id") == head_sha,
        "submitted_at": review.get("submitted_at"),
        "body": review.get("body"),
    }


def normalize_issue_comment(comment: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": comment.get("id"),
        "node_id": comment.get("node_id"),
        "url": comment.get("html_url"),
        "author": actor_from_rest(comment.get("user")),
        "author_association": comment.get("author_association"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "body": comment.get("body"),
    }


def normalize_review_comment(comment: dict[str, Any], head_sha: str) -> dict[str, Any]:
    return {
        "id": comment.get("id"),
        "node_id": comment.get("node_id"),
        "url": comment.get("html_url"),
        "review_id": comment.get("pull_request_review_id"),
        "author": actor_from_rest(comment.get("user")),
        "path": comment.get("path"),
        "line": comment.get("line"),
        "original_line": comment.get("original_line"),
        "commit_id": comment.get("commit_id"),
        "original_commit_id": comment.get("original_commit_id"),
        "is_current_head": comment.get("commit_id") == head_sha,
        "is_outdated": comment.get("position") is None,
        "in_reply_to_id": comment.get("in_reply_to_id"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "body": comment.get("body"),
    }


def normalize_timeline_event(item: dict[str, Any]) -> dict[str, Any]:
    requested = item.get("requested_reviewer") or item.get("requested_team")
    return {
        "event": item.get("event"),
        "actor": actor_from_rest(item.get("actor")),
        "created_at": item.get("created_at") or item.get("submitted_at"),
        "review_requester": actor_from_rest(item.get("review_requester")),
        "requested_reviewer": actor_from_rest(requested),
        "dismissed_review": item.get("dismissed_review"),
        "commit_id": item.get("commit_id") or item.get("sha"),
    }


def latest_reviews_by_actor(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=lambda value: value.get("submitted_at") or ""):
        author = review.get("author") or {}
        key = str(author.get("node_id") or author.get("login") or f"unknown:{review.get('id')}")
        latest[key] = review
    return list(latest.values())


def review_request_context(
    timeline: list[dict[str, Any]],
    authenticated: dict[str, Any],
    creator: dict[str, Any],
) -> dict[str, Any]:
    relevant: list[dict[str, Any]] = []
    currently_requested = False
    ever_requested_by_creator = False
    for event in timeline:
        if same_actor(event.get("requested_reviewer") or {}, authenticated) is not True:
            continue
        if event.get("event") not in {"review_requested", "review_request_removed"}:
            continue
        relevant.append(event)
        if event.get("event") == "review_requested":
            currently_requested = True
            if same_actor(event.get("review_requester") or {}, creator) is True:
                ever_requested_by_creator = True
        else:
            currently_requested = False
    return {
        "currently_requested": currently_requested,
        "ever_requested_by_pr_creator": ever_requested_by_creator,
        "events": relevant,
    }


def body_metadata(body: Any, base: Any, commits: Any, files: Any) -> dict[str, Any]:
    text = body if isinstance(body, str) else ""
    occurrences = {name: pattern.findall(text) for name, pattern in BODY_METADATA.items()}
    values = {
        name: matches[-1] if matches else None for name, matches in occurrences.items()
    }
    expected = {
        "base": str(base or ""),
        "commits": str(commits) if isinstance(commits, int) else None,
        "files": str(files) if isinstance(files, int) else None,
    }
    return {
        "schema_detected": any(occurrences.values()),
        "complete": all(len(matches) == 1 for matches in occurrences.values()),
        "consistent": all(values[name] == expected[name] for name in expected),
        "values": values,
        "expected": expected,
        "occurrence_counts": {name: len(matches) for name, matches in occurrences.items()},
    }


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_stable(label: str, before: Any, after: Any) -> None:
    if stable_json(before) != stable_json(after):
        raise EvidenceError(f"{label} changed during snapshot capture; rerun.")


def pull_fingerprint(pull: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": pull.get("number"),
        "state": pull.get("state"),
        "merged": pull.get("merged"),
        "draft": pull.get("draft"),
        "title": pull.get("title"),
        "body": pull.get("body") or "",
        "updated_at": pull.get("updated_at"),
        "commits": pull.get("commits"),
        "changed_files": pull.get("changed_files"),
        "base": {
            "ref": (pull.get("base") or {}).get("ref"),
            "sha": (pull.get("base") or {}).get("sha"),
            "repo": ((pull.get("base") or {}).get("repo") or {}).get("full_name"),
        },
        "head": {
            "ref": (pull.get("head") or {}).get("ref"),
            "sha": (pull.get("head") or {}).get("sha"),
            "repo": ((pull.get("head") or {}).get("repo") or {}).get("full_name"),
        },
    }


def capture_feedback(owner: str, name: str, repo: str, number: int) -> dict[str, Any]:
    commit_records, commit_authors_complete, viewer_can_update = fetch_commit_authors(
        owner, name, number
    )
    return {
        "commit_records": commit_records,
        "commit_authors_complete": commit_authors_complete,
        "viewer_can_update": viewer_can_update,
        "reviews_raw": paginated_rest(f"repos/{repo}/pulls/{number}/reviews?per_page=100"),
        "issue_comments_raw": paginated_rest(
            f"repos/{repo}/issues/{number}/comments?per_page=100"
        ),
        "review_comments_raw": paginated_rest(
            f"repos/{repo}/pulls/{number}/comments?per_page=100"
        ),
        "timeline_raw": paginated_rest(
            f"repos/{repo}/issues/{number}/timeline?per_page=100",
            headers=["Accept: application/vnd.github+json"],
        ),
        "threads": fetch_review_threads(owner, name, number),
    }


def build_snapshot(repo: str, number: int) -> dict[str, Any]:
    started_at = datetime.now(UTC).isoformat()
    if repo.count("/") != 1 or any(not part for part in repo.split("/", 1)):
        raise EvidenceError("Repository must use OWNER/NAME.")
    owner, name = repo.split("/", 1)
    authenticated_raw = gh_json(["api", "user"])
    pull = gh_json(["api", f"repos/{repo}/pulls/{number}"])
    if not isinstance(authenticated_raw, dict) or not isinstance(pull, dict):
        raise EvidenceError("GitHub actor or pull-request detail is malformed.")
    authenticated = actor_from_rest(authenticated_raw)
    creator = actor_from_rest(pull.get("user"))
    head_sha = str((pull.get("head") or {}).get("sha") or "")
    if not head_sha:
        raise EvidenceError("Pull request is missing an exact head SHA.")
    relation = classify_pr_relation(authenticated, creator)
    pull_body = str(pull.get("body") or "")

    evidence = capture_feedback(owner, name, repo, number)
    evidence_after = capture_feedback(owner, name, repo, number)
    pull_after = gh_json(["api", f"repos/{repo}/pulls/{number}"])
    if not isinstance(pull_after, dict):
        raise EvidenceError("Final pull-request detail is malformed.")
    require_stable("Pull request identity/scope", pull_fingerprint(pull), pull_fingerprint(pull_after))
    require_stable("Pull request feedback lifecycle", evidence, evidence_after)

    commit_records = evidence["commit_records"]
    commit_authors_complete = evidence["commit_authors_complete"]
    viewer_can_update = evidence["viewer_can_update"]
    expected_commits = pull.get("commits")
    if not isinstance(expected_commits, int) or expected_commits < 0:
        raise EvidenceError("Pull request is missing its commit count.")
    if len(commit_records) != expected_commits:
        raise EvidenceError(
            f"Commit-author evidence incomplete: expected {expected_commits}, got {len(commit_records)}."
        )
    contribution = contribution_evidence(
        authenticated,
        commit_records,
        complete=commit_authors_complete,
    )
    independence = classify_independence(relation, contribution["status"])

    reviews_raw = evidence["reviews_raw"]
    issue_comments_raw = evidence["issue_comments_raw"]
    review_comments_raw = evidence["review_comments_raw"]
    timeline_raw = evidence["timeline_raw"]
    threads, threads_complete = evidence["threads"]
    reviews = [normalize_review(review, head_sha) for review in reviews_raw]
    issue_comments = [normalize_issue_comment(comment) for comment in issue_comments_raw]
    review_comments = [
        normalize_review_comment(comment, head_sha) for comment in review_comments_raw
    ]
    timeline = [normalize_timeline_event(item) for item in timeline_raw]
    request_context = review_request_context(
        timeline,
        authenticated,
        creator,
    )

    return {
        "snapshot_version": 2,
        "capture_started_at": started_at,
        "captured_at": datetime.now(UTC).isoformat(),
        "repository": repo,
        "pull_request": {
            "number": number,
            "url": pull.get("html_url"),
            "state": pull.get("state"),
            "merged": pull.get("merged"),
            "merged_at": pull.get("merged_at"),
            "closed_at": pull.get("closed_at"),
            "draft": pull.get("draft"),
            "title": pull.get("title"),
            "body": pull_body,
            "updated_at": pull.get("updated_at"),
            "statistics": {
                "commits": expected_commits,
                "changed_files": pull.get("changed_files"),
            },
            "body_metadata": body_metadata(
                pull_body,
                (pull.get("base") or {}).get("ref"),
                pull.get("commits"),
                pull.get("changed_files"),
            ),
            "viewer_can_update": viewer_can_update,
            "creator": creator,
            "base": {
                "ref": (pull.get("base") or {}).get("ref"),
                "sha": (pull.get("base") or {}).get("sha"),
                "repo": ((pull.get("base") or {}).get("repo") or {}).get("full_name"),
            },
            "head": {
                "ref": (pull.get("head") or {}).get("ref"),
                "sha": head_sha,
                "repo": ((pull.get("head") or {}).get("repo") or {}).get("full_name"),
                "maintainer_can_modify": pull.get("maintainer_can_modify"),
            },
        },
        "identity": {
            "authenticated_actor": authenticated,
            "pr_relation": relation,
            "contribution": contribution,
            "independence": independence,
            "publication_route": publication_route(relation),
            "review_request": request_context,
        },
        "commit_authors": commit_records,
        "feedback": {
            "formal_reviews": reviews,
            "latest_formal_review_by_actor": latest_reviews_by_actor(reviews),
            "issue_comments": issue_comments,
            "review_comments": review_comments,
            "review_threads": threads,
            "timeline": timeline,
        },
        "completeness": {
            "commit_pages_exhausted": commit_authors_complete,
            "formal_reviews_paginated": True,
            "issue_comments_paginated": True,
            "review_comments_paginated": True,
            "timeline_paginated": True,
            "review_threads_paginated": threads_complete,
            "exact_head_and_scope_stable": True,
            "feedback_lifecycle_stable": True,
            "commit_count_complete": True,
            "snapshot_consistent": True,
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Capture deterministic GitHub PR identity and feedback evidence."
    )
    result.add_argument("--repo", required=True, help="OWNER/NAME")
    result.add_argument("--pr", required=True, type=int)
    result.add_argument("--compact", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        snapshot = build_snapshot(args.repo, args.pr)
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
