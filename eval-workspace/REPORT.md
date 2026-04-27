# Quality Evaluation: `/duet` skill

**Subject:** `/home/matt/.claude/skills/duet/` (SKILL.md 351 LOC + 2 reference files)
**Evaluator:** Claude Opus 4.7 (resumed session, 2026-04-27)
**Methodology:** Tier 1 static review · Tier 2 trigger benchmark (20 queries × 3 runs) · Tier 3 behavioral run
**Workspace:** `/home/matt/.claude/skills/duet-eval-workspace/`

---

## 1. Summary

**Overall verdict:** Strong protocol design with one structural gap (F4.1) that prevents the skill from running end-to-end on contentious prompts as currently written, and one anti-hallucination gap (F6.1) where verbatim discipline could be enforced structurally rather than relying on orchestrator self-policing. Recommend addressing both before broad use; remaining minors and nits are quality-of-life improvements. Tier 2 and Tier 3 produced limited signal due to a measurement artifact and a too-convergent test prompt respectively — both worth re-running once mitigations land.

**Headline findings:**

1. **F4.1 (blocker) — Phase 3 → Round 1 artifact mismatch.** The Phase 3 critique prompt produces symmetric two-position dumps; the merged-document layout expects single-quote critiques with `[PUSH-BACK]` / `[CONCEDE]` tags. The skill declares the gap closed by fiat at SKILL.md:144 but the prompt does not emit critiques. An orchestrator running the skill verbatim on a divergent prompt has no legal path to produce Round 1 — either it paraphrases (banned), invents tags (banned), or runs a hidden re-prompt (skill says no).
2. **F6.1 (major) — verbatim quote-check has an orchestrator-shaped hole.** SKILL.md:298's substring check verifies an *agent* didn't fabricate a quote, but not that the *orchestrator* didn't paraphrase while transcribing. Future rounds substring-match against the (paraphrased) doc, not against the agent's actual output. Phase 5 fact-check is the only gate, and Tier 3 produced a concrete live example: a self-disclosed orchestrator-applied ellipsis that both Phase 5 verdicts passed anyway. A 5-line sha256-hash patch closes this structurally rather than relying on Phase 5 discipline.
3. **Tier 2 (triggering benchmark): 0/30 trigger across all positive cases — but this is a harness measurement artifact, not a description-quality finding.** Two confounds in `scripts.run_eval` make `/duet` (and any "action-first" skill) unmeasurable: (a) the canonical `~/.claude/skills/duet/` competes with the harness's renamed clone for the same description and wins; (b) `run_eval.py:140-141` short-circuits whenever the first tool call is anything other than `Skill` or `Read` — and `/duet`'s first action is a Bash `find` for the Codex companion runtime. Three remediation options in §4.3; description rewrites are premature until one lands.
4. **Tier 3 (behavioral run): cleanly executed phases 1/2/3/5 in 7 minutes — but Phase 4 (negotiation rounds) was not exercised.** The pre-approved pagination prompt produced complete convergence between Claude and Codex, so 0 DISAGREED items reached Phase 4 (F4.4 short-circuit). F4.1's central hypothesis remains **live-untested**: the orchestrator never had to perform the forbidden artifact-shape transform. A divergent prompt is required to actually test the blocker.
5. **Tier 3 surfaced 4 protocol gaps not in Tier 1.** Codex CLI envelope handling (silent), Best-of-the-Best provenance shape inconsistency between SKILL.md:127–130 and final-report-template.md:60–62, missing guidance for merging different verbatim spans of the same finding, and the F6.1 live evidence above. All four are folded into §5.3 and §6.

**Read order:** §3.2 (full findings table) → §6 (recommendations) → §4 / §5 for context on what was and was not measured.

## 2. Strengths

(See Tier 1 for full citations. Highlights:)

