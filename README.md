# Duet

`/duet` is a Claude Code skill that orchestrates a symmetric collaborative analysis between Claude (main thread) and Codex (via the OpenAI codex plugin). Both agents start from an identical user-approved prompt, work independently, then cross-critique and negotiate through a structured multi-round file-based debate, ending with a synthesis pass.

This repo holds the skill source, an open simplification plan, and an evaluation workspace.

## Layout

```
skill/
  SKILL.md                       # the skill itself (~521 lines)
  references/
    duet-prompts.md              # phase prompt templates
    final-report-template.md     # synthesis template

plans/
  snoopy-sniffing-axolotl.md     # in-flight simplification proposal
                                 # (drop hash audits + Claude-as-scribe in
                                 # favor of each agent writing its own
                                 # section directly via codex:codex-rescue)

eval-workspace/
  PLAN.md, REPORT.md, etc.       # eval framework + findings
  tier1-static-review/           # static analysis of SKILL.md
  tier2-trigger-bench/           # description-triggering benchmarks
  tier3-behavioral/              # end-to-end behavioral runs
    run-1/
    run-2/                       # paused at Phase 6c (audit step hit a
                                 # bwrap sandbox limitation)
```

## Source of truth

The live skill runs from `~/.claude/skills/duet/`. Files in `skill/` here are a snapshot copied for review and remote tooling (e.g. ultraplan). When the simplification plan lands, both locations get updated.
