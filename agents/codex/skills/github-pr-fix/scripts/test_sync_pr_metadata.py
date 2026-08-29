#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("sync_pr_metadata.py")
SPEC = importlib.util.spec_from_file_location("sync_pr_metadata", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load sync_pr_metadata")
METADATA = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = METADATA
SPEC.loader.exec_module(METADATA)


def snapshot() -> object:
    return METADATA.PullSnapshot(
        state="open",
        head="a" * 40,
        base="develop",
        commits=4,
        files=12,
        body="",
    )


class MetadataBodyTests(unittest.TestCase):
    def test_updates_hidden_visible_and_head_fields(self) -> None:
        body = """# Pull Request

## PR 基线元数据

- Base: `develop`
- Commits: `3`
- Files changed: `10`

<!-- base:develop -->
<!-- commits:3 -->
<!-- files:10 -->

- [ ] 核验的是当前最新提交（HEAD SHA）：`bbbbbbb`

Keep this narrative unchanged.
"""

        updated = METADATA.canonical_body(body, snapshot())

        self.assertIn("- Commits: `4`", updated)
        self.assertIn("- Files changed: `12`", updated)
        self.assertIn(f"HEAD SHA）：`{'a' * 40}`", updated)
        self.assertEqual(updated.count("<!-- base:develop -->"), 1)
        self.assertEqual(updated.count("<!-- commits:4 -->"), 1)
        self.assertEqual(updated.count("<!-- files:12 -->"), 1)
        self.assertIn("Keep this narrative unchanged.", updated)
        self.assertEqual(METADATA.static_projection(body), METADATA.static_projection(updated))

    def test_inserts_required_hidden_markers_when_missing(self) -> None:
        body = "# Pull Request\n\nNo hidden metadata yet.\n"

        updated = METADATA.canonical_body(body, snapshot())

        self.assertTrue(updated.startswith("# Pull Request\n\nNo hidden metadata yet."))
        self.assertTrue(updated.endswith("<!-- files:12 -->\n"))
        self.assertEqual(METADATA.static_projection(body), METADATA.static_projection(updated))

    def test_removes_duplicate_hidden_markers(self) -> None:
        body = """Text
<!-- commits:1 -->
<!-- commits:2 -->
<!-- files:8 -->
<!-- base:main -->
"""

        updated = METADATA.canonical_body(body, snapshot())

        self.assertEqual(len(METADATA.HIDDEN_LINE.findall(updated)), 3)
        self.assertNotIn("commits:1", updated)
        self.assertNotIn("base:main", updated)

    def test_rejects_ambiguous_visible_fields(self) -> None:
        body = "- Commits: `1`\n- Commits: `2`\n"

        with self.assertRaisesRegex(METADATA.MetadataError, "ambiguous duplicate"):
            METADATA.canonical_body(body, snapshot())

    def test_snapshot_signature_excludes_body(self) -> None:
        first = snapshot()
        second = METADATA.PullSnapshot(
            state="open",
            head=first.head,
            base=first.base,
            commits=first.commits,
            files=first.files,
            body="changed body",
        )

        self.assertEqual(first.signature, second.signature)

    def test_apply_patches_then_verifies_exact_body(self) -> None:
        before = METADATA.PullSnapshot(
            state="open",
            head="a" * 40,
            base="develop",
            commits=4,
            files=12,
            body="# PR\n\n<!-- base:develop -->\n<!-- commits:3 -->\n<!-- files:10 -->\n",
        )
        expected = METADATA.canonical_body(before.body, before)
        after = METADATA.PullSnapshot(
            state=before.state,
            head=before.head,
            base=before.base,
            commits=before.commits,
            files=before.files,
            body=expected,
        )
        args = Namespace(
            repo="owner/repo",
            pr=9,
            expected_head=before.head,
            required_base="develop",
            apply=True,
            timeout=1.0,
            interval=0.01,
        )

        with (
            patch.object(METADATA, "repository_root", return_value=Path("/repo")),
            patch.object(METADATA, "current_repository", return_value="owner/repo"),
            patch.object(METADATA, "stable_snapshot", return_value=before),
            patch.object(METADATA, "pull_snapshot", return_value=after),
            patch.object(METADATA, "gh_json", return_value={}) as gh_call,
        ):
            result = METADATA.synchronize(args)

        self.assertEqual(result["status"], "UPDATED")
        self.assertEqual(result["head_sha"], before.head)
        self.assertEqual(gh_call.call_args.kwargs["payload"], {"body": expected})


if __name__ == "__main__":
    unittest.main()
