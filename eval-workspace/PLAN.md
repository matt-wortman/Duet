# /duet Two-File Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the merged-document architecture in the `/duet` skill with two parallel agent-anchored files plus an end-only synthesis pass, eliminating the Phase 3 → Phase 4 artifact-shape mismatch (eval finding F4.1) and adding a hash sidecar plus Codex envelope strip rule (surviving items F6.1 and Codex CLI envelope).

**Architecture:** Each session produces `<topic-slug>-claude.md` (anchored to Claude's Phase 2 report; Codex writes critiques and responses here) and `<topic-slug>-codex.md` (mirror, anchored to Codex's report). Phase 3 emits per-item tagged critiques that flow directly into Phase 4 Round 1 — no AGREED/DISAGREED/SINGLE-SOURCE classification, no orchestrator merge step. Phase 4 runs each file independently up to 7 rounds, with each round's responder reading a per-file working file (`<topic-slug>-{role}.open.md`) that holds only the still-`[PUSH-BACK]` items — open items shrink as items concede or hold, so per-round token cost stays bounded. The canonical debate file is the append-only audit-grade record; the working file is the live read target. Phase 6 (new) is a Claude-drafts / Codex-audits synthesis from the canonical files with a Disputes safety valve. Hash sidecars verify orchestrator transcription fidelity on the canonical files at end-of-round.

**Tech Stack:** Markdown skill files at `~/.claude/skills/duet/`; Bash for hash sidecar (`sha256sum`); Codex companion runtime invoked via `node "$CODEX_PATH"`; Claude subagents for parallel work.

---

## File Structure

Three files modified, all in `~/.claude/skills/duet/`:

| File | Responsibility | Change scope |
|------|---------------|--------------|
| `SKILL.md` | Workflow orchestration prose, phase definitions, anti-hallucination rules, error handling | Major rewrite of Phase 3, 4, 6 (new), Document Layout, Token & Context Management, Resume Mechanics; additions to Anti-Hallucination Guarantees and a new "Per-Round Hash Audit" subsection |
| `references/duet-prompts.md` | Templates sent to agents per phase | Replace Phase 3 prompt; modify Phase 4 prompt; add three new Phase 6 prompts (synthesis draft, audit, dispute application); minor Phase 5 update for two-file format |
| `references/final-report-template.md` | Annotated example of the on-disk artifact layout | Full rewrite — single-file skeleton becomes two-file + synthesis layout |

No new files are created in the skill directory itself. The skill *runtime* will produce three artifacts per session (`-claude.md`, `-codex.md`, `synthesis.md`) plus two `.hashes` sidecars, but those are session outputs in `docs/duet/` not skill source.

The plan keeps SKILL.md changes batched by phase number rather than by file, so one commit per phase (Tasks 2-5) keeps prose, prompt template, and template-doc changes coherent.

---

## Task 1: Document layout foundation — rewrite `final-report-template.md`

**Why first:** Tasks 2-5 reference the layout. Locking the on-disk shape first means the prose and prompts in subsequent tasks can quote concrete section headings.

**Files:**
- Modify: `~/.claude/skills/duet/references/final-report-template.md` (full rewrite — current 159 lines → new ~180 lines)

- [ ] **Step 1: Read the current template**

Run: `Read ~/.claude/skills/duet/references/final-report-template.md`
Expected: see the single-file skeleton with `## Phase 3: Merged Critique` containing `### Best of the Best` and `### Discrepancies / #### Subsection 1 / #### Subsection 2`. This is the structure being replaced.

- [ ] **Step 2: Rewrite the template top-to-bottom**

Use `Write` to replace the file with the new layout below. Key invariants the new template must teach:
- Two parallel files with **mirror structure**, each anchored to one agent's Phase 2 report
- The "anchor" agent's Phase 2 report is the **only** content in that file from Phase 2
- Phase 3 critiques in file X are written by the **other** agent (the critic), targeting items in X's Phase 2
- Phase 4 rounds alternate appends per file, capped at 7 per file independently
- A separate `synthesis.md` is produced in Phase 6 — never co-mingled with the debate files
- Per-item provenance for synthesis: when both files contain `[CONCEDE]` on the same topic with different verbatim spans, both spans are quoted as sub-bullets attributed by source

Replace entire file contents with:

````markdown
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
````

- [ ] **Step 3: Verify the file is well-formed**

Run: `wc -l ~/.claude/skills/duet/references/final-report-template.md`
Expected: roughly 180-200 lines (the new layout).

Run: `head -20 ~/.claude/skills/duet/references/final-report-template.md`
Expected: header line is `# Final Report Template — Two-File Layout`, no leftover references to "Best of the Best" or "Discrepancies / Subsection 1".

Run: `grep -c "Subsection 1\|Subsection 2\|Best of the Best\|Discrepancies" ~/.claude/skills/duet/references/final-report-template.md`
Expected: `0`

- [ ] **Step 4: Commit**

This skill directory is not a git repo; the user manages snapshots manually. **Skip git commit.** If `git rev-parse --is-inside-work-tree` succeeds in `~/.claude/skills/duet/` then commit with:

```bash
git -C ~/.claude/skills/duet add references/final-report-template.md
git -C ~/.claude/skills/duet commit -m "duet: rewrite final-report-template for two-file layout"
```

Otherwise, log the change to a per-task scratch note at `~/.claude/skills/duet-eval-workspace/CHANGES.md` (append a one-line entry: `Task 1: rewrote final-report-template.md`).

---

## Task 2: Phase 3 rewrite — per-item tagged critique format

**Why:** Phase 3 currently produces AGREED/DISAGREED/SINGLE-SOURCE classifications that the orchestrator merges into a Best-of-the-Best + Discrepancies structure. The new design has each agent emit per-item tagged critiques of the *other agent's* Phase 2 report, formatted identically to Phase 4 round responses so they flow directly into Round 1 with zero orchestrator transformation.

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md:112-147` (entire Phase 3 section)
- Modify: `~/.claude/skills/duet/references/duet-prompts.md:27-65` (Phase 3 prompt template)

- [ ] **Step 1: Read both files to confirm line ranges**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 110, limit 40)
Expected: see lines starting `## Phase 3: Critique Merge` and ending before `## Phase 4: Negotiation Rounds`.

Run: `Read ~/.claude/skills/duet/references/duet-prompts.md` (offset 27, limit 40)
Expected: the current Phase 3 prompt with the `## AGREED / ## DISAGREED / ## SINGLE-SOURCE` output format.

- [ ] **Step 2: Replace the SKILL.md Phase 3 section**

Use `Edit` with `old_string` matching from `## Phase 3: Critique Merge` through the line `Show the merged structure to the user live before starting Phase 4.` and `new_string`:

```markdown
## Phase 3: Cross-Critique

Each agent reads BOTH Phase 2 reports and writes a critique of the OTHER agent's report. Critiques are written **directly into the other agent's debate file** as per-item tagged entries with the same shape as Phase 4 round responses — they flow into Round 1 with no transformation.

There is no AGREED / DISAGREED / SINGLE-SOURCE classification step. Items the critic agrees with are tagged `[CONCEDE]` from the start (and never enter the round count). Items the critic does not address are silently absent — convergence by silence.

### Step 3a: Dispatch both agents in parallel

Send each agent (both `--fresh`) the Phase 3 critique prompt from `references/duet-prompts.md`, with both Phase 2 reports embedded and the agent's role specified (critic of which file).

- Codex critiques Claude's report → Codex's output is appended as `## Phase 3: Codex's critique of Claude's report` to `<topic-slug>-claude.md`.
- Claude critiques Codex's report → Claude's output is appended as `## Phase 3: Claude's critique of Codex's report` to `<topic-slug>-codex.md`.

### Step 3b: Orchestrator transcribes verbatim

For each file, the orchestrator inserts the agent's raw Phase 3 output verbatim under the correct heading. **No reordering, no merging across files, no paraphrase.** Hash the raw output before transcription (see "Per-Round Hash Audit") and append the hash to the corresponding `.hashes` sidecar.

The expected per-item shape (each agent must produce this; the prompt template enforces it):

```
### Item: {topic, one noun phrase}
Quoting the other agent: "{verbatim span from their Phase 2 report}"
Counter-evidence: {argument or agreement}
[PUSH-BACK | CONCEDE]
```

### Step 3c: Show the user

Display each file's Phase 3 section to the user before starting Phase 4. The set of `[PUSH-BACK]`-tagged items in each file IS the open round-count for that file.
```

- [ ] **Step 3: Replace the duet-prompts.md Phase 3 template**

Use `Edit` to replace the section starting `## Phase 3 — Critique Pass Prompt` through `Quote VERBATIM. Do not paraphrase. Use one-noun-phrase topic labels — no framing.` with:

