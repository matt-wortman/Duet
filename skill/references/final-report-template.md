# Final Report Template — Two-File Layout

This is the canonical layout for a /duet session. A session produces **three canonical files** (the permanent record), **two working files** (live during Phase 4 only), and **two integrity sidecars**:

Canonical files:
1. `<topic-slug>-claude.md` — anchored to Claude's Phase 2 report. Codex appends critiques (Phase 3) and responses (Phase 4) here. Append-only; the permanent record.
2. `<topic-slug>-codex.md` — anchored to Codex's Phase 2 report. Claude appends critiques and responses here. Append-only.
3. `<topic-slug>-synthesis.md` — produced in Phase 6 after both debate files terminate. Lists every `[CONCEDE]`-tagged item plus items the other agent did not critique. Includes a Synthesis Disputes section if Codex objected during the audit pass.

Working files (created at start of Phase 4 in each canonical file; deleted after Phase 5):
- `<topic-slug>-claude.open.md` — open items from `<slug>-claude.md`. Contains the per-item trail for items still tagged `[PUSH-BACK]`. Shrinks each round as items concede or hold.
- `<topic-slug>-codex.open.md` — mirror.

The working file is what each round's responder reads. The canonical file is the audit-grade history. Resolved items live only in the canonical file; open items live in both.

Integrity sidecars (one per canonical file):
- `<topic-slug>-claude.md.hashes`
- `<topic-slug>-codex.md.hashes`

