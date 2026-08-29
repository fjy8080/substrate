# PR identity and publication protocol

## Capture evidence

Run the bundled snapshot before analysis and again immediately before publication:

```bash
python3 scripts/pr_evidence.py --repo OWNER/NAME --pr NUMBER
```

The script reads the authenticated actor, PR creator, exact head, fully paginated formal reviews,
conversation comments, inline comments, review threads, timeline events, and GraphQL commit authors.
Do not replace it with an unpaginated `gh pr view` call.

If `pr_relation` is unknown or a required completeness field is false, do not publish. Report the
missing evidence and ask the user. An unknown contribution relation prevents claiming independent
approval, but does not turn an `OTHER_PR` into a self PR.

## Keep four dimensions separate

1. **PR relation** is determined only by authenticated GitHub actor versus the PR `creator`:
   - `SELF_PR`: same stable node ID, with login as fallback;
   - `OTHER_PR`: different actors;
   - `UNKNOWN_PR_RELATION`: insufficient evidence.
2. **Contribution relation** records whether the authenticated actor appears in commit/co-author
   identity evidence. Head-repository ownership, organization ownership, branch naming, or write
   permission are not proof that the actor created the PR.
3. **Independence** combines contribution evidence with repository rules:
   - `NON_INDEPENDENT_SELF`;
   - `NON_INDEPENDENT_CONTRIBUTOR`;
   - `PROVISIONALLY_INDEPENDENT`, which becomes independent only after project rules and other
     implementation evidence are checked;
   - `UNKNOWN_INDEPENDENCE`.
4. **Publication route** is selected from PR relation, not independence:
   - `SELF_PR` uses an ordinary PR conversation comment;
   - `OTHER_PR` uses a formal GitHub review;
   - unknown relation pauses for the user.

A review request from the PR creator is useful context but is neither proof of independence nor
authorization to publish. Later commits may change contribution and independence, but never rewrite
the historical PR creator.

## Publication matrix

“Blocking findings” means findings classified as `IN_PR_DEFECT` that pass the cumulative round's
severity threshold from [severity-and-scope.md](severity-and-scope.md). It never includes P2-P4 from
round 4 onward or a finding owned by another task.

| PR relation | Independence | Blocking findings | Publication after user confirmation |
|---|---|---:|---|
| `SELF_PR` | any | any | ordinary comment headed `授权自审查（不计入独立 Review / Approve）` |
| `OTHER_PR` | independent under project rules | >0 | formal `REQUEST_CHANGES`, counts according to project rules |
| `OTHER_PR` | `NON_INDEPENDENT_CONTRIBUTOR` | >0 | formal `REQUEST_CHANGES`, explicitly says it does not count as independent Approve |
| `OTHER_PR` | `UNKNOWN_INDEPENDENCE` | >0 | formal `REQUEST_CHANGES`, disclose unknown independence and never claim independent approval |
| `OTHER_PR` | independent under project rules | 0 | propose formal `APPROVE` or `COMMENT`; require explicit user direction |
| `OTHER_PR` | contributor or unknown | 0 | never approve; propose formal `COMMENT` or no publication |
| unknown | any | any | do not publish |

Formal `REQUEST_CHANGES` expresses actionable blocking feedback on another actor's PR. It does not
by itself prove reviewer independence. Keep the GitHub action and gate meaning separate in the body
and report.

## Exact-HEAD publication check

Before publishing, compare the new snapshot with the reviewed snapshot:

- repository and PR number;
- PR creator node ID;
- full head SHA;
- contribution and independence classification;
- draft/open state;
- newly added reviews, comments, thread resolution, and review-request events.

Any head change invalidates the technical review. An identity or feedback delta requires updating
the proposed publication and obtaining confirmation again when its meaning changes.