````markdown
## Phase 3 — Cross-Critique Prompt

Sent to BOTH agents after Phase 2 completes. Each agent critiques the OTHER agent's Phase 2 report. The output is appended directly into the other agent's debate file and serves as Round 1 of Phase 4 — no separate orchestrator transformation.

Codex `--fresh`. Claude as fresh subagent. Each agent's prompt substitutes its own role.

```
You are doing Phase 3 of a /duet — a cross-critique of the other agent's Phase 2 report.

You will read your own Phase 2 report (for context — it grounds your perspective) and the other agent's Phase 2 report (the target of your critique).

=== YOUR PHASE 2 REPORT ===
{your_report}
=== END YOUR REPORT ===

=== OTHER AGENT'S PHASE 2 REPORT (target of your critique) ===
{other_report}
=== END OTHER REPORT ===

Your critique will be appended directly to the other agent's debate file as the first round of Phase 4. Format and tagging matter — they determine what the other agent sees when responding.

For each substantive claim, finding, or recommendation in the OTHER agent's report that you have a view on, write one item using EXACTLY this format:

### Item: {topic, one noun phrase}
Quoting the other agent: "{verbatim span from their report — single contiguous quote, no ellipsis, no paraphrase}"
Counter-evidence: {your argument with evidence — one paragraph, or your statement of agreement with brief reasoning}
[PUSH-BACK | CONCEDE]

Tag rules:
- [PUSH-BACK] — you disagree, partially or fully, and want to debate. The other agent will respond in Round 2.
- [CONCEDE] — you agree with this claim. The item is logged as agreement and removed from the round count immediately.

Item-selection rules:
- Cover any claim in the other agent's report you have a substantive view on (agree or disagree). Items you simply do not address are silently absent — that's expected and not a failure.
- One topic per item. Do not bundle.
- Topic labels are one noun phrase, no framing ("event sourcing tradeoff" not "the misleading event sourcing claim").

Quote rules:
- "Quoting the other agent" must be a verbatim contiguous span from their Phase 2 report. No ellipsis. No paraphrase. No reformatting (preserve exact whitespace and punctuation).
- If you need to reference two non-contiguous spans, write two items.

Output ONLY the per-item entries. No preamble. No summary. No closing remarks.
```
````

- [ ] **Step 4: Verify Phase 3 section is consistent across both files**

Run: `grep -n "AGREED\|DISAGREED\|SINGLE-SOURCE\|Best of the Best\|Subsection 1\|Subsection 2\|Merged Critique" ~/.claude/skills/duet/SKILL.md ~/.claude/skills/duet/references/duet-prompts.md`
Expected: no matches in the Phase 3 section. (Some Phase 4 references to "Subsection 1/2" will still exist — those get cleaned in Task 3.)

Run: `grep -n "Cross-Critique\|cross-critique" ~/.claude/skills/duet/SKILL.md ~/.claude/skills/duet/references/duet-prompts.md`
Expected: at least 3 matches across the two files.

- [ ] **Step 5: Commit (per Task 1 Step 4 protocol — git commit if repo, append to CHANGES.md otherwise)**

Message: `duet: Phase 3 emits per-item tagged critiques into other agent's file`

---

## Task 3: Phase 4 rewrite — two-file parallel architecture

**Why:** The current Phase 4 has a 7-row alternation table routing both agents through paired subsections of one shared file — the artifact-shape mismatch this created was eval finding F4.1. The new design has each file independently progress one round at a time, with the agent who was NOT last to write being the next to respond. The 7-row table collapses to one rule. Per-round reading is structurally chunked via per-file working files (`*.open.md`) so token cost stays bounded as each file grows.

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md:149-213` (entire Phase 4 section, including the round structure table, per-round mechanics, re-prompt budget, and termination)
- Modify: `~/.claude/skills/duet/references/duet-prompts.md:67-120` (Phase 4 prompt template)

- [ ] **Step 1: Read both sections to confirm line ranges**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 148, limit 70)
Expected: from `## Phase 4: Negotiation Rounds (up to 7 total)` through `### Termination` ending with the "permanent dissent" bullet.

Run: `Read ~/.claude/skills/duet/references/duet-prompts.md` (offset 67, limit 56)
Expected: from `## Phase 4 — Negotiation Round Prompt` through the Round 7 special framing block.

- [ ] **Step 2: Replace the SKILL.md Phase 4 section**

Use `Edit` to replace from `## Phase 4: Negotiation Rounds (up to 7 total)` through `- **End of Round 7:** anything still in the Discrepancies section is a permanent dissent. The 7-round debate trail itself IS the record — no separate co-authored dissent block needed.` with:

````markdown
## Phase 4: Negotiation Rounds (up to 7 per file, independent)

Each debate file progresses through up to 7 rounds. The two files run in parallel and terminate **independently** — `<slug>-claude.md` may resolve at Round 3 while `<slug>-codex.md` runs all the way to Round 7, and that's fine.

### Per-file round rule

Each round, in each file, **the agent who was NOT last to write appends responses to all open items** (items still tagged `[PUSH-BACK]` from the most recent round).

- In `<slug>-claude.md`: Phase 3 was Codex's critique → Round 2 is Claude responding → Round 3 is Codex → alternating.
- In `<slug>-codex.md`: Phase 3 was Claude's critique → Round 2 is Codex responding → Round 3 is Claude → alternating.

That's it. There is no subsection routing, no per-item alternation table, no cross-file synchronization.

### Working files (live during Phase 4)

Each canonical debate file has a paired working file: `<topic-slug>-claude.open.md` and `<topic-slug>-codex.open.md`. The working file is what each round's responder actually reads. It contains only the per-item trails for items still tagged `[PUSH-BACK]` from the most recent round in that file. Items that resolve (`[CONCEDE]`) or hold (`[HOLD]`) are pruned from the working file at end-of-round — they remain in the canonical file as the permanent record.

Working file initialization (at start of Phase 4 in each file): copy each Phase 3 entry whose tag is `[PUSH-BACK]` into the working file under heading `### Open items (after Phase 3)`. `[CONCEDE]`-tagged Phase 3 items skip the working file entirely.

### Per-round mechanics

For each round (2 through 7) in each file:

1. **Snapshot both files.** Write `<slug>-{role}.md.bak.round-{N-1}` (canonical) AND `<slug>-{role}.open.md.bak.round-{N-1}` (working) before the round starts.

2. **Spawn fresh sessions.** Codex with `--fresh`. Claude as a fresh subagent. Each session starts with no prior memory.

3. **Reading scope (todo-style chunked context).** Each agent reads, in order:
   - The Phase 1 approved prompt (verbatim — small, 1-2K tokens).
   - The Phase 2 anchor section of the canonical debate file `<topic-slug>-{role}.md` for grounding (their own report if responding in their anchored file; the other agent's report if responding in the companion file).
   - The working file `<topic-slug>-{role}.open.md` — this is the round's TODO list. It contains the per-item trails for every still-open item (Phase 3 critique + every prior round's responses).

   The full canonical debate file is NOT read per round. The companion canonical file is available as a cross-reference path the agent may consult but is not loaded by default. Working file size shrinks as items resolve, so even Round 7 reads stay bounded.

4. **Per-item response.** For each open item in the working file, the agent writes one entry under `### Round N — {agent} responds`:

   ```
   #### Item: {topic from prior round}
   Quoting {prior speaker}: "{verbatim span from prior round above}"
   Response: {evidence-backed argument}
   [CONCEDE | PUSH-BACK | HOLD]
   ```

   Tag rules:
   - `[CONCEDE]` — accepts the prior round's argument. Item is logged as agreement and pruned from the working file; will not appear in subsequent rounds.
   - `[PUSH-BACK]` — maintains position. Item stays in the working file for the next round.
   - `[HOLD]` — only valid at Round 7. Signals permanent dissent. Pruned from working file at end of Round 7 (the working file ceases to exist after Round 7 anyway).

5. **Verbatim quote requirement.** When quoting the prior speaker, the span must be a contiguous verbatim substring of the prior round's text *as it appears in the working file*. No ellipsis, no paraphrase.

6. **Orchestrator transcribes — to BOTH files.** For each per-item response:
   1. Hash the raw response and append the hash to the canonical file's `.hashes` sidecar.
   2. Insert verbatim under the correct `### Round N — {agent}` heading in the canonical debate file.
   3. Append the same per-item entry under the corresponding `#### Item:` block in the working file (so future rounds see the trail).
   4. After all per-item responses are inserted, prune the working file: remove any item whose newest tag is `[CONCEDE]` or `[HOLD]`.

   The orchestrator does NOT add `Round N — agent` headers based on its own logic — the heading is part of the file's growing structure and is written before the agent runs (the prompt tells the agent which heading their content goes under).