- **Clear mental model.** SKILL.md:292 — *"The orchestrator (Claude main thread) is a scribe, not an editor"* — single sentence anchors the entire anti-hallucination contract.
- **Structurally sound tag protocol.** `[CONCEDE]` / `[PUSH-BACK]` / `[HOLD]` are explicit, machine-checkable tokens. Inferred concessions are explicitly forbidden (SKILL.md:297).
- **Phase 5 cross-check is the right belt-and-suspenders.** Both agents read the final doc with no session memory and flag misrepresentations — a structural counter to orchestrator drift.
- **Progressive disclosure works.** SKILL.md cites references inline at exactly the points they're needed (lines 87, 119, 218, 272). Each reference file is small (~150 LOC).
- **Imperative voice is consistent.** Reads as a runbook, not an essay.
- **Coherent pair with `/cowork`.** Both share Step A (Codex path discovery), the same `--write` prohibition, and the same "show everything live" rule. The deliberate `--fresh` (duet) vs. `--resume-last` (cowork) split is the right call for symmetric vs. adversarial protocols.

## 3. Findings

### 3.1 Severity counts

| Severity | Count |
|----------|-------|
| blocker | 1 |
| major | 3 |
| minor | 11 |
| nit | 4 |
| strength | 6 |

### 3.2 Findings table

