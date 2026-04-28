Plan a refined version of the duet skill simplification.

## Setup

The cwd is `~/.claude/skills/duet/`. Relevant paths (relative to repo root):
- `SKILL.md` (~521 lines) — the current `/duet` skill
- `plans/snoopy-sniffing-axolotl.md` — the in-progress plan to refine
- `eval-workspace/tier3-behavioral/run-2/` — paused evaluation artifacts

`/duet` is a Claude Code skill at `SKILL.md` that orchestrates two agents — Claude (main thread) and Codex (via the OpenAI codex plugin's `codex:codex-rescue` subagent) — to do parallel work on a user-approved prompt, cross-critique, and negotiate convergence in a multi-round file-based debate.

The current design accumulated heavy ceremony defending one specific concern: that Claude (the orchestrator) might paraphrase Codex's output when transcribing it into the canonical debate file. Today's machinery — per-agent hash sidecars, per-round end-of-round hash audits, `.bak.round-N` snapshots, derived `.open.md` working files — all exists to detect or recover from transcription drift.

The plan's central claim: **the entire scribe-verification pillar exists to defend a transcription step that doesn't need to exist.** If each agent writes its own section directly (Codex via the `codex:codex-rescue` subagent's `--write` capability, Claude via native Write/Edit), there is no transcription, and the audit machinery defending it becomes structurally unnecessary.

The claim is right in spirit but needs careful stress-testing on three points.

## Focus area 1 — stress-test the central insight

The current plan repeatedly says "each agent owns its own file." That phrasing is misleading. SKILL.md Phase 4 (lines 160–235) makes both agents alternate writes into BOTH files within rounds:

- In `<slug>-claude.md` (Claude-anchored): Round 2 = Claude writes, Round 3 = **Codex** writes, Round 4 = Claude, Round 5 = Codex, …
- In `<slug>-codex.md` (Codex-anchored): Round 2 = Codex writes, Round 3 = **Claude** writes, Round 4 = Codex, Round 5 = Claude, …

The actual claim is: **each agent writes its own section/round directly into whichever file it is authoring this turn.** "Anchor" only refers to whose Phase 2 report sits at the top of a given file. Correct this framing throughout the refined plan.

With the corrected framing, stress-test the simplification on these concrete cases — name what breaks and propose a fix, or confirm it is fine and explain why:

1. **Phase 4 Round 3+ in `<slug>-claude.md`.** Codex must read Claude's prior round response from earlier in the same file, then append `### Round 3 — Codex responds` without disturbing the Phase 2 anchor, the Phase 3 critique, or Round 2. With `--write`, Codex has filesystem write access across the whole sandbox; only the prompt constrains where it writes. What stops Codex from rewriting prior content while "appending"? See focus area 2 for the containment design.

2. **Verbatim quoting.** SKILL.md:208–209 requires Phase 4 quotes to be contiguous verbatim substrings of the prior round. Today Claude (the scribe) ensures byte-exact insertion, and the hash audit catches drift. Tomorrow, the writer agent quotes itself from a file it just read — does the existing `Failed quote verification` re-prompt path (SKILL.md:242) cover this on its own, or is a new check needed?

3. **Round handoff context / token budget.** Today each round's responder reads the working file (open items only, ~5–10K tokens). Tomorrow, with no working file, each responder reads the full canonical file. Estimate the worst-case token-per-round delta at Round 7 of a contested file (5+ open items). If the delta is unacceptable, propose a lighter alternative (e.g., a per-round "open items" section the writer maintains inline at the top of the file before each round) — but don't reintroduce a derived working file with its own derivation rules.

4. **Parallel-Codex risk.** In rare round-skew configurations, both files may need Codex in the same step (e.g., `<slug>-claude.md` at Round 5 = Codex's turn AND `<slug>-codex.md` at Round 4 = Codex's turn). Two simultaneous `codex-companion task` invocations may serialize through the broker or conflict. Today's design has the same risk; flag whether the redesign should explicitly serialize Codex calls or accept the existing behavior.

5. **Silent-failure surface left by removing hashes.** The hash audit catches *structural* drift — truncation, line-ending change, accidental block deletion — not semantic. The existing re-prompt budget table (SKILL.md:241–244) covers missing tags, failed quotes, empty responses, but not "Codex wrote into the wrong file or stomped a prior section." Identify any silent-failure path the audit used to catch and propose a lightweight replacement, OR argue persuasively that focus area 2's containment makes it unnecessary.

If any of (1–5) breaks the simplification, name it concretely and propose what to do. If none do, say so explicitly — don't paper over.

## Focus area 2 — verify codex:rescue's capability surface and propose --write blast-radius containment

**Operational facts (verified, do not re-derive — but do reference them in the plan):**

- The rescue subagent makes one Bash call to `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task ...` and returns stdout verbatim (agents/codex-rescue.md).
- It defaults to `--write` unless the user explicitly opts out for read-only / review work (codex-rescue.md line 34).
- The `/codex:rescue` command only skips its resume-or-fresh `AskUserQuestion` prompt if the request includes `--fresh` or `--resume` (commands/rescue.md lines 21–22). **Therefore /duet must always pass `--fresh` on every codex:rescue dispatch** — without it, the user is interrupted on every round. SKILL.md:519 already mandates this for v1; confirm the discipline carries over and call it out as a non-negotiable.
- `codex-companion.mjs` accepts `--write` in `task` mode (usage line, codex-companion.mjs:80).

**Conflict with current SKILL.md:** SKILL.md:515 says: "**No `--write` flag.** This is analysis/planning, not code execution." The simplification *requires* `--write` so Codex can author its own debate sections — but `--write` gives Codex filesystem write access to the whole workspace, not just `docs/duet/<slug>-*.md`. A poorly-scoped or adversarial user prompt under the new design could direct Codex to modify source files outside `docs/duet/`.

**Required design decision** — pick one approach (or propose another) and write the explicit rule into the refined plan, replacing SKILL.md:515:

a. **Prompt-level discipline.** Every codex:rescue invocation includes "Append your output ONLY to `<exact-path>`. Do not create, modify, or delete any other file." Combined with `--fresh`, this is the cheapest option but trusts the agent.

b. **Post-write structural verification.** Claude reads the file after Codex writes, confirms the expected heading was added, prior sections unchanged, file grew rather than shrank. Failure → restore from a single before-Phase-4 backup and surface to user.

c. **Workspace-level guard.** Initialize `docs/duet/` as its own git scope (or take a pre-round git snapshot) and reject any change that touches paths outside it.

d. Other.

Whichever you pick, do NOT silently drop SKILL.md:515 — replace it with the new rule.

## Focus area 3 — migration path

The user has already ruled out two of the four options the original plan invited:

- **No parallel skill** (no `/duet-lite` — original plan line 73, "Out of scope").
- **No flag-gated dual paths** — user feedback prefers simple primitives over `--legacy` modes.

The in-flight evaluation at `eval-workspace/tier3-behavioral/run-2/` is *not* active work. Its files froze ~3 hours before the synthesis hashes were last touched in a partial Phase-6c attempt that hit the bwrap sandbox limitation noted in the plan. **It is a paused-at-Phase-6c session, not work in progress.** The eval *methodology* (does the workflow produce productive disagreement?) is design-agnostic and survives a redesign; only the specific run-2 artifacts are tied to v1.

**Default migration recommendation to pressure-test (agree, refine, or disagree by step):**

1. Formally conclude run-2 by appending a one-line note to its synthesis file ("audit step skipped — bwrap limitation, terminating per current state") and treat its outputs as a final v1 record.
2. Git-tag the current SKILL.md as `duet-v1-pre-simplify` so it is recoverable.
3. Hard-cut: replace SKILL.md in place with the simplified version. No flag, no v1/v2 alongside, no `--legacy`.
4. Note in the plan that future eval runs re-baseline against the simpler design.

If you disagree with any step, name which and why. Otherwise fold these into the plan as the Migration section and remove the enumeration of rejected alternatives.

## Constraints (from user feedback — non-negotiable)

- **Skills over plugins.** Don't propose moving /duet to a plugin.
- **Simple primitives over custom orchestration.** Reuse `Agent(subagent_type="codex:codex-rescue")`, native Read/Write/Edit. Don't rebuild what the platform provides.
- **Symmetric input.** Both agents receive the IDENTICAL user-approved prompt verbatim. Claude never authors a summary or brief that biases the other agent's reasoning. The simplification preserves this; do not weaken it.

## Deliverable

1. The refined plan, written back to `plans/snoopy-sniffing-axolotl.md`. Keep what is right; sharpen what is wrong; cut what is wasted. Target length ~250 lines.
2. Below the refined plan in the same file, a "What I changed and why" summary (~300 words, max ~600). Call out anywhere you disagreed with the original plan or with the framing in this prompt.

Be willing to disagree. If after stress-testing you conclude that the simplification is unsafe or under-specified beyond what a single revision can fix, say so explicitly and propose what additional analysis or prototyping is needed before committing to the change.