(Working files are not hashed — they're derived from the canonical file and re-derivable on demand.)

**Filename convention:** descriptive slug, lowercase, hyphenated, NO date prefix. Examples:
- `docs/duet/refactor-config-system-claude.md`
- `docs/duet/refactor-config-system-codex.md`
- `docs/duet/refactor-config-system-claude.open.md`
- `docs/duet/refactor-config-system-codex.open.md`
- `docs/duet/refactor-config-system-synthesis.md`

---

## Skeleton: `<topic-slug>-claude.md` (the Claude-anchored debate file)

```markdown
# Duet (Claude-anchored): {short topic title}

**Outcome**: {Resolved at round N | N items unresolved after round 7 | User aborted at phase X}
**Phases populated in this file**: {1-2 | 1-3 | 1-4 (round N) | 1-5}
**Companion file**: `<topic-slug>-codex.md`

---

## Phase 1: Approved Prompt

{the user-approved prompt, verbatim — duplicated identically in both files for self-containment}

<details>
<summary>Q&A transcript (not seen by agents)</summary>

**Claude:** {clarifying question 1}
**User:** {answer}

...

</details>

---

## Phase 2: Claude's Report

{verbatim — full Phase 2 output from Claude. This is the anchor of this file. Codex's Phase 2 report does NOT appear here; it lives in the companion file.}

---

## Phase 3: Codex's critique of Claude's report

Per-item entries. Each item targets a specific span of Claude's Phase 2 report above. Items Codex agrees with are tagged `[CONCEDE]` from the start. Items Codex did not address are silently absent.

### Item: {topic, one noun phrase}
Quoting Claude: "{verbatim span from Claude's Phase 2 report above}"
Counter-evidence: {Codex's argument or agreement statement}
[PUSH-BACK | CONCEDE]

### Item: {next topic}
...

---

## Phase 4: Negotiation rounds (this file, up to 7)

Each round, the agent who was NOT last to write in this file appends a response to each open item (any item not yet `[CONCEDE]`'d). At Round 1 the open items are the Phase 3 `[PUSH-BACK]` entries above; Codex critiqued, so Claude responds first.

### Round 2 — Claude responds

#### Item: {topic from Phase 3}
Quoting Codex: "{verbatim span from Codex's Phase 3 critique above}"
Response: {Claude's argument with evidence}
[PUSH-BACK | CONCEDE]

#### Item: {next open topic}
...

### Round 3 — Codex responds

#### Item: {still-open topic}
Quoting Claude: "{verbatim span from Round 2 above}"
Response: {Codex's argument}
[PUSH-BACK | CONCEDE]

...

### Round 7 — {last responder} (FINAL)

#### Item: {still-open topic}
Quoting {prior speaker}: "{verbatim}"
Response: {final argument}
[PUSH-BACK | CONCEDE | HOLD]

*(`[HOLD]` only valid at Round 7; signals permanent dissent.)*

---

## Phase 4 ledger (this file)

| Round | Items open at start | Items conceded this round | Items remaining |
|-------|--------------------:|--------------------------:|----------------:|
| 1 (Phase 3) | 4                | 1                         | 3               |
| 2           | 3                | 1                         | 2               |
| 3           | 2                | 0                         | 2               |
| 4           | 2                | 0                         | 2               |
| 5           | 2                | 0                         | 2               |
| 6           | 2                | 1                         | 1               |
| 7           | 1                | 0                         | 1 (HOLD)        |

---

## Phase 5: Fact-check (this file)

### Claude's verdict on this file
{verbatim PASS or ISSUES FOUND with corrections}

### Codex's verdict on this file
{verbatim PASS or ISSUES FOUND with corrections}

### Corrections applied
{if any — list of (location, change) pairs}
```

---

## Skeleton: `<topic-slug>-codex.md` (the Codex-anchored debate file)

Mirror image of the Claude-anchored file. Phase 2 contains Codex's report. Phase 3 contains Claude's critique. Round 2 is Codex responding to Claude's critique, etc. Substitute role names throughout.

---

## Skeleton: `<topic-slug>-{role}.open.md` (the Phase 4 working file)

Working file initialization happens at the start of Phase 4 in each canonical file: copy each Phase 3 entry whose tag is `[PUSH-BACK]` into a new working file under `### Open items (after Phase 3)`. `[CONCEDE]`-tagged Phase 3 items skip the working file (they're recorded in the canonical file as agreement and never enter the round count).

After each Phase 4 round, the orchestrator appends the round's per-item entries to the corresponding `#### Item:` blocks, then prunes any item whose newest tag is `[CONCEDE]` or `[HOLD]`.

```markdown
# Working file: open items in <topic-slug>-{role}.md

> Updated after each Phase 4 round. Rebuild from canonical file if lost.
> Most recent round: {N}.

---

### Open items (after Phase 3)

#### Item: {topic, one noun phrase — copied verbatim from canonical Phase 3 entry}

**Phase 3 — {critic} critique** (verbatim from canonical):
Quoting {anchor}: "{verbatim span from canonical Phase 2 anchor}"
Counter-evidence: {argument}
[PUSH-BACK]

**Round 2 — {anchor} response** (verbatim from canonical):
Quoting {critic}: "{verbatim span from Phase 3 entry above}"
Response: {argument}
[PUSH-BACK]

**Round 3 — {critic} response** (verbatim from canonical):
Quoting {anchor}: "{verbatim span from Round 2 above}"
Response: {argument}
[PUSH-BACK]

---

#### Item: {next still-open topic}
...
```

When all items in a working file are pruned, that file's Phase 4 is complete (every item resolved or held). Delete the working file after Phase 5 fact-check passes — its purpose is purely transient.

---

## Skeleton: `<topic-slug>-synthesis.md` (Phase 6 output)

```markdown
# Duet Synthesis: {short topic title}

**Source files**:
- `<topic-slug>-claude.md` (terminated at Round {N_claude})
- `<topic-slug>-codex.md` (terminated at Round {N_codex})

**Outcome**: {N agreed items | M dispute(s) flagged}

---

## Agreed findings

Items both agents either (a) tagged `[CONCEDE]` in some round, or (b) chose not to critique in the other file. Each item carries verbatim provenance. When both files contain `[CONCEDE]` entries on the same topic with different verbatim spans, both spans appear, attributed.

- **{topic, one noun phrase}**
  - From Claude: "{verbatim span — file pointer e.g. `claude.md:142`}"
  - From Codex: "{verbatim span — file pointer e.g. `codex.md:88`}"

- **{topic}**
  - From Claude: "{verbatim — `claude.md:N`}"
  - *(Codex did not critique; included by absence.)*

- **{topic}**
  - From Codex: "{verbatim — `codex.md:N`}"
  - *(Claude did not critique; included by absence.)*

---

## Synthesis Disputes

*(Empty if Codex's audit pass returned APPROVE. Otherwise: items Codex objected to including in Agreed Findings, with Codex's verbatim objection.)*

- **{topic Claude proposed for Agreed Findings}**
  - Claude's proposed entry: {verbatim quote(s) from above}
  - Codex's objection: "{verbatim from Codex's audit response}"
```

---

## Building the documents incrementally

Per phase, what the orchestrator writes to disk:

- **End of Phase 1:** Both canonical files exist with identical Phase 1 sections (approved prompt + Q&A transcript). Phase 2 sections are stubs. No working files yet.
- **End of Phase 2:** Each canonical file's Phase 2 anchor is populated with its own agent's report. Hash sidecars are seeded with the SHA-256 of each agent's raw output.
- **End of Phase 3:** Each canonical file gets a Phase 3 section appended with the *other* agent's per-item tagged critiques. Items pre-tagged `[CONCEDE]` are recorded but do not enter the Phase 4 round count.
- **Start of Phase 4:** The orchestrator initializes each canonical file's working file (`<slug>-{role}.open.md`) by copying every Phase 3 entry tagged `[PUSH-BACK]` into it under `### Open items (after Phase 3)`. Working files are pristine snapshots of the open set; the canonical files are unchanged.
- **End of each Phase 4 round:** Two writes per round per file: (1) the agent's response is appended to the canonical file's `### Round N` section with hash sidecar update; (2) the same per-item entries are appended to the working file's `#### Item:` blocks, then any items now tagged `[CONCEDE]` or `[HOLD]` are pruned from the working file.
- **End of Phase 4 in a file:** Canonical file's ledger table is finalized. Working file may be empty or hold `[HOLD]` items pending Phase 5; either way, it ceases to be live. Files terminate independently.
- **End of Phase 5:** Each canonical file's Phase 5 fact-check section is appended; corrections (if any) applied with sidecar re-hashing. Working files are deleted (or moved to `<filename>.archive` if you want a record of the live state).
- **End of Phase 6:** `<topic-slug>-synthesis.md` is created from the canonical files. Synthesis NEVER reads working files. (No Phase 6 section is added to the debate files — synthesis lives in its own file.)

## Backup snapshots

Before each Phase 4 round, snapshot both the canonical and working files for the file being appended to:

```
docs/duet/<topic-slug>-claude.md.bak.round-{N-1}
docs/duet/<topic-slug>-claude.open.md.bak.round-{N-1}
docs/duet/<topic-slug>-codex.md.bak.round-{N-1}
docs/duet/<topic-slug>-codex.open.md.bak.round-{N-1}
```

If the round audit (structural + hash) fails, restore from the snapshot and re-run the round.
