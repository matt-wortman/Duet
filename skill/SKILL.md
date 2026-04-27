---
name: duet
description: "Symmetric collaborative analysis workflow that orchestrates Claude and Codex into parallel independent work from an identical user-approved prompt, then runs a per-file cross-critique and negotiates disagreements over up to 7 rounds in two anchored debate files, ending with a synthesis pass. Both agents receive identical input; refinement happens through the user, never via Claude-authored summaries. Use when the user invokes /duet or asks for parallel collaborative analysis with Codex."
---

# Symmetric Collaborative Analysis: Claude + Codex

You are running a symmetric collaborative analysis session. Both agents start from an identical user-approved prompt, work independently in parallel, then cross-critique each other's reports across two anchored debate files and negotiate disagreements through structured rounds — ending with a synthesis pass that distills agreed findings.

## When to Use This vs Cowork

- **Use `/cowork`** for adversarial review of a single plan: Claude proposes, Codex critiques, Claude revises. Asymmetric — Claude is the proposer.
- **Use `/duet`** for parallel collaborative analysis: both agents do the work independently from the same brief, then reconcile. Symmetric — neither leads.

The contract: in `/duet`, both agents must receive IDENTICAL input. Claude never authors a summary or brief that biases the other agent's reasoning.

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

## Step A: Codex Path Discovery

Find the Codex companion runtime dynamically. Do NOT hardcode versioned paths.

```bash
find ~/.claude/plugins/cache/openai-codex -name "codex-companion.mjs" -not -path "*/lib/*" | head -1
```

Store the result as `CODEX_PATH`. If empty, tell the user:
> Codex companion not found. Install the openai-codex plugin first, then retry.

Also verify Codex is authenticated (a small `node "$CODEX_PATH" --version` or equivalent ping). Stop the workflow if Codex is unavailable.

