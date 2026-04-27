# Remediation prompt — paste this into a fresh session

You are picking up a remediation pass on the `/duet` skill at
`~/.claude/skills/duet/`. A three-tier quality evaluation just completed;
the deliverable is at `~/.claude/skills/duet-eval-workspace/REPORT.md` and
the raw analysis is at `~/.claude/skills/duet-eval-workspace/tier1-static-review/findings.md`.

## Read first

1. `~/.claude/skills/duet-eval-workspace/REPORT.md` — §1 (Summary), §3.2
   (full findings table), §6 (Top-5 recommendations). 5 minutes.
2. `~/.claude/skills/duet/SKILL.md` and `~/.claude/skills/duet/references/duet-prompts.md`
   — the artifacts you'll be editing.
3. `~/.claude/skills/duet-eval-workspace/tier1-static-review/findings.md` —
   only when you need full context on a specific finding.

## Goal

Land the top recommendations from REPORT.md §6, in priority order. The skill
currently cannot run end-to-end on contentious prompts as written; both
problems below are the reason.

## Scope (in priority order)

1. **F4.1 — Phase 3 → Round 1 artifact mismatch (BLOCKER, design needed).**
   Rewrite the Phase 3 critique prompt at `references/duet-prompts.md:33-65`
   so that, *per DISAGREED item*, each agent emits: (a) the other's claim
   verbatim, (b) their counter-evidence, (c) a `[PUSH-BACK]` or `[CONCEDE]`
   tag. This unifies the artifact shape between Phase 3 and Phase 4 — the
   "the disagreer's initial critique IS Round 1" claim at SKILL.md:144 needs
   to actually be true. Then update SKILL.md:114-144 to match. **This is
   not mechanical — invoke `superpowers:brainstorming` first to get the
   design right before editing.**

2. **F6.1 — orchestrator-paraphrase hash check.** Add a sha256 hash check:
   when each agent's raw output is received, hash it before transcription
   and store the hash in a sidecar (e.g., `duet-output-doc.md.hashes`).
   At end-of-round audit, re-hash the verbatim block from the doc and
   compare. The Tier 3 run produced a real example of the failure mode
   (an orchestrator-applied `…` ellipsis that Phase 5 didn't catch — see
   REPORT.md §5.3 item 4). ~5-line addition to SKILL.md's anti-hallucination
   section + a one-paragraph runbook addition for the hash check itself.

3. **F4.3 — alternation contradiction.** Delete the parenthetical at
   `SKILL.md:151`. The round table at 155-163 and the Phase 4 prompt
   template at `references/duet-prompts.md:80` are coherent without it.

4. **The four Tier-3 protocol gaps (each a single-sentence SKILL.md addition):**
   - **Codex CLI envelope:** add a rule to strip runtime-emitted
     `Codex session ID:` and `Resume in Codex:` lines before transcription.
   - **Best-of-the-Best provenance shape:** SKILL.md:127-130 (flat bullets)
     and `references/final-report-template.md:60-62` (`From Claude:` /
     `From Codex:` sub-bullets) disagree. Pick one shape and update the other.
   - **Different verbatim spans of the same finding:** add — "if both agents
     support the same finding with different quote spans, include both
     verbatim, attributed."
   - **F4.2 classification merge:** add — "disagreement on classification
     (Claude AGREED vs. Codex SINGLE-SOURCE etc.) → defaults to DISAGREED →
     enters Phase 4."

## Out of scope (do not touch)

- Description rewrites (F1.1 / F1.3 / F8.3). REPORT.md §4.3 explains why
  they can't be calibrated yet — Tier 2 was a harness artifact for action-first
  skills, not a description-quality signal. Park these for after harness fixes.
- The skill-creator harness itself (`scripts.run_eval`). Separate concern.
- Other minors and nits in the findings table.

## Verification

After edits, run a divergent-prompt smoke test to actually exercise the
Phase 4 negotiation machinery (Tier 3's pagination prompt was too convergent —
0 rounds ran). Suggested divergent prompts: *"Should we adopt event sourcing
for our checkout service?"* or *"Is React Server Components the right default
for a new Next.js app?"* Capture artifacts to
`~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/`. Confirm:

- Phase 4 actually runs (≥1 round, tagged entries appear in the doc).
- The new Phase 3 prompt produces tag-shaped output that flows directly
  into Round 1 without orchestrator paraphrasing.
- The hash sidecar exists and end-of-round audit detects no drift.

## Definition of done

- `SKILL.md` and `references/duet-prompts.md` updated for items 1-4.
- A divergent-prompt run with non-zero Phase 4 rounds, hash sidecar present,
  no audit drift, both Phase 5 verdicts PASS.
- A 1-paragraph note at `~/.claude/skills/duet-eval-workspace/tier3-behavioral/run-2/notes.md`
  summarizing what changed and what the divergent run confirmed.

Please use TaskCreate to plan and the appropriate `superpowers:` skills as
you go (especially brainstorming for item 1 before editing).
