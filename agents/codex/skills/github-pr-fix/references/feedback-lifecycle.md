# PR feedback identity and lifecycle protocol

## Capture evidence

Run the bundled snapshot before creating the repair ledger and again before pushing or replying:

```bash
python3 scripts/pr_evidence.py --repo OWNER/NAME --pr NUMBER
```

It fully paginates formal reviews, conversation comments, inline comments, review threads, timeline
events, and commit authors. Preserve the original snapshot's exact head SHA as the repair baseline.

Identity fields have distinct meanings:

- `pr_relation` says whether the authenticated actor created the PR;
- `contribution.status` says whether that actor is a commit/co-author contributor;
- `independence` says whether their review can be treated as independent;
- `publication_route` is relevant to review publication, not authorization to repair;
- feedback entries retain their own author, source type, URL/ID, and head binding.

Never call a conversation comment a Change Request. Never describe the authenticated user's own
comment as colleague feedback. A contributor can review another actor's PR without that review
becoming an authorized self-review or an independent Approve.

## Keep lifecycle and truth independent

For every candidate feedback item, record lifecycle, truth, severity, scope ownership, and the
cumulative review/fix round. Read [repair-scope-and-severity.md](repair-scope-and-severity.md).

Lifecycle states:

- `ACTIVE_FEEDBACK`: still applicable to the captured head and not resolved, dismissed, or replaced;
- `SUPERSEDED`: a later review/comment explicitly replaces, withdraws, or closes it;
- `DISMISSED`: GitHub or an authorized actor dismissed the formal review;
- `OUTDATED_THREAD`: the inline location is outdated after a diff change;
- `RESOLVED_THREAD`: the thread is marked resolved;
- `WRONG_HEAD`: the evidence is bound to a different head and has not been reconfirmed;
- `INFORMATIONAL`: no requested correction;
- `NEEDS_LIFECYCLE_CLARIFICATION`: GitHub evidence is insufficient or contradictory.

Truth dispositions:

- `CONFIRMED`;
- `ALREADY_FIXED`;
- `NOT_REPRODUCIBLE`;
- `INVALID`;
- `NEEDS_CLARIFICATION`.

Only an `ACTIVE_FEEDBACK + CONFIRMED + IN_PR_SCOPE` item that passes the round severity threshold
authorizes a code correction under `修复#<number>`. Rounds 1-3 accept P0-P4; round 4 onward accepts
only P0/P1. A real P2-P4 late-round item remains non-blocking and must not be changed.
Resolved, dismissed, outdated, superseded, or wrong-head feedback remains in the ledger but is not
silently reactivated. A real defect discovered while checking inactive feedback must be reported as
a newly discovered issue; do not attribute it to a stale reviewer instruction.

## Determine lifecycle from complete history

- Formal reviews: retain review ID, author, state, submitted time, commit ID, and whether it matches
  the current head. Use dismissal timeline events and later reviews by the same actor; do not infer
  current state from the first 100 reviews.
- Inline threads: retain root/replies, resolved status, outdated status, path, and line. Resolution
  and reply are different events.
- Conversation comments: retain author and URL, but treat them as ordinary comments even when their
  prose says “request changes”.
- CI/check feedback: bind the check run and logs to the exact SHA. A failure on an old SHA is not a
  current-head failure.
- Review requests: identify who requested whom, but do not treat the request itself as feedback or
  publication authority.

When two sources describe the same defect, keep both source identities but one repair item with
cross-references. Do not double-count or post duplicate replies.

## Reconcile before push and reply

Before pushing, fetch the remote head. If it changed, compare its commits with the baseline and
rebuild the ledger before deciding whether a safe non-force push remains possible.

Before replying, take a new snapshot and compare:

- head SHA;
- each source review/comment/thread ID and author;
- lifecycle state;
- new replies or resolutions;
- current checks.

Repository-required PR body metadata is a mechanical push consequence, not reviewer feedback. After
every authorized push, bind its synchronization evidence to the exact live head and GitHub's current
base/commit/file statistics before consuming CI. Preserve the complete non-metadata body. A later
push or relevant base-statistics change makes the synchronization evidence stale even if the review
feedback ledger itself is unchanged.

Reply in the original context. State the source type accurately. Do not resolve a thread, dismiss a
review, re-request review, or publish a new review without separate authority.