7. **End-of-round audit.** After each round, before advancing the file:
   - Every `[CONCEDE]` and `[HOLD]` tag corresponds to an item that does not appear in the next round's working file.
   - Every quoted attribution exists verbatim in this file's working file (or in the immediately-prior round of the canonical file if the agent quoted across the round boundary).
   - No item appears twice in the same round.
   - Round markers are consecutive within the canonical file.
   - **Hash audit:** re-hash the just-inserted Round N block in the canonical file and compare to the entry in `.hashes`. Mismatch → restore canonical and working files from their `.bak.round-{N-1}` snapshots, re-transcribe.
   - **Working file consistency:** the set of open items in the working file equals the set of items whose newest canonical-file tag is `[PUSH-BACK]`. Mismatch → restore working file from snapshot and re-derive from canonical.

   If audit fails twice in a row, surface to user.

### File termination

A file terminates when any of these conditions is met:
- All Phase 3 items in this file resolved to `[CONCEDE]` (no rounds needed beyond Phase 3).
- A round produces zero new `[PUSH-BACK]` tags (everything either conceded or held).
- Round 7 completes.

When a file terminates, finalize its Phase 4 ledger table and proceed to Phase 5 for that file. The other file continues independently if not yet terminated.

### Re-prompt budget on malformed output

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Missing tag on a response | Regex check post-round | Re-prompt the agent up to **2 retries** with explicit format reminder. After 2 failed retries, surface to user: pick the tag manually or skip this item for this round. |
| Failed quote verification | Substring match against this file | Re-prompt up to 2 retries: "You attributed '{quote}' but the file contains '{actual}'. Please correct." After 2 failures, treat as `[PUSH-BACK]` and flag for user attention. |
| Empty or trivially short response (<50 chars or no substance) | Length + heuristic | Re-prompt up to 2 retries with format reminder. After 2 failures, mark as `[PUSH-BACK]`. |
| Hash audit mismatch | Re-hash compared to `.hashes` | Restore from snapshot, re-prompt the orchestrator's transcription step (this is an orchestrator bug, not an agent bug — the agent's raw output was correct but transcription drifted). |

Never silent loops. Always cap retries at 2.

### Show the debate live

After each round in each file, display the updated file state to the user. They can interrupt at any point.

### Termination summary

- **Item resolves at any round** when an agent writes `[CONCEDE]` — drops from the open set immediately.
- **End of Round 7 in a file:** anything still tagged `[PUSH-BACK]` is unresolved; the 7-round debate trail in that file IS the record. Items tagged `[HOLD]` at Round 7 are explicitly logged as permanent dissents.
````

- [ ] **Step 3: Replace the duet-prompts.md Phase 4 template**

Use `Edit` to replace from `## Phase 4 — Negotiation Round Prompt` through the Round 7 special framing block (ending `Use [HOLD] if you cannot in good conscience concede and want this logged as a genuine impasse.` and the closing triple-backtick) with:

````markdown
## Phase 4 — Negotiation Round Prompt

Sent to ONE agent at a time per round, per file. Each invocation is `--fresh`. The agent reads the file, responds to all items still open, and writes responses with terminal tags.

```
You are participating in /duet Round {round_number} of 7.

You are responding to all open items in the working file:
{working_filepath}        ← READ THIS — your todo list and full per-item debate trail

For grounding context, also read the Phase 2 anchor section of:
{canonical_filepath}      ← READ ONLY the "## Phase 2:" section

The Phase 1 approved prompt (the original task both agents are working):
{phase1_prompt_inline}

The companion canonical file at {companion_filepath} is available if you need to cross-reference, but is not required reading.

Your responses go into the canonical file under this exact heading (already written there):

### Round {round_number} — {your_role_name} responds

For each open item in the working file, write ONE entry in this exact format:

#### Item: {topic, copied verbatim from the working file's Item heading}
Quoting {prior_speaker_name}: "{verbatim contiguous span from the prior round's response in the working file}"
Response: {your evidence-backed argument or statement}
[CONCEDE | PUSH-BACK | HOLD]

Tag rules:
- [CONCEDE] — you accept the prior speaker's argument. The item drops from the debate.
- [PUSH-BACK] — you maintain position. The item continues to the next round.
- [HOLD] — only valid at Round 7. Signals permanent dissent.

CRITICAL RULES:
- Quote VERBATIM from the prior round's response in the working file. Single contiguous span. No ellipsis. No paraphrase. No reformatting.
- Tag exactly one of [CONCEDE] / [PUSH-BACK] / [HOLD] per item.
- Respond to EVERY open item in the working file. Do not skip items.
- Do not invent new disagreements — work only the items in the working file.
- Do not write anything outside the per-item entries (no preamble, no summary, no commentary on the process).

Open items requiring your response this round:
{numbered_list_of_open_item_topics_from_working_file}
```

### Round 7 special framing

For round 7, append to the prompt above:

```
NOTE: This is Round 7 — the FINAL round in this file. After this round, any item still ending in [PUSH-BACK] is logged as unresolved. Use [HOLD] instead of [PUSH-BACK] if you want to explicitly signal a genuine impasse rather than ongoing dispute.
```
````

- [ ] **Step 4: Verify Phase 4 sections are consistent**

Run: `grep -n "Subsection 1\|Subsection 2\|originator\|disagreer" ~/.claude/skills/duet/SKILL.md ~/.claude/skills/duet/references/duet-prompts.md`
Expected: no matches.

Run: `grep -n "alternation table\|round 1.*round 2.*round 3" ~/.claude/skills/duet/SKILL.md`
Expected: no matches (the 7-row table is gone).

Run: `grep -c "two files\|both files\|each file\|per file\|in this file" ~/.claude/skills/duet/SKILL.md`
Expected: at least 8 matches.

- [ ] **Step 5: Commit**

Message: `duet: Phase 4 runs each file independently, no subsection routing`

---

## Task 4: Phase 5 update — two-file fact-check

**Why:** Phase 5 currently fact-checks "the document" (singular). It now needs to fact-check both files. Each agent fact-checks both files (their positions appear as Phase 2 anchor in their own file and as critiques+responses in the other file).

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md:214-225` (Phase 5: Fact-Check Pass section)
- Modify: `~/.claude/skills/duet/references/duet-prompts.md:124-150` (Phase 5 prompt)

- [ ] **Step 1: Read both sections**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 213, limit 15)
Expected: the current Phase 5 section starting `## Phase 5: Fact-Check Pass`.

Run: `Read ~/.claude/skills/duet/references/duet-prompts.md` (offset 124, limit 27)
Expected: the current Phase 5 prompt template.

- [ ] **Step 2: Replace SKILL.md Phase 5 section**

Use `Edit` to replace from `## Phase 5: Fact-Check Pass` through `Append a `## Phase 5: Fact-Check` section recording each agent's verdict.` with:

````markdown
## Phase 5: Fact-Check Pass

Once both canonical debate files have terminated (each independently), fact-check both canonical files. Working files are not part of fact-check — they're a transient view, not the record. Each agent reads BOTH canonical files because their positions appear in both: as the Phase 2 anchor in their own file, and as critiques + responses in the other file.

Send each agent (both `--fresh`) the Phase 5 prompt from `references/duet-prompts.md`, with both canonical file paths embedded. Each agent confirms:

1. In the canonical file anchored to them: is their Phase 2 report quoted accurately when the other agent critiques it? Are their `[CONCEDE]` decisions and arguments preserved verbatim?
2. In the other canonical file: are their critiques (Phase 3) and round responses (Phase 4) preserved verbatim, with correct round attribution?
3. Are any of their arguments quietly softened, dropped, or merged across rounds?

