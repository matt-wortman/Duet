#!/usr/bin/env python3
"""Tier 3 invariant checks for /duet behavioral run.

Six checks from the plan:
  1. verbatim_quotes  — quoted attributions to the other agent must substring-match
                        the prior round's content for that item
  2. tag_presence     — every Phase 4 item response ends with exactly one of
                        [CONCEDE] | [PUSH-BACK] | [HOLD]
  3. round_consecutive — round markers in the document are 1, 2, 3, ... no gaps
  4. concession_promotion — every [CONCEDE] in Discrepancies has a matching
                            entry in Best of the Best
  5. snapshot_files   — .bak.round-{N-1} exists for each round started
  6. phase5_verdicts  — both Claude and Codex verdicts appear in Phase 5

Output: writes audit-checks.json next to this script with per-check pass/fail
and supporting evidence.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
DOC = HERE / "duet-output-doc.md"
OUT = HERE / "audit-checks.json"

TAG_RE = re.compile(r"\[(CONCEDE|PUSH-BACK|HOLD)\]")
ROUND_RE = re.compile(r"\*\*Round\s+(\d+)\b", re.IGNORECASE)
ITEM_RE = re.compile(r"^\s*-\s+\*\*Item\s+([A-Z][A-Z0-9]?):", re.MULTILINE)
QUOTE_RE = re.compile(r'"([^"]{6,})"')  # min 6 chars to skip trivial matches


def load_doc() -> str:
    if not DOC.exists():
        return ""
    return DOC.read_text(encoding="utf-8", errors="replace")


def split_sections(doc: str) -> dict[str, str]:
    """Split by `## Phase N:` and `### Best of the Best` / `### Discrepancies`."""
    sections: dict[str, str] = {}
    headers = list(re.finditer(r"^##\s+(.+)$", doc, re.MULTILINE))
    for i, m in enumerate(headers):
        name = m.group(1).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(doc)
        sections[name] = doc[start:end]
    # Sub-split Phase 3 into Best/Discrepancies
    phase3 = next((v for k, v in sections.items() if k.startswith("Phase 3")), None)
    if phase3:
        for sub in re.finditer(r"^###\s+(.+)$", phase3, re.MULTILINE):
            name = sub.group(1).strip()
            start = sub.end()
            rest = phase3[start:]
            next_sub = re.search(r"^###\s+", rest, re.MULTILINE)
            block = rest[: next_sub.start()] if next_sub else rest
            sections[f"Phase 3 :: {name}"] = block
    return sections


def find_items(text: str) -> list[tuple[str, str]]:
    """Return [(item_label, item_block)] from a Discrepancies subsection."""
    items: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^\s*-\s+\*\*Item\s+([A-Z][A-Z0-9]?)[^\n]*$", text, re.MULTILINE))
    for i, m in enumerate(matches):
        label = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        items.append((label, text[start:end]))
    return items


def check_tag_presence(doc: str) -> dict:
    """Every Round-{N} bullet in a Phase 4 item should end with a tag."""
    sections = split_sections(doc)
    phase3_full = next((v for k, v in sections.items() if k.startswith("Phase 3")), "")
    discrepancies_blocks = [
        v for k, v in sections.items()
        if k.startswith("Phase 3 :: Discrepancies") or "Subsection" in k
    ]
    if not discrepancies_blocks:
        # fallback: scan all of phase3
        discrepancies_blocks = [phase3_full]

    missing: list[str] = []
    total = 0
    for block in discrepancies_blocks:
        items = find_items(block)
        for label, item_block in items:
            for round_match in ROUND_RE.finditer(item_block):
                round_num = round_match.group(1)
                # capture the bullet's content up to the next bullet or item
                bstart = item_block.rfind("\n", 0, round_match.start())
                if bstart < 0:
                    bstart = 0
                # find end of this bullet (next "- **" or end of block)
                rest = item_block[round_match.end():]
                next_bullet = re.search(r"\n\s*-\s+\*\*", rest)
                bullet_end = round_match.end() + (next_bullet.start() if next_bullet else len(rest))
                bullet_text = item_block[bstart:bullet_end]
                total += 1
                if not TAG_RE.search(bullet_text):
                    missing.append(f"Item {label} Round {round_num}: no tag")
    return {
        "name": "tag_presence",
        "total_round_bullets": total,
        "missing_tag": missing,
        "pass": len(missing) == 0 and total > 0,
    }


def check_round_consecutive(doc: str) -> dict:
    """Round numbers across the document increment without gaps (per item)."""
    sections = split_sections(doc)
    discrepancies_blocks = [v for k, v in sections.items() if "Subsection" in k]
    if not discrepancies_blocks:
        phase3 = next((v for k, v in sections.items() if k.startswith("Phase 3")), "")
        discrepancies_blocks = [phase3]

    gaps: list[str] = []
    items_checked = 0
    for block in discrepancies_blocks:
        for label, item_block in find_items(block):
            rounds = [int(m.group(1)) for m in ROUND_RE.finditer(item_block)]
            if not rounds:
                continue
            items_checked += 1
            expected = list(range(1, len(rounds) + 1))
            if rounds != expected:
                gaps.append(f"Item {label}: rounds {rounds} (expected {expected})")
    return {
        "name": "round_consecutive",
        "items_checked": items_checked,
        "gaps": gaps,
        "pass": len(gaps) == 0,
    }


def check_concession_promotion(doc: str) -> dict:
    """Every [CONCEDE] item should appear in Best of the Best."""
    sections = split_sections(doc)
    best = next((v for k, v in sections.items() if "Best of the Best" in k), "")
    discrepancies_blocks = [v for k, v in sections.items() if "Subsection" in k]

    conceded_items: list[str] = []
    not_promoted: list[str] = []
    for block in discrepancies_blocks:
        for label, item_block in find_items(block):
            if "[CONCEDE]" in item_block:
                conceded_items.append(label)
                # heuristic: look for "Item {label}" or "Subsection ... Round" reference in best
                if not re.search(rf"\bItem\s+{label}\b|\bPromoted\b", best, re.IGNORECASE):
                    not_promoted.append(label)

    return {
        "name": "concession_promotion",
        "conceded_items": conceded_items,
        "not_in_best_of_best": not_promoted,
        "pass": len(not_promoted) == 0,
    }


def check_verbatim_quotes(doc: str) -> dict:
    """Quotes inside Round N+1 critiques should substring-match prior round's content
    for that item. Implementation: per item, for each Round bullet that contains a
    "..." quote, verify the quoted text appears verbatim somewhere earlier in the
    same item block (Phase 2 finding or earlier round bullets).
    """
    sections = split_sections(doc)
    discrepancies_blocks = [v for k, v in sections.items() if "Subsection" in k]
    if not discrepancies_blocks:
        phase3 = next((v for k, v in sections.items() if k.startswith("Phase 3")), "")
        discrepancies_blocks = [phase3]

    misses: list[dict] = []
    quotes_checked = 0
    for block in discrepancies_blocks:
        for label, item_block in find_items(block):
            # Walk each round bullet in order, accumulate prior text
            round_marks = list(ROUND_RE.finditer(item_block))
            for i, m in enumerate(round_marks):
                prior_text = item_block[: m.start()]
                next_start = round_marks[i + 1].start() if i + 1 < len(round_marks) else len(item_block)
                bullet_text = item_block[m.start(): next_start]
                # Find quotes in this bullet (skip the verbatim-marker quotes around tags)
                for q in QUOTE_RE.finditer(bullet_text):
                    qstr = q.group(1).strip()
                    if not qstr or qstr.startswith("[") or qstr in {"PASS", "ISSUES FOUND"}:
                        continue
                    quotes_checked += 1
                    if qstr not in prior_text:
                        misses.append({
                            "item": label,
                            "round": int(m.group(1)),
                            "quote": qstr[:80] + ("…" if len(qstr) > 80 else ""),
                        })
    return {
        "name": "verbatim_quotes",
        "quotes_checked": quotes_checked,
        "non_substring_matches": misses,
        "pass": len(misses) == 0,
    }


def check_snapshot_files() -> dict:
    """`.bak.round-{N-1}` exists for each round started.
    If max round in doc is K, expect snapshots for rounds 0..K-1.
    """
    doc = load_doc()
    rounds_in_doc = [int(m.group(1)) for m in ROUND_RE.finditer(doc)]
    max_round = max(rounds_in_doc) if rounds_in_doc else 0
    expected = [f".bak.round-{n}" for n in range(0, max_round)]  # round-0 through round-{K-1}
    present = sorted(p.name for p in HERE.glob("duet-output-doc.md.bak.round-*"))
    missing = [e for e in expected if not (HERE / f"duet-output-doc.md{e}").exists()]
    return {
        "name": "snapshot_files",
        "max_round_in_doc": max_round,
        "expected_snapshots": expected,
        "present": present,
        "missing": missing,
        "pass": len(missing) == 0 and max_round > 0,
    }


def check_phase5_verdicts(doc: str) -> dict:
    sections = split_sections(doc)
    phase5 = next((v for k, v in sections.items() if k.startswith("Phase 5")), "")
    has_claude = bool(re.search(r"Claude'?s\s+verdict", phase5, re.IGNORECASE))
    has_codex = bool(re.search(r"Codex'?s\s+verdict", phase5, re.IGNORECASE))
    return {
        "name": "phase5_verdicts",
        "phase5_present": bool(phase5.strip()),
        "claude_verdict_present": has_claude,
        "codex_verdict_present": has_codex,
        "pass": has_claude and has_codex,
    }


def main() -> int:
    doc = load_doc()
    if not doc:
        result = {
            "doc_path": str(DOC),
            "doc_present": False,
            "checks": [],
            "summary": {"all_pass": False, "reason": "duet-output-doc.md not found"},
        }
        OUT.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return 1

    checks = [
        check_verbatim_quotes(doc),
        check_tag_presence(doc),
        check_round_consecutive(doc),
        check_concession_promotion(doc),
        check_snapshot_files(),
        check_phase5_verdicts(doc),
    ]
    result = {
        "doc_path": str(DOC),
        "doc_present": True,
        "doc_size_bytes": len(doc),
        "checks": checks,
        "summary": {
            "passed": [c["name"] for c in checks if c["pass"]],
            "failed": [c["name"] for c in checks if not c["pass"]],
            "all_pass": all(c["pass"] for c in checks),
        },
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["summary"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
