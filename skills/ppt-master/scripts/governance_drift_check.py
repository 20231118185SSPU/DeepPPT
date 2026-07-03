#!/usr/bin/env python3
"""
PPT Master - Governance Drift Check

Checks lightweight agent-facing entry files for drift from AGENTS.md and
SKILL.md on high-risk workflow rules.

Usage:
    python3 skills/ppt-master/scripts/governance_drift_check.py
    python3 skills/ppt-master/scripts/governance_drift_check.py --root <repo_root>

Examples:
    python3 skills/ppt-master/scripts/governance_drift_check.py
    python3 skills/ppt-master/scripts/governance_drift_check.py --root C:/Users/FUTIAN/Desktop/DeepPPT

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


LOW_AUTHORITY_FILES = (
    ".clinerules",
    ".windsurfrules",
    "CLAUDE.md",
    "hermes.md",
    "docs/ai-rules-shared.md",
    "docs/claude-reference.md",
    "docs/routing.md",
)

DOCS_CLAUDE_REFERENCE = "docs/claude-reference.md"
DOCS_RULES_DIR = "docs/rules"

TOPIC_BLOCK_RE = re.compile(
    r"(topic[- ]only|no source(?: material| file)?|source-free|only a topic)",
    re.IGNORECASE,
)
DASHBOARD_COMMAND_RE = re.compile(
    r"dashboard/server\.py(?P<args>[^\r\n`]*)",
    re.IGNORECASE,
)
RULE_STATUS_RE = re.compile(r"^>\s*Status:\s*(?P<status>.+)$", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
OLD_PROJECT_PATH_PATTERNS = (
    ("old pages/ directory", re.compile(r"(?<![\w./-])pages/")),
    ("old source/ directory", re.compile(r"(?<![\w./-])source/")),
)
ROOT_PPTX_PLACEHOLDER_RE = re.compile(r"<[^>/\\]+>\.pptx")


@dataclass
class CheckResult:
    status: str
    name: str
    message: str
    details: tuple[str, ...] = ()


def _repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _line_ref(path: Path, root: Path, line_no: int) -> str:
    rel = path.relative_to(root).as_posix()
    return f"{rel}:{line_no}"


def _existing_low_authority_files(root: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing: list[str] = []
    for rel in LOW_AUTHORITY_FILES:
        path = root / rel
        if path.is_file():
            files.append(path)
        else:
            missing.append(rel)
    return files, missing


def _iter_topic_blocks(text: str) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    current_lines: list[str] = []
    current_start = 1

    def flush() -> None:
        nonlocal current_lines, current_start
        if current_lines:
            blocks.append((current_start, "\n".join(current_lines)))
            current_lines = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not current_lines:
                current_start = line_no
            current_lines.append(line)
        else:
            flush()
    flush()
    return blocks


def check_topic_only_routing(root: Path) -> CheckResult:
    files, missing = _existing_low_authority_files(root)
    direct_routes: list[str] = []
    scanned_blocks = 0

    for path in files:
        text = _read_text(path)
        if text is None:
            direct_routes.append(f"{path.relative_to(root).as_posix()}: unreadable")
            continue
        for start_line, block in _iter_topic_blocks(text):
            if not TOPIC_BLOCK_RE.search(block) or "deep-research" not in block:
                continue
            scanned_blocks += 1
            if "ppt-briefing" not in block:
                direct_routes.append(
                    f"{_line_ref(path, root, start_line)} mentions topic-only deep-research "
                    "without ppt-briefing in the same routing block"
                )

    if direct_routes:
        return CheckResult(
            "FAIL",
            "topic-only routing",
            "Topic-only routing can bypass ppt-briefing before deep-research.",
            tuple(direct_routes),
        )
    if scanned_blocks == 0:
        details = tuple(f"missing optional entry: {rel}" for rel in missing)
        return CheckResult(
            "WARN",
            "topic-only routing",
            "No topic-only deep-research routing blocks were found in scanned entry files.",
            details,
        )

    details = [f"scanned topic-routing blocks: {scanned_blocks}"]
    details.extend(f"missing optional entry: {rel}" for rel in missing)
    return CheckResult(
        "PASS",
        "topic-only routing",
        "Topic-only mentions keep ppt-briefing before deep-research.",
        tuple(details),
    )


def _is_contextual_no_browser_line(line: str) -> bool:
    lower = line.lower()
    context_tokens = (
        "only",
        "headless",
        "remote",
        "explicit",
        "no-window",
        "no window",
        "asks not",
        "asks no",
        "does not want",
        "add --no-browser",
        "explicit user",
    )
    return any(token in lower for token in context_tokens)


def check_dashboard_default(root: Path) -> CheckResult:
    files, missing = _existing_low_authority_files(root)
    forced_no_browser: list[str] = []
    dashboard_mentions = 0

    for path in files:
        text = _read_text(path)
        if text is None:
            forced_no_browser.append(f"{path.relative_to(root).as_posix()}: unreadable")
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            match = DASHBOARD_COMMAND_RE.search(line)
            if not match:
                continue
            dashboard_mentions += 1
            args = match.group("args")
            if "--daemon" in args and "--no-browser" in args and not _is_contextual_no_browser_line(line):
                forced_no_browser.append(
                    f"{_line_ref(path, root, line_no)} makes --no-browser part of the default command"
                )

    if forced_no_browser:
        return CheckResult(
            "FAIL",
            "dashboard default",
            "Dashboard default appears to force --daemon --no-browser.",
            tuple(forced_no_browser),
        )
    if dashboard_mentions == 0:
        details = tuple(f"missing optional entry: {rel}" for rel in missing)
        return CheckResult(
            "WARN",
            "dashboard default",
            "No Dashboard command mentions were found in scanned entry files.",
            details,
        )

    details = [f"scanned dashboard command mentions: {dashboard_mentions}"]
    details.extend(f"missing optional entry: {rel}" for rel in missing)
    return CheckResult(
        "PASS",
        "dashboard default",
        "Dashboard default uses --daemon without forcing --no-browser.",
        tuple(details),
    )


def check_rule_status(root: Path) -> CheckResult:
    rules_dir = root / DOCS_RULES_DIR
    if not rules_dir.is_dir():
        return CheckResult(
            "FAIL",
            "docs/rules status",
            f"Rules directory is missing: {DOCS_RULES_DIR}",
        )

    draft_adopted: list[str] = []
    adopted_files = 0
    for path in sorted(rules_dir.glob("*.md")):
        text = _read_text(path)
        if text is None:
            draft_adopted.append(f"{path.relative_to(root).as_posix()}: unreadable")
            continue
        first_screen = "\n".join(text.splitlines()[:12])
        status_match = next(
            (RULE_STATUS_RE.match(line) for line in first_screen.splitlines() if RULE_STATUS_RE.match(line)),
            None,
        )
        is_adopted = "adopted by `AGENTS.md`" in first_screen or "adopted by AGENTS.md" in first_screen
        if is_adopted:
            adopted_files += 1
        if is_adopted and status_match and re.search(r"\b(draft|proposed)\b", status_match.group("status"), re.I):
            draft_adopted.append(
                f"{_line_ref(path, root, text.splitlines().index(status_match.group(0)) + 1)} "
                f"status is {status_match.group('status').strip()!r}"
            )

    if draft_adopted:
        return CheckResult(
            "FAIL",
            "docs/rules status",
            "A rules file adopted by AGENTS.md is still marked draft/proposed.",
            tuple(draft_adopted),
        )
    if adopted_files == 0:
        return CheckResult(
            "WARN",
            "docs/rules status",
            "No adopted docs/rules status headers were detected.",
        )
    return CheckResult(
        "PASS",
        "docs/rules status",
        "Adopted docs/rules files are not marked draft/proposed.",
        (f"adopted rule files checked: {adopted_files}",),
    )


def check_claude_reference_project_paths(root: Path) -> CheckResult:
    path = root / DOCS_CLAUDE_REFERENCE
    text = _read_text(path)
    if text is None:
        return CheckResult(
            "FAIL",
            "claude-reference project paths",
            f"Required file is missing or unreadable: {DOCS_CLAUDE_REFERENCE}",
        )

    stale_refs: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for label, pattern in OLD_PROJECT_PATH_PATTERNS:
            if pattern.search(line):
                stale_refs.append(f"{_line_ref(path, root, line_no)} contains {label}")
        if _has_root_pptx_placeholder(line):
            stale_refs.append(
                f"{_line_ref(path, root, line_no)} contains root-level angle-bracket PPTX placeholder"
            )

    if stale_refs:
        return CheckResult(
            "FAIL",
            "claude-reference project paths",
            "docs/claude-reference.md contains stale project path conventions.",
            tuple(stale_refs),
        )
    return CheckResult(
        "PASS",
        "claude-reference project paths",
        "No stale pages/, source/, or root-level <name>.pptx conventions found.",
    )


def _has_root_pptx_placeholder(line: str) -> bool:
    """Return True when a PPTX placeholder is shown at project root."""
    match = ROOT_PPTX_PLACEHOLDER_RE.search(line)
    if not match:
        return False
    prefix = line[:match.start()]
    if "/" in prefix or "\\" in prefix:
        return False
    stripped_prefix = prefix.strip()
    return not stripped_prefix.startswith(("│", "|"))


def _strip_anchor_and_query(target: str) -> str:
    return target.split("#", 1)[0].split("?", 1)[0]


def check_rules_relative_skill_links(root: Path) -> CheckResult:
    rules_dir = root / DOCS_RULES_DIR
    if not rules_dir.is_dir():
        return CheckResult(
            "FAIL",
            "docs/rules skill links",
            f"Rules directory is missing: {DOCS_RULES_DIR}",
        )

    broken_links: list[str] = []
    checked_links = 0
    for path in sorted(rules_dir.glob("*.md")):
        text = _read_text(path)
        if text is None:
            broken_links.append(f"{path.relative_to(root).as_posix()}: unreadable")
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in MD_LINK_RE.finditer(line):
                target = match.group("target")
                clean_target = _strip_anchor_and_query(target)
                if not clean_target.startswith("../skills/"):
                    continue
                checked_links += 1
                resolved = (path.parent / clean_target).resolve()
                if not resolved.exists():
                    broken_links.append(
                        f"{_line_ref(path, root, line_no)} -> {target} resolves outside the real skills tree"
                    )

    if broken_links:
        return CheckResult(
            "FAIL",
            "docs/rules skill links",
            "../skills/... links in docs/rules resolve incorrectly from their current location.",
            tuple(broken_links),
        )
    return CheckResult(
        "PASS",
        "docs/rules skill links",
        "No incorrectly resolved ../skills/... links found in docs/rules.",
        (f"../skills links checked: {checked_links}",),
    )


def run_checks(root: Path) -> list[CheckResult]:
    return [
        check_topic_only_routing(root),
        check_dashboard_default(root),
        check_rule_status(root),
        check_claude_reference_project_paths(root),
        check_rules_relative_skill_links(root),
    ]


def print_report(results: list[CheckResult]) -> None:
    for result in results:
        print(f"[{result.status}] {result.name}: {result.message}")
        for detail in result.details:
            print(f"  - {detail}")
    failed = sum(1 for result in results if result.status == "FAIL")
    warned = sum(1 for result in results if result.status == "WARN")
    passed = sum(1 for result in results if result.status == "PASS")
    print()
    print(f"Result: {passed} PASS, {warned} WARN, {failed} FAIL")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check low-authority agent entry files for governance drift.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_repo_root_from_script(),
        help="Repository root to scan (default: inferred from this script path).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not (root / "AGENTS.md").is_file() or not (root / "skills/ppt-master/SKILL.md").is_file():
        print(
            f"ERROR: {root} does not look like the DeepPPT repository root.",
            file=sys.stderr,
        )
        return 2

    results = run_checks(root)
    print_report(results)
    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