If either agent flags a misrepresentation, the orchestrator fixes the specific line in the canonical file (verbatim from the agent's correction, with hash sidecar updated) and re-runs the fact-check on that file. Otherwise, both canonical files are final.

After Phase 5 passes for both files, delete the two working files (`<slug>-{claude,codex}.open.md`) — their purpose was Phase 4 only.

Append a `## Phase 5: Fact-check (this file)` section to EACH canonical file recording both agents' verdicts on that file.
````

- [ ] **Step 3: Replace duet-prompts.md Phase 5 template**

Use `Edit` to replace from `## Phase 5 — Fact-Check Pass Prompt` through the closing of the prompt template (ending `only flag misrepresentations of YOUR positions.` and the closing triple-backtick) with:

````markdown
## Phase 5 — Fact-Check Pass Prompt

Sent to BOTH agents (`--fresh` each) after both debate files terminate. Each agent reads BOTH files and confirms neither file misrepresents their positions.

```
You are doing the final fact-check for a /duet session. Two files are now in their final shape:

- {claude_filepath} — anchored to Claude's Phase 2 report
- {codex_filepath} — anchored to Codex's Phase 2 report

Read both files in full.

Your job is narrow: confirm neither file misrepresents YOUR positions.

Specifically check:

1. In the file anchored to you: is your Phase 2 report quoted verbatim where the other agent critiques it? Are quotes from your round responses (in subsequent rounds) verbatim?

2. In the file anchored to the other agent: are your Phase 3 critiques and Phase 4 round responses preserved verbatim, with correct round attribution? Specifically: does each "Round N — {you} responds" section contain text you actually wrote, with no paraphrase, ellipsis, or insertion?

3. Round attributions: did the orchestrator correctly attribute your responses (e.g., your Round 3 push-back appears under "Round 3 — {you} responds", not paraphrased into a Round 4 summary or merged with another round)?

4. Tag preservation: are your `[CONCEDE]` / `[PUSH-BACK]` / `[HOLD]` tags exactly as you wrote them?

Output format:

## Fact-check result on {claude_filepath}
{PASS | ISSUES FOUND}

## Issues on {claude_filepath} (if any)
- **{location, e.g., "Phase 3 critique by Codex of Claude, Item: event sourcing"}**: {what is wrong} — {what should be there instead, with verbatim correction}

## Fact-check result on {codex_filepath}
{PASS | ISSUES FOUND}

## Issues on {codex_filepath} (if any)
- **{location}**: {what is wrong} — {verbatim correction}

Be terse. This is a fact-check pass, not re-litigation. Do NOT raise new arguments. Do NOT object to the other agent's positions on the merits — only flag misrepresentations of YOUR positions.
```
````

- [ ] **Step 4: Verify**

Run: `grep -n "the document\|final document" ~/.claude/skills/duet/SKILL.md`
Expected: no matches in the Phase 5 section. (The phrase "single source of truth across all phases" near the top of SKILL.md gets updated in Task 8.)

- [ ] **Step 5: Commit**

Message: `duet: Phase 5 fact-checks both files independently`

---

## Task 5: Phase 6 (new) — synthesis with audit and disputes

**Why:** Without a final convergent step, a /duet session leaves two debate files but no single "what we agreed on" output. Phase 6 is a Claude-drafts / Codex-audits synthesis with a Disputes safety valve — one audit pass, no iteration loop.

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md` — insert a new `## Phase 6: Synthesis` section between current Phase 5 and `## Document Layout` (around line 226)
- Modify: `~/.claude/skills/duet/references/duet-prompts.md` — append three new prompt templates at the end of the file (Phase 6a synthesis draft, Phase 6b Codex audit, Phase 6c orchestrator dispute application)

- [ ] **Step 1: Read SKILL.md to find insertion point**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 220, limit 15)
Expected: end of Phase 5 section (post-Task 4 edits) followed by `## Document Layout — `docs/duet/<topic-slug>.md``.

- [ ] **Step 2: Update Phase 5 termination — and insert Phase 6 in SKILL.md**

The text immediately after Phase 5 currently jumps to Document Layout. Use `Edit` to insert a new Phase 6 section between them. Match `old_string` against `Append a `## Phase 5: Fact-check (this file)` section to EACH file recording both agents' verdicts on that file.\n\n## Document Layout` and replace with the same Phase 5 closing line, then a new Phase 6 section, then `## Document Layout`:

````markdown
Append a `## Phase 5: Fact-check (this file)` section to EACH file recording both agents' verdicts on that file.

## Phase 6: Synthesis

After both canonical debate files have passed Phase 5 fact-check (and working files have been deleted), a third canonical file is produced: `<topic-slug>-synthesis.md`. This is a Claude-drafts / Codex-audits pipeline with one audit pass. There is no iteration loop — disputes Codex raises during the audit are moved to a Synthesis Disputes section as the safety valve.

Synthesis reads ONLY the canonical debate files. The working files no longer exist at this point and would be the wrong source anyway — they only ever held open items.

### Step 6a: Claude drafts the synthesis

Send Claude (fresh subagent) the Phase 6a synthesis-draft prompt from `references/duet-prompts.md`, with both canonical debate file paths embedded.

The draft `synthesis.md` lists every item that meets at least one of these inclusion conditions:
- Tagged `[CONCEDE]` in either file at any phase (Phase 3 pre-tagged, or Phase 4 Round N).
- Present as a claim in one file's Phase 2 anchor and never critiqued in the other file's Phase 3 (silent agreement).

Each item is recorded with verbatim quotes and file+line pointers — no paraphrase. When both files contain `[CONCEDE]` entries on the same topic with different verbatim spans, both spans appear, attributed by source ("From Claude:" / "From Codex:" sub-bullets).

The orchestrator hashes Claude's draft output and seeds `<topic-slug>-synthesis.md.hashes` before writing the file.

### Step 6b: Codex audits

Send Codex (`--fresh`) the Phase 6b audit prompt from `references/duet-prompts.md`, with the draft `synthesis.md` and both debate files' paths embedded.

Codex's output is one of:
- `APPROVE` — synthesis is faithful. No change needed.
- Per-item objections — for each item Codex disputes including, Codex gives a verbatim correction (either a fixed quote or "this item should not be in Agreed Findings because…").

### Step 6c: Orchestrator applies Codex's audit

If Codex returned `APPROVE`: the synthesis file is final. Add a `> Audited by Codex: APPROVE.` note at the top.

If Codex returned objections:
- For each objection where Codex provided a verbatim correction to a quote: apply the correction in place (re-hash sidecar).
- For each objection where Codex disputes the inclusion of an item: move that item from `## Agreed findings` to a new `## Synthesis Disputes` section at the end of the file, with Codex's verbatim objection appended.

After applying Codex's audit, the synthesis file is final. **No second audit pass.** The Synthesis Disputes section is the explicit record of unresolved synthesis-level disagreement.

### Step 6d: Show the user

Display the final `synthesis.md` to the user along with both debate files' final ledgers. The user sees:
- Agreed findings count
- Disputes count (zero in convergent sessions)
- Each debate file's outcome line

## Document Layout
````

- [ ] **Step 3: Append Phase 6 prompt templates to duet-prompts.md**

Read the end of the file first to confirm the insertion point:

Run: `Read ~/.claude/skills/duet/references/duet-prompts.md` (offset 145, limit 10)
Expected: end of Phase 5 prompt template (the closing triple-backtick).