| Sev | Category | Location | Issue | Recommendation |
|-----|----------|----------|-------|----------------|
| **blocker** | Protocol coherence | SKILL.md:114–144, references/duet-prompts.md:33–65 | **F4.1** — Phase 3 critique prompt outputs symmetric `## DISAGREED` two-position dumps; merged-doc structure expects Round 1 critiques with `[PUSH-BACK]` tags + critique framing. Orchestrator can't bridge the gap without paraphrasing (banned). Skill declares the gap closed by fiat at line 144 ("the disagreer's initial critique IS Round 1") but the prompt does not emit critiques — only positions. | Rewrite the Phase 3 prompt to ask each agent, *per DISAGREED item*, for: (a) the other's claim verbatim, (b) their counter-evidence, (c) a `[PUSH-BACK]`/`[CONCEDE]` tag. Unifies Phase 3/4 artifact shape. |
| major | Protocol coherence | SKILL.md:114–124 | **F4.2** — When the two classification passes disagree (Claude says AGREED, Codex says SINGLE-SOURCE; etc.) the merge logic is unspecified. These are common, not corner cases. | Add a "Reconcile classification disagreement" step: "Any item with disagreement on classification defaults to DISAGREED and enters Phase 4." |
| major | Protocol coherence | SKILL.md:151 vs. 155–163 vs. references/duet-prompts.md:80 | **F4.3** — Round-assignment alternation is internally contradictory: SKILL.md:151 says "alternating per item between originator and disagreer," but the round table at 155–163 fixes one role per subsection per round, and the Phase 4 prompt template only expresses one role per subsection. | Delete the parenthetical at line 151. The round table + prompt template are consistent without it. |
| major | Anti-hallucination | SKILL.md:298, 180–181, 190–192 | **F6.1** — The substring quote-check verifies an *agent* didn't fabricate a quote, but it does **not** verify the *orchestrator* didn't paraphrase the agent's response when transcribing it. Future rounds substring-match against the (paraphrased) doc, not against the agent's actual output. Phase 5 fact-check is the only gate that catches this. | Hash (sha256) each agent's raw output before transcription; store hashes alongside the doc; end-of-round audit re-hashes the verbatim block from the doc and compares. ~5-line change, closes the loop. |
| minor | Triggering | SKILL.md:3 | **F1.1** — Description's "Use when" anchors only on literal `/duet` and the jargon phrase "parallel collaborative analysis." Likely natural phrasings ("get a second take from Codex," "have Claude and Codex both look at X") are not anchored. | Expand "Use when" with 2–3 paraphrases. See finding for example wording. |
| minor | Structure | references/*.md | **F2.2** — Reference files don't link back to SKILL.md sections. A reader who lands on a reference can't quickly orient. | Add one-line back-pointers per template. |
| minor | Structure | SKILL.md:274–322 | **F2.3** — Token & Context / Anti-Hallucination / Error Handling are dense sequential prose. | Add a "summary box" listing the four invariants (verbatim, stateless, sliced, audited). |
| minor | Writing style | SKILL.md:70–74 | **F3.2** — "MUST NOT" list lacks rationale. The "why" is at line 15 but 55 lines away. | Inline a one-line rationale or back-reference. |
| minor | Protocol coherence | SKILL.md:149–212 | **F4.4** — If both Discrepancies subsections are empty after Phase 3, the skill doesn't say to skip to Phase 5. A literal reader could spawn empty rounds. | Add: "If both Discrepancies subsections are empty after Phase 3, skip directly to Phase 5." |
| minor | Protocol coherence | SKILL.md:222–223 | **F4.5** — Phase 5 fact-check can only "fix the specific line." If Best-of-the-Best contains a wrongly-promoted item, that needs a block-move + round-trail restoration, not a line edit. | "If correction implies wrong promotion, restore the item to its prior subsection from `.bak.round-N` and re-run fact-check." |
| minor | Edge cases | SKILL.md:192–193, 326–330, 351 | **F4.6** — Snapshot-restore base case unspecified. Round-1 has no `.bak.round-0`; corrupt/missing snapshots fall through to a generic /tmp emergency dump. | Add: "Round 1 audit-failure restores from the post-Phase-3 doc as `.bak.round-0`. Missing/corrupt snapshots surface to user with the in-progress doc path; do not blindly proceed." |
| minor | Protocol coherence | SKILL.md:339 | **F4.7** — Resume detection is ambiguous when one subsection is genuinely empty since Phase 3 ("all items resolved/conceded" applies trivially). | Mark empty subsections with `<!-- empty-since-phase-3 -->`; resume logic ignores marked subsections when judging round completeness. |
| minor | Edge cases | SKILL.md:199–203 | **F5.1** — Re-prompt fallback maps every malformed-output failure to `[PUSH-BACK]`. At Round 7, this erases the agent's chance to express `[HOLD]`. | At Round 7, fallback should default to user-prompt rather than auto-`[PUSH-BACK]`. |
| minor | Edge cases | SKILL.md:306–314 | **F5.2** — Codex-unavailable handler covers Phase 4 only. Phase 2 (one report missing) and Phase 5 (only one verdict) fallbacks are not specified. | Add explicit Phase 2 and Phase 5 fallbacks. |
| minor | UX | SKILL.md:92, 207–208 | **F7.1** — "Show the debate live" doesn't hold during Phase 2: Codex runs `run_in_background: true`, so the user sees Claude's work live but Codex is hidden until completion. | Tail Codex's bg output with progress markers, OR downgrade the promise: "Show the debate live during Phase 4. Phase 2 reports appear in batch." |
| minor | UX | SKILL.md:43–44, 336–340 | **F7.2** — Resume auto-detect doesn't define behavior for "zero in-progress sessions, bare `/duet`." | One sentence: "If zero in-progress sessions, proceed to Phase 1." |
| minor | UX | SKILL.md:43–44 | **F7.3** — Multi-session disambiguation undefined. | "If multiple in-progress sessions exist, list them with last-completed round and ask the user to pick." |
| minor | Consistency w/ /cowork | both descriptions | **F8.3** — Both descriptions begin "{Adjective} collaborative ... workflow that orchestrates Claude and Codex." A trigger model picking between them needs explicit contrast in the descriptions. | Add a "not /cowork" anchor to one or both descriptions. |
| nit | Triggering | SKILL.md:3 | **F1.2** — First sentence is jargon-heavy ("parallel independent work"); the body's framing is clearer. | Lead with body's phrasing. |
| nit | Triggering | SKILL.md:3 vs. cowork:3 | **F1.3** — Differentiation from /cowork is implicit (overlaps F8.3). | (Same as F8.3.) |
| nit | Protocol coherence | SKILL.md:178–179, 211–212 | **F4.8** — `[HOLD]` is "permanent dissent" but `[PUSH-BACK]` at Round 7 also is. Distinction never surfaces in the final doc. | Either lean in (make distinction observable in Final Summary), or drop `[HOLD]` and let `[PUSH-BACK]` at Round 7 carry both meanings. |
| nit | Edge cases | SKILL.md:316–322 | **F5.4** — User interrupt during Phase 1 not addressed. | Sentence: "Phase 1 is interactive — if user aborts, the doc is not yet created; nothing to clean up." |

(Strengths cited inline in §2 above; raw analysis in `tier1-static-review/findings.md`.)

## 4. Triggering benchmark

`scripts.run_eval` from `skill-creator` ran 20 candidate queries × 3 runs = 60 invocations against `claude-opus-4-7`. Headline summary `{total: 20, passed: 10, failed: 10}` is misleading: every "should-trigger" item failed by triggering 0/3, and every "should-not-trigger" item "passed" by triggering 0/3 (correct outcome by accident). The trigger rate is **0/30 on positives and 0/30 on negatives** — uniform across the eval set. **This is almost certainly a measurement artifact for action-first skills, not a description-quality finding.**

### 4.1 Per-query verdicts

| # | Query (truncated) | Should-trigger? | Triggered | Verdict |
|---|---|---|---|---|
| 1 | `/duet compare cursor vs offset pagination for our REST API` | yes | 0/3 | FAIL |
| 2 | `/duet` | yes | 0/3 | FAIL |
| 3 | `Run a duet on the auth refactor decision` | yes | 0/3 | FAIL |
| 4 | `Have Claude and Codex both analyze our caching strategy ind...` | yes | 0/3 | FAIL |
| 5 | `Get a second independent take from Codex on this migration...` | yes | 0/3 | FAIL |
| 6 | `I want parallel collaborative analysis with Codex on postgr...` | yes | 0/3 | FAIL |
| 7 | `Side-by-side analysis with Codex on REST vs GraphQL...` | yes | 0/3 | FAIL |
| 8 | `Run both you and Codex on this design question in parallel...` | yes | 0/3 | FAIL |
| 9 | `Symmetric analysis with Codex: both weigh in on auth model...` | yes | 0/3 | FAIL |
| 10 | `Have Claude and Codex independently review postgres-vs-mysql` | yes | 0/3 | FAIL |
| 11 | `Write a plan for the auth migration and have Codex critique...` | no | 0/3 | PASS |
| 12 | `Have Codex review my proposed plan adversarially and iterate` | no | 0/3 | PASS |
| 13 | `Ask Codex to fix this null pointer bug in the user service` | no | 0/3 | PASS |
| 14 | `Use Codex to write unit tests for this module` | no | 0/3 | PASS |
| 15 | `Implement a binary tree in Python with insertion and search` | no | 0/3 | PASS |
| 16 | `Analyze the parallel processing logic in worker.go for races` | no | 0/3 | PASS |
| 17 | `Refactor this function for clarity and add docstrings` | no | 0/3 | PASS |
| 18 | `Compare the two implementations of the rate limiter in file` | no | 0/3 | PASS |
| 19 | `Send this README to Codex for a quick proofread pass` | no | 0/3 | PASS |
| 20 | `How do I read both files and merge them in bash, second tak...` | no | 0/3 | PASS |

### 4.2 Aggregate

- **Should-trigger rate:** 0 / 30 (0%)
- **Should-not-trigger correct-by-accident rate:** 30 / 30 (vacuous — nothing ever triggered)
- **Harness summary:** `{total: 20, passed: 10, failed: 10}` — meaningless as a quality signal. A description that always returned "no trigger" would score identically.

### 4.3 Calibration commentary

**This is a harness measurement artifact, not a description failure.** Mechanism (verified by reading `run_eval.py:43–182` and a follow-up clean-room probe whose stream output was preserved at `/tmp/duet-probe-stream.json`):

1. The harness installs a renamed clone of the skill at `<project-root>/.claude/commands/{skill_name}-skill-{uuid}.md`.
2. A "trigger" is only counted if claude invokes the **Skill** (or **Read**) tool with the *renamed clone's* name in the input JSON (`run_eval.py:147`: `if clean_name in accumulated_json: return True`).
3. **Confound 1 — canonical-name preference.** The user has the original `duet` skill installed at `~/.claude/skills/duet/`. Both `duet` and `duet-skill-{uuid}` appear in the session-start system reminder with identical descriptions. With no signal to prefer one, claude picks the canonical `duet`. The renamed clone's name never appears in tool input → trigger counted as 0.
4. **Confound 2 — action-first short-circuit.** `run_eval.py:140-141` short-circuits to `return False` if any tool *other than* `Skill` or `Read` is the first tool call. The clean-room probe confirmed claude in `/duet -p` mode immediately invokes `Bash` (Step A: `find ~/.claude/plugins/cache/openai-codex -name "codex-companion.mjs"` to locate the Codex companion runtime). For *any* action-first skill (one whose first tool call is something other than Skill/Read), the harness will report 0% regardless of description quality.

**What it would take to actually measure /duet's description quality:**

- **(a) Uninstall the canonical clone** (`~/.claude/skills/duet/` and any plugin-shipped `duet`) before the eval run so the renamed clone is the only candidate. Cheapest one-shot fix; eliminates Confound 1 but leaves Confound 2.
- **(b) Patch `run_eval.py`** so a hit on the original skill name (or any skill whose description string-matches the candidate) also counts as a trigger, and remove or relax the Skill/Read first-tool gate at lines 140–141. Most general fix; benefits every action-first skill, not just `/duet`.
- **(c) Rewrite `/duet` to start with a `Skill` invocation** (e.g., a thin `duet-bootstrap` skill that then shells out) instead of a Bash `find`. Only option that also benefits cold-session real users — but a heavy lift for a measurement-only motivation.

**Recommendation:** description rewrite is premature until (a) or (b) gives a real signal. F1.1 / F1.3 / F8.3 stand on their own qualitative grounds, but their ranking in §6 should not be calibrated against this benchmark in its current form.

## 5. Behavioral run

A `general-purpose` subagent ran `/duet` end-to-end on a pre-approved test prompt: *"Compare two design approaches for adding pagination to a hypothetical REST API: cursor-based vs. offset-based. Make 4–6 numbered claims. Recommend one with brief justification."* The prompt was selected as a tractable smoke test; in retrospect it was **too convergent** to exercise the negotiation machinery (see 5.3).

### 5.1 Workflow execution

- **Phase 1:** skipped (pre-approved prompt).
- **Phase 2:** completed — both Claude and Codex produced reports independently.
- **Phase 3:** completed — both classification passes returned **0 DISAGREED items**. Per F4.4's escape hatch ("if both Discrepancies subsections are empty, log and skip to Phase 5"), the orchestrator skipped Phase 4 entirely.
- **Phase 4:** **skipped — 0 rounds run.** No `[PUSH-BACK]` / `[CONCEDE]` / `[HOLD]` tags were emitted. No `.bak.round-N>0` snapshots created (only the conservatively-named `.bak.round-0` from before Phase 3).
- **Phase 5:** completed — both Claude and Codex returned PASS verdicts on the final doc.
- **Wall time:** ~7 minutes (against a 45-minute cap).
- **Best of the Best:** 10 items — 6 multi-source AGREED findings (stability under concurrent writes, performance at depth, random-access UX favoring offset, sort-key requirement, default cursor recommendation, offset acceptable for small/static cases) + 4 SINGLE-SOURCE items each agent accepted from the other (cursor opacity / API evolution and operational observability from Claude; client/human simplicity and arbitrary-sorting flexibility from Codex).
- **Permanent dissent:** 0 items.

No blockers were encountered. The subagent did surface 4 protocol gaps (5.3) and self-flagged one minor non-verbatim transcription that both Phase 5 verdicts still passed.

### 5.2 Invariant checks

`audit-checks.py` (pre-written before the run) returned 3 of 6 checks failing. **None represent a real document defect** — the script's assertions assumed Phase 4 ran:

| Check | Result | Evidence |
|-------|--------|----------|
| `tag_presence` | ❌ FAIL (vacuous) | 0 round bullets to tag-check; no Round-N entries exist. |
| `snapshot_files` | ❌ FAIL (vacuous) | `max_round_in_doc=0`; no `.bak.round-N>0` files were ever expected. |
| `phase5_verdicts` | ❌ FAIL (script bug) | Both verdicts present in doc (Claude line 153, Codex line 175). The `split_sections` helper extracts only 24 bytes for the Phase 5 section, missing the body. Fix: replace per-section approach with a doc-wide regex search for both verdict headings. **Not a doc defect.** |
| `verbatim_quotes` | ✅ PASS (vacuous) | 0 quotes checked — no Round-N quote attribution to verify. |
| `round_consecutive` | ✅ PASS (vacuous) | 0 round items — sequence trivially in order. |
| `concession_promotion` | ✅ PASS (vacuous) | 0 `[CONCEDE]` items emitted; trivially nothing to promote. |

Net: the audit script provided essentially zero substantive validation in a Phase-4-skipped run. Most invariants weren't testable because the artifacts they check don't exist when Phase 4 is short-circuited.

### 5.3 Qualitative observations

**The convergence-coverage problem.** The pagination prompt is well-trodden territory and both agents converged on every substantive claim (cursor-by-default, with offset acceptable for small/static cases). The negotiation machinery — `[PUSH-BACK]` / `[CONCEDE]` / `[HOLD]` tags, per-round structure, snapshot-restore, Round-7 cap, `[CONCEDE]` → Best-of-the-Best promotion — was not exercised. **F4.1's central hypothesis** (Phase 3's two-position dump cannot legally be reshaped into Round 1's tagged single-quote form) **remains live-untested**: the orchestrator never had to perform the forbidden artifact-shape transform. A divergent prompt — e.g., "should we adopt event sourcing for our checkout service?" or "is React Server Components the right default for a new Next.js app?" — would force genuine disagreement and exercise Phase 4.

**Four protocol gaps surfaced by the live run** (worth folding into a v2 review):

1. **Codex CLI envelope.** Codex outputs end with runtime-emitted `Codex session ID:` / `Resume in Codex:` lines. SKILL.md is silent on whether these are content-to-quote-verbatim or transport metadata to strip. Subagent stripped them as a judgment call (`claude-subagent.log` lines 22–25). **Recommendation:** add a single sentence — "strip Codex CLI envelope lines (`Codex session ID:`, `Resume in Codex:`) before transcribing."
2. **Best-of-the-Best provenance shape inconsistency.** `SKILL.md:127–130` shows a flat single-bullet shape; `references/final-report-template.md:60–62` shows nested `From Claude:` / `From Codex:` sub-bullets. The two are inconsistent. Subagent followed the template. **Recommendation:** pick one and update the other.
3. **Different verbatim spans for the same finding.** When both agents quote the same finding from different parts of their own reports (Codex quoted bold headings; Claude quoted body sentences), SKILL.md is silent on how to merge. Subagent included both. **Recommendation:** add a one-line rule — "if both agents support the same finding with different quote spans, include both verbatim, attributed."
4. **Self-disclosed minor non-verbatim — concrete F6.1 evidence.** The subagent used a `…` ellipsis to elide the middle of one long sentence when promoting it into Best of the Best, then self-flagged the shortening in its own Phase 5 verdict (`duet-output-doc.md` line 169). Both agents' Phase 5 verdicts still returned PASS. This is exactly the F6.1 failure mode: detection here depended on the orchestrator volunteering the disclosure rather than any structural check. An unprincipled orchestrator could perform the same elision silently and Phase 5 would not catch it. The hash-check recommended in F6.1's remediation would have flagged this automatically.

**Note on the audit script bug.** The `phase5_verdicts: codex_verdict_present=False` failure is a script bug, not a doc problem. Easy fix: have `check_phase5_verdicts` do a doc-wide regex search for both `### Claude's verdict` and `### Codex's verdict` headings instead of relying on `split_sections` to extract the Phase 5 section body. Not patched in this report — left as a follow-up in `audit-checks.py`.

## 6. Top-5 recommendations (ranked by leverage)

1. **Fix F4.1 (the blocker).** Rewrite the Phase 3 prompt to produce Round 1 critiques with `[PUSH-BACK]` / `[CONCEDE]` tags, unifying the artifact shape between Phase 3 and Phase 4. Without this, the skill cannot run as written without an orchestrator paraphrasing (which it forbids). **Live-untested in Tier 3** — the convergent test prompt produced 0 DISAGREED items, so a divergent re-run (or an actual user invocation on a contentious prompt) is required to fully confirm the gap. Until then, treat F4.1 as a strongly-evidenced static finding waiting on dynamic confirmation.
2. **Add F6.1's hash check.** Five lines of code close the orchestrator-paraphrase gap that Phase 5 alone can't reliably catch. **Tier 3 produced concrete live evidence:** an orchestrator-applied `…` ellipsis silently elided sentence content when transcribing into Best of the Best; both Phase 5 verdicts still passed (the orchestrator self-disclosed, but a less-principled one would not). With sha256 of each agent's raw output stored alongside the doc and re-checked end-of-round, this becomes structurally enforced rather than disciplinary.
3. **Resolve F4.3 (alternation contradiction) and the four Tier-3 protocol gaps.** Single-sentence patches each: (a) delete the parenthetical at SKILL.md:151 — the round table and prompt template are coherent without it; (b) add a Codex-CLI-envelope stripping rule (`Codex session ID:` / `Resume in Codex:`); (c) unify Best-of-the-Best provenance shape between SKILL.md:127–130 and final-report-template.md:60–62; (d) add a "different-verbatim-spans-of-the-same-finding" merge rule. All five fit on one page of SKILL.md and remove sources of orchestrator improvisation.
4. **Specify F4.2 (classification merge).** A one-line policy ("disagreement on classification → DISAGREED → enters Phase 4") removes the most common source of orchestrator improvisation that Tier 1 found. Cheap, low-risk, immediately actionable.
5. **Patch the eval harness, not the description (yet).** F1.1 / F1.3 / F8.3 description improvements remain valid on qualitative grounds, but Tier 2's 0/30 result is a harness artifact (canonical-name preference + first-tool-must-be-Skill/Read short-circuit), not a description-quality signal. Either uninstall the canonical clone before re-running, or patch `run_eval.py` to count canonical-name triggers and drop the Skill/Read first-tool gate. Until one of these lands, description rewrites cannot be calibrated against measurement. Treat this as a recommendation about the *evaluation methodology* as much as the skill.

## 7. Appendix

- Tier 1 raw findings: `tier1-static-review/findings.md`
- Tier 2 eval set: `tier2-trigger-bench/eval_set.json`
- Tier 2 results: `tier2-trigger-bench/results.json`
- Tier 2 stderr: `tier2-trigger-bench/run-stderr.log`
- Tier 2 notes: `tier2-trigger-bench/notes.md`
- Tier 3 working doc: `tier3-behavioral/run-1/duet-output-doc.md`
- Tier 3 audit script: `tier3-behavioral/run-1/audit-checks.py`
- Tier 3 audit results: `tier3-behavioral/run-1/audit-checks.json`
- Tier 3 logs: `tier3-behavioral/run-1/codex-companion.log`, `claude-subagent.log`
