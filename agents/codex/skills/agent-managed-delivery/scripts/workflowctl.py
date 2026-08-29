#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TRANSITIONS: dict[str, list[str]] = {
    "CANDIDATE": ["CLAIMED", "SERIOUSLY_BLOCKED"],
    "CLAIMED": ["EXPLORING", "SERIOUSLY_BLOCKED"],
    "EXPLORING": ["DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "DEVELOPING": ["SELF_TESTING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "SELF_TESTING": ["IMPLEMENTATION_READY_FOR_DOCS", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "IMPLEMENTATION_READY_FOR_DOCS": ["DOCUMENTING", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "DOCUMENTING": ["PR_CREATING", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "PR_CREATING": ["CI_PENDING", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "CI_PENDING": ["REVIEW_REQUESTED", "FIXING_CI", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "FIXING_CI": ["SELF_TESTING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "REVIEW_REQUESTED": ["REVIEWING", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "REVIEWING": ["FIXING_REVIEW", "MERGE_READY", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "FIXING_REVIEW": ["SELF_TESTING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "MERGE_READY": ["MERGING", "REVIEWING", "DEVELOPING", "SCOPE_BLOCKED", "SERIOUSLY_BLOCKED"],
    "MERGING": ["MERGED", "SERIOUSLY_BLOCKED"],
    "MERGED": ["VERIFYING_DEVELOP", "SERIOUSLY_BLOCKED"],
    "VERIFYING_DEVELOP": ["POST_MERGE_MEMORY", "SERIOUSLY_BLOCKED"],
    "POST_MERGE_MEMORY": ["COMPLETED", "SERIOUSLY_BLOCKED"],
    "SCOPE_BLOCKED": ["EXPLORING", "SERIOUSLY_BLOCKED"],
    "COMPLETED": [],
    "SERIOUSLY_BLOCKED": [],
}
TERMINAL = {"COMPLETED", "SERIOUSLY_BLOCKED"}

FINDING_CATEGORIES = {
    "IN_SCOPE_DEFECT",
    "PREDECESSOR_DEFECT",
    "UNMERGED_DEPENDENCY",
    "FUTURE_WBS_GAP",
    "WBS_AMBIGUITY",
    "HARDENING_SUGGESTION",
    "NOT_REPRODUCIBLE",
    "ALREADY_FIXED",
    "INVALID",
}
SCOPE_BLOCKING_CATEGORIES = {
    "PREDECESSOR_DEFECT",
    "UNMERGED_DEPENDENCY",
    "WBS_AMBIGUITY",
}
SEVERE_CROSS_TASK_CATEGORIES = {"FUTURE_WBS_GAP"}
NO_LIVE_DEFECT_CATEGORIES = {"NOT_REPRODUCIBLE", "ALREADY_FIXED", "INVALID"}
FINDING_SEVERITIES = {"P0", "P1", "P2", "P3", "P4", "NA"}
LATE_REVIEW_BLOCKING_SEVERITIES = {"P0", "P1"}
LATE_REVIEW_START_ROUND = 4


class WorkflowError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(UTC).isoformat()


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode:
        raise WorkflowError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode:
        raise WorkflowError("Run workflowctl inside a Git repository.")
    return Path(result.stdout.strip()).resolve()


def state_path(root: Path) -> Path:
    raw = Path(git(root, "rev-parse", "--git-common-dir"))
    common = raw if raw.is_absolute() else root / raw
    return common.resolve() / "agent-managed-delivery" / "state.json"


def load(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.is_file():
        raise WorkflowError(f"Missing runtime state: {path}; run init first.")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read runtime state: {exc}") from exc
    if state.get("schema_version") != 1:
        raise WorkflowError(f"Unsupported schema_version={state.get('schema_version')!r}")
    return state


def save(root: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now()
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def head(root: Path) -> str:
    return git(root, "rev-parse", "HEAD")


def branch(root: Path) -> str:
    return git(root, "branch", "--show-current")


def event(task: dict[str, Any], kind: str, **data: Any) -> None:
    task.setdefault("events", []).append({"at": now(), "kind": kind, **data})


def active(state: dict[str, Any]) -> dict[str, Any]:
    task_id = state.get("active_task_id")
    task = state.get("tasks", {}).get(task_id)
    if not isinstance(task, dict):
        raise WorkflowError("No active task.")
    return task


def assert_task_binding(root: Path, task: dict[str, Any], *, require_head: bool = True) -> None:
    current_branch = branch(root)
    if current_branch != task.get("branch"):
        raise WorkflowError(
            f"Active task is bound to branch {task.get('branch')}, not {current_branch or '(detached)'}"
        )
    if require_head and head(root) != task.get("head_sha"):
        raise WorkflowError("Current HEAD differs from runtime; run sync-head in the task worktree.")


def exact_pass(record: Any, current_head: str) -> bool:
    return isinstance(record, dict) and record.get("status") == "PASS" and record.get("head_sha") == current_head


def scope_revision(task: dict[str, Any]) -> int | None:
    scope = task.get("scope")
    if not isinstance(scope, dict):
        return None
    revision = scope.get("revision")
    return revision if isinstance(revision, int) and revision > 0 else None


def exact_scope_pass(task: dict[str, Any]) -> bool:
    check = task.get("scope_check")
    revision = scope_revision(task)
    return (
        isinstance(check, dict)
        and check.get("status") == "PASS"
        and check.get("head_sha") == task.get("head_sha")
        and check.get("scope_revision") == revision
    )


def valid_repo_pattern(pattern: str) -> bool:
    candidate = Path(pattern)
    return bool(pattern.strip()) and not candidate.is_absolute() and ".." not in candidate.parts


def path_allowed(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern)
        or (pattern.endswith("/") and path.startswith(pattern))
        for pattern in patterns
    )


def changed_paths(root: Path, baseline_head: str, current_head: str) -> list[str]:
    if baseline_head == current_head:
        return []
    output = git(root, "diff", "--name-only", f"{baseline_head}..{current_head}")
    return [line for line in output.splitlines() if line]


def validated_baseline(root: Path, raw: str, current_head: str) -> str:
    candidate = raw.strip()
    if len(candidate) != 40 or any(character not in "0123456789abcdefABCDEF" for character in candidate):
        raise WorkflowError("Legacy scope baseline must be a full 40-character commit SHA.")
    resolved = git(root, "rev-parse", "--verify", f"{candidate}^{{commit}}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", resolved, current_head],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if ancestor.returncode != 0:
        raise WorkflowError("Legacy scope baseline must be an ancestor of the current HEAD.")
    return resolved


def parse_dependency(raw: str) -> dict[str, str]:
    task_id, separator, status = raw.partition("::")
    if not separator or not task_id.strip() or not status.strip():
        raise WorkflowError("Each dependency must use TASK-ID::STATUS.")
    return {"task_id": task_id.strip(), "status": status.strip()}


def parse_finding(raw: str) -> dict[str, str]:
    try:
        finding = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid finding JSON: {exc}") from exc
    if not isinstance(finding, dict):
        raise WorkflowError("Each finding must be a JSON object.")
    required = ("id", "category", "severity", "summary", "reproduction", "scope_basis")
    normalized: dict[str, str] = {}
    for key in required:
        value = finding.get(key)
        if not isinstance(value, str) or not value.strip():
            raise WorkflowError(f"Finding field {key!r} must be a non-empty string.")
        normalized[key] = value.strip()
    if normalized["category"] not in FINDING_CATEGORIES:
        raise WorkflowError(
            f"Unsupported finding category {normalized['category']!r}; "
            f"choose from {sorted(FINDING_CATEGORIES)}"
        )
    if normalized["severity"] not in FINDING_SEVERITIES:
        raise WorkflowError(
            f"Unsupported finding severity {normalized['severity']!r}; "
            f"choose from {sorted(FINDING_SEVERITIES)}"
        )
    category = normalized["category"]
    severity = normalized["severity"]
    if category in NO_LIVE_DEFECT_CATEGORIES and severity != "NA":
        raise WorkflowError(f"{category} requires severity NA because no live defect remains.")
    if category not in NO_LIVE_DEFECT_CATEGORIES and severity == "NA":
        raise WorkflowError(f"{category} requires a P0-P4 severity.")
    if category == "HARDENING_SUGGESTION" and severity in {"P0", "P1"}:
        raise WorkflowError(
            "HARDENING_SUGGESTION cannot be P0/P1; classify the blocking owner instead."
        )
    source = finding.get("source", "")
    if source:
        if not isinstance(source, str):
            raise WorkflowError("Finding field 'source' must be a string when provided.")
        normalized["source"] = source.strip()
    return normalized


def finding_counts(findings: list[dict[str, str]]) -> dict[str, int]:
    counts = {category: 0 for category in sorted(FINDING_CATEGORIES)}
    for finding in findings:
        counts[finding["category"]] += 1
    return counts


def severity_counts(findings: list[dict[str, str]]) -> dict[str, int]:
    counts = {severity: 0 for severity in sorted(FINDING_SEVERITIES)}
    for finding in findings:
        counts[finding["severity"]] += 1
    return counts


def severity_is_blocking(severity: str, review_round: int) -> bool:
    return (
        review_round < LATE_REVIEW_START_ROUND
        or severity in LATE_REVIEW_BLOCKING_SEVERITIES
    )


def finding_is_blocking(finding: dict[str, str], review_round: int) -> bool:
    return finding["category"] == "IN_SCOPE_DEFECT" and severity_is_blocking(
        finding["severity"], review_round
    )


def finding_is_scope_blocking(finding: dict[str, str], review_round: int) -> bool:
    if finding["category"] in SEVERE_CROSS_TASK_CATEGORIES:
        return finding["severity"] in LATE_REVIEW_BLOCKING_SEVERITIES
    return finding["category"] in SCOPE_BLOCKING_CATEGORIES and severity_is_blocking(
        finding["severity"], review_round
    )


def triage_in_scope_blockers(triage: Any) -> int:
    if not isinstance(triage, dict):
        return 0
    explicit = triage.get("in_scope_blocking_findings")
    if isinstance(explicit, int) and explicit >= 0:
        return explicit
    counts = triage.get("category_counts")
    if not isinstance(counts, dict):
        return 0
    # Backward-compatible read for runtimes created before severity-aware triage.
    return int(counts.get("IN_SCOPE_DEFECT", 0))


def latest_review_round(task: dict[str, Any]) -> int:
    rounds: list[int] = []
    for record_name in ("review_triage", "review"):
        record = task.get(record_name)
        if isinstance(record, dict) and isinstance(record.get("round"), int):
            rounds.append(record["round"])
    for item in task.get("events", []):
        if (
            isinstance(item, dict)
            and item.get("kind") in {"review_triage", "review"}
            and isinstance(item.get("round"), int)
        ):
            rounds.append(item["round"])
    for item in task.get("review_triage_history", []):
        if isinstance(item, dict) and isinstance(item.get("round"), int):
            rounds.append(item["round"])
    return max(rounds, default=0)


def triage_scope_blockers(triage: Any) -> int:
    if not isinstance(triage, dict):
        return 0
    explicit = triage.get("scope_blocking_findings")
    if isinstance(explicit, int) and explicit >= 0:
        return explicit
    counts = triage.get("category_counts")
    if not isinstance(counts, dict):
        return 0
    return sum(int(counts.get(category, 0)) for category in SCOPE_BLOCKING_CATEGORIES)


def exact_triage(task: dict[str, Any]) -> dict[str, Any] | None:
    triage = task.get("review_triage")
    if not isinstance(triage, dict):
        return None
    if (
        triage.get("head_sha") != task.get("head_sha")
        or triage.get("scope_revision") != scope_revision(task)
    ):
        return None
    return triage


def exact_review_fix_record(task: dict[str, Any]) -> bool:
    record = task.get("review_fix_record")
    authorization = task.get("review_fix_authorization")
    return (
        isinstance(record, dict)
        and isinstance(authorization, dict)
        and authorization.get("status") == "RECORDED"
        and record.get("repair_head_sha") == task.get("head_sha")
        and record.get("scope_revision") == scope_revision(task)
        and set(record.get("resolved_finding_ids", []))
        == set(authorization.get("authorized_finding_ids", []))
    )


def invalidate(task: dict[str, Any], new_head: str) -> None:
    old = task.get("head_sha")
    task["head_sha"] = new_head
    if old and old != new_head:
        authorization = task.get("review_fix_authorization")
        if isinstance(authorization, dict):
            if authorization.get("status") in {"AUTHORIZED", "PENDING_RECORD", "RECORDED"}:
                authorization["status"] = "PENDING_RECORD"
                authorization["repair_head_sha"] = new_head
                authorization["updated_at"] = now()
                task["review_fix_record"] = None
        for key in (
            "scope_check",
            "review_triage",
            "self_test",
            "docs_gate",
            "task_report",
            "create_pr_approval",
            "pr",
            "ci",
            "review",
            "merge_approval",
            "merge",
        ):
            task[key] = None
        event(task, "head_changed", old_head=old, head_sha=new_head)


def delegated_authorized(state: dict[str, Any], task: dict[str, Any], action: str) -> bool:
    auth = state["authorization"]
    return (
        auth["mode"] == "DELEGATED_BATCH"
        and not auth.get("revoked", False)
        and task["task_id"] in auth.get("task_ids", [])
        and auth.get(action) is True
    )


def action_authorized(state: dict[str, Any], task: dict[str, Any], action: str) -> bool:
    if delegated_authorized(state, task, action):
        return True
    key = "create_pr_approval" if action == "create_pr" else "merge_approval"
    approval = task.get(key)
    return isinstance(approval, dict) and approval.get("head_sha") == task.get("head_sha")


def exact_pr_metadata_pass(pr: Any, current_head: str) -> bool:
    if not isinstance(pr, dict):
        return False
    metadata = pr.get("metadata")
    return (
        isinstance(metadata, dict)
        and metadata.get("status") in {"PASS", "NOT_REQUIRED"}
        and metadata.get("head_sha") == current_head
        and bool(str(metadata.get("evidence") or "").strip())
    )


def gate_errors(state: dict[str, Any], task: dict[str, Any], gate: str) -> list[str]:
    current = str(task.get("head_sha", ""))
    errors: list[str] = []
    if gate in {"create_pr", "review", "merge"} and not exact_scope_pass(task):
        errors.append("exact-HEAD scope check is not PASS for the active scope revision")
    if gate in {"create_pr", "merge"}:
        if not exact_pass(task.get("self_test"), current):
            errors.append("exact-HEAD self-test is not PASS")
        if not exact_pass(task.get("docs_gate"), current):
            errors.append("exact-HEAD docs gate is not PASS")
        if not str(task.get("task_report") or "").strip():
            errors.append("task report is empty")
    if gate == "create_pr":
        if not isinstance(task.get("pr_identity"), dict) and not action_authorized(
            state, task, "create_pr"
        ):
            errors.append("create-PR authorization is missing for this mode/task/HEAD")
    if gate == "review":
        pr = task.get("pr")
        if not isinstance(pr, dict) or pr.get("head_sha") != current:
            errors.append("Ready PR is not bound to the exact HEAD")
        elif pr.get("template_complete") is not True or pr.get("base") != state["repository"]["base"]:
            errors.append("PR template/base gate failed")
        elif not exact_pr_metadata_pass(pr, current):
            errors.append("repository-required PR body metadata is not verified for the exact HEAD")
        elif pr.get("mergeable") != "MERGEABLE" or pr.get("source") != "github-live":
            errors.append("PR is not a live, conflict-free GitHub observation")
        if not exact_pass(task.get("ci"), current):
            errors.append("exact-HEAD required CI is not PASS")
        elif task["ci"].get("source") != "github-live":
            errors.append("CI PASS is not from a live GitHub observation")
    if gate == "merge":
        errors.extend(gate_errors(state, task, "review"))
        triage = exact_triage(task)
        if triage is None:
            errors.append("exact-HEAD review triage is missing")
        elif triage_scope_blockers(triage):
            errors.append("review triage contains unresolved scope blockers")
        review = task.get("review")
        if not isinstance(review, dict) or review.get("head_sha") != current:
            errors.append("exact-HEAD review comment is missing")
        elif (
            review.get("verdict") != "APPROVED_FOR_MERGE_BY_COMMENT"
            or review.get("in_scope_blocking_findings") != 0
        ):
            errors.append("review is not approved with zero blocking findings")
        if not action_authorized(state, task, "merge"):
            errors.append("merge authorization is missing for this mode/task/HEAD")
    if gate == "complete":
        if not isinstance(task.get("develop_verified"), dict):
            errors.append("remote base merge verification is missing")
        memory = task.get("memory_gate")
        if not isinstance(memory, dict) or memory.get("status") != "PASS":
            errors.append("memory gate is not PASS")
        elif not memory.get("files") or not memory.get("summary") or memory.get("secrets_check") != "PASS":
            errors.append("memory files, durable summary, or secrets check is incomplete")
    return errors


def cmd_init(args: argparse.Namespace, root: Path) -> None:
    if state_path(root).exists():
        raise WorkflowError(f"Runtime already exists: {state_path(root)}")
    if args.mode == "DELEGATED_BATCH" and (not args.task or not args.evidence.strip()):
        raise WorkflowError("Delegated mode requires exact --task entries and non-empty --evidence.")
    if args.mode == "DELEGATED_BATCH" and not (
        args.delegate_create_pr and args.delegate_merge
    ):
        raise WorkflowError(
            "DELEGATED_BATCH requires explicit PR-creation and merge delegation; use SUPERVISED otherwise."
        )
    tasks: dict[str, Any] = {}
    for raw in args.task:
        task_id, separator, title = raw.partition("::")
        if not task_id.strip() or not separator or not title.strip():
            raise WorkflowError("Each --task must use TASK-ID::Title.")
        if task_id in tasks:
            raise WorkflowError(f"Duplicate task ID: {task_id}")
        tasks[task_id] = {"task_id": task_id, "title": title, "state": "CANDIDATE", "events": []}
    state = {
        "schema_version": 1,
        "batch_id": args.batch_id,
        "repository": {"root": str(root), "remote": args.remote, "base": args.base},
        "authorization": {
            "mode": args.mode,
            "task_ids": sorted(tasks),
            "create_pr": args.delegate_create_pr,
            "merge": args.delegate_merge,
            "evidence": args.evidence.strip(),
            "granted_at": now(),
            "revoked": False,
        },
        "active_task_id": None,
        "tasks": tasks,
        "updated_at": now(),
    }
    save(root, state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def cmd_candidate(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    if args.task_id in state["tasks"]:
        raise WorkflowError(f"Task already exists: {args.task_id}")
    if state["authorization"]["mode"] == "DELEGATED_BATCH":
        raise WorkflowError("Cannot expand a delegated batch after authorization.")
    state["tasks"][args.task_id] = {"task_id": args.task_id, "title": args.title, "state": "CANDIDATE", "events": []}
    save(root, state)


def cmd_claim(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    current_active = state.get("active_task_id")
    if current_active:
        prior = state["tasks"][current_active]
        if prior.get("state") not in TERMINAL:
            raise WorkflowError(f"Active task is not terminal: {current_active}={prior.get('state')}")
    task = state["tasks"].get(args.task_id)
    if not isinstance(task, dict) or task.get("state") != "CANDIDATE":
        raise WorkflowError("Task must exist in CANDIDATE state.")
    if not args.evidence.strip():
        raise WorkflowError("Claim evidence must be non-empty.")
    if state["authorization"]["mode"] == "DELEGATED_BATCH" and args.task_id not in state["authorization"]["task_ids"]:
        raise WorkflowError("Task is outside delegated batch scope.")
    current_branch = branch(root)
    if not current_branch or current_branch in {state["repository"]["base"], "main", "master"}:
        raise WorkflowError("Claim from a dedicated task branch/worktree, not a protected base branch.")
    task.update({
        "state": "CLAIMED", "branch": current_branch, "head_sha": head(root), "claim_evidence": args.evidence.strip(),
        "scope": None, "scope_history": [], "scope_check": None, "scope_blocker": None,
        "scope_change_approval": None, "review_triage": None,
        "review_triage_history": [], "review_fix_authorization": None,
        "review_fix_record": None, "review_fix_history": [],
        "self_test": None, "docs_gate": None, "task_report": None, "create_pr_approval": None,
        "pr_identity": None, "pr": None, "ci": None, "review": None,
        "merge_approval": None, "merge": None,
        "develop_verified": None, "memory_gate": None,
    })
    event(task, "claimed", evidence=args.evidence.strip())
    state["active_task_id"] = args.task_id
    save(root, state)


def scope_payload(
    args: argparse.Namespace,
    task: dict[str, Any],
    *,
    revision: int,
    baseline_head_sha: str,
) -> dict[str, Any]:
    required_text = {
        "wbs_source": args.wbs_source,
        "independent_output": args.independent_output,
        "acceptance": args.acceptance,
        "test_requirement": args.test_requirement,
        "evidence": args.evidence,
    }
    for key, value in required_text.items():
        if not value.strip():
            raise WorkflowError(f"Scope field {key!r} must be non-empty.")
    if not args.authoritative_input or not args.in_scope or not args.out_of_scope:
        raise WorkflowError(
            "Scope requires authoritative inputs, in-scope capabilities, and explicit exclusions."
        )
    if not args.allowed_path:
        raise WorkflowError("Scope requires at least one allowed repository path pattern.")
    allowed_paths = [value.strip() for value in args.allowed_path]
    invalid = [pattern for pattern in allowed_paths if not valid_repo_pattern(pattern)]
    if invalid:
        raise WorkflowError(f"Invalid allowed path patterns: {invalid}")
    dependencies = [parse_dependency(raw) for raw in args.dependency]
    return {
        "revision": revision,
        "task_id": task["task_id"],
        "baseline_head_sha": baseline_head_sha,
        "wbs_source": args.wbs_source.strip(),
        "independent_output": args.independent_output.strip(),
        "acceptance": args.acceptance.strip(),
        "test_requirement": args.test_requirement.strip(),
        "authoritative_inputs": [value.strip() for value in args.authoritative_input],
        "in_scope": [value.strip() for value in args.in_scope],
        "out_of_scope": [value.strip() for value in args.out_of_scope],
        "dependencies": dependencies,
        "allowed_paths": allowed_paths,
        "evidence": args.evidence.strip(),
        "recorded_at": now(),
    }


def cmd_scope_record(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "EXPLORING":
        raise WorkflowError("Record the initial scope only in EXPLORING.")
    if isinstance(task.get("scope"), dict):
        raise WorkflowError("Scope already exists; explicit user approval is required to change it.")
    task["scope"] = scope_payload(
        args,
        task,
        revision=1,
        baseline_head_sha=task["head_sha"],
    )
    task["scope_check"] = None
    event(task, "scope_recorded", revision=1, baseline_head_sha=task["head_sha"])
    save(root, state)


def cmd_scope_change(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "SCOPE_BLOCKED":
        raise WorkflowError("Change scope only from SCOPE_BLOCKED after a user decision.")
    old_scope = task.get("scope")
    if not args.approval_evidence.strip():
        raise WorkflowError("Scope change requires explicit user approval evidence.")
    current_head = head(root)
    if isinstance(old_scope, dict):
        if args.baseline_head:
            raise WorkflowError("Do not replace the baseline of an existing scope contract.")
        old_revision = scope_revision(task)
        if old_revision is None:
            raise WorkflowError("Current scope revision is invalid.")
        new_revision = old_revision + 1
        baseline_head_sha = str(old_scope["baseline_head_sha"])
        task.setdefault("scope_history", []).append(old_scope)
        event_kind = "scope_changed"
    else:
        if not args.baseline_head:
            raise WorkflowError(
                "A legacy task without scope requires --baseline-head with the original task baseline."
            )
        old_revision = None
        new_revision = 1
        baseline_head_sha = validated_baseline(root, args.baseline_head, current_head)
        task.setdefault("scope_history", [])
        event_kind = "legacy_scope_adopted"
    task["scope"] = scope_payload(
        args,
        task,
        revision=new_revision,
        baseline_head_sha=baseline_head_sha,
    )
    task["scope_change_approval"] = {
        "revision": new_revision,
        "evidence": args.approval_evidence.strip(),
        "at": now(),
    }
    for key in (
        "scope_check",
        "review_triage",
        "self_test",
        "docs_gate",
        "task_report",
        "create_pr_approval",
        "pr",
        "ci",
        "review",
        "merge_approval",
        "merge",
    ):
        task[key] = None
    task["review_fix_authorization"] = None
    task["review_fix_record"] = None
    task["scope_blocker"] = None
    old_state = task["state"]
    task["state"] = "EXPLORING"
    event(
        task,
        event_kind,
        old_revision=old_revision,
        revision=new_revision,
        baseline_head_sha=baseline_head_sha,
    )
    event(
        task,
        "transition",
        source=old_state,
        target="EXPLORING",
        reason="User-approved scope decision recorded",
    )
    save(root, state)


def cmd_scope_check(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task, require_head=False)
    current = head(root)
    invalidate(task, current)
    scope = task.get("scope")
    revision = scope_revision(task)
    if not isinstance(scope, dict) or revision is None:
        raise WorkflowError("Record the task scope before running a scope check.")
    if task["state"] in TERMINAL or task["state"] in {"MERGING", "MERGED", "VERIFYING_DEVELOP", "POST_MERGE_MEMORY"}:
        raise WorkflowError(f"Cannot record a scope check in {task['state']}.")
    if not args.evidence.strip():
        raise WorkflowError("Scope check evidence must be non-empty.")
    authorization = task.get("review_fix_authorization")
    if (
        isinstance(authorization, dict)
        and authorization.get("status") in {"AUTHORIZED", "PENDING_RECORD", "RECORDED"}
        and args.status == "PASS"
        and not exact_review_fix_record(task)
    ):
        raise WorkflowError(
            "Review repair must record the exact authorized finding IDs and changed capabilities "
            "before scope-check PASS."
        )
    paths = changed_paths(root, str(scope["baseline_head_sha"]), current)
    allowed_paths = list(scope.get("allowed_paths", []))
    outside = [path for path in paths if not path_allowed(path, allowed_paths)]
    if args.status == "PASS" and outside:
        raise WorkflowError(
            "Scope check cannot PASS with paths outside the approved scope: " + ", ".join(outside)
        )
    task["scope_check"] = {
        "status": args.status,
        "head_sha": current,
        "scope_revision": revision,
        "changed_paths": paths,
        "outside_allowed_paths": outside,
        "drift_triggers": [value.strip() for value in args.drift_trigger],
        "evidence": args.evidence.strip(),
        "at": now(),
    }
    event(
        task,
        "scope_check",
        status=args.status,
        head_sha=current,
        scope_revision=revision,
        outside_allowed_paths=len(outside),
        drift_triggers=len(args.drift_trigger),
    )
    save(root, state)


def cmd_sync_head(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task, require_head=False)
    invalidate(task, head(root))
    save(root, state)
    print(task["head_sha"])


def cmd_advance(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    source = task["state"]
    if args.to not in TRANSITIONS.get(source, []):
        raise WorkflowError(f"Illegal transition {source} -> {args.to}")
    if args.to in {"SERIOUSLY_BLOCKED", "SCOPE_BLOCKED", "MERGING"}:
        raise WorkflowError(f"Use the dedicated command for {args.to}.")
    if source == "SCOPE_BLOCKED" and args.to == "EXPLORING":
        raise WorkflowError("Use scope-change with explicit user approval to resume SCOPE_BLOCKED.")
    if source == "EXPLORING" and args.to == "DEVELOPING" and not exact_scope_pass(task):
        raise WorkflowError("Exploration requires an exact-HEAD PASS scope check before development.")
    if (
        source in {"DEVELOPING", "FIXING_CI", "FIXING_REVIEW"}
        and args.to == "SELF_TESTING"
        and not exact_scope_pass(task)
    ):
        raise WorkflowError("Run an exact-HEAD PASS scope check before self-testing.")
    if source == "FIXING_REVIEW" and args.to == "SELF_TESTING" and not exact_review_fix_record(task):
        raise WorkflowError("Record the exact authorized review-fix set before self-testing.")
    if args.to == "IMPLEMENTATION_READY_FOR_DOCS" and not exact_pass(task.get("self_test"), task["head_sha"]):
        raise WorkflowError("Self-test gate failed.")
    if args.to == "IMPLEMENTATION_READY_FOR_DOCS" and not exact_scope_pass(task):
        raise WorkflowError("Exact-HEAD scope check is not PASS.")
    checks: list[str] = []
    if args.to == "PR_CREATING":
        checks = gate_errors(state, task, "create_pr")
    elif args.to == "CI_PENDING":
        pr = task.get("pr")
        if not isinstance(pr, dict) or pr.get("head_sha") != task["head_sha"] or pr.get("draft") is True:
            checks = ["Ready PR is not bound to current HEAD"]
        elif not exact_pr_metadata_pass(pr, task["head_sha"]):
            checks = ["PR body metadata is not synchronized and read-back verified for current HEAD"]
    elif args.to == "REVIEW_REQUESTED":
        checks = gate_errors(state, task, "review")
    elif source == "REVIEWING" and args.to == "FIXING_REVIEW":
        triage = exact_triage(task)
        review = task.get("review")
        if triage is None:
            checks = ["exact-HEAD review triage is missing"]
        elif triage_scope_blockers(triage):
            checks = ["review contains scope blockers; use scope-block instead of fixing"]
        elif triage_in_scope_blockers(triage) <= 0:
            checks = ["FIXING_REVIEW requires at least one severity-eligible IN_SCOPE_DEFECT"]
        elif (
            not isinstance(review, dict)
            or review.get("head_sha") != task["head_sha"]
            or review.get("verdict") != "CHANGES_REQUIRED_BY_COMMENT"
        ):
            checks = ["exact-HEAD classified changes-required comment is missing"]
        else:
            authorization = task.get("review_fix_authorization")
            if (
                not isinstance(authorization, dict)
                or authorization.get("status") != "AUTHORIZED"
                or authorization.get("reviewed_head_sha") != task["head_sha"]
                or set(authorization.get("authorized_finding_ids", []))
                != set(triage.get("blocking_finding_ids", []))
            ):
                checks = ["review-fix authorization does not match the triaged blocking whitelist"]
    elif args.to == "MERGE_READY":
        checks = gate_errors(state, task, "merge")
    elif args.to == "MERGED" and not isinstance(task.get("merge"), dict):
        checks = ["merge record is missing"]
    elif args.to == "POST_MERGE_MEMORY" and not isinstance(task.get("develop_verified"), dict):
        checks = ["remote base verification is missing"]
    elif args.to == "COMPLETED":
        checks = gate_errors(state, task, "complete")
    if checks:
        raise WorkflowError("; ".join(checks))
    task["state"] = args.to
    event(task, "transition", source=source, target=args.to, reason=args.reason)
    save(root, state)


def cmd_record(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task, require_head=False)
    current = head(root)
    invalidate(task, current)
    allowed_states = {
        "self_test": {"SELF_TESTING"},
        "docs_gate": {"DOCUMENTING"},
        "ci": {"CI_PENDING", "FIXING_CI", "FIXING_REVIEW"},
    }
    if task["state"] not in allowed_states[args.kind]:
        raise WorkflowError(f"Cannot record {args.kind} in {task['state']}.")
    if not args.evidence.strip():
        raise WorkflowError("Evidence must be non-empty.")
    task[args.kind] = {
        "status": args.status,
        "head_sha": current,
        "evidence": args.evidence.strip(),
        "source": getattr(args, "source", "local-evidence"),
        "at": now(),
    }
    event(task, args.kind, status=args.status, head_sha=current)
    save(root, state)


def cmd_report(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "DOCUMENTING" or not args.summary.strip():
        raise WorkflowError("Record a non-empty report in DOCUMENTING.")
    task["task_report"] = args.summary.strip()
    event(task, "task_report", head_sha=task["head_sha"])
    save(root, state)


def cmd_approve(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    if state["authorization"]["mode"] != "SUPERVISED":
        raise WorkflowError("Per-action approval is only recorded in SUPERVISED mode.")
    task = active(state)
    assert_task_binding(root, task)
    if not args.evidence.strip():
        raise WorkflowError("Approval evidence must be non-empty.")
    if args.action == "create_pr":
        if task["state"] != "DOCUMENTING":
            raise WorkflowError("Create-PR approval is recorded only after the task report in DOCUMENTING.")
        current = task["head_sha"]
        if (
            not exact_pass(task.get("self_test"), current)
            or not exact_pass(task.get("docs_gate"), current)
            or not str(task.get("task_report") or "").strip()
        ):
            raise WorkflowError("Create-PR approval requires exact-HEAD tests, docs, and task report.")
    else:
        if task["state"] != "REVIEWING":
            raise WorkflowError("Merge approval is recorded only after review in REVIEWING.")
        review = task.get("review")
        triage = exact_triage(task)
        if (
            triage is None
            or triage_scope_blockers(triage) != 0
            or not isinstance(review, dict)
            or review.get("head_sha") != task["head_sha"]
            or review.get("verdict") != "APPROVED_FOR_MERGE_BY_COMMENT"
            or review.get("in_scope_blocking_findings") != 0
        ):
            raise WorkflowError("Merge approval requires an exact-HEAD approved review with zero blockers.")
    key = "create_pr_approval" if args.action == "create_pr" else "merge_approval"
    task[key] = {"head_sha": task["head_sha"], "evidence": args.evidence.strip(), "at": now()}
    event(task, key, head_sha=task["head_sha"])
    save(root, state)


def cmd_attach_pr(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] not in {"PR_CREATING", "CI_PENDING", "REVIEW_REQUESTED", "REVIEWING", "MERGE_READY"}:
        raise WorkflowError("Attach or refresh PR only after PR_CREATING and before merge.")
    if not args.metadata_evidence.strip():
        raise WorkflowError("PR metadata evidence must be non-empty.")
    identity = task.get("pr_identity")
    if isinstance(identity, dict):
        if identity.get("number") != args.number:
            raise WorkflowError(
                f"Task is already bound to PR #{identity.get('number')}; refusing PR #{args.number}."
            )
        if identity.get("url") != args.url or identity.get("base") != args.base:
            raise WorkflowError("Bound PR URL/base identity cannot be replaced or retargeted.")
    if not isinstance(identity, dict):
        task["pr_identity"] = {
            "number": args.number,
            "url": args.url,
            "base": args.base,
            "created_head_sha": head(root),
            "at": now(),
        }
        event(task, "pr_identity_bound", number=args.number, head_sha=head(root))
    task["pr"] = {
        "number": args.number, "url": args.url, "base": args.base, "head_sha": head(root),
        "draft": args.draft, "template_complete": args.template_complete,
        "mergeable": args.mergeable, "source": "github-live", "at": now(),
        "metadata": {
            "status": args.metadata_status,
            "head_sha": head(root),
            "evidence": args.metadata_evidence.strip(),
            "source": (
                "github-live-readback"
                if args.metadata_status == "PASS"
                else "repository-contract-audit"
            ),
            "at": now(),
        },
    }
    save(root, state)


def cmd_review_triage(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "REVIEWING":
        raise WorkflowError("Triage review findings only in REVIEWING.")
    if not exact_scope_pass(task):
        raise WorkflowError("Review triage requires an exact-HEAD PASS scope check.")
    if args.round <= 0:
        raise WorkflowError("Review round must be positive.")
    latest_round = latest_review_round(task)
    current_triage = exact_triage(task)
    review = task.get("review")
    replacing_unpublished_current_round = (
        current_triage is not None
        and current_triage.get("round") == args.round
        and not (
            isinstance(review, dict)
            and review.get("head_sha") == task.get("head_sha")
            and review.get("round") == args.round
        )
    )
    if not replacing_unpublished_current_round and args.round != latest_round + 1:
        raise WorkflowError(
            f"Review round must advance monotonically; expected {latest_round + 1}, got {args.round}."
        )
    replacement_reason = str(getattr(args, "replacement_reason", "") or "").strip()
    if replacing_unpublished_current_round and not replacement_reason:
        raise WorkflowError(
            "Replacing an unpublished triage in the same round requires --replacement-reason."
        )
    if not args.scope_audit_evidence.strip():
        raise WorkflowError("Review triage requires scope-audit evidence.")
    if args.round > 1 and not args.prior_round_delta.strip():
        raise WorkflowError("Review rounds after the first must explain the delta from the prior round.")
    if args.clean and args.finding_json:
        raise WorkflowError("A clean triage cannot include findings.")
    if not args.clean and not args.finding_json:
        raise WorkflowError("Use --clean or provide at least one --finding-json.")
    findings = [parse_finding(raw) for raw in args.finding_json]
    identifiers = [finding["id"] for finding in findings]
    if len(set(identifiers)) != len(identifiers):
        raise WorkflowError("Review finding IDs must be unique within a round.")
    counts = finding_counts(findings)
    severities = severity_counts(findings)
    blocking_ids = [
        finding["id"] for finding in findings if finding_is_blocking(finding, args.round)
    ]
    deferred_ids = [
        finding["id"]
        for finding in findings
        if finding["category"] == "IN_SCOPE_DEFECT"
        and not finding_is_blocking(finding, args.round)
    ]
    scope_blocking_ids = [
        finding["id"]
        for finding in findings
        if finding_is_scope_blocking(finding, args.round)
    ]
    deferred_scope_ids = [
        finding["id"]
        for finding in findings
        if finding["category"] in SCOPE_BLOCKING_CATEGORIES
        and finding["id"] not in scope_blocking_ids
    ]
    deferred_scope_category_counts = {
        category: sum(
            1
            for finding in findings
            if finding["id"] in deferred_scope_ids and finding["category"] == category
        )
        for category in sorted(SCOPE_BLOCKING_CATEGORIES)
    }
    triage_record = {
        "round": args.round,
        "head_sha": head(root),
        "scope_revision": scope_revision(task),
        "findings": findings,
        "category_counts": counts,
        "severity_counts": severities,
        "blocking_severities": (
            sorted(LATE_REVIEW_BLOCKING_SEVERITIES)
            if args.round >= LATE_REVIEW_START_ROUND
            else ["P0", "P1", "P2", "P3", "P4"]
        ),
        "in_scope_blocking_findings": len(blocking_ids),
        "blocking_finding_ids": blocking_ids,
        "deferred_non_blocking_findings": len(deferred_ids),
        "deferred_non_blocking_finding_ids": deferred_ids,
        "scope_blocking_findings": len(scope_blocking_ids),
        "scope_blocking_finding_ids": scope_blocking_ids,
        "deferred_scope_finding_ids": deferred_scope_ids,
        "deferred_scope_findings": len(deferred_scope_ids),
        "deferred_scope_category_counts": deferred_scope_category_counts,
        "scope_audit_evidence": args.scope_audit_evidence.strip(),
        "prior_round_delta": args.prior_round_delta.strip(),
        "drift_triggers": [value.strip() for value in args.drift_trigger],
        "replacement_reason": replacement_reason,
        "at": now(),
    }
    task["review_triage"] = triage_record
    task.setdefault("review_triage_history", []).append(triage_record)
    event(
        task,
        "review_triage",
        round=args.round,
        head_sha=head(root),
        in_scope_blocking=len(blocking_ids),
        deferred_non_blocking=len(deferred_ids),
        scope_blocking=task["review_triage"]["scope_blocking_findings"],
        finding_ids=identifiers,
        replacement_reason=replacement_reason,
    )
    save(root, state)


def cmd_review(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "REVIEWING":
        raise WorkflowError("Record review only in REVIEWING.")
    triage = exact_triage(task)
    if triage is None or triage.get("round") != args.round:
        raise WorkflowError("Publish a review only after exact-HEAD triage for the same round.")
    if triage_scope_blockers(triage):
        raise WorkflowError("Review contains scope blockers; use scope-block and request user direction.")
    expected_blocking = triage_in_scope_blockers(triage)
    blocking_ids = list(triage.get("blocking_finding_ids", []))
    if len(blocking_ids) != expected_blocking:
        raise WorkflowError(
            "Triage blocking ID whitelist is incomplete for the expected blocking count."
        )
    if args.blocking != expected_blocking:
        raise WorkflowError(
            f"Published blocking count {args.blocking} does not match triaged "
            f"severity-eligible IN_SCOPE_DEFECT count {expected_blocking}."
        )
    if args.verdict == "APPROVED_FOR_MERGE_BY_COMMENT" and expected_blocking != 0:
        raise WorkflowError("Approved review must have zero in-scope blocking findings.")
    if args.verdict == "CHANGES_REQUIRED_BY_COMMENT" and expected_blocking == 0:
        raise WorkflowError(
            "Changes-required review needs at least one severity-eligible IN_SCOPE_DEFECT."
        )
    if not args.evidence.strip():
        raise WorkflowError("Published review comment evidence must be non-empty.")
    task["review"] = {
        "verdict": args.verdict,
        "blocking_findings": expected_blocking,
        "in_scope_blocking_findings": expected_blocking,
        "category_counts": triage["category_counts"],
        "severity_counts": triage.get("severity_counts", {}),
        "blocking_severities": triage.get("blocking_severities", []),
        "deferred_non_blocking_findings": triage.get(
            "deferred_non_blocking_findings", 0
        ),
        "deferred_scope_findings": triage.get("deferred_scope_findings", 0),
        "deferred_scope_finding_ids": triage.get("deferred_scope_finding_ids", []),
        "deferred_scope_category_counts": triage.get(
            "deferred_scope_category_counts", {}
        ),
        "scope_revision": scope_revision(task),
        "round": args.round,
        "head_sha": head(root), "evidence": args.evidence.strip(), "source": "ordinary-pr-comment", "at": now(),
    }
    if args.verdict == "CHANGES_REQUIRED_BY_COMMENT":
        blocking_findings = [
            finding
            for finding in triage.get("findings", [])
            if finding.get("id") in blocking_ids
        ]
        task["review_fix_authorization"] = {
            "status": "AUTHORIZED",
            "round": args.round,
            "reviewed_head_sha": head(root),
            "scope_revision": scope_revision(task),
            "authorized_finding_ids": blocking_ids,
            "authorized_findings": blocking_findings,
            "repair_head_sha": None,
            "created_at": now(),
        }
        task["review_fix_record"] = None
    else:
        task["review_fix_authorization"] = None
        task["review_fix_record"] = None
    event(
        task,
        "review",
        verdict=args.verdict,
        round=args.round,
        head_sha=head(root),
        in_scope_blocking=expected_blocking,
    )
    save(root, state)


def cmd_review_fix_record(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task, require_head=False)
    if task["state"] not in {"FIXING_REVIEW", "FIXING_CI", "DEVELOPING"}:
        raise WorkflowError(
            "Record an active review repair only in FIXING_REVIEW, FIXING_CI, or DEVELOPING."
        )
    current = head(root)
    invalidate(task, current)
    authorization = task.get("review_fix_authorization")
    if not isinstance(authorization, dict) or authorization.get("status") != "PENDING_RECORD":
        raise WorkflowError("No pending severity-eligible review-fix authorization exists.")
    if authorization.get("repair_head_sha") != current:
        raise WorkflowError("Review-fix authorization is not bound to the current repair HEAD.")
    if authorization.get("scope_revision") != scope_revision(task):
        raise WorkflowError("Review-fix authorization belongs to another scope revision.")
    if authorization.get("reviewed_head_sha") == current:
        raise WorkflowError("Review fixes require a new HEAD after the changes-required review.")
    resolved_ids = [value.strip() for value in args.finding_id if value.strip()]
    if len(set(resolved_ids)) != len(resolved_ids):
        raise WorkflowError("Resolved review finding IDs must be unique.")
    expected_ids = list(authorization.get("authorized_finding_ids", []))
    if set(resolved_ids) != set(expected_ids):
        raise WorkflowError(
            "Resolved IDs must exactly equal the authorized blocking whitelist; "
            f"expected={sorted(expected_ids)}, got={sorted(resolved_ids)}."
        )
    capabilities = [value.strip() for value in args.changed_capability if value.strip()]
    if not capabilities or not args.evidence.strip():
        raise WorkflowError(
            "Review-fix record requires changed capabilities and non-empty scope evidence."
        )
    record = {
        "round": authorization["round"],
        "reviewed_head_sha": authorization["reviewed_head_sha"],
        "repair_head_sha": current,
        "scope_revision": scope_revision(task),
        "resolved_finding_ids": resolved_ids,
        "changed_capabilities": capabilities,
        "evidence": args.evidence.strip(),
        "at": now(),
    }
    authorization["status"] = "RECORDED"
    authorization["repair_head_sha"] = current
    authorization["recorded_at"] = record["at"]
    task["review_fix_record"] = record
    task.setdefault("review_fix_history", []).append(
        {**record, "authorized_findings": authorization.get("authorized_findings", [])}
    )
    event(
        task,
        "review_fix_recorded",
        round=authorization["round"],
        reviewed_head_sha=authorization["reviewed_head_sha"],
        repair_head_sha=current,
        resolved_finding_ids=resolved_ids,
    )
    save(root, state)


def cmd_begin_merge(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "MERGE_READY":
        raise WorkflowError("Task is not MERGE_READY.")
    errors = gate_errors(state, task, "merge")
    if errors:
        raise WorkflowError("; ".join(errors))
    task["state"] = "MERGING"
    event(task, "merge_started", head_sha=task["head_sha"])
    save(root, state)


def cmd_merge_record(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "MERGING":
        raise WorkflowError("Record merge only in MERGING.")
    task["merge"] = {"merge_sha": args.merge_sha, "reviewed_head_sha": task["head_sha"], "at": now()}
    save(root, state)


def cmd_develop_verified(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "VERIFYING_DEVELOP" or not args.evidence.strip():
        raise WorkflowError("Record remote base verification in VERIFYING_DEVELOP with evidence.")
    remote_ref = f"{state['repository']['remote']}/{state['repository']['base']}"
    git(root, "fetch", state["repository"]["remote"], state["repository"]["base"])
    actual_remote_sha = git(root, "rev-parse", remote_ref)
    if actual_remote_sha != args.remote_base_sha:
        raise WorkflowError(f"Recorded remote base SHA is stale; actual={actual_remote_sha}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", args.merge_sha, remote_ref], cwd=root, check=False
    )
    if ancestor.returncode != 0:
        raise WorkflowError(f"Merge commit is not an ancestor of {remote_ref}.")
    task["develop_verified"] = {"merge_sha": args.merge_sha, "remote_base_sha": args.remote_base_sha, "evidence": args.evidence.strip(), "at": now()}
    save(root, state)


def cmd_memory(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task)
    if task["state"] != "POST_MERGE_MEMORY":
        raise WorkflowError("Record memory only in POST_MERGE_MEMORY.")
    if args.status == "PASS" and (not args.file or not args.summary.strip() or args.secrets_check != "PASS"):
        raise WorkflowError("PASS requires memory files, durable summary, and secrets check PASS.")
    for raw in args.file:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts or not (root / path).is_file():
            raise WorkflowError(f"Invalid or missing project memory file: {raw}")
    task["memory_gate"] = {"status": args.status, "files": args.file, "summary": args.summary.strip(), "secrets_check": args.secrets_check, "at": now()}
    save(root, state)


def cmd_revoke(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    if not args.evidence.strip():
        raise WorkflowError("Revocation evidence must be non-empty.")
    state["authorization"]["previous_mode"] = state["authorization"]["mode"]
    state["authorization"]["mode"] = "SUPERVISED"
    state["authorization"]["revoked"] = True
    state["authorization"]["revocation_evidence"] = args.evidence.strip()
    state["authorization"]["revoked_at"] = now()
    save(root, state)


def cmd_scope_block(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task, require_head=False)
    current = head(root)
    invalidate(task, current)
    if task["state"] in TERMINAL or task["state"] in {
        "SCOPE_BLOCKED",
        "MERGING",
        "MERGED",
        "VERIFYING_DEVELOP",
        "POST_MERGE_MEMORY",
    }:
        raise WorkflowError(f"Cannot enter SCOPE_BLOCKED from {task['state']}.")
    if (
        not args.condition.strip()
        or not args.evidence
        or not args.investigation
        or not args.option
        or not args.required_action.strip()
    ):
        raise WorkflowError(
            "Scope block requires a condition, evidence, safe investigation, decision options, "
            "and required user action."
        )
    source = task["state"]
    if "SCOPE_BLOCKED" not in TRANSITIONS.get(source, []):
        raise WorkflowError(f"Illegal transition {source} -> SCOPE_BLOCKED")
    task["state"] = "SCOPE_BLOCKED"
    task["scope_blocker"] = {
        "condition": args.condition.strip(),
        "evidence": [value.strip() for value in args.evidence],
        "investigation": [value.strip() for value in args.investigation],
        "options": [value.strip() for value in args.option],
        "required_action": args.required_action.strip(),
        "source_state": source,
        "head_sha": current,
        "scope_revision": scope_revision(task),
        "at": now(),
    }
    event(
        task,
        "transition",
        source=source,
        target="SCOPE_BLOCKED",
        reason=args.condition.strip(),
    )
    save(root, state)


def cmd_block(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    task = active(state)
    assert_task_binding(root, task, require_head=False)
    if task["state"] in TERMINAL or not args.evidence or not args.attempt or not args.required_action.strip():
        raise WorkflowError("Block requires a non-terminal task, evidence, attempts, and required action.")
    task["state"] = "SERIOUSLY_BLOCKED"
    task["blocker"] = {"condition": args.condition, "evidence": args.evidence, "attempts": args.attempt, "required_action": args.required_action, "at": now()}
    save(root, state)


def cmd_status(args: argparse.Namespace, root: Path) -> None:
    print(json.dumps(load(root), ensure_ascii=False, indent=2))


def cmd_batch_status(args: argparse.Namespace, root: Path) -> None:
    state = load(root)
    statuses = {key: value["state"] for key, value in state["tasks"].items()}
    unfinished = {key: value for key, value in statuses.items() if value not in TERMINAL}
    print(json.dumps({"batch_id": state["batch_id"], "mode": state["authorization"]["mode"], "tasks": statuses, "unfinished": unfinished}, ensure_ascii=False, indent=2))
    if unfinished:
        raise SystemExit(2)


def add_scope_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--wbs-source", required=True)
    command.add_argument("--independent-output", required=True)
    command.add_argument("--acceptance", required=True)
    command.add_argument("--test-requirement", required=True)
    command.add_argument("--authoritative-input", action="append", default=[], required=True)
    command.add_argument("--in-scope", action="append", default=[], required=True)
    command.add_argument("--out-of-scope", action="append", default=[], required=True)
    command.add_argument("--dependency", action="append", default=[])
    command.add_argument("--allowed-path", action="append", default=[], required=True)
    command.add_argument("--evidence", required=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Reusable Agent managed delivery state controller")
    sub = result.add_subparsers(dest="command", required=True)
    command = sub.add_parser("init")
    command.add_argument("--batch-id", required=True)
    command.add_argument("--mode", choices=["SUPERVISED", "DELEGATED_BATCH"], required=True)
    command.add_argument("--remote", required=True)
    command.add_argument("--base", required=True)
    command.add_argument("--task", action="append", default=[])
    command.add_argument("--delegate-create-pr", action="store_true")
    command.add_argument("--delegate-merge", action="store_true")
    command.add_argument("--evidence", default="")
    command.set_defaults(func=cmd_init)
    command = sub.add_parser("candidate"); command.add_argument("--task-id", required=True); command.add_argument("--title", required=True); command.set_defaults(func=cmd_candidate)
    command = sub.add_parser("claim"); command.add_argument("--task-id", required=True); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_claim)
    command = sub.add_parser("scope-record"); add_scope_arguments(command); command.set_defaults(func=cmd_scope_record)
    command = sub.add_parser("scope-change"); add_scope_arguments(command); command.add_argument("--approval-evidence", required=True); command.add_argument("--baseline-head"); command.set_defaults(func=cmd_scope_change)
    command = sub.add_parser("scope-check"); command.add_argument("--status", choices=["PASS", "BLOCKED"], required=True); command.add_argument("--drift-trigger", action="append", default=[]); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_scope_check)
    command = sub.add_parser("sync-head"); command.set_defaults(func=cmd_sync_head)
    command = sub.add_parser("advance"); command.add_argument("--to", required=True); command.add_argument("--reason", default=""); command.set_defaults(func=cmd_advance)
    for name, kind, states in (("self-test", "self_test", ["PASS", "FAIL"]), ("docs-gate", "docs_gate", ["PASS", "FAIL"]), ("ci", "ci", ["PASS", "FAIL"])):
        command = sub.add_parser(name); command.add_argument("--status", choices=states, required=True); command.add_argument("--evidence", required=True)
        if name == "ci":
            command.add_argument("--source", choices=["github-live", "local-diagnostic"], default="github-live")
        command.set_defaults(func=cmd_record, kind=kind)
    command = sub.add_parser("report"); command.add_argument("--summary", required=True); command.set_defaults(func=cmd_report)
    command = sub.add_parser("approve"); command.add_argument("--action", choices=["create_pr", "merge"], required=True); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_approve)
    command = sub.add_parser("attach-pr"); command.add_argument("--number", type=int, required=True); command.add_argument("--url", required=True); command.add_argument("--base", required=True); command.add_argument("--draft", action="store_true"); command.add_argument("--template-complete", action="store_true"); command.add_argument("--mergeable", choices=["MERGEABLE", "CONFLICTING", "UNKNOWN"], required=True); command.add_argument("--metadata-status", choices=["PASS", "NOT_REQUIRED"], required=True); command.add_argument("--metadata-evidence", required=True); command.set_defaults(func=cmd_attach_pr)
    command = sub.add_parser("review-triage"); command.add_argument("--round", type=int, required=True); command.add_argument("--finding-json", action="append", default=[]); command.add_argument("--clean", action="store_true"); command.add_argument("--scope-audit-evidence", required=True); command.add_argument("--prior-round-delta", default=""); command.add_argument("--drift-trigger", action="append", default=[]); command.add_argument("--replacement-reason", default=""); command.set_defaults(func=cmd_review_triage)
    command = sub.add_parser("review"); command.add_argument("--verdict", choices=["CHANGES_REQUIRED_BY_COMMENT", "APPROVED_FOR_MERGE_BY_COMMENT"], required=True); command.add_argument("--blocking", type=int, required=True); command.add_argument("--round", type=int, required=True); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_review)
    command = sub.add_parser("review-fix-record"); command.add_argument("--finding-id", action="append", required=True); command.add_argument("--changed-capability", action="append", required=True); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_review_fix_record)
    command = sub.add_parser("begin-merge"); command.set_defaults(func=cmd_begin_merge)
    command = sub.add_parser("merge-record"); command.add_argument("--merge-sha", required=True); command.set_defaults(func=cmd_merge_record)
    command = sub.add_parser("develop-verified"); command.add_argument("--merge-sha", required=True); command.add_argument("--remote-base-sha", required=True); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_develop_verified)
    command = sub.add_parser("memory-gate"); command.add_argument("--status", choices=["PASS", "FAIL"], required=True); command.add_argument("--file", action="append", default=[]); command.add_argument("--summary", default=""); command.add_argument("--secrets-check", choices=["PASS", "FAIL"], default="FAIL"); command.set_defaults(func=cmd_memory)
    command = sub.add_parser("revoke-delegation"); command.add_argument("--evidence", required=True); command.set_defaults(func=cmd_revoke)
    command = sub.add_parser("scope-block"); command.add_argument("--condition", required=True); command.add_argument("--evidence", action="append", required=True); command.add_argument("--investigation", action="append", required=True); command.add_argument("--option", action="append", required=True); command.add_argument("--required-action", required=True); command.set_defaults(func=cmd_scope_block)
    command = sub.add_parser("block"); command.add_argument("--condition", required=True); command.add_argument("--evidence", action="append", required=True); command.add_argument("--attempt", action="append", required=True); command.add_argument("--required-action", required=True); command.set_defaults(func=cmd_block)
    command = sub.add_parser("status"); command.set_defaults(func=cmd_status)
    command = sub.add_parser("batch-status"); command.set_defaults(func=cmd_batch_status)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        root = repo_root()
        args.func(args, root)
        return 0
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