Use `Edit` to append the new Phase 6 templates. Match `old_string` against the final closing of the Phase 5 template (something like `only flag misrepresentations of YOUR positions.\n```` followed by EOF or trailing content) and append:

`````markdown
only flag misrepresentations of YOUR positions.
```

---

## Phase 6a — Synthesis Draft Prompt (Claude)

Sent to Claude (fresh subagent) after both debate files pass Phase 5 fact-check.

```
You are drafting the Phase 6 synthesis for a /duet session. Two debate files are in their final, fact-checked shape:

- {claude_filepath} — anchored to your Phase 2 report
- {codex_filepath} — anchored to Codex's Phase 2 report

Your job is to produce `synthesis.md` listing every item that the two of you ultimately agreed on, with verbatim provenance.

Inclusion rules (an item appears in Agreed findings if EITHER condition is met):

1. Tagged [CONCEDE] in either file at any phase (Phase 3 pre-tagged or any Phase 4 round).
2. Present in one file's Phase 2 anchor as a substantive claim AND never critiqued in the other file's Phase 3 (silent agreement by absence).

For each agreed item, write one bullet in this exact format:

- **{topic, one noun phrase}**
  - From Claude: "{verbatim span — file pointer, e.g. `claude.md:142`}"
  - From Codex: "{verbatim span — file pointer, e.g. `codex.md:88`}"

Provenance rules:
- If both files contain [CONCEDE] entries on the same topic with different verbatim spans, include BOTH spans as sub-bullets, attributed.
- If only one file contains the source (silent-agreement case), include only that source and add a sub-bullet: "*(Other agent did not critique; included by absence.)*"
- Quote VERBATIM. Single contiguous span. No ellipsis. No paraphrase. No reformatting.
- The file pointer is the source filename and line range, e.g. `claude.md:142-148`.

Output the full `synthesis.md` content following this skeleton:

# Duet Synthesis: {short topic title — derived from the debate files' titles}

**Source files**:
- `{claude_filepath}` (terminated at Round {N_claude})
- `{codex_filepath}` (terminated at Round {N_codex})

**Outcome**: {N agreed items}

---

## Agreed findings

{bulleted items per the format above}

---

## Synthesis Disputes

*(Empty at draft time. Codex's audit pass may add items here.)*

Output ONLY the file contents. No preamble, no commentary on the process.
```

---

## Phase 6b — Synthesis Audit Prompt (Codex)

Sent to Codex (`--fresh`) after Claude's draft synthesis is written to disk.

```
You are auditing the Phase 6 synthesis for a /duet session. Three files are in scope:

- {synthesis_filepath} — Claude's draft synthesis (target of your audit)
- {claude_filepath} — Claude-anchored debate file (source)
- {codex_filepath} — Codex-anchored debate file (source)

Your job is narrow: verify the synthesis faithfully represents what both of you agreed on.

For each item under "## Agreed findings" in {synthesis_filepath}:

1. Verify the verbatim quotes appear at the cited file:line pointers in the source files.
2. Verify the inclusion is justified — either tagged [CONCEDE] in some round, or present in one Phase 2 anchor and never critiqued in the other Phase 3.
3. Verify provenance is complete — if both files contain [CONCEDE] on the same topic, both spans appear (not just Claude's).

Output format:

## Audit result
{APPROVE | OBJECTIONS}

## Objections (if any)

For each objection, one entry:

- **{item topic from synthesis}**: {one of}
  - Quote correction: cited as "{quoted text in synthesis}" but the source contains "{verbatim correction from source}". File: {source filepath}, line {N}.
  - Inclusion dispute: this item should not be in Agreed Findings because {reason — typically "I never conceded this; my Phase 4 final tag was [PUSH-BACK]" or "my Phase 2 anchor explicitly rejected this claim"}.
  - Provenance gap: my [CONCEDE] on this topic at {file}:{line} is missing from the provenance sub-bullets.

Be terse. Do NOT raise new disagreements. Do NOT object to the substance of items both files conceded — only flag synthesis fidelity issues.
```

---

## Phase 6c — Orchestrator notes (no agent prompt)

This is the orchestrator-side procedure for applying Codex's Phase 6b output. Not a prompt template; included here as a reference for the SKILL.md procedure.

- If Codex returned `APPROVE`: prepend `> Audited by Codex: APPROVE.` to `<topic-slug>-synthesis.md`. Done.
- For each Codex objection:
  - **Quote correction**: replace the cited verbatim quote in the synthesis with the verbatim correction from Codex. Update the `.hashes` sidecar.
  - **Inclusion dispute**: cut the item from `## Agreed findings`. Append it under `## Synthesis Disputes` with a sub-bullet `Codex's objection: "{verbatim from Codex's audit response}"`.
  - **Provenance gap**: add the missing sub-bullet using the file:line pointer Codex supplied.

After applying all objections, the synthesis is final — no second Codex pass.
`````

- [ ] **Step 4: Verify Phase 6 wiring**

Run: `grep -n "Phase 6\|synthesis.md\|Synthesis" ~/.claude/skills/duet/SKILL.md`
Expected: at least 6 matches in the Phase 6 section and updates to Document Layout (Document Layout updates land in Task 8 — for now just the Phase 6 section.)

Run: `grep -n "Phase 6a\|Phase 6b\|Phase 6c" ~/.claude/skills/duet/references/duet-prompts.md`
Expected: 3 distinct matches for the three new templates.

- [ ] **Step 5: Commit**

Message: `duet: add Phase 6 synthesis with Codex audit and disputes safety valve`

---

## Task 6: Hash sidecar — implementation across SKILL.md

**Why:** Surviving item F6.1 from the prior remediation prompt. Catches orchestrator transcription drift (e.g., the canonical ellipsis at `tier3-behavioral/run-1/duet-output-doc.md:169`). Implementation is a ~5-line addition to anti-hallucination + a one-paragraph runbook entry.

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md` — add a new "Per-Round Hash Audit" subsection inside the existing `## Anti-Hallucination Guarantees` section, and reference it from `## Step A: Codex Path Discovery` (where pre-flight checks live)

- [ ] **Step 1: Read the Anti-Hallucination Guarantees section**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 290, limit 18)
Expected: the current `## Anti-Hallucination Guarantees` section ending with "...Stop and surface to user." (line numbers will have shifted from prior tasks; locate by content).

- [ ] **Step 2: Append "Per-Round Hash Audit" subsection**

Use `Edit` to extend the Anti-Hallucination Guarantees section. Match `old_string` against `If the orchestrator ever feels the need to paraphrase, summarize, or "improve" wording — that's a bug. Stop and surface to user.` and append:

````markdown
If the orchestrator ever feels the need to paraphrase, summarize, or "improve" wording — that's a bug. Stop and surface to user.

### Per-Round Hash Audit

Each agent's raw output is hashed with SHA-256 BEFORE the orchestrator transcribes it into a debate file. The hash is appended to a sidecar (`<filename>.hashes`) with a label identifying what was hashed (which phase, which round, which agent). At end-of-round (and end-of-phase for Phase 2/3/5/6), the orchestrator re-hashes the just-inserted block and compares to the sidecar.

Mismatch → orchestrator transcription bug → restore from `.bak.round-{N-1}`, re-transcribe (NOT re-prompt the agent — the agent's raw output is already correct; the bug is in the orchestrator's writing step).

Sidecar format (one entry per line):

```
phase-2-claude-anchor <sha256>
phase-2-codex-anchor <sha256>
phase-3-codex-critique-of-claude <sha256>
round-2-claude <sha256>
round-3-codex <sha256>
phase-5-fact-check-claude-on-claude-file <sha256>
```

Implementation in Bash:

```bash
echo "round-${N}-${AGENT} $(echo -n "$RAW_OUTPUT" | sha256sum | cut -d' ' -f1)" \
  >> "${FILEPATH}.hashes"
```

End-of-round verification extracts the just-inserted block (between the round heading and the next round heading or EOF), re-hashes it, and compares:

```bash
INSERTED=$(awk "/^### Round ${N} — /{flag=1;next}/^### Round ${NEXT} — /{flag=0}flag" "${FILEPATH}")
ACTUAL=$(echo -n "$INSERTED" | sha256sum | cut -d' ' -f1)
EXPECTED=$(grep "^round-${N}-${AGENT} " "${FILEPATH}.hashes" | awk '{print $2}')
[ "$ACTUAL" = "$EXPECTED" ] || { echo "Hash mismatch — restoring snapshot"; ... }
```

The hash audit catches structural transcription bugs (truncation, ellipsis, line-ending changes) but not semantic ones (paraphrase). The per-item tagged Phase 3 + per-round verbatim-quote requirement in Phase 4 minimize semantic-drift opportunity to begin with.
````

- [ ] **Step 3: Add hash sidecar to pre-flight checks**

Find the pre-flight checks block in `## Step A: Codex Path Discovery` and add a sidecar-init line.

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 38, limit 8)
Expected: the pre-flight checks bullets ending `...if exactly one found, ask the user: resume or start fresh`.

Use `Edit` to extend pre-flight checks. Match `old_string` against `- If no `--resume` flag, scan `docs/duet/` for incomplete sessions; if exactly one found, ask the user: resume or start fresh` and replace with:

```markdown
- If no `--resume` flag, scan `docs/duet/` for incomplete sessions; if exactly one found, ask the user: resume or start fresh
- For new sessions, plan to seed `<topic-slug>-claude.md.hashes` and `<topic-slug>-codex.md.hashes` at the start of Phase 2 (one entry per agent's raw report). See "Per-Round Hash Audit" under Anti-Hallucination Guarantees.
- The two working files (`<topic-slug>-{claude,codex}.open.md`) are NOT created at session start — they're initialized at the start of Phase 4 from each canonical file's Phase 3 `[PUSH-BACK]` entries. No working file is needed if a file's Phase 3 produced zero `[PUSH-BACK]` items (full convergence — skip directly to Phase 5 for that file).
```

- [ ] **Step 4: Verify hash sidecar wiring**

Run: `grep -c "sha256\|hashes" ~/.claude/skills/duet/SKILL.md`
Expected: at least 8 matches.

Run: `grep -n "Per-Round Hash Audit" ~/.claude/skills/duet/SKILL.md`
Expected: 2 matches (one for the section heading, one for the cross-reference in pre-flight checks).

- [ ] **Step 5: Commit**

Message: `duet: add per-round hash sidecar for transcription fidelity audit`

---

## Task 7: Codex envelope strip rule

**Why:** Codex's CLI runtime emits `Codex session ID:` and `Resume in Codex:` lines in its output. These are runtime artifacts, not part of the agent's response, and would pollute the debate files (and potentially break verbatim quote audits in later rounds). Strip them before transcription.

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md` — add a Codex output post-processing rule. Best location: a new bullet under Anti-Hallucination Guarantees, plus a procedural reference where Codex output is captured (Phase 2 dispatch and Phase 4 dispatch).

- [ ] **Step 1: Add envelope strip rule to Anti-Hallucination Guarantees**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 290, limit 5)
Expected: the bullet list under Anti-Hallucination Guarantees.

Use `Edit` to add one new bullet to the Anti-Hallucination Guarantees list. Match `old_string` against `- Phase 5 fact-check is the final guard against subtle misrepresentation.` and replace with:

```markdown
- Phase 5 fact-check is the final guard against subtle misrepresentation.
- **Codex CLI envelope strip:** before transcribing any Codex output, remove runtime-emitted lines matching `^Codex session ID:` and `^Resume in Codex:`. These are CLI artifacts, not agent content. Strip BEFORE hashing (so the hash represents the substantive output, not the CLI envelope).
```

- [ ] **Step 2: Add a procedural note at the Codex dispatch site**

Find the Codex dispatch in Phase 2 (around the `node "$CODEX_PATH" task --fresh` line).

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 84, limit 12)
Expected: the Codex dispatch block with the bash command.

Use `Edit` to add a post-processing note. Match `old_string`:

````markdown
```bash
node "$CODEX_PATH" task --fresh "$(cat "$PHASE2_PROMPT_FILE")"
```

Run with `run_in_background: true` so Claude can do its parallel work without blocking.
````

Replace with:

````markdown
```bash
node "$CODEX_PATH" task --fresh "$(cat "$PHASE2_PROMPT_FILE")" \
  | sed -E '/^Codex session ID:/d; /^Resume in Codex:/d' \
  > "$CODEX_RAW_OUTPUT"
```

Run with `run_in_background: true` so Claude can do its parallel work without blocking. The `sed` filter strips Codex CLI envelope lines before the output is captured (see "Codex CLI envelope strip" under Anti-Hallucination Guarantees). The same filter must be applied to Codex output in Phase 3, Phase 4 rounds, Phase 5, and Phase 6 audit.
````

- [ ] **Step 3: Verify**

Run: `grep -n "Codex session ID\|Resume in Codex\|envelope strip" ~/.claude/skills/duet/SKILL.md`
Expected: at least 3 matches.

- [ ] **Step 4: Commit**

Message: `duet: strip Codex CLI envelope lines before transcription`

---

## Task 8: Document Layout, Token & Context Management, Resume Mechanics — update for two-file architecture

**Why:** These three sections in SKILL.md still describe the single-document architecture. They need to reflect the two-file + synthesis layout. This is the largest single SKILL.md edit and is left until last so all phase-section changes are settled.

**Files:**
- Modify: `~/.claude/skills/duet/SKILL.md` — `## Document Layout` section (full rewrite), `## Token & Context Management` (update tokens estimate and reading-scope rules), `## Resume Mechanics` (two-file termination), and the description string in frontmatter (narrow architectural-accuracy fix; not a triggering rewrite)

- [ ] **Step 1: Read current Document Layout section**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 226, limit 50)
Expected: the `## Document Layout — `docs/duet/<topic-slug>.md`` section with the markdown skeleton showing single-doc structure.

