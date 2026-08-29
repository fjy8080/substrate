#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("workflowctl.py")
SPEC = importlib.util.spec_from_file_location("workflowctl", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load workflowctl")
WORKFLOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORKFLOW)


def ready_task() -> dict:
    head = "a" * 40
    return {
        "task_id": "TASK-1",
        "head_sha": head,
        "scope": {
            "revision": 1,
            "baseline_head_sha": "0" * 40,
            "allowed_paths": ["src/**", "tests/**"],
        },
        "scope_check": {
            "status": "PASS",
            "head_sha": head,
            "scope_revision": 1,
        },
        "self_test": {"status": "PASS", "head_sha": head},
        "docs_gate": {"status": "PASS", "head_sha": head},
        "task_report": "complete report",
        "pr": {
            "number": 1,
            "head_sha": head,
            "base": "develop",
            "draft": False,
            "template_complete": True,
            "mergeable": "MERGEABLE",
            "source": "github-live",
            "metadata": {
                "status": "PASS",
                "head_sha": head,
                "evidence": "body read-back matches live base/commits/files",
            },
        },
        "ci": {"status": "PASS", "head_sha": head, "source": "github-live"},
        "review_triage": {
            "round": 1,
            "head_sha": head,
            "scope_revision": 1,
            "in_scope_blocking_findings": 0,
            "scope_blocking_findings": 0,
            "category_counts": {
                category: 0 for category in WORKFLOW.FINDING_CATEGORIES
            },
        },
        "review": {
            "verdict": "APPROVED_FOR_MERGE_BY_COMMENT",
            "blocking_findings": 0,
            "in_scope_blocking_findings": 0,
            "head_sha": head,
        },
    }


