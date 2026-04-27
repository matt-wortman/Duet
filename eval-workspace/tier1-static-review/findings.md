# Tier 1 — Static Review Findings

Source files reviewed:
- `/home/matt/.claude/skills/duet/SKILL.md` (351 lines)
- `/home/matt/.claude/skills/duet/references/duet-prompts.md` (150 lines)
- `/home/matt/.claude/skills/duet/references/final-report-template.md` (159 lines)
- `/home/matt/.claude/skills/cowork/SKILL.md` (204 lines, comparison anchor only)

Severity rubric:
- **blocker** — workflow can't run as written without an orchestrator papering over it
- **major** — protocol gap that allows a careless orchestrator to silently violate the skill's own contract
- **minor** — ambiguity or missing edge-case handling; orchestrator can guess but shouldn't have to
- **nit** — wording or polish; no functional risk

---

## 1. Frontmatter description

### F1.1 [minor] Description trigger anchors are narrow vs. natural-language phrasings
**Location:** SKILL.md:3 (frontmatter `description`)
**Quote:** *"Use when the user invokes /duet or asks for parallel collaborative analysis with Codex."*

The "Use when" clause anchors on two phrases: literal `/duet` and "parallel collaborative analysis with Codex." Real users almost never type "parallel collaborative analysis." Likely natural phrasings the description does not anchor:
- "get a second take from Codex on X"
- "have Claude and Codex both look at X and reconcile"
- "I want both AIs to analyze this independently"
- "side-by-side analysis with Codex"
- "have Codex analyze this in parallel with you"
- "double-check by running this through both"

skill-creator's guidance is to be "a little pushy" — overtrigger > undertrigger when the action is reversible (the user can always say no). The current phrasing leans under-trigger.

**Recommendation:** Expand "Use when" with 2–3 natural-language paraphrases, e.g.:
> Use when the user invokes /duet, asks for parallel collaborative analysis with Codex, wants Claude and Codex to independently analyze the same task and reconcile, or asks for a "second take" / side-by-side / parallel review with Codex.

### F1.2 [nit] First sentence is jargon-heavy
**Location:** SKILL.md:3
The phrase "Symmetric collaborative analysis workflow that orchestrates Claude and Codex into parallel independent work" is dense. The body opens better ("Both agents start from an identical user-approved prompt, work independently in parallel, then merge their findings"). Consider leading with the body's framing in the description.

### F1.3 [nit] Differentiation from /cowork is implicit
**Location:** SKILL.md:3 vs. cowork/SKILL.md:3
Both descriptions begin with "{Adjective} collaborative ... workflow that orchestrates Claude and Codex." A user comparing them must parse "symmetric" vs. "adversarial" and "analysis" vs. "planning." The body of duet (lines 10–13) makes the distinction crisp; the description doesn't. A trigger model evaluating which of the two skills to load when the user says "have Claude and Codex review this plan" needs the description-level contrast to be clear.

**Recommendation:** Add a "not /cowork" anchor to one or both descriptions, e.g., for duet: "use /cowork instead if Claude is the proposer and Codex is the critic."

---

## 2. Body length / progressive disclosure

### F2.1 [strength, no action] References are pulled in only when needed
SKILL.md cites references at exactly the points where they're needed:
- Line 87: Phase 2 prompt template
- Line 119: Phase 3 critique prompt
- Line 218: Phase 5 fact-check prompt
- Line 272: Final report template (annotated)

Each pointer is in-line, named, and the file is small (150 / 159 lines). Good progressive disclosure.

### F2.2 [minor] References do not link back to SKILL.md sections
**Location:** references/duet-prompts.md, references/final-report-template.md
A reader who lands on a reference (e.g., from a search hit) cannot quickly orient: "where in SKILL.md is this used?" One-line back-pointers per template would help. Low-cost.

### F2.3 [nit] SKILL.md body is 351 lines — fine, but dense
At 351 lines the file is well under the 500-line soft cap. However, lines 274–322 ("Token & Context Management" + "Anti-Hallucination Guarantees" + "Error Handling") are dense sequential prose with no scannable summary. A short "summary box" up top listing the four invariants the skill enforces (verbatim, stateless, sliced, audited) would help fast scanners.