- [ ] **Step 2: Replace Document Layout section**

Use `Edit` to replace from `## Document Layout — `docs/duet/<topic-slug>.md`` through the end of the markdown code block + `See `references/final-report-template.md` for an annotated example.` with:

````markdown
## Document Layout — `docs/duet/<topic-slug>-{claude,codex}.md`, `<topic-slug>-{claude,codex}.open.md`, `<topic-slug>-synthesis.md`

A session produces three canonical files (the permanent record), two transient working files (live during Phase 4 only), and two integrity sidecars:

```
docs/duet/<topic-slug>-claude.md          # Canonical: Claude's anchor + Codex's critiques + responses (append-only)
docs/duet/<topic-slug>-codex.md           # Canonical: Codex's anchor + Claude's critiques + responses (append-only)
docs/duet/<topic-slug>-claude.open.md     # Working: open items in claude.md (created at Phase 4 start, deleted after Phase 5)
docs/duet/<topic-slug>-codex.open.md      # Working: open items in codex.md (same lifecycle)
docs/duet/<topic-slug>-synthesis.md       # Canonical: Phase 6 output, agreed findings + (optional) disputes
docs/duet/<topic-slug>-claude.md.hashes   # SHA-256 sidecar for the Claude-anchored canonical file
docs/duet/<topic-slug>-codex.md.hashes    # SHA-256 sidecar for the Codex-anchored canonical file
```

The working file is what each Phase 4 round's responder reads — it carries only still-`[PUSH-BACK]` items, so its size shrinks each round. The canonical file is the audit-grade history (every round, every concession, every quote). Only the canonical files are hashed; working files are derivable from canonical state.

Each debate file's structure (mirror image — substitute role names):

```markdown
# Duet ({Claude|Codex}-anchored): {short topic title}

**Outcome**: {Resolved at round N | N items unresolved after round 7 | User aborted}
**Companion file**: `<topic-slug>-{codex|claude}.md`

## Phase 1: Approved Prompt
{verbatim — duplicated identically in both files}

<details>
<summary>Q&A transcript (not seen by agents)</summary>
...
</details>

## Phase 2: {Claude|Codex}'s Report
{verbatim — full Phase 2 output from the anchor agent only}

## Phase 3: {Other agent}'s critique of {anchor}'s report
### Item: {topic}
Quoting {anchor}: "{verbatim span from Phase 2 above}"
Counter-evidence: {argument}
[PUSH-BACK | CONCEDE]
...

## Phase 4: Negotiation rounds (this file)
### Round 2 — {anchor} responds
#### Item: {topic from Phase 3}
Quoting {other}: "{verbatim from Phase 3 above}"
Response: {argument}
[CONCEDE | PUSH-BACK]
...
### Round 3 — {other} responds
...

## Phase 4 ledger (this file)
| Round | Items open at start | Items conceded | Items remaining |
| ... |

## Phase 5: Fact-check (this file)
### Claude's verdict
{verbatim}
### Codex's verdict
{verbatim}
### Corrections applied
{if any}
```

The synthesis file structure:

```markdown
# Duet Synthesis: {short topic title}

**Source files**: ...
**Outcome**: {N agreed items | M dispute(s)}

> Audited by Codex: APPROVE.    # Or omitted if Codex raised objections.

## Agreed findings
- **{topic}**
  - From Claude: "{verbatim — `claude.md:N`}"
  - From Codex: "{verbatim — `codex.md:N`}"
- ...

## Synthesis Disputes      # Empty section if Codex returned APPROVE.
- **{topic}**
  - Claude's proposed entry: ...
  - Codex's objection: "{verbatim}"
```

See `references/final-report-template.md` for the full annotated example.
````

- [ ] **Step 3: Update Token & Context Management**

Run: `Read ~/.claude/skills/duet/SKILL.md` (search for `## Token & Context Management`)
Expected: the existing 3-principle section.

Use `Edit` to replace the section. Match `old_string` from `## Token & Context Management` through `Worst case (5 contested items, all surviving 7 rounds) is ~200K tokens.` and replace with:

````markdown
## Token & Context Management

The "mountain of tokens" risk is mitigated by four principles:

1. **Stateless sessions.** Every Codex invocation is `--fresh`. Every Claude subagent is freshly spawned. No session accumulates context across rounds.

2. **Working file is the default per-round read.** During Phase 4, each round's responder reads a focused working file at `<topic-slug>-{role}.open.md` containing only the per-item trails for items still tagged `[PUSH-BACK]`. The agent additionally reads the Phase 2 anchor section of the canonical debate file (their own report — for grounding context), plus the Phase 1 approved prompt. The full canonical debate file is NOT loaded per round — it grows append-only as the permanent record, but the working file is what gets read live.

3. **Working file shrinks as the canonical file grows.** After each round, the orchestrator (a) inserts the agent's response verbatim into the canonical file, (b) appends those same per-item entries into the working file, then (c) prunes any items that just tagged `[CONCEDE]` or `[HOLD]` from the working file. So the working file size at Round N reflects open items only, not the full history.

4. **Two canonical files, no merged read.** The companion canonical file is available as a cross-reference but is not loaded by default. Phase 6 synthesis reads the two canonical files (not the working files — those are transient). At no phase does any agent read three files at once.

