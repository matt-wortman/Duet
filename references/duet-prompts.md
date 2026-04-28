# Duet Prompt Templates

All prompts use `{placeholder}` substitution. Both agents receive structurally identical prompts; only the role tags differ where the protocol calls for it. **Do not paraphrase or "improve" these templates per session — fidelity is part of the symmetric contract.**

---

## Phase 2 — Parallel Work Prompt

Used to dispatch the user-approved task to BOTH agents at the start of Phase 2. Codex is invoked with `--fresh`. Claude's parallel work uses the same prompt text in a fresh subagent (or in the main thread if Claude is doing the analysis directly).

```
You are one half of a /duet — a parallel collaborative analysis with the other agent (Claude or Codex). The other agent is independently working this same task right now. You will not see the other agent's work until both of you complete. Do not assume what the other agent will produce. Form your own view.

The user approved this prompt for both of us:

=== TASK ===
{user_approved_prompt}
=== END TASK ===

Read any referenced files yourself. Produce your work substantively — your output will be compared with the other agent's. Agreements between you will be locked in; disagreements will be negotiated round-by-round.

Structure your output so individual findings, claims, or recommendations can be referenced by the other agent. Use clear headings and numbered points where appropriate.
```

---

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

---

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

---

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
