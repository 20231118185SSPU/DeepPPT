#!/usr/bin/env python3
"""PPT Master - Local Run Metrics Summary

Aggregate ``<project>/trace.jsonl`` (plus optional sidecar reports) into a
versioned ``quality/run_summary.json`` so later optimization decisions are
driven by real run data — local, non-sensitive, low-intrusion.

Null vs 0 semantics (trace-contract.md T5.6): ``duration_ms: null`` = not
measured; ``0`` = a real measurement. Metrics with no wiring signal in the
trace are reported as null with a "not-wired" warning — never fabricated as 0.

Sensitive fields fail closed: any event containing a forbidden key (prompt /
api_key / token / secret / password / credential / session / authorization /
cookie) aborts with exit 1 and a diagnosable message; the summary is not
written.

Usage:
    python3 scripts/run_summary.py <project_path> [-o <out_path>]

Dependencies:
    None (stdlib only; trace events must never carry source text / prompt
    bodies / credentials — see dashboard/trace_writer.py T5.3).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SUMMARY_SCHEMA = "ppt-master.run-summary.v1"
_SENSITIVE_KEY_RE = re.compile(
    r"(prompt|api[_-]?key|token|secret|password|passwd|credential|"
    r"authorization|session|cookie)",
    re.IGNORECASE,
)
_IMAGE_OP_RE = re.compile(r"image[_-]?(gen|search|attempt)", re.IGNORECASE)
_ANNOTATION_OP_RE = re.compile(r"annotation|live[_-]?preview", re.IGNORECASE)
_REGENERATION_OP_RE = re.compile(r"regen|svg[_-]?regenerat", re.IGNORECASE)
_REEXPORT_OP_RE = re.compile(r"re-?export|reexport|pptx_export", re.IGNORECASE)
_LEGACY_EVENT = "legacy event (no schema_version)"


def _load_trace(project: Path) -> tuple[list[dict[str, Any]], list[str]]:
    trace_path = project / "trace.jsonl"
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not trace_path.is_file():
        return events, ["trace.jsonl missing — all trace-derived metrics are null"]
    bad_lines = 0
    legacy = 0
    for line_number, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            bad_lines += 1
            continue
        if not isinstance(event, dict):
            bad_lines += 1
            continue
        for key in event:
            if _SENSITIVE_KEY_RE.search(key):
                raise _SensitiveFieldError(
                    f"trace.jsonl line {line_number} contains sensitive key {key!r}; "
                    "writers must never record prompt bodies or credentials (T5.3)"
                )
        if "schema_version" not in event:
            legacy += 1
        events.append(event)
    if bad_lines:
        warnings.append(f"{bad_lines} unparseable trace line(s) skipped")
    if legacy:
        warnings.append(f"{legacy} {_LEGACY_EVENT}(s) tolerated")
    return events, warnings


class _SensitiveFieldError(RuntimeError):
    pass


def _op(event: dict[str, Any]) -> str:
    """Stable operation key: explicit operation, else gate (for gate_result),
    else event type."""
    op = event.get("operation")
    if op is not None:
        return str(op)
    if event.get("type") == "gate_result" and event.get("gate") is not None:
        return str(event["gate"])
    return str(event.get("type") or "unknown")


def _stage_durations(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Pair step_start / step_complete by (operation, step) into durations."""
    from datetime import datetime, timezone

    stages: dict[str, dict[str, Any]] = {}

    def key(event: dict[str, Any]) -> tuple[str, Any]:
        return (_op(event), event.get("step"))

    def slot(stage: dict[str, Any], field: str, ts: str) -> None:
        if field not in stage or stage[field] is None:
            stage[field] = ts

    for event in events:
        etype = event.get("type")
        ts = str(event.get("ts") or "")
        if etype == "step_start":
            stage = stages.setdefault(key(event)[0], {})
            if event.get("step") is not None:
                stage["step"] = event["step"]
            slot(stage, "start", ts)
        elif etype == "step_complete":
            stage = stages.setdefault(key(event)[0], {})
            if event.get("step") is not None:
                stage["step"] = event["step"]
            slot(stage, "end", ts)
            if event.get("duration_ms") is not None:
                stage["duration_ms"] = event["duration_ms"]
    for stage in stages.values():
        start, end = stage.get("start"), stage.get("end")
        # 写入方实测 duration_ms 优先（真实测量）；否则由 start/end 计算；否则 null
        if stage.get("duration_ms") is not None:
            continue
        if not (start and end):
            stage["duration_ms"] = None
            continue
        try:
            fmt = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
            start_dt = fmt(start)
            end_dt = fmt(end)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            stage["duration_ms"] = max(0, int((end_dt - start_dt).total_seconds() * 1000))
        except (ValueError, TypeError):
            stage["duration_ms"] = None
    return stages


def _gate_statuses(events: list[dict[str, Any]]) -> dict[str, str]:
    latest: dict[str, tuple[str, str]] = {}
    for event in events:
        if event.get("type") != "gate_result":
            continue
        gate = str(event.get("gate") or _op(event))
        status = str(event.get("status") or "")
        ts = str(event.get("ts") or "")
        if gate not in latest or ts >= latest[gate][0]:
            latest[gate] = (ts, status)
    return {gate: status for gate, (_ts, status) in latest.items()}