In typical sessions (most disagreements converge in 2-3 rounds per file), per-round reads stay under ~15K tokens because the working file holds only live items. Worst case (5 contested items per file, all surviving 7 rounds) is ~30-40K tokens per round read because the working file accumulates per-item trails but never the resolved-item trails. Total session token spend lands around 80-150K typical, ~200K worst case.
````

- [ ] **Step 4: Update Resume Mechanics**

Run: `Read ~/.claude/skills/duet/SKILL.md` (search for `## Resume Mechanics`)
Expected: the current resume section.

Use `Edit` to replace from `## Resume Mechanics` through `To detect the last completed round: read the doc, find the highest round marker that has both subsections fully populated (or all items resolved/conceded).` with:

````markdown
## Resume Mechanics

Two ways to resume an interrupted session:

1. **Explicit:** `/duet --resume docs/duet/<topic-slug>` (slug only — orchestrator will discover both `-claude.md` and `-codex.md`).
2. **Auto-detect:** bare `/duet` invocation. If exactly one in-progress session exists in `docs/duet/` (a session with at least one of the two files present and not yet at Phase 5 verdicts), prompt: *"Found a paused session at `<slug>` (Claude file paused at Round N_c, Codex file paused at Round N_d). Resume, or start fresh?"*

To detect the last completed round in each file: read the file, find the highest `### Round N — {agent} responds` heading whose section is fully populated. The two files may be at different rounds — that is expected.

On resume:
- If a file is mid-round (round was started but not completed), restore from `.bak.round-{N-1}` for that file and re-run the round.
- Files at different rounds resume independently.
- Hash sidecars are validated on resume — if the file's existing rounds don't match the sidecar, surface to user (the file may have been edited externally).
````

- [ ] **Step 5: Update the description in frontmatter**

The current description says "merges their findings". The two-file design has no merging; it has a synthesis pass at the end. This is a narrow factual fix to the description (NOT a rewrite for triggering — that change is parked per REPORT.md §4.3).

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 1, limit 5)
Expected: frontmatter with current description.

Use `Edit` to replace the description. Match `old_string`:

```
description: "Symmetric collaborative analysis workflow that orchestrates Claude and Codex into parallel independent work from an identical user-approved prompt, then merges their findings and negotiates disagreements over up to 7 rounds. Both agents receive identical input; refinement happens through the user, never via Claude-authored summaries. Use when the user invokes /duet or asks for parallel collaborative analysis with Codex."
```

with:

```
description: "Symmetric collaborative analysis workflow that orchestrates Claude and Codex into parallel independent work from an identical user-approved prompt, then runs a per-file cross-critique and negotiates disagreements over up to 7 rounds in two anchored debate files, ending with a synthesis pass. Both agents receive identical input; refinement happens through the user, never via Claude-authored summaries. Use when the user invokes /duet or asks for parallel collaborative analysis with Codex."
```

- [ ] **Step 6: Update the Important Rules section**

Run: `Read ~/.claude/skills/duet/SKILL.md` (search for `## Important Rules`)
Expected: the Important Rules bullet list at the bottom of SKILL.md.

Use `Edit` to update two bullets that reference the old single-doc structure. Match `old_string`:

```
- **One file per session.** Q&A transcript, Phase 2 reports, critique merge, negotiation log, and Phase 5 fact-check all live in `docs/duet/<topic-slug>.md`. Descriptive filename, no date prefix.
```

Replace with:

```
- **Three canonical files per session.** Two debate files (`<slug>-claude.md`, `<slug>-codex.md`) and one synthesis file (`<slug>-synthesis.md`). Plus two transient working files (`<slug>-claude.open.md`, `<slug>-codex.open.md`) live during Phase 4 only, and two `.hashes` sidecars on the canonical debate files. Descriptive slug, no date prefix.
```

Then in the same section update the orchestrator rule. Match `old_string`:

```
- **Verbatim only.** The orchestrator never paraphrases. Quotes are literal substrings of prior content.
```

Replace with:

```
- **Verbatim only.** The orchestrator never paraphrases. Quotes are literal substrings of prior content. The hash sidecar audit catches structural transcription drift.
```

- [ ] **Step 7: Verify the architecture sections are coherent**

Run: `grep -c "single document\|the document\|one file per session\|merged document" ~/.claude/skills/duet/SKILL.md`
Expected: 0 (all references to the old single-doc design are replaced).

Run: `grep -c "two files\|both files\|each file\|companion file\|synthesis" ~/.claude/skills/duet/SKILL.md`
Expected: at least 15.

Run: `grep -n "^## " ~/.claude/skills/duet/SKILL.md`
Expected: phase headings in order — Step A, Phase 1, Phase 2, Phase 3 (Cross-Critique), Phase 4 (Negotiation Rounds — up to 7 per file), Phase 5 (Fact-Check Pass), Phase 6 (Synthesis), Document Layout, Token & Context Management, Anti-Hallucination Guarantees, Error Handling, Resume Mechanics, Important Rules.

- [ ] **Step 8: Update the Architecture Overview block at top of SKILL.md**

Run: `Read ~/.claude/skills/duet/SKILL.md` (offset 17, limit 12)
Expected: the `## Architecture Overview` section with the 5-phase diagram and the line "The document on disk at `docs/duet/<topic-slug>.md` is the single source of truth across all phases."

Use `Edit` to replace from `## Architecture Overview` through the closing of the ascii diagram with:

````markdown
## Architecture Overview

Six phases. Two parallel debate files at `docs/duet/<topic-slug>-claude.md` and `<topic-slug>-codex.md` are the source of truth for the negotiation; a third file `<topic-slug>-synthesis.md` is produced in Phase 6 from those two. Every agent invocation is **stateless** — each round, each session starts `--fresh` and reads the relevant file from disk. No session memory is reused across rounds.

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
Prompt    Parallel   Cross-     Negotiate  Fact-     Synthesis
optimize  work       critique   (≤7 rds    check     (Claude
          (anchors   (per-item  per file,  (both     drafts,
          each       tagged     independ.) files)    Codex
          file)      directly                        audits)
                     into other
                     agent's
                     file)
```
````

- [ ] **Step 9: Commit**

Message: `duet: update document layout, token mgmt, resume, and overview for two-file design`

---

## Task 9: Self-review pass

**Why:** Catches inconsistencies introduced across Tasks 1-8 — type/name drift between sections, references to obsolete concepts, broken cross-references.

**Files:** All three modified files.

- [ ] **Step 1: Cross-file consistency grep**

Run each grep and confirm expected output:

```bash
# No leftover single-doc concepts anywhere
grep -rn "Best of the Best\|Subsection 1\|Subsection 2\|AGREED\|DISAGREED\|SINGLE-SOURCE\|merged critique\|merged document\|single document" ~/.claude/skills/duet/
```
Expected: zero matches.

```bash
# Phase 6 is referenced consistently
grep -rn "Phase 6\|synthesis.md\|Synthesis Disputes" ~/.claude/skills/duet/
```
Expected: at least 12 matches across the three files.

```bash
# Hash sidecar is referenced consistently
grep -rn "hashes\|sha256\|SHA-256" ~/.claude/skills/duet/
```
Expected: at least 8 matches.

```bash
# Codex envelope strip is documented
grep -rn "Codex session ID\|Resume in Codex\|envelope strip" ~/.claude/skills/duet/
```
Expected: at least 3 matches.

```bash
# Two-file architecture is the dominant frame
grep -rn "two files\|both files\|each file\|companion file" ~/.claude/skills/duet/
```
Expected: at least 18 matches.

```bash
# Working file is documented as the Phase 4 read target
grep -rn "open.md\|working file\|open items" ~/.claude/skills/duet/
```
Expected: at least 10 matches across SKILL.md, duet-prompts.md, and final-report-template.md. Spot-check that the Phase 4 prompt template points to the working file (not the canonical file) for reads, and that the canonical file is named for grounding context only.

```bash
# Canonical-vs-working terminology is consistent
grep -rn "canonical file\|canonical debate file" ~/.claude/skills/duet/
```
Expected: at least 6 matches. Confirms the docs distinguish canonical (audit-grade, append-only) from working (transient, derivable).

```bash
# Synthesis reads canonical only — no leak of working file into Phase 6
grep -rnE "synthesis.*open\.md|open\.md.*synthesis" ~/.claude/skills/duet/
```
Expected: zero matches (synthesis must never reference working files).

If any expectation fails, locate the gap and fix before continuing.

- [ ] **Step 2: Phase numbering walkthrough**

Open `~/.claude/skills/duet/SKILL.md` and read top-to-bottom. Confirm phase numbers in:
- Architecture overview ascii diagram (Phase 1-6)
- Section headings (Phase 1 through Phase 6)
- Cross-references in body text (e.g., Phase 5 mentions "after both debate files have terminated")
- Important Rules section (no leftover references to "Phase 1-5 only")

- [ ] **Step 3: Tag-name consistency**

Run: `grep -n "\[CONCEDE\]\|\[PUSH-BACK\]\|\[HOLD\]" ~/.claude/skills/duet/SKILL.md ~/.claude/skills/duet/references/duet-prompts.md`
Expected: tags appear consistently (`[CONCEDE]`, `[PUSH-BACK]`, `[HOLD]` — no rogue `[CONCEDED]` or `[PUSHBACK]` typos).

- [ ] **Step 4: Filename pattern consistency**

Run: `grep -n "topic-slug\|<slug>\|<topic" ~/.claude/skills/duet/SKILL.md ~/.claude/skills/duet/references/final-report-template.md`
Expected: pattern is consistent — primarily `<topic-slug>-claude.md` / `<topic-slug>-codex.md` / `<topic-slug>-synthesis.md` (with companion `.hashes` sidecars). Some prose may use `<slug>` shorthand — that's fine if explained on first use.

- [ ] **Step 5: No git commit needed for self-review (read-only verification)**

If issues were found and fixed, commit those fixes with message: `duet: fix cross-file inconsistencies surfaced by self-review`.

- [ ] **Step 6: Update task status**

Mark Task #1 (the implementation plan write-up — the parent task tracking *this* plan) as completed only after Tasks 1-9 of THIS plan are done. The plan itself is now ready for executing-plans to take over.

---

## Task 10: Verification — divergent-prompt smoke test

**Why:** The Definition of Done requires demonstrating that Phase 4 actually runs (≥1 round in at least one file) and that all DoD criteria are met end-to-end.

**Files:**
- Create: `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/duet-claude.md`
- Create: `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/duet-codex.md`
- Create: `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/duet-synthesis.md`
- Create: corresponding `.hashes` sidecars
- Create: `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/notes.md`

- [ ] **Step 1: Spawn a subagent for the smoke test**

This is a multi-minute Codex-driven workflow. Run it in a subagent so the main thread doesn't fill with verbose Codex output. Use the Agent tool with `subagent_type: "general-purpose"`.

Subagent prompt template (the executing engineer must adapt slightly with concrete file paths):

```
You are running a verification smoke test of the redesigned /duet skill at ~/.claude/skills/duet/.

