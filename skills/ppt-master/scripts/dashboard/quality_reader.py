#!/usr/bin/env python3
"""
PPT Master - Dashboard Quality Reader

Normalize already-written quality report files for dashboard display. The
dashboard does not run heavy checks by default.

Usage:
    report = quality_report(Path("projects/example"))

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from artifact_registry import latest_pptx


_CHECK_FILES = {
    "svg_quality": (
        "svg_quality_report.json",
        "quality/svg_quality.json",
        "analysis/svg_quality_report.json",
    ),
    "spec_compliance": (
        "spec_compliance_report.json",
        "quality/spec_compliance.json",
        "analysis/spec_compliance_report.json",
    ),
    "e2e": (
        "e2e_validate_report.json",
        "quality/e2e.json",
        "analysis/e2e_validate_report.json",
    ),
    "harness": (
        "harness_gate_report.json",
        "quality/harness.json",
        "analysis/harness_gate_report.json",
    ),
    "integrated_review": (
        "integrated_review.json",
        "quality/integrated_review.json",
        "analysis/integrated_review.json",
    ),
    "visual_review": (
        "vision_check_report.json",
        "visual_review_report.json",
        "quality/visual_review.json",
        "analysis/visual_review_report.json",
        ".review/visual_review.json",
        ".review/brand_review.json",
    ),
}

_CHECK_LABELS = {
    "spec_compliance": "Spec Compliance",
    "svg_quality": "SVG Quality",
    "e2e": "E2E Validation",
    "visual_review": "Visual Review",
    "harness": "Harness Gate",
    "integrated_review": "Integrated Review",
}

_SUMMARY_CHECKS = ("spec_compliance", "svg_quality", "e2e", "visual_review")
_ISSUE_GROUPS = ("must_fix", "should_fix", "accepted_risks")
_STATUS_RANK = {"fail": 3, "warn": 2, "unknown": 1, "pass": 0}


@dataclass
class ReportFile:
    check: str
    source_file: str
    updated_at: str
    data: dict[str, Any] | None = None
    parse_warning: str = ""
    raw_text: str = ""


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return _now()


def _clip_text(value: str, limit: int = 50000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"


def _read_report_file(project: Path, check: str) -> ReportFile | None:
    candidates = _CHECK_FILES.get(check)
    if not candidates:
        return None
    for rel in candidates:
        path = project / rel
        if not path.is_file():
            continue
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            return ReportFile(
                check=check,
                source_file=rel,
                updated_at=_mtime_iso(path),
                parse_warning=f"Cannot read report: {exc}",
            )
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            return ReportFile(
                check=check,
                source_file=rel,
                updated_at=_mtime_iso(path),
                parse_warning=(
                    f"Cannot parse JSON: {exc.msg} at line {exc.lineno}, "
                    f"column {exc.colno}"
                ),
                raw_text=_clip_text(raw_text),
            )
        if not isinstance(parsed, dict):
            return ReportFile(
                check=check,
                source_file=rel,
                updated_at=_mtime_iso(path),
                parse_warning=f"Expected a JSON object, got {type(parsed).__name__}",
                raw_text=_clip_text(raw_text),
            )
        parsed.setdefault("_path", rel)
        return ReportFile(
            check=check,
            source_file=rel,
            updated_at=_mtime_iso(path),
            data=parsed,
        )
    return None


def _status_from_data(data: dict | None) -> str:
    return _legacy_status(_normalize_status(data))


def _normalize_status(data: dict | None, parse_warning: str = "") -> str:
    if parse_warning:
        return "warn"
    if not data:
        return "unknown"

    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    raw = str(
        data.get("overall")
        or data.get("status")
        or data.get("gate_status")
        or summary.get("gate_status")
        or data.get("result")
        or ""
    ).strip().lower()

    if raw in {"pass", "passed", "ok", "clean", "success", "ready"}:
        return "pass"
    if raw in {"warn", "warning", "warnings", "pass_with_warnings", "acceptable_with_risks"}:
        return "warn"
    if raw in {"fail", "failed", "error", "blocked", "needs_fix", "needs-fix"}:
        return "fail"
    if raw in {"skip", "skipped", "unknown", "n/a", "none"}:
        return "unknown"

    if data.get("passed") is True:
        return "warn" if _has_count(data.get("warnings")) else "pass"
    if data.get("passed") is False:
        return "fail"

    must_total = summary.get("total_must_fix")
    should_total = summary.get("total_should_fix")
    if isinstance(must_total, int) and must_total > 0:
        return "fail"
    if isinstance(should_total, int) and should_total > 0:
        return "warn"

    if _has_count(data.get("errors")):
        return "fail"
    if _has_count(data.get("warnings")):
        return "warn"
    if "errors" in data or "warnings" in data or "issues" in data:
        return "pass"
    return "unknown"


def _legacy_status(status: str) -> str:
    return {
        "pass": "PASS",
        "warn": "PASS_WITH_WARNINGS",
        "fail": "FAIL",
        "unknown": "SKIP",
    }.get(status, "SKIP")


def _has_count(value: Any) -> bool:
    if isinstance(value, int):
        return value > 0
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def _overall_status(checks: list[dict[str, Any]], harness: ReportFile | None) -> str:
    if harness and harness.data:
        return _normalize_status(harness.data, harness.parse_warning)
    present_statuses = [item["status"] for item in checks if item["status"] != "unknown"]
    if not present_statuses:
        return "unknown"
    return max(present_statuses, key=lambda status: _STATUS_RANK.get(status, 1))


def _message_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("message", "detail", "summary", "text", "error"):
            if value.get(key):
                return str(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _severity_for_group(group: str) -> str:
    return {
        "must_fix": "error",
        "should_fix": "warn",
        "accepted_risks": "info",
    }.get(group, "info")


def _group_for_severity(severity: str) -> str:
    normalized = str(severity or "").lower()
    if normalized in {"error", "fail", "failed", "must_fix", "critical", "hard"}:
        return "must_fix"
    if normalized in {"warn", "warning", "should_fix", "medium"}:
        return "should_fix"
    return "accepted_risks"


def _project_relative_path(path: str) -> str:
    normalized = str(path or "").replace("\\", "/")
    if not normalized:
        return ""
    parts = normalized.split("/")
    for root in ("svg_output", "svg_final", "images", "exports", "quality", "analysis", "notes"):
        if root in parts:
            idx = parts.index(root)
            return "/".join(parts[idx:])
    return normalized


def _base_issue(
    *,
    group: str,
    check: str,
    source_file: str,
    message: Any,
    severity: str = "",
    path: str = "",
    file: str = "",
    recommendation: str = "",
) -> dict[str, str]:
    item_path = _project_relative_path(path)
    return {
        "severity": severity or _severity_for_group(group),
        "check": check,
        "source_file": source_file,
        "file": file or (Path(item_path).name if item_path else ""),
        "path": item_path,
        "message": _message_text(message),
        "recommendation": recommendation,
    }


def _extend_issue_group(
    issues: dict[str, list[dict[str, str]]],
    group: str,
    check: str,
    source_file: str,
    values: Any,
    *,
    path: str = "",
    file: str = "",
) -> None:
    if not isinstance(values, list):
        return
    for value in values:
        if isinstance(value, dict):
            item_path = str(value.get("path") or value.get("file") or path or "")
            issues[group].append(
                _base_issue(
                    group=group,
                    check=str(value.get("check") or check),
                    source_file=source_file,
                    message=value,
                    severity=str(value.get("severity") or ""),
                    path=item_path,
                    file=str(value.get("file") or file or ""),
                    recommendation=str(value.get("recommendation") or value.get("suggestion") or ""),
                )
            )
        else:
            issues[group].append(
                _base_issue(
                    group=group,
                    check=check,
                    source_file=source_file,
                    message=value,
                    path=path,
                    file=file,
                )
            )


def _issues_from_report(report: ReportFile) -> dict[str, list[dict[str, str]]]:
    issues: dict[str, list[dict[str, str]]] = {group: [] for group in _ISSUE_GROUPS}
    check = report.check

    if report.parse_warning:
        issues["should_fix"].append(
            _base_issue(
                group="should_fix",
                check=check,
                source_file=report.source_file,
                message=report.parse_warning,
                path=report.source_file,
                recommendation="Open or regenerate this report JSON before relying on it.",
            )
        )
        return issues

    data = report.data
    if not data:
        return issues

    for group in _ISSUE_GROUPS:
        _extend_issue_group(issues, group, check, report.source_file, data.get(group))
    _extend_issue_group(issues, "accepted_risks", check, report.source_file, data.get("accepted"))

    pages = data.get("pages")
    if isinstance(pages, dict):
        for page_name, page_report in pages.items():
            if not isinstance(page_report, dict):
                continue
            page_path = f"svg_output/{page_name}" if str(page_name).endswith(".svg") else str(page_name)
            for group in _ISSUE_GROUPS:
                _extend_issue_group(
                    issues,
                    group,
                    check,
                    report.source_file,
                    page_report.get(group),
                    path=page_path,
                    file=str(page_name),
                )
            _extend_issue_group(
                issues,
                "accepted_risks",
                check,
                report.source_file,
                page_report.get("accepted"),
                path=page_path,
                file=str(page_name),
            )

    results = data.get("results")
    if isinstance(results, list):
        for result in results:
            if not isinstance(result, dict):
                continue
            path = str(result.get("path") or result.get("file") or "")
            _extend_issue_group(
                issues,
                "must_fix",
                check,
                report.source_file,
                result.get("errors"),
                path=path,
                file=str(result.get("file") or ""),
            )
            _extend_issue_group(
                issues,
                "should_fix",
                check,
                report.source_file,
                result.get("warnings"),
                path=path,
                file=str(result.get("file") or ""),
            )

    report_issues = data.get("issues")
    if isinstance(report_issues, list):
        for item in report_issues:
            if not isinstance(item, dict):
                continue
            group = _group_for_severity(str(item.get("severity") or ""))
            issues[group].append(
                _base_issue(
                    group=group,
                    check=str(item.get("check") or check),
                    source_file=report.source_file,
                    message=item,
                    severity=str(item.get("severity") or ""),
                    path=str(item.get("path") or item.get("file") or ""),
                    file=str(item.get("file") or ""),
                    recommendation=str(item.get("recommendation") or item.get("detail") or ""),
                )
            )

    details = data.get("details")
    if isinstance(details, list):
        for detail in details:
            if not isinstance(detail, dict) or detail.get("passed", True):
                continue
            message = detail.get("stderr") or detail.get("stdout") or "Check failed"
            issues["must_fix"].append(
                _base_issue(
                    group="must_fix",
                    check=str(detail.get("label") or check),
                    source_file=report.source_file,
                    message=message,
                    recommendation=f"Inspect {detail.get('label') or check} output.",
                )
            )

    top_errors = data.get("errors")
    top_warnings = data.get("warnings")
    if isinstance(top_errors, list):
        _extend_issue_group(issues, "must_fix", check, report.source_file, top_errors)
    if isinstance(top_warnings, list):
        _extend_issue_group(issues, "should_fix", check, report.source_file, top_warnings)

    return issues


def _merge_issues(reports: dict[str, ReportFile]) -> dict[str, list[dict[str, str]]]:
    merged: dict[str, list[dict[str, str]]] = {group: [] for group in _ISSUE_GROUPS}
    for report in reports.values():
        per_report = _issues_from_report(report)
        for group in _ISSUE_GROUPS:
            merged[group].extend(per_report[group])
    return merged


def _raw_payload(reports: dict[str, ReportFile]) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    for check, report in reports.items():
        if report.data is not None:
            raw[check] = report.data
        else:
            raw[check] = {
                "_path": report.source_file,
                "parse_warning": report.parse_warning,
                "raw_text": report.raw_text,
            }
    return raw


def _detail_command(detail: dict[str, Any]) -> str:
    command = detail.get("command")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command or "")


def _failed_details(reports: dict[str, ReportFile]) -> list[dict[str, Any]]:
    failed: list[dict[str, Any]] = []
    for report in reports.values():
        data = report.data or {}
        details = data.get("details")
        if not isinstance(details, list):
            continue
        for detail in details:
            if not isinstance(detail, dict) or detail.get("passed", True):
                continue
            failed.append({
                "check": str(detail.get("label") or report.check),
                "source_file": report.source_file,
                "command": _detail_command(detail),
                "returncode": detail.get("returncode"),
                "stderr": str(detail.get("stderr") or "")[:1000],
                "stdout": str(detail.get("stdout") or "")[:1000],
            })
    return failed


def _diagnostics(
    project: Path,
    reports: dict[str, ReportFile],
    checks: list[dict[str, Any]],
    issues: dict[str, list[dict[str, str]]],
    overall: str,
) -> dict[str, Any]:
    report_files = [
        {
            "check": report.check,
            "source_file": report.source_file,
            "updated_at": report.updated_at,
        }
        for report in reports.values()
    ]
    report_files.sort(key=lambda item: item["updated_at"] or "", reverse=True)
    latest_check = report_files[0] if report_files else None
    failed_checks = [
        item for item in checks
        if item.get("status") == "fail"
    ]
    failed_details = _failed_details(reports)
    must_fix = issues.get("must_fix", [])
    related_files = []
    for item in must_fix + issues.get("should_fix", []):
        path = item.get("path") or item.get("source_file")
        if path and path not in related_files:
            related_files.append(path)
    failed_scripts = [
        item.get("check") for item in failed_details
        if item.get("check")
    ] or [item.get("id") for item in failed_checks if item.get("id")]
    commands = []
    if any(name in failed_scripts for name in ("spec_compliance", "spec")):
        commands.append(f"python skills/ppt-master/scripts/spec_compliance_check.py {project}")
    if any(name in failed_scripts for name in ("svg_quality", "svg")):
        commands.append(f"python skills/ppt-master/scripts/svg_quality_checker.py {project}")
    if failed_scripts or overall == "fail":
        commands.append(f"python skills/ppt-master/scripts/harness_gate.py {project} --quick")
    return {
        "latest_check": latest_check,
        "failed_scripts": failed_scripts,
        "failed_stage": failed_scripts[0] if failed_scripts else None,
        "error_summary": (must_fix[0].get("message") if must_fix else ""),
        "related_files": related_files[:10],
        "recommended_commands": commands,
        "final_export_path": latest_pptx(project),
        "report_files": report_files,
        "failed_details": failed_details[:5],
    }


def _check_entry(check: str, report: ReportFile | None) -> dict[str, Any]:
    if report is None:
        return {
            "id": check,
            "label": _CHECK_LABELS.get(check, check.replace("_", " ").title()),
            "status": "unknown",
            "source_file": None,
            "updated_at": None,
        }
    return {
        "id": check,
        "label": _CHECK_LABELS.get(check, check.replace("_", " ").title()),
        "status": _normalize_status(report.data, report.parse_warning),
        "source_file": report.source_file,
        "updated_at": report.updated_at,
        "parse_warning": report.parse_warning or None,
    }


def _legacy_harness(
    reports: dict[str, ReportFile],
    checks: list[dict[str, Any]],
    overall: str,
) -> dict[str, Any]:
    harness = reports.get("harness")
    if harness and harness.data:
        data = dict(harness.data)
        data.setdefault("overall", _legacy_status(_normalize_status(harness.data)))
        return data

    statuses = {item["id"]: _legacy_status(item["status"]) for item in checks}
    return {
        "spec_compliance": statuses.get("spec_compliance", "SKIP"),
        "svg_quality": statuses.get("svg_quality", "SKIP"),
        "e2e": statuses.get("e2e", "SKIP"),
        "visual_review": statuses.get("visual_review", "SKIP"),
        "overall": _legacy_status(overall),
        "details": [],
    }


def normalize_quality_report(project: Path) -> Optional[dict]:
    """Return a structured quality report, or None when no report file exists."""
    reports = {
        check: report
        for check in _CHECK_FILES
        if (report := _read_report_file(project, check)) is not None
    }
    if not reports:
        return None

    checks = [_check_entry(check, reports.get(check)) for check in _SUMMARY_CHECKS]
    overall = _overall_status(checks, reports.get("harness"))
    if overall == "unknown" and reports.get("integrated_review"):
        integrated = reports["integrated_review"]
        overall = _normalize_status(integrated.data, integrated.parse_warning)
    harness = _legacy_harness(reports, checks, overall)

    issues = _merge_issues(reports)
    return {
        "overall": overall,
        "checks": checks,
        "issues": issues,
        "diagnostics": _diagnostics(project, reports, checks, issues, overall),
        "raw": _raw_payload(reports),
        "parse_warnings": [
            {
                "check": report.check,
                "source_file": report.source_file,
                "message": report.parse_warning,
            }
            for report in reports.values()
            if report.parse_warning
        ],
        "checked_at": _now(),
        "harness": harness,
        "svg_quality": reports.get("svg_quality").data if reports.get("svg_quality") else None,
        "spec_compliance": reports.get("spec_compliance").data if reports.get("spec_compliance") else None,
        "e2e": reports.get("e2e").data if reports.get("e2e") else None,
        "integrated_review": (
            reports.get("integrated_review").data if reports.get("integrated_review") else None
        ),
        "visual_review": reports.get("visual_review").data if reports.get("visual_review") else None,
    }


def load_check(project: Path, check: str) -> dict | None:
    """Return one normalized check report, or None when absent."""
    if check not in _CHECK_FILES:
        return None
    report = _read_report_file(project, check)
    if report is None:
        return None
    checked_at = report.updated_at
    if report.data:
        checked_at = report.data.get("checked_at") or report.data.get("generated_at") or checked_at
    return {
        "check": check,
        "status": _legacy_status(_normalize_status(report.data, report.parse_warning)),
        "checked_at": checked_at,
        "source_file": report.source_file,
        "parse_warning": report.parse_warning or None,
        "data": report.data,
        "raw_text": report.raw_text or None,
    }


def quality_report(project: Path) -> Optional[dict]:
    """Return aggregate quality report, or None when no report exists."""
    return normalize_quality_report(project)


def quality_summary(project: Path) -> dict | None:
    """Return PipelineState.quality_summary, or None."""
    report = quality_report(project)
    if report is None:
        return None
    harness = report["harness"]
    return {
        "spec_compliance": harness.get("spec_compliance", "SKIP"),
        "svg_quality": harness.get("svg_quality", "SKIP"),
        "e2e": harness.get("e2e", "SKIP"),
        "visual_review": harness.get("visual_review", "SKIP"),
        "overall": harness.get("overall", "SKIP"),
        "checked_at": report.get("checked_at") or _now(),
    }


