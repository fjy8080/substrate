# Issue draft and publication protocol

## State flow

```text
TEXT_RECEIVED
  -> REPOSITORY_RESOLVED
  -> CODE_AND_DUPLICATES_CHECKED
  -> DRAFTED
  -> AWAITING_USER_APPROVAL
       -> DRAFTED                 (user edits the proposal)
       -> REFRESHING_EVIDENCE     (user explicitly approves publication)
            -> AWAITING_USER_APPROVAL  (material repository/evidence delta)
            -> PUBLISHING
                 -> VERIFIED
                 -> PUBLICATION_BLOCKED
```

Only `PUBLISHING` may mutate GitHub. The initial `创建issue` request never skips
`AWAITING_USER_APPROVAL`.

## Truth and publication disposition

| Truth | Meaning | Default publication behavior |
|---|---|---|
| `CONFIRMED` | Current code/reproduction supports the report | Draft as a defect |
| `PARTIALLY_CONFIRMED` | Only part of the text is supported | Correct the unsupported parts and disclose the delta |
| `VALID_REQUIREMENT` | A requested capability/change, not a current-code defect | Draft as feature/change request |
| `NOT_REPRODUCIBLE` | Faithful checks do not reproduce it | Report evidence; publish only if reframed and approved |
| `ALREADY_FIXED` | Current code already contains the correction | Link the fixing evidence; normally do not create |
| `NEEDS_CLARIFICATION` | Evidence cannot safely determine the claim | Ask a focused question before drafting final text |

Record publication disposition independently:

- `DRAFT_NEW`;
- `DO_NOT_CREATE_DUPLICATE` (an existing Issue owns it);
- `ACTIVE_WORK_EXISTS` (an open PR/branch owns it even without an Issue);
- `REFRAME_REQUIRED`;
- `NO_PUBLICATION`.

A confirmed P0-P4 defect keeps that severity even when disposition is duplicate/active work. Only
the publication action changes.

## Required duplicate search

Search beyond exact titles:

- open and closed Issues;
- open and merged PRs;
- fully paginated file/commit/review/comment evidence for open PRs before declaring no active work;
- error strings, API routes, class/function names, configuration keys, and affected behavior;
- Issue links in active PR bodies and commit/branch context when available.

An open PR implementing the request is active work even when no Issue exists. Include it in the
draft decision instead of creating a competing Issue silently.

## Draft structure

Adapt to the repository template. A complete default body contains:

```md
## 问题/需求

<concise user-visible or engineering problem>

## 当前行为与证据

- inspected commit: `<FULL-SHA>`
- relevant code/config: `<PATH/SYMBOL>`
- reproduction or code evidence: <EVIDENCE>

## 期望行为

<observable result>

## 复现步骤

1. ...

## 范围与非范围

- In scope: ...
- Out of scope: ...

## 分级、归属与契约影响

- Severity: `P0|P1|P2|P3|P4|NA`
- Owning task/WBS: ...
- Dependency/adjacent owner: ...
- Contract impact: `NONE|IMPLEMENT_EXISTING|CHANGE_REQUIRES_DECISION`
- Publication disposition: `DRAFT_NEW|DO_NOT_CREATE_DUPLICATE|ACTIVE_WORK_EXISTS|REFRAME_REQUIRED|NO_PUBLICATION`

## 验收标准

- [ ] ...

## 验证建议

- ...

## 关联与依赖

- Duplicate search: none / links
- Active PRs: none / links
```

Omit inapplicable headings rather than inventing content. Never paste secrets or excessive logs.

## Approval binding

Approval binds to:

- exact `OWNER/REPO`;
- exact title and complete body;
- exact existing labels;
- verification classification and material evidence;
- severity, owning task/WBS, inclusions/exclusions, dependencies, and contract impact;
- publication disposition and existing owner;
- the relevant repository/PR/Issue state presented to the user.

Typographical server normalization does not invalidate approval. Any material claim, scope, target,
label, duplicate, or active-work change does.

## Publication verification

After creation, verify through GitHub:

- Issue number and URL;
- repository and author;
- title/body/labels;
- open state;
- no unintended assignee, milestone, project, or linked mutation.

Do not say “created” until the live Issue is re-read successfully.

Publishing a `CHANGE_REQUIRES_DECISION` Issue records a decision request only. It does not approve
the contract/WBS change or authorize implementation.