The redesign just landed. You must run the skill end-to-end on a divergent prompt and capture all artifacts to ~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/.

Use this prompt for the /duet session (it's pre-approved — skip Phase 1 prompt iteration):

"Should we adopt event sourcing for our checkout service? We process ~10K orders/day, currently use a transactional MySQL system with audit logs, and the team has no prior event sourcing experience. Cover: scaling fit, ops burden, team learning curve, migration risk."

The Codex companion runtime is at: $(find ~/.claude/plugins/cache/openai-codex -name "codex-companion.mjs" -not -path "*/lib/*" | head -1)

Workflow:
1. Skip Phase 1 (prompt is pre-approved). Create the two debate file stubs at ~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/duet-{claude,codex}.md with Phase 1 sections containing the verbatim prompt.

2. Phase 2: dispatch Claude (a fresh subagent) and Codex (`node ... task --fresh`) in parallel with the Phase 2 prompt template from ~/.claude/skills/duet/references/duet-prompts.md. Strip Codex envelope lines. Hash each report and seed the .hashes sidecars. Append each report to its anchored file.

3. Phase 3: dispatch both agents in parallel with the Phase 3 prompt template (cross-critique). Strip Codex envelope. Hash. Append Codex's critique to duet-claude.md and Claude's critique to duet-codex.md.

4. Phase 4: run rounds until each file terminates. Snapshot before each round. Hash each round's output. End-of-round audit: structural + hash. Maximum 7 rounds per file. Cap total time at 30 minutes — if it's taking longer, stop and surface what's happened so far.

5. Phase 5: both agents fact-check both files. Append verdicts to each file.

6. Phase 6: Claude drafts synthesis.md. Codex audits. Apply any disputes. Final synthesis file written.

For each phase, follow the SKILL.md procedure exactly. Do not invent shortcuts.

Verification checklist (report on each at the end):
- [ ] Both files exist with anchored Phase 2 reports.
- [ ] Phase 3 produced tag-shaped output (### Item: ... [PUSH-BACK | CONCEDE]) that flows into Phase 4 with no orchestrator paraphrase.
- [ ] Phase 4 actually ran (≥1 round in at least one file).
- [ ] Hash sidecars exist for both debate files.
- [ ] End-of-round audit detected no drift (or did detect drift — report that too).
- [ ] Phase 5 verdicts both PASS for both files.
- [ ] Phase 6 produced synthesis.md (with Synthesis Disputes section if Codex objected).

Report under 800 words. Include the final outcome line of each file (Resolved at round N | unresolved after 7 | aborted) and the synthesis Outcome line.
```

- [ ] **Step 2: Review the subagent's report**

Confirm each verification checklist item:
- Files exist? Run `ls -la ~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/`
- Hash sidecars exist?
- Phase 4 ran ≥1 round? Inspect the debate files.
- Phase 5 verdicts both PASS? Grep for `## Fact-check result on` in both files; values should be `PASS` (or note specifically what failed).
- synthesis.md exists?

If verification fails, do not write the notes.md yet. Surface the failure to the user with concrete file pointers and ask whether to:
- (a) Re-run with adjustments
- (b) Treat the failure as a learning, fix the skill, then re-verify
- (c) Accept partial verification with a documented gap in notes.md

- [ ] **Step 3: Commit captured artifacts**

The eval-workspace is not a git repo, so artifacts are just file writes. Confirm they are present and readable. No commit step.

---

## Task 11: Write tier3 run-2 notes.md

**Why:** Definition of Done requires a one-paragraph summary at `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/notes.md`.

**Files:**
- Create: `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/notes.md`

- [ ] **Step 1: Draft the summary**

The note must cover:
- What changed in the skill since run-1 (two-file architecture, Phase 6 synthesis, hash sidecar, Codex envelope strip — one sentence each)
- What this divergent run confirmed (which DoD criteria PASSed, including specifically that Phase 4 ran ≥1 round)
- Anything notable that didn't go as expected (rounds taken, items conceded vs. held, hash audit hits if any)

Target: one paragraph, ~150 words. Concrete and falsifiable, not impressionistic.

- [ ] **Step 2: Write the file**

Use `Write` to create `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/notes.md` with the drafted paragraph. No frontmatter.

- [ ] **Step 3: Final check — Definition of Done walkthrough**

Open `~/.claude/skills/duet-eval-workspace/REDESIGN-PROMPT.md` and walk through each item in the "Definition of done" block. Confirm:

- [ ] `~/.claude/skills/duet/SKILL.md` updated to two-file architecture? (Task 8)
- [ ] `~/.claude/skills/duet/references/duet-prompts.md` updated? (Tasks 2-5)
- [ ] `~/.claude/skills/duet/references/final-report-template.md` updated? (Task 1)
- [ ] Hash sidecar implemented and documented? (Task 6)
- [ ] Codex envelope strip rule added? (Task 7)
- [ ] Divergent-prompt run with non-zero Phase 4 rounds, hash sidecar present, no audit drift, both Phase 5 verdicts PASS, Phase 6 synthesis produced? (Task 10)
- [ ] notes.md summary present? (this Task)

If any item is incomplete, fix before declaring done.

- [ ] **Step 4: Mark all parent tasks completed via TaskUpdate**

Mark Task #2, #3, #4 in the orchestrator's task list as completed once the corresponding plan tasks are done.

---

## Self-Review Notes (post-write)

This plan was written knowing:

1. **The skill directory is not a git repo** by default. The plan handles both cases (commit if repo, append to CHANGES.md otherwise) so the executing engineer doesn't need to detect this themselves.

2. **The verification step runs Codex through real CLI invocations** and may take 10-30 minutes. Spawned as a subagent (Task 10 Step 1) to keep the main thread's context clean.

3. **The plan does not change the skill's directory structure** — only file contents within the existing directory layout. No new skill files, no plugin manifest changes.

4. **The "description rewrite" item is partially in scope** despite the briefing saying it's parked: the architectural-accuracy fix (Task 8 Step 5) updates the description from "merges their findings" to reflect the two-file synthesis flow. This is a correctness fix, not a triggering rewrite — the parked item was the latter.

5. **Token management is structural, not a fallback.** Per-round reading scope is the working file (`<slug>-{role}.open.md`) plus the responder's own Phase 2 anchor — never the full canonical debate file. The two-file architecture is non-negotiable; the working file is the durable answer to token cost in late rounds.