class WorkflowTests(unittest.TestCase):
    def run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_delegated_batch_authorizes_only_scoped_task(self) -> None:
        task = ready_task()
        state = {
            "repository": {"base": "develop"},
            "authorization": {
                "mode": "DELEGATED_BATCH",
                "task_ids": ["TASK-1"],
                "create_pr": True,
                "merge": True,
                "revoked": False,
            },
        }
        self.assertEqual(WORKFLOW.gate_errors(state, task, "create_pr"), [])
        self.assertEqual(WORKFLOW.gate_errors(state, task, "merge"), [])
        task["task_id"] = "TASK-2"
        self.assertTrue(WORKFLOW.gate_errors(state, task, "create_pr"))
        state["authorization"]["revoked"] = True
        task["task_id"] = "TASK-1"
        self.assertTrue(WORKFLOW.gate_errors(state, task, "merge"))

    def test_late_stage_head_changes_have_safe_revalidation_path(self) -> None:
        for state in (
            "IMPLEMENTATION_READY_FOR_DOCS",
            "DOCUMENTING",
            "PR_CREATING",
            "CI_PENDING",
            "REVIEW_REQUESTED",
            "REVIEWING",
            "MERGE_READY",
        ):
            self.assertIn("DEVELOPING", WORKFLOW.TRANSITIONS[state], state)

    def test_supervised_requires_two_exact_head_approvals(self) -> None:
        task = ready_task()
        state = {
            "repository": {"base": "develop"},
            "authorization": {"mode": "SUPERVISED", "task_ids": []},
        }
        self.assertTrue(WORKFLOW.gate_errors(state, task, "create_pr"))
        task["create_pr_approval"] = {"head_sha": task["head_sha"]}
        self.assertEqual(WORKFLOW.gate_errors(state, task, "create_pr"), [])
        self.assertTrue(WORKFLOW.gate_errors(state, task, "merge"))
        task["merge_approval"] = {"head_sha": task["head_sha"]}
        self.assertEqual(WORKFLOW.gate_errors(state, task, "merge"), [])

    def test_bound_pr_identity_does_not_consume_repeat_creation_approval(self) -> None:
        task = ready_task()
        task["pr_identity"] = {"number": 1, "url": "https://example.invalid/pr/1"}
        state = {
            "repository": {"base": "develop"},
            "authorization": {"mode": "SUPERVISED", "task_ids": []},
        }
        self.assertEqual(WORKFLOW.gate_errors(state, task, "create_pr"), [])

    def test_bound_pr_identity_rejects_url_or_base_replacement(self) -> None:
        task = ready_task()
        task.update({
            "state": "PR_CREATING",
            "branch": "feature/task",
            "pr_identity": {
                "number": 1,
                "url": "https://example.invalid/repo/pull/1",
                "base": "develop",
            },
        })
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(
            number=1,
            url="https://example.invalid/other/pull/1",
            base="develop",
            draft=False,
            template_complete=True,
            mergeable="MERGEABLE",
            metadata_status="PASS",
            metadata_evidence="read-back verified",
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "URL/base identity"):
                WORKFLOW.cmd_attach_pr(args, Path("."))

    def test_new_head_invalidates_report_and_all_head_evidence(self) -> None:
        task = ready_task()
        task["events"] = []
        task["pr_identity"] = {"number": 1, "url": "https://example.invalid/pr/1"}
        task["create_pr_approval"] = {"head_sha": task["head_sha"]}
        task["merge_approval"] = {"head_sha": task["head_sha"]}
        WORKFLOW.invalidate(task, "b" * 40)
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
            self.assertIsNone(task[key], key)
        self.assertEqual(task["scope"]["revision"], 1)
        self.assertEqual(task["pr_identity"]["number"], 1)

    def test_review_fix_whitelist_survives_repair_head_change(self) -> None:
        task = ready_task()
        task.update(
            {
                "state": "FIXING_REVIEW",
                "events": [],
                "review_fix_authorization": {
                    "status": "AUTHORIZED",
                    "round": 4,
                    "reviewed_head_sha": task["head_sha"],
                    "scope_revision": 1,
                    "authorized_finding_ids": ["F10"],
                },
                "review_fix_record": None,
            }
        )
        new_head = "b" * 40
        WORKFLOW.invalidate(task, new_head)
        self.assertEqual(task["review_fix_authorization"]["status"], "PENDING_RECORD")
        self.assertEqual(task["review_fix_authorization"]["repair_head_sha"], new_head)

    def test_extra_head_after_self_testing_reopens_review_fix_gate(self) -> None:
        task = ready_task()
        reviewed_head = "9" * 40
        repair_head = task["head_sha"]
        task.update(
            {
                "state": "SELF_TESTING",
                "branch": "feature/task",
                "events": [],
                "review_fix_authorization": {
                    "status": "RECORDED",
                    "round": 4,
                    "reviewed_head_sha": reviewed_head,
                    "repair_head_sha": repair_head,
                    "scope_revision": 1,
                    "authorized_finding_ids": ["F10"],
                },
                "review_fix_record": {
                    "reviewed_head_sha": reviewed_head,
                    "repair_head_sha": repair_head,
                    "scope_revision": 1,
                    "resolved_finding_ids": ["F10"],
                },
            }
        )
        extra_head = "b" * 40
        WORKFLOW.invalidate(task, extra_head)
        self.assertEqual(task["review_fix_authorization"]["status"], "PENDING_RECORD")
        self.assertFalse(WORKFLOW.exact_review_fix_record(task))
        task["state"] = "DEVELOPING"
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(status="PASS", evidence="attempted unrecorded extra head", drift_trigger=[])
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=extra_head),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "Review repair must record"):
                WORKFLOW.cmd_scope_check(args, Path("."))

    def test_review_gate_rejects_missing_or_stale_pr_metadata(self) -> None:
        task = ready_task()
        state = {
            "repository": {"base": "develop"},
            "authorization": {"mode": "SUPERVISED", "task_ids": []},
        }
        task["pr"]["metadata"] = None
        self.assertTrue(any("metadata" in item for item in WORKFLOW.gate_errors(state, task, "review")))
        task["pr"]["metadata"] = {
            "status": "PASS",
            "head_sha": "b" * 40,
            "evidence": "stale read-back",
        }
        self.assertTrue(any("metadata" in item for item in WORKFLOW.gate_errors(state, task, "review")))

    def test_not_required_metadata_needs_exact_head_evidence(self) -> None:
        task = ready_task()
        task["pr"]["metadata"] = {
            "status": "NOT_REQUIRED",
            "head_sha": task["head_sha"],
            "evidence": "repository has no dynamic PR body metadata validator",
        }
        self.assertTrue(WORKFLOW.exact_pr_metadata_pass(task["pr"], task["head_sha"]))

    def test_ci_pending_rejects_pr_without_exact_head_metadata(self) -> None:
        task = ready_task()
        task.update({"state": "PR_CREATING", "branch": "feature/task", "events": []})
        task["pr"]["metadata"] = None
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(to="CI_PENDING", reason="")
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "metadata"):
                WORKFLOW.cmd_advance(args, Path("."))

    def test_attach_pr_records_exact_head_metadata_evidence(self) -> None:
        task = ready_task()
        task.update({"state": "PR_CREATING", "branch": "feature/task", "events": []})
        task.pop("pr", None)
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(
            number=7,
            url="https://example.invalid/repo/pull/7",
            base="develop",
            draft=False,
            template_complete=True,
            mergeable="MERGEABLE",
            metadata_status="PASS",
            metadata_evidence="UPDATED and live body read back",
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=task["head_sha"]),
            patch.object(WORKFLOW, "save"),
        ):
            WORKFLOW.cmd_attach_pr(args, Path("."))

        self.assertEqual(task["pr"]["metadata"]["status"], "PASS")
        self.assertEqual(task["pr"]["metadata"]["head_sha"], task["head_sha"])

    def test_scope_gate_is_exact_head_and_revision_bound(self) -> None:
        task = ready_task()
        self.assertTrue(WORKFLOW.exact_scope_pass(task))
        task["scope_check"]["head_sha"] = "b" * 40
        self.assertFalse(WORKFLOW.exact_scope_pass(task))
        task["scope_check"]["head_sha"] = task["head_sha"]
        task["scope"]["revision"] = 2
        self.assertFalse(WORKFLOW.exact_scope_pass(task))

    def test_scope_patterns_reject_parent_escape_and_detect_drift(self) -> None:
        self.assertFalse(WORKFLOW.valid_repo_pattern("../outside/**"))
        self.assertFalse(WORKFLOW.valid_repo_pattern("/absolute/**"))
        self.assertTrue(WORKFLOW.valid_repo_pattern("backend/app/ai/stream/**"))
        patterns = ["backend/app/ai/stream/**", "backend/tests/**"]
        self.assertTrue(WORKFLOW.path_allowed("backend/app/ai/stream/handler.py", patterns))
        self.assertFalse(WORKFLOW.path_allowed("backend/app/ai/llm/adapter.py", patterns))

    def test_review_findings_are_classified_and_scope_blockers_do_not_merge(self) -> None:
        finding = WORKFLOW.parse_finding(
            '{"id":"F1","category":"PREDECESSOR_DEFECT",'
            '"severity":"P1",'
            '"summary":"adapter defect","reproduction":"focused test fails",'
            '"scope_basis":"belongs to TASK-0"}'
        )
        counts = WORKFLOW.finding_counts([finding])
        task = ready_task()
        task["review_triage"]["category_counts"] = counts
        task["review_triage"]["scope_blocking_findings"] = 1
        self.assertEqual(WORKFLOW.triage_scope_blockers(task["review_triage"]), 1)
        state = {
            "repository": {"base": "develop"},
            "authorization": {"mode": "SUPERVISED", "task_ids": []},
        }
        task["merge_approval"] = {"head_sha": task["head_sha"]}
        errors = WORKFLOW.gate_errors(state, task, "merge")
        self.assertTrue(any("scope blockers" in error for error in errors))

    def test_scope_blocker_cannot_be_published_as_review_verdict(self) -> None:
        task = ready_task()
        task["state"] = "REVIEWING"
        task["review_triage"]["category_counts"]["UNMERGED_DEPENDENCY"] = 1
        task["review_triage"]["scope_blocking_findings"] = 1
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(
            verdict="CHANGES_REQUIRED_BY_COMMENT",
            blocking=0,
            round=1,
            evidence="comment URL",
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "save"),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "scope blockers"):
                WORKFLOW.cmd_review(args, Path("."))

    def test_review_blocking_count_means_only_in_scope_defects(self) -> None:
        findings = [
            WORKFLOW.parse_finding(
                '{"id":"F1","category":"IN_SCOPE_DEFECT",'
                '"severity":"P1",'
                '"summary":"terminal order","reproduction":"state test fails",'
                '"scope_basis":"current WBS acceptance"}'
            ),
            WORKFLOW.parse_finding(
                '{"id":"F2","category":"FUTURE_WBS_GAP",'
                '"severity":"P2",'
                '"summary":"recovery assembly","reproduction":"not assembled",'
                '"scope_basis":"future TASK-2"}'
            ),
        ]
        counts = WORKFLOW.finding_counts(findings)
        self.assertEqual(counts["IN_SCOPE_DEFECT"], 1)
        self.assertEqual(counts["FUTURE_WBS_GAP"], 1)
        triage = {"category_counts": counts}
        self.assertEqual(WORKFLOW.triage_scope_blockers(triage), 0)

    def test_review_finding_requires_severity(self) -> None:
        with self.assertRaisesRegex(WORKFLOW.WorkflowError, "severity"):
            WORKFLOW.parse_finding(
                '{"id":"F1","category":"IN_SCOPE_DEFECT",'
                '"summary":"missing severity","reproduction":"test fails",'
                '"scope_basis":"current WBS acceptance"}'
            )

    def test_na_and_high_severity_category_combinations_are_fail_closed(self) -> None:
        with self.assertRaisesRegex(WORKFLOW.WorkflowError, "requires a P0-P4"):
            WORKFLOW.parse_finding(
                '{"id":"F1","category":"PREDECESSOR_DEFECT","severity":"NA",'
                '"summary":"predecessor issue","reproduction":"test fails",'
                '"scope_basis":"predecessor task"}'
            )
        with self.assertRaisesRegex(WORKFLOW.WorkflowError, "cannot be P0/P1"):
            WORKFLOW.parse_finding(
                '{"id":"F2","category":"HARDENING_SUGGESTION","severity":"P1",'
                '"summary":"misclassified blocker","reproduction":"core test fails",'
                '"scope_basis":"current task"}'
            )
        with self.assertRaisesRegex(WORKFLOW.WorkflowError, "requires severity NA"):
            WORKFLOW.parse_finding(
                '{"id":"F3","category":"INVALID","severity":"P3",'
                '"summary":"invalid claim","reproduction":"premise disproved",'
                '"scope_basis":"authoritative contract"}'
            )

    def test_round_four_only_p0_p1_findings_block(self) -> None:
        p1 = WORKFLOW.parse_finding(
            '{"id":"F1","category":"IN_SCOPE_DEFECT","severity":"P1",'
            '"summary":"critical regression","reproduction":"test fails",'
            '"scope_basis":"current WBS acceptance"}'
        )
        p2 = WORKFLOW.parse_finding(
            '{"id":"F2","category":"IN_SCOPE_DEFECT","severity":"P2",'
            '"summary":"bounded defect","reproduction":"edge case fails",'
            '"scope_basis":"current WBS acceptance"}'
        )
        self.assertTrue(WORKFLOW.finding_is_blocking(p2, 3))
        self.assertTrue(WORKFLOW.finding_is_blocking(p1, 4))
        self.assertFalse(WORKFLOW.finding_is_blocking(p2, 4))

    def test_round_four_low_severity_scope_observation_is_nonblocking(self) -> None:
        p1 = WORKFLOW.parse_finding(
            '{"id":"F1","category":"WBS_AMBIGUITY","severity":"P1",'
            '"summary":"acceptance owner unknown","reproduction":"WBS rows conflict",'
            '"scope_basis":"current and adjacent WBS rows"}'
        )
        p2 = WORKFLOW.parse_finding(
            '{"id":"F2","category":"PREDECESSOR_DEFECT","severity":"P2",'
            '"summary":"bounded predecessor issue","reproduction":"edge case fails",'
            '"scope_basis":"owned by predecessor TASK-0"}'
        )
        self.assertTrue(WORKFLOW.finding_is_scope_blocking(p2, 3))
        self.assertTrue(WORKFLOW.finding_is_scope_blocking(p1, 4))
        self.assertFalse(WORKFLOW.finding_is_scope_blocking(p2, 4))

    def test_severe_future_wbs_gap_requires_scope_decision(self) -> None:
        finding = WORKFLOW.parse_finding(
            '{"id":"F1","category":"FUTURE_WBS_GAP","severity":"P1",'
            '"summary":"future task blocks current acceptance",'
            '"reproduction":"core acceptance test fails",'
            '"scope_basis":"owned by future TASK-2"}'
        )
        self.assertTrue(WORKFLOW.finding_is_scope_blocking(finding, 1))
        self.assertTrue(WORKFLOW.finding_is_scope_blocking(finding, 4))

    def test_review_round_history_cannot_reset_after_head_invalidation(self) -> None:
        task = ready_task()
        task["events"] = [
            {"kind": "review_triage", "round": 1},
            {"kind": "review", "round": 1},
            {"kind": "review_triage", "round": 2},
            {"kind": "review", "round": 2},
            {"kind": "review_triage", "round": 3},
            {"kind": "review", "round": 3},
        ]
        task["review_triage"] = None
        task["review"] = None
        self.assertEqual(WORKFLOW.latest_review_round(task), 3)

    def test_round_four_triage_defers_p2_and_allows_approval(self) -> None:
        task = ready_task()
        task.update({"state": "REVIEWING", "branch": "feature/task"})
        task["events"] = [
            {"kind": kind, "round": review_round}
            for review_round in (1, 2, 3)
            for kind in ("review_triage", "review")
        ]
        task["review_triage"] = None
        task["review"] = None
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        triage_args = Namespace(
            round=4,
            clean=False,
            finding_json=[
                '{"id":"F9","category":"IN_SCOPE_DEFECT","severity":"P2",'
                '"summary":"bounded edge case","reproduction":"edge test fails",'
                '"scope_basis":"current task but not core acceptance"}'
            ],
            scope_audit_evidence="exact-HEAD P0/P1-focused audit",
            prior_round_delta="round 3 fixes verified",
            drift_trigger=[],
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=task["head_sha"]),
            patch.object(WORKFLOW, "save"),
        ):
            WORKFLOW.cmd_review_triage(triage_args, Path("."))
            self.assertEqual(task["review_triage"]["in_scope_blocking_findings"], 0)
            self.assertEqual(task["review_triage"]["deferred_non_blocking_findings"], 1)
            WORKFLOW.cmd_review(
                Namespace(
                    verdict="APPROVED_FOR_MERGE_BY_COMMENT",
                    blocking=0,
                    round=4,
                    evidence="ordinary comment URL",
                ),
                Path("."),
            )
        self.assertEqual(task["review"]["deferred_non_blocking_findings"], 1)

    def test_review_round_cannot_reset_after_three_cycles(self) -> None:
        task = ready_task()
        task.update({"state": "REVIEWING", "branch": "feature/task"})
        task["events"] = [
            {"kind": "review", "round": review_round} for review_round in (1, 2, 3)
        ]
        task["review_triage"] = None
        task["review"] = None
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(
            round=1,
            clean=True,
            finding_json=[],
            scope_audit_evidence="attempted reset",
            prior_round_delta="",
            drift_trigger=[],
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "expected 4"):
                WORKFLOW.cmd_review_triage(args, Path("."))

    def test_same_round_unpublished_triage_replacement_requires_reason(self) -> None:
        task = ready_task()
        task.update({"state": "REVIEWING", "branch": "feature/task", "events": []})
        task["review"] = None
        task["review_triage_history"] = []
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(
            round=1,
            clean=True,
            finding_json=[],
            scope_audit_evidence="corrected bounded audit",
            prior_round_delta="",
            drift_trigger=[],
            replacement_reason="",
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=task["head_sha"]),
            patch.object(WORKFLOW, "save"),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "replacement-reason"):
                WORKFLOW.cmd_review_triage(args, Path("."))
            args.replacement_reason = "fixed a transcription error before publication"
            WORKFLOW.cmd_review_triage(args, Path("."))
        self.assertEqual(len(task["review_triage_history"]), 1)
        self.assertEqual(task["review_triage"]["replacement_reason"], args.replacement_reason)

    def test_round_four_mixed_p1_p2_triage_dispatches_only_p1(self) -> None:
        task = ready_task()
        task.update({"state": "REVIEWING", "branch": "feature/task"})
        task["events"] = [
            {"kind": kind, "round": review_round}
            for review_round in (1, 2, 3)
            for kind in ("review_triage", "review")
        ]
        task["review_triage"] = None
        task["review"] = None
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        triage_args = Namespace(
            round=4,
            clean=False,
            finding_json=[
                '{"id":"F10","category":"IN_SCOPE_DEFECT","severity":"P1",'
                '"summary":"core regression","reproduction":"core test fails",'
                '"scope_basis":"current acceptance"}',
                '{"id":"F11","category":"IN_SCOPE_DEFECT","severity":"P2",'
                '"summary":"bounded edge case","reproduction":"edge test fails",'
                '"scope_basis":"current task but not core acceptance"}',
            ],
            scope_audit_evidence="exact-HEAD P0/P1-focused audit",
            prior_round_delta="round 3 fixes verified",
            drift_trigger=[],
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=task["head_sha"]),
            patch.object(WORKFLOW, "save"),
        ):
            WORKFLOW.cmd_review_triage(triage_args, Path("."))
            self.assertEqual(task["review_triage"]["blocking_finding_ids"], ["F10"])
            self.assertEqual(
                task["review_triage"]["deferred_non_blocking_finding_ids"], ["F11"]
            )
            WORKFLOW.cmd_review(
                Namespace(
                    verdict="CHANGES_REQUIRED_BY_COMMENT",
                    blocking=1,
                    round=4,
                    evidence="ordinary comment URL",
                ),
                Path("."),
            )
        self.assertEqual(task["review"]["blocking_findings"], 1)
        self.assertEqual(
            task["review_fix_authorization"]["authorized_finding_ids"], ["F10"]
        )

    def test_round_four_deferred_scope_finding_is_published_in_review_record(self) -> None:
        task = ready_task()
        task.update({"state": "REVIEWING", "branch": "feature/task"})
        task["events"] = [
            {"kind": "review", "round": review_round} for review_round in (1, 2, 3)
        ]
        task["review_triage"] = None
        task["review"] = None
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        args = Namespace(
            round=4,
            clean=False,
            finding_json=[
                '{"id":"F12","category":"PREDECESSOR_DEFECT","severity":"P2",'
                '"summary":"bounded predecessor edge","reproduction":"edge test fails",'
                '"scope_basis":"predecessor TASK-0"}'
            ],
            scope_audit_evidence="bounded scope audit",
            prior_round_delta="round 3 fixes verified",
            drift_trigger=[],
            replacement_reason="",
        )
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=task["head_sha"]),
            patch.object(WORKFLOW, "save"),
        ):
            WORKFLOW.cmd_review_triage(args, Path("."))
            WORKFLOW.cmd_review(
                Namespace(
                    verdict="APPROVED_FOR_MERGE_BY_COMMENT",
                    blocking=0,
                    round=4,
                    evidence="ordinary comment URL",
                ),
                Path("."),
            )
        self.assertEqual(task["review"]["deferred_scope_finding_ids"], ["F12"])
        self.assertEqual(
            task["review"]["deferred_scope_category_counts"]["PREDECESSOR_DEFECT"], 1
        )

    def test_review_fix_record_rejects_nonblocking_finding_id(self) -> None:
        task = ready_task()
        task.update({"state": "FIXING_REVIEW", "branch": "feature/task"})
        reviewed_head = task["head_sha"]
        task["events"] = []
        task["review_fix_authorization"] = {
            "status": "AUTHORIZED",
            "round": 4,
            "reviewed_head_sha": reviewed_head,
            "scope_revision": 1,
            "authorized_finding_ids": ["F10"],
            "authorized_findings": [
                {"id": "F10", "category": "IN_SCOPE_DEFECT", "severity": "P1"}
            ],
            "repair_head_sha": None,
        }
        task["review_fix_record"] = None
        task["review_fix_history"] = []
        state = {"tasks": {"TASK-1": task}, "active_task_id": "TASK-1"}
        new_head = "b" * 40
        with (
            patch.object(WORKFLOW, "load", return_value=state),
            patch.object(WORKFLOW, "assert_task_binding"),
            patch.object(WORKFLOW, "head", return_value=new_head),
            patch.object(WORKFLOW, "save"),
        ):
            with self.assertRaisesRegex(WORKFLOW.WorkflowError, "authorized blocking whitelist"):
                WORKFLOW.cmd_review_fix_record(
                    Namespace(
                        finding_id=["F10", "F11"],
                        changed_capability=["repair core state transition"],
                        evidence="diff maps only to F10 and approved scope",
                    ),
                    Path("."),
                )
            WORKFLOW.cmd_review_fix_record(
                Namespace(
                    finding_id=["F10"],
                    changed_capability=["repair core state transition"],
                    evidence="diff maps only to F10 and approved scope",
                ),
                Path("."),
            )
        self.assertTrue(WORKFLOW.exact_review_fix_record(task))
        self.assertEqual(task["review_fix_history"][0]["resolved_finding_ids"], ["F10"])

    def test_all_worktrees_share_private_git_common_state_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            linked = Path(directory) / "linked"
            root.mkdir()
            subprocess.run(["git", "init", "-b", "develop"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Workflow Test"], cwd=root, check=True)
            (root / "README.md").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "chore: baseline"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "worktree", "add", "-b", "feature/task", str(linked)], cwd=root, check=True, capture_output=True)
            self.assertEqual(WORKFLOW.state_path(root), WORKFLOW.state_path(linked))
            self.assertIn(".git/agent-managed-delivery/state.json", WORKFLOW.state_path(root).as_posix())

    def test_scope_drift_blocks_development_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-b", "develop"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Workflow Test"], cwd=root, check=True)
            (root / "README.md").write_text("baseline\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "chore: baseline"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "switch", "-c", "feature/task"], cwd=root, check=True, capture_output=True)

            commands = [
                ("init", "--batch-id", "scope-test", "--mode", "SUPERVISED", "--remote", "origin", "--base", "develop"),
                ("candidate", "--task-id", "TASK-1", "--title", "Scoped task"),
                ("claim", "--task-id", "TASK-1", "--evidence", "user claim"),
                ("advance", "--to", "EXPLORING"),
                (
                    "scope-record",
                    "--wbs-source", "WBS row",
                    "--independent-output", "stream handler",
                    "--acceptance", "terminal order",
                    "--test-requirement", "state tests",
                    "--authoritative-input", "system design section 4",
                    "--in-scope", "stream state machine",
                    "--out-of-scope", "adapter redesign",
                    "--allowed-path", "src/**",
                    "--evidence", "mapped from WBS",
                ),
                ("scope-check", "--status", "PASS", "--evidence", "no drift"),
                ("advance", "--to", "DEVELOPING"),
            ]
            for command in commands:
                result = self.run_cli(root, *command)
                self.assertEqual(result.returncode, 0, result.stderr)

            (root / "outside.txt").write_text("scope expansion\n", encoding="utf-8")
            subprocess.run(["git", "add", "outside.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "feat: expand scope"], cwd=root, check=True, capture_output=True)
            self.assertEqual(self.run_cli(root, "sync-head").returncode, 0)
            blocked = self.run_cli(
                root,
                "scope-check",
                "--status", "PASS",
                "--evidence", "should be rejected",
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("outside the approved scope", blocked.stderr)

            commands = [
                (
                    "scope-check", "--status", "BLOCKED",
                    "--drift-trigger", "outside path",
                    "--evidence", "outside.txt is not owned by TASK-1",
                ),
                (
                    "scope-block",
                    "--condition", "user decision required for outside.txt",
                    "--evidence", "scope drift evidence",
                    "--investigation", "compared changed paths with WBS ownership",
                    "--option", "remove outside.txt",
                    "--option", "approve scope revision",
                    "--required-action", "user chooses one bounded option",
                ),
                (
                    "scope-change",
                    "--wbs-source", "user-approved revised WBS row",
                    "--independent-output", "stream handler plus approved fixture",
                    "--acceptance", "terminal order and fixture",
                    "--test-requirement", "state tests",
                    "--authoritative-input", "system design section 4",
                    "--in-scope", "stream state machine",
                    "--out-of-scope", "adapter redesign",
                    "--allowed-path", "src/**",
                    "--allowed-path", "outside.txt",
                    "--evidence", "re-audited revised boundary",
                    "--approval-evidence", "user explicitly approved revision 2",
                ),
            ]
            for command in commands:
                result = self.run_cli(root, *command)
                self.assertEqual(result.returncode, 0, result.stderr)

            status = self.run_cli(root, "status")
            self.assertEqual(status.returncode, 0, status.stderr)
            task = json.loads(status.stdout)["tasks"]["TASK-1"]
            self.assertEqual(task["state"], "EXPLORING")
            self.assertEqual(task["scope"]["revision"], 2)
            self.assertEqual(task["scope_history"][0]["revision"], 1)
            self.assertEqual(
                task["scope_change_approval"]["evidence"],
                "user explicitly approved revision 2",
            )

    def test_legacy_scope_adoption_requires_historical_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-b", "develop"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Workflow Test"], cwd=root, check=True)
            (root / "README.md").write_text("baseline\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "chore: baseline"], cwd=root, check=True, capture_output=True)
            baseline = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            subprocess.run(["git", "switch", "-c", "feature/legacy"], cwd=root, check=True, capture_output=True)
            (root / "src").mkdir()
            (root / "src" / "feature.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/feature.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "feat: legacy work"], cwd=root, check=True, capture_output=True)
            current = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()

            state = {
                "schema_version": 1,
                "batch_id": "legacy",
                "repository": {"root": str(root), "remote": "origin", "base": "develop"},
                "authorization": {
                    "mode": "SUPERVISED", "task_ids": [], "create_pr": False,
                    "merge": False, "evidence": "", "revoked": False,
                },
                "active_task_id": "TASK-1",
                "tasks": {
                    "TASK-1": {
                        "task_id": "TASK-1", "title": "Legacy task", "state": "SCOPE_BLOCKED",
                        "branch": "feature/legacy", "head_sha": current, "scope": None,
                        "events": [],
                    }
                },
            }
            state_file = WORKFLOW.state_path(root)
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state), encoding="utf-8")

            command = (
                "scope-change",
                "--wbs-source", "WBS row",
                "--independent-output", "legacy output",
                "--acceptance", "legacy acceptance",
                "--test-requirement", "legacy tests",
                "--authoritative-input", "authority",
                "--in-scope", "feature",
                "--out-of-scope", "adjacent task",
                "--allowed-path", "src/**",
                "--evidence", "legacy audit",
                "--approval-evidence", "user approved adoption",
                "--baseline-head", baseline,
            )
            result = self.run_cli(root, *command)
            self.assertEqual(result.returncode, 0, result.stderr)
            task = json.loads(self.run_cli(root, "status").stdout)["tasks"]["TASK-1"]
            self.assertEqual(task["state"], "EXPLORING")
            self.assertEqual(task["scope"]["revision"], 1)
            self.assertEqual(task["scope"]["baseline_head_sha"], baseline)
            self.assertEqual(task["scope_history"], [])


if __name__ == "__main__":
    unittest.main()
