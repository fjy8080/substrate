#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("pr_evidence.py")
SPEC = importlib.util.spec_from_file_location("pr_evidence", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load pr_evidence")
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)


class EvidenceTests(unittest.TestCase):
    def test_self_pr_uses_ordinary_comment(self) -> None:
        actor = {"login": "owner", "node_id": "U1"}
        relation = EVIDENCE.classify_pr_relation(actor, dict(actor))
        self.assertEqual(relation, "SELF_PR")
        self.assertEqual(EVIDENCE.publication_route(relation), "ORDINARY_ISSUE_COMMENT")
        self.assertEqual(
            EVIDENCE.classify_independence(relation, "CONTRIBUTOR"),
            "NON_INDEPENDENT_SELF",
        )

    def test_other_authored_contributor_pr_uses_formal_review(self) -> None:
        authenticated = {"login": "octocat", "node_id": "U_HP"}
        creator = {"login": "contributor-a", "node_id": "U_CTA"}
        commits = [
            {
                "oid": "a" * 40,
                "authors": [
                    {"login": "contributor-a", "node_id": "U_CTA"},
                    {"login": "octocat", "node_id": "U_HP"},
                ],
            }
        ]
        relation = EVIDENCE.classify_pr_relation(authenticated, creator)
        contribution = EVIDENCE.contribution_evidence(
            authenticated,
            commits,
            complete=True,
        )
        self.assertEqual(relation, "OTHER_PR")
        self.assertEqual(contribution["status"], "CONTRIBUTOR")
        self.assertEqual(
            EVIDENCE.classify_independence(relation, contribution["status"]),
            "NON_INDEPENDENT_CONTRIBUTOR",
        )
        self.assertEqual(EVIDENCE.publication_route(relation), "FORMAL_REVIEW")

    def test_other_non_contributor_is_only_provisionally_independent(self) -> None:
        authenticated = {"login": "reviewer", "node_id": "U1"}
        creator = {"login": "author", "node_id": "U2"}
        contribution = EVIDENCE.contribution_evidence(
            authenticated,
            [{"oid": "a" * 40, "authors": [{"login": "author", "node_id": "U2"}]}],
            complete=True,
        )
        relation = EVIDENCE.classify_pr_relation(authenticated, creator)
        self.assertEqual(contribution["status"], "NON_CONTRIBUTOR")
        self.assertEqual(
            EVIDENCE.classify_independence(relation, contribution["status"]),
            "PROVISIONALLY_INDEPENDENT",
        )

    def test_unmapped_commit_author_fails_closed(self) -> None:
        contribution = EVIDENCE.contribution_evidence(
            {"login": "reviewer", "node_id": "U1"},
            [
                {
                    "oid": "a" * 40,
                    "authors": [
                        {
                            "login": None,
                            "node_id": None,
                            "name": "unknown",
                            "email_fingerprint": "abc123",
                        }
                    ],
                }
            ],
            complete=True,
        )
        self.assertEqual(contribution["status"], "UNKNOWN_CONTRIBUTION")

    def test_latest_review_is_selected_per_actor(self) -> None:
        reviews = [
            {
                "id": 1,
                "author": {"login": "reviewer", "node_id": "U1"},
                "state": "CHANGES_REQUESTED",
                "submitted_at": "2026-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "author": {"login": "reviewer", "node_id": "U1"},
                "state": "APPROVED",
                "submitted_at": "2026-01-02T00:00:00Z",
            },
        ]
        latest = EVIDENCE.latest_reviews_by_actor(reviews)
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]["id"], 2)

    def test_removed_review_request_is_not_current(self) -> None:
        authenticated = {"login": "reviewer", "node_id": "U1"}
        creator = {"login": "author", "node_id": "U2"}
        timeline = [
            {
                "event": "review_requested",
                "review_requester": creator,
                "requested_reviewer": authenticated,
            },
            {
                "event": "review_request_removed",
                "review_requester": creator,
                "requested_reviewer": authenticated,
            },
        ]
        context = EVIDENCE.review_request_context(timeline, authenticated, creator)
        self.assertTrue(context["ever_requested_by_pr_creator"])
        self.assertFalse(context["currently_requested"])

    def test_pull_scope_fingerprint_rejects_body_change(self) -> None:
        before = {
            "number": 12,
            "state": "open",
            "title": "fix: bug",
            "body": "original scope",
            "updated_at": "2026-08-03T01:00:00Z",
            "commits": 1,
            "changed_files": 2,
            "base": {"ref": "develop", "sha": "a" * 40},
            "head": {"ref": "fix/bug", "sha": "b" * 40},
        }
        after = {
            **before,
            "body": "expanded scope",
            "updated_at": "2026-08-03T01:01:00Z",
        }
        with self.assertRaisesRegex(EVIDENCE.EvidenceError, "changed during snapshot"):
            EVIDENCE.require_stable(
                "Pull request identity/scope",
                EVIDENCE.pull_fingerprint(before),
                EVIDENCE.pull_fingerprint(after),
            )

    def test_paginated_rest_rejects_malformed_items(self) -> None:
        with patch.object(EVIDENCE, "gh_json", return_value=[[{"id": 1}, "bad"]]):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "Expected object item"):
                EVIDENCE.paginated_rest("repos/o/r/pulls/12/reviews?per_page=100")

    def test_run_timeout_and_launch_failure_are_fail_closed(self) -> None:
        timeout = subprocess.TimeoutExpired(cmd=["gh"], timeout=60)
        with patch.object(EVIDENCE.subprocess, "run", side_effect=timeout):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "timed out"):
                EVIDENCE.run(["gh", "api", "user"])
        with patch.object(EVIDENCE.subprocess, "run", side_effect=FileNotFoundError("missing")):
            with self.assertRaisesRegex(EVIDENCE.EvidenceError, "Cannot execute"):
                EVIDENCE.run(["gh", "api", "user"])

    def test_body_metadata_binds_live_pr_statistics(self) -> None:
        body = "<!-- base:develop -->\n<!-- commits:4 -->\n<!-- files:12 -->\n"

        metadata = EVIDENCE.body_metadata(body, "develop", 4, 12)

        self.assertTrue(metadata["schema_detected"])
        self.assertTrue(metadata["complete"])
        self.assertTrue(metadata["consistent"])

    def test_duplicate_or_stale_body_metadata_fails_closed(self) -> None:
        body = (
            "<!-- base:develop -->\n<!-- commits:3 -->\n<!-- commits:4 -->\n"
            "<!-- files:10 -->\n"
        )

        metadata = EVIDENCE.body_metadata(body, "develop", 4, 12)

        self.assertFalse(metadata["complete"])
        self.assertFalse(metadata["consistent"])
        self.assertEqual(metadata["occurrence_counts"]["commits"], 2)


if __name__ == "__main__":
    unittest.main()
