#!/usr/bin/env python3
"""
PPT Master - Chart Candidate Recall

Recall a deterministic chart-template shortlist from page-shape semantic tags,
or validate selected chart keys against the live chart catalog.

Usage:
    python3 scripts/chart_recall.py recall --page P03 --tag "time series" --tag "three metrics" --tag "trend"
    python3 scripts/chart_recall.py validate line_chart bar_chart

Examples:
    python3 scripts/chart_recall.py recall --page P07 --tag "named quadrants" \
        --tag "bullet lists" --tag "SWOT" --limit 6
    python3 scripts/chart_recall.py validate quadrant_text_bullets

Dependencies:
    None (only uses standard library)

See scripts/docs/chart-recall.md for the Strategist workflow and output contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

_INDEX_PATH = _SCRIPTS_DIR.parent / "templates" / "charts" / "charts_index.json"
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PAGE_RE = re.compile(r"^P\d{2,}$")
_KEY_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_SKIP_RE = re.compile(r"\bskip\s+(?:if|for)\b", re.IGNORECASE)
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "if",
    "in",
    "into",
    "of",
    "on",
    "or",
    "per",
    "the",
    "to",
    "use",
    "with",
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("_", " ")
    return " ".join(_TOKEN_RE.findall(normalized))


def _stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _tokens(text: str) -> set[str]:
    return {
        _stem(token)
        for token in _TOKEN_RE.findall(_normalize(text))
        if token not in _STOP_WORDS
    }


def load_catalog() -> dict[str, str]:
    """Load and validate the live chart catalog."""
    try:
        payload = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read chart catalog {_INDEX_PATH}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Chart catalog {_INDEX_PATH} root must be an object")
    raw_charts = payload.get("charts")
    if not isinstance(raw_charts, dict) or not raw_charts:
        raise RuntimeError(f"Chart catalog {_INDEX_PATH} has no non-empty 'charts' object")

    charts: dict[str, str] = {}
    for key, item in raw_charts.items():
        if (
            not isinstance(key, str)
            or _KEY_RE.fullmatch(key) is None
            or not isinstance(item, dict)
        ):
            raise RuntimeError(f"Chart catalog entry {key!r} is malformed")
        summary = item.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError(f"Chart catalog entry {key!r} has no non-empty summary")
        charts[key] = summary.strip()
    return charts


def _score_candidate(key: str, summary: str, tags: list[str]) -> tuple[int, list[str]]:
    skip_match = _SKIP_RE.search(summary)
    if skip_match is None:
        pick_clause, skip_clause = summary, ""
    else:
        pick_clause = summary[:skip_match.start()]
        skip_clause = summary[skip_match.start():]
    key_text = _normalize(key)
    pick_text = _normalize(pick_clause)
    skip_text = _normalize(skip_clause)
    key_tokens = _tokens(key)
    pick_tokens = _tokens(pick_clause)
    skip_tokens = _tokens(skip_clause)
    score = 0
    matched_tags: list[str] = []

    for tag in tags:
        tag_text = _normalize(tag)
        tag_tokens = _tokens(tag)
        positive_score = 0
        negative_score = 0
        if tag_text and tag_text in key_text:
            positive_score += 20
        elif tag_text and tag_text in pick_text:
            positive_score += 14
        if tag_text and tag_text in skip_text:
            negative_score += 12

        for token in tag_tokens:
            if token in key_tokens:
                positive_score += 9
            elif token in pick_tokens:
                positive_score += 5
            if token in skip_tokens:
                negative_score += 6

        if positive_score:
            matched_tags.append(tag)
        score += positive_score - negative_score

    return score, matched_tags


def recall_candidates(
    page: str,
    tags: list[str],
    limit: int,
    *,
    force_semantic_fallback: bool = False,
) -> dict[str, object]:
    """Recall a deterministic shortlist for one page."""
    charts = load_catalog()
    scored: list[tuple[int, str, str, list[str]]] = []
    for key, summary in charts.items():
        score, matched_tags = _score_candidate(key, summary, tags)
        if score > 0 and matched_tags:
            scored.append((score, key, summary, matched_tags))
    scored.sort(key=lambda item: (-item[0], item[1]))

    candidates = [
        {
            "key": key,
            "path": f"templates/charts/{key}.svg",
            "summary": summary,
            "score": score,
            "matched_tags": matched_tags,
        }
        for score, key, summary, matched_tags in scored[:limit]
    ]

    top_score = candidates[0]["score"] if candidates else 0
    if top_score >= 35:
        confidence = "high"
    elif top_score >= 15:
        confidence = "medium"
    elif top_score > 0:
        confidence = "low"
    else:
        confidence = "none"

    if force_semantic_fallback and confidence not in {"low", "none"}:
        raise ValueError(
            "--semantic-fallback is only allowed when lexical confidence is low or none; "
            f"this recall is {confidence}."
        )

    fallback_required = confidence in {"low", "none"} and not force_semantic_fallback
    if fallback_required:
        no_match_instruction = (
            f"Lexical confidence is {confidence}. Select a bounded candidate when one "
            "fits; otherwise rerun the same recall with --semantic-fallback before "
            "recording no-template-match in Design Spec Section VII. Omit the negative "
            "result from spec_lock page_charts."
        )
    else:
        no_match_instruction = (
            "Use only when none of the reviewed candidates fits. Record the chosen "
            "fallback and reason in Design Spec Section VII, and omit the page from "
            "spec_lock page_charts."
        )

    result: dict[str, object] = {
        "page": page,
        "semantic_tags": tags,
        "confidence": confidence,
        "candidates": candidates,
        "no_template_match": {
            "allowed": not fallback_required,
            "key": "no-template-match",
            "instruction": no_match_instruction,
        },
    }
    if force_semantic_fallback:
        result["semantic_fallback"] = {
            "reason": f"lexical-confidence-{confidence}",
            "instruction": (
                "Semantically compare the page tags with every returned selection rule. "
                "Choose one exact catalog key or retain no-template-match."
            ),
            "path_pattern": "templates/charts/{key}.svg",
            "catalog": [
                {
                    "key": key,
                    "path": f"templates/charts/{key}.svg",
                    "summary": summary,
                }
                for key, summary in charts.items()
            ],
        }
    return result


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        normalized = _normalize(stripped)
        if not stripped or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(stripped)
    return result


def _run_recall(args: argparse.Namespace) -> int:
    page = args.page.upper()
    if not _PAGE_RE.fullmatch(page):
        print("Error: --page must match P<NN>, for example P03.", file=sys.stderr)
        return 2

    tags = _dedupe(args.tag)
    if not 3 <= len(tags) <= 8:
        print("Error: recall requires 3-8 distinct non-empty --tag values.", file=sys.stderr)
        return 2

    try:
        result = recall_candidates(
            page,
            tags,
            args.limit,
            force_semantic_fallback=args.semantic_fallback,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _validate_key_inputs(
    values: list[str],
) -> tuple[list[str], list[int], list[dict[str, int | str]]]:
    selected: list[str] = []
    empty_positions: list[int] = []
    duplicates: list[dict[str, int | str]] = []
    first_positions: dict[str, int] = {}
    for position, value in enumerate(values, start=1):
        key = value.strip()
        normalized = _normalize(key)
        if not key or not normalized:
            empty_positions.append(position)
            continue
        first_position = first_positions.get(normalized)
        if first_position is None:
            first_positions[normalized] = position
        else:
            duplicates.append({
                "key": key,
                "position": position,
                "first_position": first_position,
            })
        selected.append(key)
    return selected, empty_positions, duplicates


def _run_validate(args: argparse.Namespace) -> int:
    selected, empty_positions, duplicates = _validate_key_inputs(args.keys)
    charts = load_catalog()
    invalid = sorted({key for key in selected if key not in charts})
    result = {
        "duplicates": duplicates,
        "empty_positions": empty_positions,
        "invalid": invalid,
        "valid": sorted({key for key in selected if key in charts}),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if empty_positions or duplicates or invalid:
        print(
            "Error: keys must be non-empty, unique, exact catalog identifiers. Replace "
            "invalid keys with recalled catalog keys, or record no-template-match in "
            "Design Spec Section VII and omit it from page_charts.",
            file=sys.stderr,
        )
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recall chart-template candidates or validate selected keys.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    recall = subparsers.add_parser("recall", help="Recall candidates for one planned page.")
    recall.add_argument("--page", required=True, help="Planned page key, for example P03.")
    recall.add_argument(
        "--tag",
        action="append",
        required=True,
        help="English semantic content-shape tag; repeat 3-8 times.",
    )
    recall.add_argument(
        "--limit",
        type=int,
        choices=range(3, 9),
        default=6,
        metavar="3..8",
        help="Candidate count (default: 6).",
    )
    recall.add_argument(
        "--semantic-fallback",
        action="store_true",
        help="Include the full catalog only after a bounded low/none-confidence review.",
    )
    recall.set_defaults(handler=_run_recall)

    validate = subparsers.add_parser("validate", help="Validate selected catalog keys.")
    validate.add_argument("keys", nargs="+", help="One or more selected chart keys.")
    validate.set_defaults(handler=_run_validate)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
