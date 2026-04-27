# /duet simplification plan

## Context

You asked: *"we have gone through so much optimization simply to get two agents to negotiate a plan using a file. why have we deviated from the simple tools that we already have and that work now. wouldn't it have been simpler just to use the codex tools we have and architect around them?"*

The skill's complexity is real and the critique lands. Concrete evidence from the current `~/.claude/skills/duet/SKILL.md`:

- **Transport bypass.** Line 97 calls `node "$CODEX_PATH" task --fresh ...` directly. The platform already provides `codex:codex-rescue` at `~/.claude/plugins/cache/openai-codex/codex/1.0.4/agents/codex-rescue.md` — a thin forwarder whose entire job is to dispatch Codex, strip CLI envelope, and return stdout verbatim. /duet reimplements it inline including the same `sed -E '/^Codex session ID:/d; /^Resume in Codex:/d'` envelope strip.
- **Custom state ceremony.** Each session produces: 3 canonical files (`-claude.md`, `-codex.md`, `-synthesis.md`), 2 working files (`.open.md`), 2 hash sidecars (`.md.hashes`), per-round `.bak.round-N` snapshots. The hash-audit and working-file derivation machinery is ~150 lines of SKILL.md.
- **Why the ceremony exists.** It defends against one specific failure mode: Claude paraphrasing Codex's output during transcription. Phase 4 has Claude read Codex's response, then write it into the canonical file as a "verbatim scribe." Hashes verify Claude didn't drift.

The deepest observation: **the entire scribe-verification pillar exists because we assumed Claude must transcribe Codex.** That assumption is wrong on this platform. Codex's native file-write capability is real and works (your `/tmp/codex-filetest.txt` test confirmed this 30 minutes ago). If each agent writes its own section directly, there is no transcription step, and the audit machinery defending it becomes unnecessary.

## Recommendation: simplify around two principles

**Principle 1 — Use the existing transport.** Replace direct `codex-companion.mjs` invocations with `Agent(subagent_type="codex:codex-rescue", prompt=...)`. The rescue subagent handles dispatch, envelope strip, and error surfacing. /duet stops carrying that code.

**Principle 2 — Each agent owns its own file.** Codex writes directly into `<topic>-codex.md` via codex:rescue with file-write permission. Claude writes directly into `<topic>-claude.md` using its own Write/Edit tools. No agent ever transcribes the other. The "verbatim scribe contract" disappears, and so does its supporting machinery.

## Concrete changes to /duet

**Delete:**
- All hash sidecar logic (`.md.hashes` files, sha256 append-on-write, end-of-round audit, restoration-on-mismatch). ~80 lines under "Per-Round Hash Audit" in SKILL.md.
- Working file derivation (`<topic>-{claude,codex}.open.md`, the prune-resolved-items rules). The `[PUSH-BACK]`/`[CONCEDE]` tagging stays — but reading-context discipline becomes "read the file, focus on tagged-open items" rather than maintaining a derived working file.
- Per-round `.bak.round-N` snapshots. If recovery is needed, git or single before-Phase-4 backup is enough.
- The Codex envelope-strip incantation duplicated across phases. codex:rescue handles it.
- The Codex-path-discovery preamble (Step A, lines 33–44). The rescue subagent owns this.

**Replace:**
- Every `node "$CODEX_PATH" task --fresh "..."` call with `Agent(subagent_type="codex:codex-rescue", prompt="...")`. SKILL.md lines 97, plus equivalent calls in Phase 3, Phase 4, Phase 5, Phase 6.
- Phase 4 round mechanics: instead of "Claude reads Codex's response, transcribes verbatim into canonical file, hash-audits, then drafts own response," the new flow is: dispatch both agents in parallel via codex:rescue and main-thread Claude — each writes their own section directly to their own anchored file.

**Keep:**
- Phase 1 (prompt optimization) — this is where Claude's value is concentrated and needs no Codex.
- Phase 2 (parallel work) — already maps cleanly to the new transport.
- Phase 3 (cross-critique) and Phase 4 (negotiation rounds) — still useful, just simpler internally.
- Per-file independent termination from SKILL.md:228–235 — sound design, no change.
- Phase 6 synthesis — but the audit step (which is what hit the bwrap wall in the run-2 session) becomes opt-in. Default skill flow ends after negotiation converges.

## Critical files

- `~/.claude/skills/duet/SKILL.md` — the main rewrite target. Currently 521+ lines, target ~250.
- `~/.claude/skills/duet/references/duet-prompts.md` — phase prompt templates need updates so Codex is told to write directly rather than return a report Claude will transcribe.
- `~/.claude/skills/duet/references/final-report-template.md` — synthesis template likely unchanged.

## Existing primitives this plan reuses

- `~/.claude/plugins/cache/openai-codex/codex/1.0.4/agents/codex-rescue.md` — the codex transport.
- `~/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs` — already supports `--write` flag for filesystem write capability.
- Claude Code's native `Agent`, `Read`, `Write`, `Edit` tools — sufficient for everything else.

## Tradeoffs and what we lose

- **Audit-grade scribe integrity.** Today, hash audits prove Claude transcribed Codex losslessly. After the change, the file *is* what Codex wrote — so transcription drift is impossible by construction, but if Codex writes something we don't expect, there's no Claude-side guard. This feels like a win (fewer ways to be wrong) rather than a loss.
- **The `tier3-behavioral/run-2/` evaluation.** That run was conducted under the current design and validated the scribe-contract behavior. A redesign doesn't invalidate the eval *methodology* (the eval workspace measures whether agents disagree productively, which is design-independent), but the specific run-2 artifacts are tied to the current SKILL.md. Future eval runs would re-baseline against the simpler design.
- **Resumability of in-flight sessions.** Any session captured in current canonical-file format would not load cleanly in the new flow. Either gate the change behind a SKILL version bump, or hold until run-2 wraps.

## Verification

End-to-end test of the simplified skill:

1. `/duet brainstorm a small architecture decision` (e.g., "should we use SQLite or DuckDB for X")
2. Confirm Phase 1 produces a locked prompt as today.
3. Confirm Phase 2 dispatches Codex via `codex:codex-rescue` subagent (not direct `node ... codex-companion.mjs`). Verify by checking the agent dispatch in transcript.
4. Confirm both agents' Phase 2 reports land in their respective canonical files without Claude transcribing.
5. Confirm no `.hashes` sidecar is created.
6. Confirm Phase 3 cross-critique works: each agent appends to the other's file directly.
7. Confirm Phase 4 converges or hits round cap, files terminate independently.
8. Re-test on Ubuntu 24.04+ (this machine) to confirm bwrap restriction no longer matters — codex:rescue dispatches the rescue subagent which will pick the working Codex code path automatically.

## Out of scope

- Building a separate `/duet-lite` and keeping `/duet` heavyweight. One skill, simplified.
- Touching the eval workspace (`~/.claude/skills/duet-eval-workspace/`) or any of its CHANGES.md tasks.
- Finishing the paused 6c on the run-2 directory (the user can do that with the current design or skip it as discussed).