Pre-flight checks before continuing to Phase 1:
- `docs/duet/` exists and is writable (create if missing)
- If `--resume <path>` was provided, the file exists and contains valid round markers
- If no `--resume` flag, scan `docs/duet/` for incomplete sessions; if exactly one found, ask the user: resume or start fresh
- For new sessions, plan to seed `<topic-slug>-claude.md.hashes` and `<topic-slug>-codex.md.hashes` at the start of Phase 2 (one entry per agent's raw report). See "Per-Round Hash Audit" under Anti-Hallucination Guarantees.
- The two working files (`<topic-slug>-{claude,codex}.open.md`) are NOT created at session start — they're initialized at the start of Phase 4 from each canonical file's Phase 3 `[PUSH-BACK]` entries. No working file is needed if a file's Phase 3 produced zero `[PUSH-BACK]` items (full convergence — skip directly to Phase 5 for that file).

## Phase 1: Collaborative Prompt Optimization

The goal of Phase 1 is to produce a single approved prompt that will be sent to both agents verbatim.

1. **Read referenced files for context only.** Do NOT produce a summary. The user's input is the user's input — your job is to refine it WITH them, not for them.

2. **Ask clarifying questions one at a time.** Soft cap of 3–5 questions total.
   - Discipline rule: only ask if the answer would meaningfully sharpen the prompt for both agents.
   - Stop early if the prompt is already tight.
   - Can extend past 5 only if the user is actively pushing.
   - Question style: concrete and answerable, not framing-laden.

3. **Draft the OPTIMIZED PROMPT.** This is the literal text both agents will receive. Show it to the user with these options:
   - **approve** — sign off, lock the prompt
   - **edit** — user provides inline changes; you incorporate, show the full revised prompt again
   - **rewrite** — user takes the keyboard

   Each iteration shows the FULL prompt, not a diff.

4. **What you ARE allowed to do** while drafting:
   - Tighten phrasing
   - Fold the user's Q&A answers into the prompt
   - Suggest scope boundaries the user implied (flag as a suggestion)
   - Propose a deliverable shape (flag as a suggestion)

5. **What you MUST NOT do**:
   - Insert opinions or framing the user didn't endorse
   - Pre-bias toward an answer
   - Hide changes
   - Author a summary that stands in for the user's input

6. **On approval**, write the prompt as `## Phase 1: Approved Prompt` in BOTH `docs/duet/<topic-slug>-claude.md` and `docs/duet/<topic-slug>-codex.md` — duplicated identically so each canonical file is self-contained. Filename: descriptive slug, NO date prefix. The third canonical file `<topic-slug>-synthesis.md` is created later in Phase 6.

   Save the Q&A transcript inside a `<details>` block below the prompt in BOTH files for the record. **Neither agent will see the Q&A** — both see only the final approved prompt.

## Phase 2: Parallel Work

Both agents receive the IDENTICAL approved prompt. Both write blind — neither sees the other's output until both complete.

### Dispatch to Codex (background)

Use the Phase 2 prompt template from `references/duet-prompts.md`, substituting `{user_approved_prompt}` with the locked `## Phase 1: Approved Prompt` text (identical in both canonical files).

```bash
node "$CODEX_PATH" task --fresh "$(cat "$PHASE2_PROMPT_FILE")" \
  | sed -E '/^Codex session ID:/d; /^Resume in Codex:/d' \
  > "$CODEX_RAW_OUTPUT"
```

Run with `run_in_background: true` so Claude can do its parallel work without blocking. The `sed` filter strips Codex CLI envelope lines before the output is captured (see "Codex CLI envelope strip" under Anti-Hallucination Guarantees). The same filter must be applied to Codex output in Phase 3, Phase 4 rounds, Phase 5, and Phase 6 audit.

### Claude's parallel work (main thread)

Same prompt text. Same task. Read referenced files yourself. Produce a substantive report. Do NOT speculate about what Codex might write.

### When both complete

Each report becomes the anchor of its own canonical file. Hash each agent's raw output (after Codex envelope strip) BEFORE transcription and seed the two `.hashes` sidecars (see "Per-Round Hash Audit" under Anti-Hallucination Guarantees).

Append to `docs/duet/<topic-slug>-claude.md` (Claude's anchored debate file):

```markdown
## Phase 2: Claude's Report

{claude_report_verbatim}
```

Append to `docs/duet/<topic-slug>-codex.md` (Codex's anchored debate file):

```markdown
## Phase 2: Codex's Report

{codex_report_verbatim}
```

Reports do NOT cross files — Claude's report lives only in `<slug>-claude.md`, Codex's only in `<slug>-codex.md`. The companion agent's report appears in the other file via Phase 3 critique quotes.

## Phase 3: Cross-Critique

Each agent reads BOTH Phase 2 reports and writes a critique of the OTHER agent's report. Critiques are written **directly into the other agent's debate file** as per-item tagged entries with the same shape as Phase 4 round responses — they flow into Round 1 with no transformation.

Items the critic agrees with are tagged `[CONCEDE]` from the start and never enter the round count. Items the critic does not address are silently absent — convergence by silence.

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

## Phase 5: Fact-Check Pass

Once both canonical debate files have terminated (each independently), fact-check both canonical files. Working files are not part of fact-check — they're a transient view, not the record. Each agent reads BOTH canonical files because their positions appear in both: as the Phase 2 anchor in their own file, and as critiques + responses in the other file.

Send each agent (both `--fresh`) the Phase 5 prompt from `references/duet-prompts.md`, with both canonical file paths embedded. Each agent confirms:

1. In the canonical file anchored to them: is their Phase 2 report quoted accurately when the other agent critiques it? Are their `[CONCEDE]` decisions and arguments preserved verbatim?
2. In the other canonical file: are their critiques (Phase 3) and round responses (Phase 4) preserved verbatim, with correct round attribution?
3. Are any of their arguments quietly softened, dropped, or merged across rounds?

If either agent flags a misrepresentation, the orchestrator fixes the specific line in the canonical file (verbatim from the agent's correction, with hash sidecar updated) and re-runs the fact-check on that file. Otherwise, both canonical files are final.

After Phase 5 passes for both files, delete the two working files (`<slug>-{claude,codex}.open.md`) — their purpose was Phase 4 only.

Append a `## Phase 5: Fact-check (this file)` section to EACH canonical file recording both agents' verdicts on that file.

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

## Token & Context Management

The "mountain of tokens" risk is mitigated by four principles:

1. **Stateless sessions.** Every Codex invocation is `--fresh`. Every Claude subagent is freshly spawned. No session accumulates context across rounds.

2. **Working file is the default per-round read.** During Phase 4, each round's responder reads a focused working file at `<topic-slug>-{role}.open.md` containing only the per-item trails for items still tagged `[PUSH-BACK]`. The agent additionally reads the Phase 2 anchor section of the canonical debate file (their own report — for grounding context), plus the Phase 1 approved prompt. The full canonical debate file is NOT loaded per round — it grows append-only as the permanent record, but the working file is what gets read live.

3. **Working file shrinks as the canonical file grows.** After each round, the orchestrator (a) inserts the agent's response verbatim into the canonical file, (b) appends those same per-item entries into the working file, then (c) prunes any items that just tagged `[CONCEDE]` or `[HOLD]` from the working file. So the working file size at Round N reflects open items only, not the full history.

4. **Two canonical files, no merged read.** The companion canonical file is available as a cross-reference but is not loaded by default. Phase 6 synthesis reads the two canonical files (not the working files — those are transient). At no phase does any agent read three files at once.

In typical sessions (most disagreements converge in 2-3 rounds per file), per-round reads stay under ~15K tokens because the working file holds only live items. Worst case (5 contested items per file, all surviving 7 rounds) is ~30-40K tokens per round read because the working file accumulates per-item trails but never the resolved-item trails. Total session token spend lands around 80-150K typical, ~200K worst case.

## Anti-Hallucination Guarantees

The orchestrator (Claude main thread) is a **scribe, not an editor**:

- Verbatim insertion of agent responses under the correct item — no rewording.
- No cross-file merging — each debate file is single source of truth for its anchor agent. Synthesis (Phase 6) is the only place content from both files appears together, and even there the orchestrator only applies Codex's audit fixes literally (quote correction, dispute relocation), never authors prose.
- Round-marker insertion only.
- Tag-based protocol: orchestrator only acts on `[CONCEDE]` / `[PUSH-BACK]` / `[HOLD]` tags. Inferred concessions are forbidden.
- Quote verification: all attributions to the other agent must exist verbatim in prior content.
- End-of-round structural audit catches any drift.
- Phase 5 fact-check is the final guard against subtle misrepresentation.
- **Codex CLI envelope strip:** before transcribing any Codex output, remove runtime-emitted lines matching `^Codex session ID:` and `^Resume in Codex:`. These are CLI artifacts, not agent content. Strip BEFORE hashing (so the hash represents the substantive output, not the CLI envelope).

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

## Error Handling

### Codex unavailable mid-session

Pause. Save state. Tell the user:
> Codex unreachable at Round {N} in `{slug}-{role}.md`. Both canonical files saved. Choose: retry now / pause and resume later / ship as-is (each canonical file's current ledger + a partial Phase 6 synthesis over already-conceded items).

### Rate limit / transient failure

Backoff: 30s → 90s → 240s. Three attempts, then fall through to "Codex unavailable" handler.

### User interrupt

Doc is always in a consistent state because rounds commit atomically. On interrupt:
- Mid-round: in-flight round was not committed → on resume, re-run that round.
- Between rounds: doc is clean → resume picks up at the next round.
- During Phase 2: finished agent's report is saved; on resume only the unfinished agent re-runs.

User can interrupt at natural checkpoints (Phase 1 approval, post-Phase 2, post-Phase 3, between Phase 4 rounds in either file, post-Phase 5, post-Phase 6 audit) or via Ctrl+C.

### Round audit failure

Restore from `.bak.round-{N-1}` and re-run. If audit fails twice in a row, surface to user — likely indicates an upstream parsing bug.

### Filesystem errors

Surface immediately. Attempt to write state to `/tmp/duet-emergency-{timestamp}.md`, exit with the path.

## Resume Mechanics

Two ways to resume an interrupted session:

1. **Explicit:** `/duet --resume docs/duet/<topic-slug>` (slug only — orchestrator will discover both `-claude.md` and `-codex.md`).
2. **Auto-detect:** bare `/duet` invocation. If exactly one in-progress session exists in `docs/duet/` (a session with at least one of the two files present and not yet at Phase 5 verdicts), prompt: *"Found a paused session at `<slug>` (Claude file paused at Round N_c, Codex file paused at Round N_d). Resume, or start fresh?"*

To detect the last completed round in each file: read the file, find the highest `### Round N — {agent} responds` heading whose section is fully populated. The two files may be at different rounds — that is expected.

On resume:
- If a file is mid-round (round was started but not completed), restore from `.bak.round-{N-1}` for that file and re-run the round.
- Files at different rounds resume independently.
- Hash sidecars are validated on resume — if the file's existing rounds don't match the sidecar, surface to user (the file may have been edited externally).

## Important Rules

- **Run the orchestrator in the main thread.** Phase 2 work and Phase 4 rounds spawn fresh subagents/Codex sessions, but the orchestrator coordinates from the main conversation thread.
- **Symmetric input is non-negotiable.** Both agents see the same user-approved prompt. Phase 2 is identical text. Phase 4 prompts use the same template per agent.
- **No `--write` flag.** This is analysis/planning, not code execution.
- **Verbatim only.** The orchestrator never paraphrases. Quotes are literal substrings of prior content. The hash sidecar audit catches structural transcription drift.
- **Show everything live.** The user sees the full debate as it happens.
- **Three canonical files per session.** Two debate files (`<slug>-claude.md`, `<slug>-codex.md`) and one synthesis file (`<slug>-synthesis.md`). Plus two transient working files (`<slug>-claude.open.md`, `<slug>-codex.open.md`) live during Phase 4 only, and two `.hashes` sidecars on the canonical debate files. Descriptive slug, no date prefix.
- **Stateless sessions.** Always `--fresh`. Never `--resume-last`.
- **Re-prompt budget = 2.** No silent loops; surface to user after 2 retries.
- **Snapshot before each round.** `.bak.round-{N-1}` before round N starts.