def _errors(events: list[dict[str, Any]]) -> dict[str, Any]:
    codes = Counter(
        str(event.get("error_code") or "unspecified")
        for event in events
        if event.get("type") == "error"
    )
    count = sum(codes.values())
    return {
        "count": count,
        "by_code": dict(sorted(codes.items())) if codes else {},
    }


def _retry_count(events: list[dict[str, Any]]) -> int:
    """Repeated start-like events per operation = retries.

    Only step_start / gate_result / *attempt* operations count as starts; a
    step_start + step_complete pair is one run, not a retry.
    """
    occurrences = Counter(
        _op(event)
        for event in events
        if event.get("type") in ("step_start", "gate_result")
        or "attempt" in _op(event).lower()
    )
    return sum(n - 1 for n in occurrences.values() if n > 1)


def _op_count(events: list[dict[str, Any]], pattern: re.Pattern[str]) -> int:
    return sum(1 for event in events if pattern.search(_op(event)))


def _counted_metric(
    events: list[dict[str, Any]],
    pattern: re.Pattern[str],
    label: str,
    warnings: list[str],
) -> int | None:
    """Count matching events; null + not-wired warning when nothing matches."""
    count = _op_count(events, pattern)
    if count:
        return count
    warnings.append(f"{label} not wired (no matching event written by any script)")
    return None


def _final_results(project: Path) -> dict[str, Any]:
    results: dict[str, Any] = {}

    def read_json(rel: str) -> dict[str, Any] | None:
        path = project / rel
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return data if isinstance(data, dict) else None

    harness = read_json("quality/harness.json")
    results["e2e"] = (harness or {}).get("overall") if harness is not None else None

    quality = read_json("quality/pptx_quality.json")
    if quality is not None:
        results["delivery"] = quality.get("status")
        summary = quality.get("summary")
        slide_count = summary.get("slide_count") if isinstance(summary, dict) else None
        results["slide_count"] = slide_count if isinstance(slide_count, int) else None
    else:
        results["delivery"] = None
        results["slide_count"] = None

    visual = read_json("quality/rendered_visual_gate.json")
    results["visual"] = (visual or {}).get("status") if visual is not None else None
    return results


def _annotation_count(
    project: Path,
    events: list[dict[str, Any]],
    warnings: list[str],
) -> int | None:
    """Live-preview annotations: count `<project>/annotations.jsonl` records
    (written by svg_editor server), falling back to trace events."""
    jsonl = project / "annotations.jsonl"
    if jsonl.is_file():
        try:
            records = [
                line for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()
            ]
        except OSError:
            records = []
        if records:
            return len(records)
    return _counted_metric(events, _ANNOTATION_OP_RE, "live-preview annotations", warnings)


def build_summary(project: Path) -> dict[str, Any]:
    events, warnings = _load_trace(project)
    final = _final_results(project)
    route_counter = Counter(
        str(event["route"]) for event in events if event.get("route") is not None
    )
    image_attempts = _counted_metric(events, _IMAGE_OP_RE, "image attempts", warnings)
    annotations = {
        "live_preview_count": _annotation_count(project, events, warnings),
        "svg_regeneration_count": _counted_metric(
            events, _REGENERATION_OP_RE, "svg regeneration", warnings
        ),
        "pptx_reexport_count": _counted_metric(
            events, _REEXPORT_OP_RE, "pptx re-export", warnings
        ),
    }
    stages = _stage_durations(events)
    return {
        "schema": SUMMARY_SCHEMA,
        "project": str(project),
        "events_total": len(events),
        "route": route_counter.most_common(1)[0][0] if route_counter else None,
        "slide_count": final["slide_count"],
        "stages": dict(sorted(stages.items())),
        "gates": _gate_statuses(events),
        "errors": _errors(events),
        "retry_count": _retry_count(events),
        "image_attempts": image_attempts,
        "annotations": annotations,
        "final_results": {
            "delivery": final["delivery"],
            "e2e": final["e2e"],
            "visual": final["visual"],
        },
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_summary.py",
        description=(
            "聚合项目 trace 与 sidecar 报告为 quality/run_summary.json（本地、非敏感）。"
            "敏感字段（prompt/凭据）出现时 exit 1 且不写文件。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="PPT 项目目录（含 trace.jsonl）")
    parser.add_argument(
        "-o", "--out",
        help="输出路径（默认 <project>/quality/run_summary.json）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project = Path(args.project_path)
    if not project.is_dir():
        print(f"[ERROR] project path not found: {project}", file=sys.stderr)
        return 2
    try:
        summary = build_summary(project)
    except _SensitiveFieldError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    out = Path(args.out) if args.out else project / "quality" / "run_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SUMMARY] events={summary['events_total']} route={summary['route']} "
          f"slides={summary['slide_count']}")
    print(f"[REPORT] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