---

## 3. Writing style

### F3.1 [strength, no action] Mental model is explicit
**Location:** SKILL.md:292 — *"The orchestrator (Claude main thread) is a scribe, not an editor"*
This single sentence does most of the heavy lifting for the anti-hallucination contract. It anchors all the rigid rules to a clear role.

### F3.2 [minor] "MUST NOT" list at lines 70–74 lacks rationale
**Location:** SKILL.md:70–74
> What you MUST NOT do:
> - Insert opinions or framing the user didn't endorse
> - Pre-bias toward an answer
> - Hide changes
> - Author a summary that stands in for the user's input

The "why" is in line 15 ("Claude never authors a summary or brief that biases the other agent's reasoning") but is 55 lines away. Either inline a one-liner in this MUST NOT block, or add a back-reference: "See line 15 — symmetric input contract."

### F3.3 [strength, no action] Imperative form is consistent
The skill is uniformly imperative ("Read", "Send", "Append", "Surface", "Restore"). Easy to follow as a runbook.

---

## 4. Protocol coherence

### F4.1 [BLOCKER] Phase 3 output does not match Phase 3 merged-doc structure
**Location:** SKILL.md:114–141, references/duet-prompts.md:33–65, SKILL.md:144

The Phase 3 critique prompt (duet-prompts.md:33–65) tells each agent to output classifications:
```
## DISAGREED
- **{topic}**:
  - Your position: {verbatim from your report}
  - Other's position: {verbatim from other report}
```

The merged-document layout in SKILL.md (lines 132–141) expects:
```
#### Subsection 1: Claude found, Codex disagrees
- **Item A:** {Claude's finding}
  - **Codex (Round 1):** "On line {N} you said '{quote}', but I disagree because {evidence}." [PUSH-BACK]
```

These are different artifacts. The Phase 3 prompt produces a *symmetric two-position dump* with no [PUSH-BACK] tag and no "but I disagree because {evidence}" critique form. The merged doc shows *adversarial round-1 critiques with terminal tags*. Line 144 declares the gap closed by fiat — *"The disagreer's initial critique IS Round 1. No separate 'round 1' pass is needed"* — but this only holds if you redefine the merged doc to be the verbatim DISAGREED block, dropping the [PUSH-BACK] tags and the critique-style framing.

For an orchestrator to produce the merged doc as shown at lines 132–141 from the actual Phase 3 prompt outputs, it must either:
1. Synthesize the [PUSH-BACK] tag (orchestrator authoring tags is paraphrasing — banned by line 297 *"Inferred concessions are forbidden"* — by symmetry inferred push-backs should also be banned),
2. Synthesize the "but I disagree because {evidence}" framing (paraphrasing — banned by line 145 *"Never paraphrase agent output"*), or
3. Run an extra hidden Round 1 pass (the skill says no).

This is the central protocol gap. Either the Phase 3 prompt needs to produce Round 1 critiques (with tags + verbatim quotes + evidence), or the merged-doc structure needs to drop the tag and critique framing for Round 1 entries (and the round table at lines 155–163 needs to be updated so Round 1 is genuinely "no responses yet, just the two positions").

**Recommendation:** Adopt option 1. Rewrite the Phase 3 prompt to ask each agent for, *per DISAGREED item*: (a) the other's claim verbatim, (b) their counter-evidence, (c) a [PUSH-BACK] tag (or [CONCEDE] if they're persuaded on review). This unifies the artifact shape across Phase 3 and Phase 4 and removes the orchestrator's temptation to paraphrase.

### F4.2 [major] Merge logic when the two classification passes disagree is unspecified
**Location:** SKILL.md:114–124

