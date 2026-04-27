# /duet two-file redesign — fresh session prompt

You are picking up a redesign of the `/duet` skill at `~/.claude/skills/duet/`.
A prior session ran a Tier 1–3 evaluation, then brainstormed a structural fix
with the user. The eval is at `~/.claude/skills/duet-eval-workspace/REPORT.md`;
the original (now-superseded) remediation plan is at
`~/.claude/skills/duet-eval-workspace/REMEDIATION-PROMPT.md` — read it for
context but **do not execute it as written**. The user-approved design below
replaces several of its items wholesale.

## What changed since REMEDIATION-PROMPT.md

The blocker (F4.1 — Phase 3 output shape doesn't flow into Phase 4 Round 1)
was traced to the merged-document architecture itself: fusing two parallel
reports into one Best-of-the-Best + Discrepancies section creates a constant
paraphrase temptation and an artifact-shape mismatch the orchestrator can't
bridge legally. The user approved a two-file redesign that eliminates the
fusion step entirely.

## Locked design (do not re-brainstorm)

**Architecture.** Two parallel files instead of one merged doc:
- `File A` = Claude's Phase 2 report. Codex's critiques and Phase 4 responses
  append here.
- `File B` = Codex's Phase 2 report. Claude's critiques and Phase 4 responses
  append here.

Each file is a chronological debate thread anchored to one agent's original
report. The orchestrator inserts only round markers and verbatim agent output —
never fuses across files.

**Phase 3 (revised).** Each agent reads BOTH Phase 2 reports and writes a
critique of the OTHER agent's report, formatted as per-item tagged entries
(same shape as Phase 4 Round 1 — they flow directly):

```markdown
### Phase 3 critique by {Codex} of {Claude}'s report
#### Item: {topic, one noun phrase}
Quoting the other agent: "{verbatim span from Claude's report}"
Counter-evidence: {argument or agreement}
[PUSH-BACK | CONCEDE]
```

**No AGREED / DISAGREED / SINGLE-SOURCE classification step.** Items the
critic agrees with are `[CONCEDE]` from the start. Items they don't address
are silently absent.

**Phase 4 (revised).** Per round, two parallel invocations:
- In each file, whichever agent wasn't last to write is up next.
- Each file caps at 7 rounds and terminates independently.
- Agents may READ both files for context but WRITE only in their assigned
  file per round.
- `[CONCEDE]` / `[PUSH-BACK]` / `[HOLD]` semantics unchanged; `[HOLD]` only
  valid at Round 7.

The round-alternation table at SKILL.md:155-163 collapses to one rule:
*"each round, the agent who isn't last to write in a file appends their
response to the open items in that file."*

**Phase 5 fact-check.** Both agents fact-check positions across both files
(each agent's positions appear as claims in their own file and as critiques
in the other's). Output and PASS/ISSUES-FOUND format unchanged.

**Phase 6 — End-only synthesis (new).** After both files terminate:
1. Claude drafts `synthesis.md` listing every `[CONCEDE]`-tagged item plus
   items that received no opposing critique. Verbatim, attributed, with
   file+line pointers. No paraphrase.
2. Codex audits. Output: `APPROVE` or per-item objections with verbatim
   corrections.
3. Claude applies Codex's verbatim corrections. Items Codex disputes the
   inclusion of move to `## Synthesis Disputes` at the file end.
4. **One audit pass, no iteration loop** — disputes section is the safety
   valve.

When both agents have CONCEDE entries on the same topic with different
verbatim spans, include both spans, attributed. Provenance shape:
`From Claude: "{verbatim}"` / `From Codex: "{verbatim}"` as sub-bullets per
item (matches the existing `references/final-report-template.md:60-62` shape;
update that template if the synthesis layout differs anywhere).

## Surviving items from the prior remediation prompt

- **Hash sidecar (F6.1).** Still applies. On each agent's raw output, sha256
  before transcription, store in a `<filename>.hashes` sidecar; re-hash the
  verbatim block in the doc at end-of-round and compare. ~5-line addition to
  SKILL.md anti-hallucination section + a one-paragraph runbook entry. The
  Tier 3 ellipsis case (REPORT.md §5.3 item 4 / `tier3-behavioral/run-1/duet-output-doc.md:169`)
  is the canonical motivating example.
- **Codex CLI envelope strip.** Add a rule: strip runtime-emitted
  `Codex session ID:` and `Resume in Codex:` lines from Codex output before
  transcription.

Items that disappear under the new design (do not patch separately):
F4.2 (no classification step), F4.3 (alternation table is being rewritten,
not patched), F4.4 (no merged Discrepancies section to skip).

## Out of scope

- Description rewrites (F1.1 / F1.3 / F8.3) — REPORT.md §4.3 explains why
  Tier 2 is a harness artifact, not a description-quality signal. Park.
- The skill-creator harness itself.

## Process

1. **Use `TaskCreate`** to plan and track. Skip the brainstorming skill —
   design is locked.
2. **Use `superpowers:writing-plans`** to produce a written implementation
   plan from the locked design above, then `superpowers:executing-plans` to
   land the changes.
3. **Spawn subagents** to preserve context — especially for the verification
   smoke test (long Codex run) and any large reads (REPORT.md, the full
   prior duet output doc). Don't burn main-thread context on artifacts you
   only need a summary of.
4. **Push back on the design if implementation surfaces a real tension** the
   prior brainstorm missed — but raise it explicitly with the user, don't
   silently rework. The biggest area where this might happen: token cost of
   "read both files" during late Phase 4 rounds; if it's bad, propose a
   sliced-read mitigation rather than going back to merged docs.

## Verification

Run a divergent-prompt smoke test that actually exercises Phase 4 negotiation
(the prior Tier 3 run was too convergent — 0 rounds ran). Suggested prompts:
*"Should we adopt event sourcing for our checkout service?"* or *"Is React
Server Components the right default for a new Next.js app?"*

Capture artifacts to `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/`.
Confirm:
- Both files exist with anchored Phase 2 reports.
- Phase 3 produces tag-shaped output that flows directly into Phase 4 Round 1
  with no orchestrator paraphrase.
- Phase 4 actually runs (≥1 round in at least one file).
- Hash sidecar exists; end-of-round audit detects no drift.
- Phase 5 verdicts both PASS for both files.
- Phase 6 produces a `synthesis.md` (with `Synthesis Disputes` section if
  Codex objected to anything).

## Definition of done

- `~/.claude/skills/duet/SKILL.md` and
  `~/.claude/skills/duet/references/duet-prompts.md` updated to the new
  architecture; `references/final-report-template.md` updated to reflect
  two-file + synthesis layout.
- Hash sidecar implemented and documented.
- Codex envelope strip rule added.
- A divergent-prompt run with non-zero Phase 4 rounds, hash sidecar present,
  no audit drift, both Phase 5 verdicts PASS, Phase 6 synthesis produced.
- A 1-paragraph note at
  `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/notes.md`
  summarizing what changed and what the divergent run confirmed.
