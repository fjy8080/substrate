#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("issue_evidence.py")
SPEC = importlib.util.spec_from_file_location("issue_evidence", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load issue_evidence")
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)


class IssueEvidenceTests(unittest.TestCase):
    def test_extracts_unique_issue_references(self) -> None:
        self.assertEqual(
            EVIDENCE.extract_issue_numbers("Fixes #12, relates to #7 and #12"),
            [7, 12],
        )

    def test_does_not_treat_url_fragment_as_issue_reference(self) -> None:
        self.assertEqual(
            EVIDENCE.extract_issue_numbers("https://example.invalid/path/#12"),
            [],
        )

    def test_parse_worktrees_preserves_branch_ownership(self) -> None:
        raw = (
            "worktree /repo\nHEAD aaa\nbranch refs/heads/develop\n\n"
            "worktree /tmp/fix-12\nHEAD bbb\nbranch refs/heads/fix/issue-12-bug\n\n"
        )
        worktrees = EVIDENCE.parse_worktrees(raw)
        self.assertEqual(len(worktrees), 2)
        self.assertEqual(worktrees[1]["worktree"], "/tmp/fix-12")
        self.assertEqual(worktrees[1]["branch"], "refs/heads/fix/issue-12-bug")

    def test_remote_url_credentials_and_query_are_redacted(self) -> None:
        value = EVIDENCE.redact_remote_url(
            "https://secret-token@github.com/acme/repo.git?access_token=hidden#fragment"
        )

        self.assertEqual(value, "https://github.com/acme/repo.git")

    def test_scp_style_remote_url_is_preserved(self) -> None:
        self.assertEqual(
            EVIDENCE.redact_remote_url("git@github.com:acme/repo.git"),
            "git@github.com:acme/repo.git",
        )

    def test_normalize_pull_links_issue_and_exact_head(self) -> None:
        pull = EVIDENCE.normalize_pull(
            {
                "number": 30,
                "title": "fix: repair scheduler (#12)",
                "body": "Fixes #12",
                "head": {"ref": "fix/issue-12", "sha": "a" * 40, "repo": {"full_name": "o/r"}},
                "base": {"ref": "develop", "sha": "b" * 40},
                "user": {"login": "author", "node_id": "U1"},
            }
        )
        self.assertEqual(pull["issue_references"], [12])
        self.assertEqual(pull["head"]["sha"], "a" * 40)
        self.assertEqual(pull["base"]["ref"], "develop")

    def test_normalize_issue_distinguishes_pull_requests(self) -> None:
        issue = EVIDENCE.normalize_issue(
            {"number": 12, "title": "bug", "pull_request": {"url": "x"}, "labels": []}
        )
        self.assertTrue(issue["is_pull_request"])

    def test_pull_detail_captures_paginated_conflict_evidence(self) -> None:
        raw = {
            "number": 30,
            "title": "fix: scheduler",
            "body": "Fixes #12",
            "head": {"ref": "fix/issue-12", "sha": "a" * 40},
            "base": {"ref": "develop", "sha": "b" * 40},
        }

        def values(endpoint: str, **_: object) -> list[dict[str, object]]:
            if "/files?" in endpoint:
                return [{"filename": "backend/app/job.py", "status": "modified"}]
            if "/reviews?" in endpoint:
                return [{"id": 1, "state": "CHANGES_REQUESTED"}]
            if "/issues/" in endpoint:
                return [{"id": 2, "body": "active feedback"}]
            if "/comments?" in endpoint:
                return [{"id": 3, "path": "backend/app/job.py", "line": 9}]
            if "/commits?" in endpoint:
                return [{"sha": "c" * 40, "commit": {"message": "fix: job"}}]
            return []

        detail = {**raw, "changed_files": 1, "commits": 1}
        with (
            patch.object(EVIDENCE, "paginated_rest", side_effect=values) as mocked,
            patch.object(EVIDENCE, "gh_json", return_value=detail),
        ):
            pull = EVIDENCE.pull_detail("o/r", raw)
        self.assertEqual(mocked.call_count, 5)
        self.assertEqual(pull["files"][0]["path"], "backend/app/job.py")
        self.assertTrue(all(pull["detail_completeness"].values()))

    def test_paginated_rest_rejects_malformed_items(self) -> None:
        with patch.object(EVIDENCE, "gh_json", return_value=[[{"id": 1}, "bad"]]):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "Expected object item"):
                EVIDENCE.paginated_rest("repos/o/r/issues?per_page=100")

    def test_pull_detail_rejects_truncated_files(self) -> None:
        raw = {
            "number": 30,
            "state": "open",
            "head": {"ref": "fix/x", "sha": "a" * 40},
            "base": {"ref": "develop", "sha": "b" * 40},
        }
        detail = {**raw, "changed_files": 2, "commits": 0}

        def values(endpoint: str, **_: object) -> list[dict[str, object]]:
            return [{"filename": "one.py"}] if "/files?" in endpoint else []

        with (
            patch.object(EVIDENCE, "gh_json", return_value=detail),
            patch.object(EVIDENCE, "paginated_rest", side_effect=values),
        ):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "file evidence incomplete"):
                EVIDENCE.pull_detail("o/r", raw)

    def test_pull_detail_rejects_head_change_during_capture(self) -> None:
        raw = {
            "number": 30,
            "state": "open",
            "head": {"ref": "fix/x", "sha": "a" * 40},
            "base": {"ref": "develop", "sha": "b" * 40},
        }
        before = {**raw, "changed_files": 0, "commits": 0}
        after = {
            **before,
            "head": {"ref": "fix/x", "sha": "c" * 40},
        }
        with (
            patch.object(EVIDENCE, "gh_json", side_effect=[before, after]),
            patch.object(EVIDENCE, "paginated_rest", return_value=[]),
        ):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "changed during detail capture"):
                EVIDENCE.pull_detail("o/r", raw)

    def test_pull_detail_rejects_body_change_during_capture(self) -> None:
        raw = {
            "number": 30,
            "state": "open",
            "title": "fix: original",
            "body": "Fixes #12",
            "updated_at": "2026-08-03T01:00:00Z",
            "head": {"ref": "fix/x", "sha": "a" * 40},
            "base": {"ref": "develop", "sha": "b" * 40},
        }
        before = {**raw, "changed_files": 0, "commits": 0}
        after = {
            **before,
            "body": "Fixes #12\n\nExpanded scope",
            "updated_at": "2026-08-03T01:01:00Z",
        }
        with (
            patch.object(EVIDENCE, "gh_json", side_effect=[before, after]),
            patch.object(EVIDENCE, "paginated_rest", return_value=[]),
        ):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "changed during detail capture"):
                EVIDENCE.pull_detail("o/r", raw)

    def test_issue_detail_rejects_change_during_capture(self) -> None:
        before = {
            "number": 12,
            "state": "open",
            "title": "scheduler fails",
            "body": "original report",
            "updated_at": "2026-08-03T01:00:00Z",
            "labels": [{"name": "bug"}],
            "assignees": [],
        }
        after = {
            **before,
            "body": "changed report",
            "updated_at": "2026-08-03T01:01:00Z",
        }
        with (
            patch.object(EVIDENCE, "gh_json", side_effect=[before, after]),
            patch.object(EVIDENCE, "paginated_rest", return_value=[]),
        ):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "changed during detail capture"):
                EVIDENCE.issue_detail("o/r", 12)

    def test_run_timeout_is_fail_closed(self) -> None:
        error = subprocess.TimeoutExpired(cmd=["gh"], timeout=60)
        with patch.object(EVIDENCE.subprocess, "run", side_effect=error):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "timed out"):
                EVIDENCE.run(["gh", "api", "user"])

    def test_run_os_error_is_fail_closed(self) -> None:
        with patch.object(EVIDENCE.subprocess, "run", side_effect=FileNotFoundError("missing")):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "Cannot execute"):
                EVIDENCE.run(["gh", "api", "user"])

    def test_open_pull_snapshot_is_bounded(self) -> None:
        pulls = [{"number": number} for number in range(1, EVIDENCE.MAX_OPEN_PULLS + 2)]
        with self.assertRaisesRegex(EVIDENCE.EvidenceError, "bounded snapshot limit"):
            EVIDENCE.collect_pull_details("o/r", pulls)

    def test_zero_remotes_is_not_complete(self) -> None:
        matching, complete = EVIDENCE.repository_remote_completeness(
            {"remotes": []}, "o/r", "develop"
        )
        self.assertEqual(matching, [])
        self.assertFalse(complete)


if __name__ == "__main__":
    unittest.main()