Each agent independently classifies findings into AGREED / DISAGREED / SINGLE-SOURCE. The orchestrator then "merges the two classification passes into the working document structure" (line 117). What happens when:
- Claude classifies finding X as AGREED, Codex classifies X as SINGLE-SOURCE (Codex didn't notice it)?
- Claude classifies X as DISAGREED, Codex classifies X as AGREED?
- Both classify X as SINGLE-SOURCE but each says the *other* sourced it?

These are common, not corner cases — two agents will frequently disagree about which buckets findings belong in. The skill is silent.

**Recommendation:** Add a "Step 3c: Reconcile classification disagreement" with a deterministic policy — e.g., "any item with disagreement on classification defaults to DISAGREED and enters Phase 4," with a one-line rationale.

### F4.3 [major] Round-assignment alternation is internally contradictory
**Location:** SKILL.md:151 vs. SKILL.md:155–163 vs. references/duet-prompts.md:80

Line 151:
> Within each round, both subsections are worked in parallel — Codex writes in Subsection 1, Claude writes in Subsection 2 (**or vice versa, alternating per item between originator and disagreer**).

The bolded clause suggests *per-item* alternation. But the round table at 155–163 fixes a *per-round-per-subsection* assignment (Round 2: Claude in S1, Codex in S2; Round 3: Codex in S1, Claude in S2; etc.). And the Phase 4 prompt template (duet-prompts.md:80) says *"YOUR ROLE THIS ROUND in {subsection_name}: {originator | disagreer}"* — singular, one role per subsection per round.

If alternation is per-item within a subsection, then half the items in a subsection are written by one agent and half by the other in the same round. The Phase 4 prompt template can't express that without restructuring.

**Recommendation:** Delete the parenthetical at line 151. The table at 155–163 plus the prompt template are consistent and clear on their own; the parenthetical adds nothing but ambiguity.

### F4.4 [minor] Phase 4 short-circuit when Discrepancies is empty is implicit
**Location:** SKILL.md:149–212

If Phase 3 produces zero items in either Discrepancies subsection (both agents agreed on everything), Phase 4 has nothing to negotiate. The skill does not explicitly say "if Discrepancies is empty after Phase 3, skip to Phase 5." A literal reader could spawn empty rounds.

**Recommendation:** Add to Phase 4 opening: "If both Discrepancies subsections are empty after Phase 3, skip directly to Phase 5."

### F4.5 [minor] Phase 5 cannot demote items from Best-of-the-Best
**Location:** SKILL.md:222–223
> *"If either agent flags a misrepresentation, the orchestrator fixes the specific line (verbatim from the agent's correction) and re-runs the fact-check."*

The most likely Phase 5 finding is *"Item X in Best-of-the-Best was promoted from Subsection 1 at Round 4 — I never CONCEDE'd, the orchestrator misread my [PUSH-BACK] tag."* Restoring that item requires moving a block from Best-of-the-Best back into Discrepancies and re-establishing its round trail — not a single-line fix. The skill's "fixes the specific line" framing doesn't cover this.

**Recommendation:** Add a clause: "If a fact-check correction implies an item was wrongly promoted, restore it to its prior subsection with its full round trail (use the most recent `.bak.round-N` snapshot), then re-run fact-check."

### F4.6 [minor] Snapshot-restore base case unspecified
**Location:** SKILL.md:192–193, 326–330, 351
The audit-failure recovery path is "restore from `.bak.round-{N-1}`." But what if:
- The snapshot for round N-1 is corrupt or zero-byte?
- The user manually deleted snapshots between rounds?
- Round 1 audit fails (there is no `.bak.round-0`)?

Filesystem-error handling at lines 326–330 catches it generically (write to `/tmp/duet-emergency-{ts}.md` and exit), which loses the in-flight state for ~no reason. The Round-1 case is a real one and worth a sentence.

**Recommendation:** Add: "If `.bak.round-{N-1}` is missing or corrupt, surface to the user with the path to the in-progress doc; do not blindly proceed. Round 1 audit-failure restores from the post-Phase-3 doc, which is the natural pre-Round-1 snapshot — take it as `.bak.round-0`."

### F4.7 [minor] Resume detection is ambiguous when one subsection is genuinely empty
**Location:** SKILL.md:339
> *"To detect the last completed round: read the doc, find the highest round marker that has both subsections fully populated (or all items resolved/conceded)."*

If Subsection 2 was empty from Phase 3 onward (e.g., Codex had no unique findings), then "all items resolved/conceded" applies trivially every round, and the heuristic always picks the highest round marker — even if that round is mid-flight on Subsection 1. A genuinely empty subsection should not satisfy "resolved/conceded" by default; it should be explicitly marked complete.

**Recommendation:** When merging Phase 3, mark each empty subsection with a `<!-- empty-since-phase-3 -->` HTML comment. Resume logic ignores empty-since-phase-3 subsections when judging round completeness. Cheap.

### F4.8 [nit] [HOLD] tag is semantically redundant
**Location:** SKILL.md:178–179, 211–212
[HOLD] is "only valid at Round 7" and "signals a permanent dissent." But [PUSH-BACK] at Round 7 *also* becomes a permanent dissent (line 211–212: *"End of Round 7: anything still in the Discrepancies section is a permanent dissent"*). So the tag distinguishes "intentional dissent" from "still arguing but ran out of rounds" — a real semantic difference, but the skill never makes it observable in the final doc layout (`final-report-template.md:85` shows `[HOLD]` in one example and `[PUSH-BACK]` would render the same way visually). Either lean in (make the distinction surface in the Final Summary), or drop [HOLD] and let [PUSH-BACK] at Round 7 carry both meanings.

---

## 5. Edge cases / error handling

### F5.1 [minor] Re-prompt fallback contradicts Round 7 tag rules
**Location:** SKILL.md:199–203
The re-prompt budget table maps every kind of malformed-output failure to "treat as PUSH-BACK." At Round 7, [PUSH-BACK] and [HOLD] are both meaningful (per F4.8). The fallback erases the agent's chance to express [HOLD] when its output was malformed. Probably fine in practice (the user gets surfaced after 2 retries anyway), but worth a sentence: at Round 7, the fallback should default to user-prompt rather than auto-PUSH-BACK.

### F5.2 [minor] Codex unavailable during Phase 1 or Phase 5 not addressed
**Location:** SKILL.md:306–314
The "Codex unavailable mid-session" handler is framed around Round N (Phase 4). What if Codex is unreachable during Phase 1 (clarifying questions are Claude-only, so this is fine), Phase 2 (one agent's report missing — the skill needs to either pause or downgrade to single-agent analysis), or Phase 5 (final fact-check has only Claude's verdict)? The skill should explicitly cover Phase 2 and Phase 5 fallbacks.

### F5.3 [strength, no action] Backoff schedule and retry cap are reasonable
30s → 90s → 240s with 3 attempts is sensible for transient API issues. The fall-through to the manual handler is correct.

### F5.4 [nit] User interrupt during Phase 1 is not addressed
**Location:** SKILL.md:316–322
Phase 1 is interactive — the user can abort mid-Q&A. The skill describes interrupt handling for Phase 2 and Phase 4 rounds, but not Phase 1. Likely no action needed beyond "the doc isn't created until prompt is approved" — but worth a sentence.

---

## 6. Anti-hallucination guarantees

### F6.1 [major] Quote-substring check is weaker than the verbatim claim
**Location:** SKILL.md:298, 180–181, 190–192

The skill claims *"Quote verification: all attributions to the other agent must exist verbatim in prior content"* (line 298). Implementation: a substring match against the prior round's content in the doc.

This catches one class of hallucination (an agent inventing a quote) but does **not** catch the orchestrator paraphrasing the agent's own response while transcribing it into the doc. Sequence:
1. Codex emits a Round 3 response: `"Your line 5 said 'X', but Y, therefore Z. [PUSH-BACK]"`
2. Orchestrator transcribes it (incorrectly paraphrased) as: `"Your line 5 said 'X', but Y', therefore Z'. [PUSH-BACK]"` — Y' and Z' are slight rewording.
3. The orchestrator's quote of Codex's prior content (line 5: 'X') is correct → substring check passes.
4. End-of-round audit passes.
5. Round 4 from Claude correctly substring-matches against Y' / Z' as written, → substring check passes.
6. Codex's actual Y / Z are gone from the record. Phase 5 fact-check is the *only* gate that can catch this, and only if Codex notices its position is misrepresented (no session memory: must infer from context).

The real verbatim guarantee is "the orchestrator does not paraphrase when transcribing." That's *discipline*, not a structural check. The substring quote-check is a structural check on agent outputs *given* the doc is faithful — it does not verify the doc is faithful to agent outputs.

**Recommendation:** Add a structural check: hash (sha256) each agent's raw response output before transcription, and store the hashes alongside the doc. End-of-round audit recomputes hashes from the transcribed verbatim block — if they differ, the orchestrator paraphrased. This is a 5-line change and closes the loop. (See also Tier 3 audit-checks design.)

### F6.2 [strength, no action] Tag protocol is structurally sound
[CONCEDE] / [PUSH-BACK] / [HOLD] are explicit, machine-checkable tokens. Inferred concessions are forbidden. This part of the contract is well-designed and machine-verifiable.

### F6.3 [strength, no action] Phase 5 cross-check is the right belt-and-suspenders move
Having both agents read the final doc with no session memory and flag misrepresentations is the right structural counter to F6.1. Combined with F6.1's hash check it would be near-impenetrable.

---

## 7. UX

### F7.1 [minor] "Show the debate live" is aspirational during Phase 2 background work
**Location:** SKILL.md:92, 207–208
Phase 2 dispatches Codex with `run_in_background: true`. The orchestrator does its parallel work in the main thread. The user sees Claude's work live, but Codex's is hidden until it completes (line 100: "When both complete"). The skill's overall promise of "show the debate live" (line 207) doesn't quite hold during Phase 2.

**Recommendation:** Either tail Codex's bg output and show progress markers, or downgrade the promise: "Show the debate live during Phase 4. Phase 2 reports appear in batch when both complete."

### F7.2 [minor] Resume auto-detect is undefined when no in-progress sessions exist
**Location:** SKILL.md:43–44, 336–340
The resume logic covers (a) explicit `--resume <path>`, (b) bare `/duet` with exactly one in-progress session, and (c) bare `/duet` with multiple in-progress sessions. The "zero in-progress sessions, bare `/duet`" case is left implicit — assumed to flow into Phase 1. Fine, but a sentence ("If zero in-progress sessions, proceed to Phase 1") removes the ambiguity.

### F7.3 [minor] Multi-session disambiguation when more than one is in-progress
**Location:** SKILL.md:43–44
If the user has two paused sessions (interrupted earlier work), bare `/duet` does not specify what to do. Line 43 says "if exactly one found, ask the user." If multiple found, the skill is silent. List them and ask which? Refuse and require `--resume <path>`?

**Recommendation:** "If multiple in-progress sessions exist, list them with their last-completed round and ask the user to pick one (or to start fresh)."

---

## 8. Consistency with /cowork

### F8.1 [strength, no action] Voice and structure align
Both skills use Step A (Codex path discovery), the same `find ~/.claude/plugins/cache/openai-codex` command, the same imperative voice, the same "show everything live" rule, and the same `--write` flag prohibition. They feel like a coherent pair.

### F8.2 [observation, no action] Codex session continuity differs deliberately
- /cowork uses `--resume-last` for rounds 2–5 (cowork/SKILL.md:102).
- /duet uses `--fresh` for every Codex invocation (duet/SKILL.md:88, 349).

This is the right call for the symmetric protocol — `--fresh` ensures the agent re-reads the doc each round and has no "head start" the other lacks. /cowork's `--resume-last` also makes sense for an asymmetric back-and-forth where Codex maintains its critique stance across revisions.

### F8.3 [minor] Both descriptions could explicitly distinguish themselves from each other
See F1.3. As a coexisting pair, each description should mention the other to help the trigger model route.

---

## Findings summary by severity

| Severity | Count | Notes |
|----------|-------|-------|
| blocker  | 1 | F4.1 (Phase 3 prompt vs. merged-doc structure mismatch) |
| major    | 3 | F4.2 (classification merge), F4.3 (alternation contradiction), F6.1 (verbatim weaker than claimed) |
| minor    | 11 | F1.1, F2.2, F2.3, F3.2, F4.4, F4.5, F4.6, F4.7, F5.1, F5.2, F7.1, F7.2, F7.3, F8.3 |
| nit      | 4 | F1.2, F1.3 dup, F4.8, F5.4 |
| strength | 6 | F2.1, F3.1, F3.3, F5.3, F6.2, F6.3, F8.1, F8.2 |

The single blocker (F4.1) plus the three majors (F4.2 / F4.3 / F6.1) are the bulk of what a fix-pass would target. The minors are individually small but add up — most are one-or-two-sentence additions that close ambiguity.
