#!/usr/bin/env python3
"""
PPT Master - Deep Research Quality Gate

Validates that a deep-research project satisfies the research depth contract
before outputs are synced into the main PPT pipeline.

Usage:
    python3 scripts/research/research_gate.py <project_path>

Examples:
    python3 skills/ppt-master/scripts/research/research_gate.py projects/my_deck

Dependencies:
    None (only uses standard library)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


URL_RE = re.compile(r"https?://[^\s\]\)\}\"'<>，。；;]+", re.IGNORECASE)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
STORYLINE_ALTERNATIVES_RE = re.compile(
    r"<!--\s*STORYLINE_ALTERNATIVES\s*(\{.*?\})\s*-->",
    re.IGNORECASE | re.DOTALL,
)
EVIDENCE_ID_RE = re.compile(r"^E\d{3,}$")
STORYLINE_ID_RE = re.compile(r"^S[1-9]\d*$")
CONSULTING_EVIDENCE_SOURCES = {
    "user_request",
    "ppt_brief",
    "orchestrator_classification",
}
EVIDENCE_GAP_MARKERS = {
    "not provided",
    "not derivable",
    "directional only",
    "needs external verification",
}


@dataclass
class Issue:
    severity: str
    message: str
    return_step: str


class ResearchGate:
    """Validate deep-research outputs against the machine-checkable contract."""

    def __init__(self, project_path: Path):
        self.project = project_path.resolve()
        self.issues: list[Issue] = []
        self.warnings: list[Issue] = []

    def run(self) -> int:
        if not self.project.is_dir():
            print(f"ERROR: project directory not found: {self.project}", file=sys.stderr)
            print("Fix: pass the canonical project folder created by project_manager.py.", file=sys.stderr)
            return 2

        plan = self._load_json("_research/step2_search_plan/search_plan.json", "Step 2")
        manifest = self._load_json("_research/step3_search/search_manifest.json", "Step 3")
        analysis = self._load_json("_research/step5_analysis/research_analysis.json", "Step 5")
        visual = self._load_json("_research/step7_visual/visual_strategy.json", "Step 7")
        report_text = self._load_text("_research/step6_narrative/research_report.md", "Step 6")

        if isinstance(plan, dict):
            self._check_search_plan(plan)
        if isinstance(plan, dict) and isinstance(manifest, dict):
            self._check_search_manifest(plan, manifest)
        if isinstance(manifest, dict) or report_text:
            self._check_sources(manifest if isinstance(manifest, dict) else {}, report_text)
        if isinstance(analysis, dict) or report_text:
            self._check_research_analysis(analysis if isinstance(analysis, dict) else {}, report_text)
        if report_text:
            self._check_report(report_text, analysis if isinstance(analysis, dict) else {})
        if isinstance(visual, dict):
            self._check_visual_strategy(visual)

        self._print_result()
        return 1 if self.issues else 0

    def _load_json(self, rel_path: str, return_step: str) -> Any:
        path = self.project / rel_path
        if not path.exists():
            self._fail(f"Missing {rel_path}.", return_step, f"Run {return_step} and write this artifact.")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._fail(
                f"Invalid JSON in {rel_path}: {exc}.",
                return_step,
                "Rewrite the file as valid JSON before continuing.",
            )
            return None

    def _load_text(self, rel_path: str, return_step: str) -> str:
        path = self.project / rel_path
        if not path.exists():
            self._fail(f"Missing {rel_path}.", return_step, f"Run {return_step} and write this artifact.")
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            self._fail(f"Cannot read {rel_path}: {exc}.", return_step, "Fix file permissions or rewrite it.")
            return ""

    def _fail(self, message: str, return_step: str, fix: str) -> None:
        self.issues.append(Issue("FAIL", f"{message} Fix: {fix}", return_step))

    def _warn(self, message: str, return_step: str, fix: str) -> None:
        self.warnings.append(Issue("WARN", f"{message} Fix: {fix}", return_step))

    def _check_search_plan(self, plan: dict[str, Any]) -> None:
        dimensions = _as_list(plan.get("dimensions"))
        if not 4 <= len(dimensions) <= 6:
            self._fail(
                f"search_plan.json has {len(dimensions)} search dimensions; expected 4-6.",
                "Step 2",
                "Return to Step 2 and rebuild the dimension plan before searching.",
            )

        for index, dimension in enumerate(dimensions, 1):
            if not isinstance(dimension, dict):
                self._fail(
                    f"Dimension #{index} is not an object.",
                    "Step 2",
                    "Rewrite dimensions[] as objects with dimension_id, search_rounds, and source targets.",
                )
                continue
            dim_id = str(dimension.get("dimension_id") or f"#{index}")
            rounds = _as_list(dimension.get("search_rounds"))
            if len(rounds) < 3:
                self._fail(
                    f"{dim_id} has {len(rounds)} search rounds; expected >=3.",
                    "Step 2",
                    "Add at least three distinct search rounds with different purposes.",
                )
            tier12_count = _count_source_targets(dimension)
            if tier12_count < 2:
                self._fail(
                    f"{dim_id} has {tier12_count} Tier 1-2 source targets; expected >=2.",
                    "Step 2",
                    "Add official reports, papers, primary datasets, regulator sources, or authoritative media/research targets.",
                )

        pages = _planned_pages(plan)
        for page in pages:
            page_id = _page_id(page)
            if not page_id:
                continue
            if not page.get("skip_search"):
                if not _as_list(page.get("dimension_ids")):
                    self._fail(
                        f"{page_id} is missing dimension_ids.",
                        "Step 2",
                        "Bind every searched page to one or more search dimensions.",
                    )
                if len(_as_list(page.get("search_rounds"))) < 3:
                    self._fail(
                        f"{page_id} has fewer than 3 planned search rounds.",
                        "Step 2",
                        "Attach at least three round IDs inherited from the relevant dimension(s).",
                    )
                if _count_source_targets(page) < 2:
                    self._fail(
                        f"{page_id} has fewer than 2 planned Tier 1-2 source targets.",
                        "Step 2",
                        "Fill source_targets with tier12_min/preferred_domains or explicit source targets.",
                    )

    def _check_search_manifest(self, plan: dict[str, Any], manifest: dict[str, Any]) -> None:
        planned_ids = {
            _normalize_page_id(_page_id(page))
            for page in _planned_pages(plan)
            if _page_id(page) and not page.get("skip_search")
        }
        result_map = {
            _normalize_page_id(str(item.get("page_id") or item.get("slide") or "")): item
            for item in _as_list(manifest.get("results"))
            if isinstance(item, dict)
        }
        missing = sorted(page_id for page_id in planned_ids if page_id not in result_map)
        if missing:
            self._fail(
                f"search_manifest.json does not cover planned pages: {', '.join(missing)}.",
                "Step 3",
                "Search those pages or mark them skip_search=true with a source-sufficient reason in Step 2.",
            )

        self._check_search_manifest_summary(manifest)

        for page_id in sorted(planned_ids & set(result_map)):
            item = result_map[page_id]
            if "search_triggered" not in item or "execution_route" not in item:
                self._warn(
                    f"{page_id} lacks explicit Step 3 trigger/execution metadata.",
                    "Step 3",
                    "Re-run browse_ai.py so search_manifest.json records trigger_reason, skip_reason, and execution_route.",
                )
            if item.get("fallback") or item.get("needs_manual_websearch") or item.get("quality") in {"low", "failed"}:
                if not item.get("fallback_reason"):
                    self._fail(
                        f"{page_id} used fallback or has low quality but lacks fallback_reason.",
                        "Step 3",
                        "Record why browser/platform search failed and which fallback path was used.",
                    )
                if not item.get("quality_gap"):
                    self._fail(
                        f"{page_id} used fallback or has low quality but lacks quality_gap.",
                        "Step 3",
                        "Record the remaining evidence/source/asset gap, or state 'none' after manual repair.",
                    )
            else:
                if "fallback_reason" not in item or "quality_gap" not in item:
                    self._warn(
                        f"{page_id} lacks the new fallback_reason/quality_gap keys.",
                        "Step 3",
                        "Re-run browse_ai.py or add empty strings for successful non-fallback results.",
                    )

    def _check_search_manifest_summary(self, manifest: dict[str, Any]) -> None:
        results = [item for item in _as_list(manifest.get("results")) if isinstance(item, dict)]
        actual_skipped = sum(1 for item in results if item.get("status") == "skipped")
        actual_manual_required = sum(1 for item in results if item.get("needs_manual_websearch"))
        actual_fallback_success = sum(
            1 for item in results if item.get("fallback") and item.get("status") == "success"
        )
        expected = {
            "total_skipped": actual_skipped,
            "needs_manual_websearch": actual_manual_required,
            "fallback_used": actual_fallback_success,
        }
        for key, actual in expected.items():
            recorded = manifest.get(key)
            if recorded is not None and recorded != actual:
                self._fail(
                    f"search_manifest.json summary {key}={recorded}, but results[] imply {actual}.",
                    "Step 3",
                    "Regenerate search_manifest.json with browse_ai.py or fix the summary after manual repair.",
                )

        execution_summary = manifest.get("execution_summary")
        if execution_summary is None:
            self._warn(
                "search_manifest.json lacks execution_summary.",
                "Step 3",
                "Re-run browse_ai.py so logs show browser-AI, manual WebSearch, and skipped counts.",
            )
        elif isinstance(execution_summary, dict):
            actual_manual_completed = sum(
                1 for item in results if item.get("execution_route") == "manual_websearch_completed"
            )
            recorded_manual_completed = execution_summary.get("manual_websearch_completed")
            if (
                recorded_manual_completed is not None
                and recorded_manual_completed != actual_manual_completed
            ):
                self._fail(
                    "search_manifest.json execution_summary.manual_websearch_completed="
                    f"{recorded_manual_completed}, but results[] imply {actual_manual_completed}.",
                    "Step 3",
                    "Regenerate search_manifest.json after browser/manual fallback repair.",
                )
        else:
            self._fail(
                "search_manifest.json execution_summary must be an object.",
                "Step 3",
                "Rewrite execution_summary with route counts or re-run browse_ai.py.",
            )

    def _check_sources(self, manifest: dict[str, Any], report_text: str) -> None:
        urls: set[str] = set(URL_RE.findall(report_text or ""))
        urls.update(_collect_urls(manifest))
        search_dir = self.project / "_research" / "step3_search"
        if search_dir.is_dir():
            for md_file in search_dir.glob("*.md"):
                try:
                    urls.update(URL_RE.findall(md_file.read_text(encoding="utf-8")))
                except OSError:
                    continue
        if len(urls) < 15:
            self._fail(
                f"Only {len(urls)} unique source URLs found; expected >=15.",
                "Step 3",
                "Return to Step 3 and add authoritative sources, then re-run consolidation/narrative.",
            )

    def _check_research_analysis(self, analysis: dict[str, Any], report_text: str) -> None:
        cross_count = _count_records_by_key(analysis, ("cross", "verified", "fact"))
        if cross_count == 0:
            cross_count = len(re.findall(r"交叉验证|cross-verified|cross verified", report_text, re.IGNORECASE))
        if cross_count < 8:
            self._fail(
                f"Only {cross_count} cross-verified facts found; expected >=8.",
                "Step 5",
                "Return to Step 5 and record facts confirmed by at least two independent sources.",
            )

        data_count = _count_records_by_key(
            analysis,
            ("structured_data", "data_points", "statistics", "timeline", "comparison", "quote"),
        )
        if data_count == 0:
            data_count = _count_structured_markers(report_text)
        if data_count < 10:
            self._fail(
                f"Only {data_count} structured data points found; expected >=10.",
                "Step 5",
                "Return to Step 5 and extract statistics, timeline events, comparisons, and sourced quotes.",
            )

        self._check_consulting_evidence(analysis)

    def _check_consulting_evidence(self, analysis: dict[str, Any]) -> None:
        receipt = analysis.get("consulting_evidence")
        if not isinstance(receipt, dict):
            self._fail(
                "research_analysis.json lacks the consulting_evidence routing receipt.",
                "Step 5",
                "Record enabled, reason, and source before deciding whether evidence_table applies.",
            )
            return

        enabled = receipt.get("enabled")
        if not isinstance(enabled, bool):
            self._fail(
                "consulting_evidence.enabled must be true or false.",
                "Step 5",
                "Write an explicit boolean routing decision.",
            )
            return
        if not _nonempty_string(receipt.get("reason")):
            self._fail(
                "consulting_evidence.reason is missing.",
                "Step 5",
                "Record why the decision-oriented evidence layer is enabled or disabled.",
            )
        if receipt.get("source") not in CONSULTING_EVIDENCE_SOURCES:
            self._fail(
                "consulting_evidence.source is invalid.",
                "Step 5",
                "Use user_request, ppt_brief, or orchestrator_classification.",
            )

        if not enabled:
            if "evidence_table" in analysis:
                self._fail(
                    "evidence_table must be omitted when consulting_evidence.enabled is false.",
                    "Step 5",
                    "Remove the placeholder table or enable the layer with a valid reason.",
                )
            return

        evidence_table = analysis.get("evidence_table")
        if not isinstance(evidence_table, list) or not evidence_table:
            self._fail(
                "consulting evidence is enabled but evidence_table is missing or empty.",
                "Step 5",
                "Build traceable evidence rows before narrative construction.",
            )
            return

        source_registry = _source_registry_ids(analysis)
        seen_ids: set[str] = set()
        for index, row in enumerate(evidence_table, 1):
            if not isinstance(row, dict):
                self._fail(
                    f"evidence_table row #{index} is not an object.",
                    "Step 5",
                    "Rewrite every evidence row with the documented fields.",
                )
                continue

            evidence_id = str(row.get("evidence_id") or "").strip()
            if EVIDENCE_ID_RE.fullmatch(evidence_id) is None:
                self._fail(
                    f"evidence_table row #{index} has invalid evidence_id {evidence_id!r}.",
                    "Step 5",
                    "Use a stable ID such as E001.",
                )
            elif evidence_id in seen_ids:
                self._fail(
                    f"evidence_table repeats evidence_id {evidence_id}.",
                    "Step 5",
                    "Keep evidence IDs unique and stable.",
                )
            else:
                seen_ids.add(evidence_id)

            for field_name in (
                "claim_or_data",
                "value",
                "unit",
                "period",
                "source_location",
                "conflict_or_caveat",
                "implication",
                "recommended_visual",
            ):
                if not _present_scalar(row.get(field_name)):
                    self._fail(
                        f"{evidence_id or f'row #{index}'} lacks {field_name}.",
                        "Step 5",
                        "Preserve the original scope or use an explicit evidence-gap marker.",
                    )

            if row.get("confidence") not in {"high", "medium", "low"}:
                self._fail(
                    f"{evidence_id or f'row #{index}'} has invalid confidence.",
                    "Step 5",
                    "Use high, medium, or low based on source quality and cross-checks.",
                )

            source_ids = row.get("source_ids")
            if not isinstance(source_ids, list) or not all(
                isinstance(source_id, str) and source_id.strip() for source_id in source_ids
            ):
                self._fail(
                    f"{evidence_id or f'row #{index}'} source_ids must be a string array.",
                    "Step 5",
                    "Reference sources[] IDs, or use an empty array only for an explicit gap row.",
                )
                continue
            normalized_source_ids = {source_id.strip() for source_id in source_ids}
            unknown_ids = sorted(normalized_source_ids - source_registry)
            if unknown_ids:
                self._fail(
                    f"{evidence_id or f'row #{index}'} references unknown sources: "
                    f"{', '.join(unknown_ids)}.",
                    "Step 5",
                    "Add the sources to sources[] or correct source_ids.",
                )
            if not normalized_source_ids and not _has_evidence_gap_marker(row):
                self._fail(
                    f"{evidence_id or f'row #{index}'} has no source_ids and no gap marker.",
                    "Step 5",
                    "Cite a source or mark the evidence as not provided/not derivable.",
                )

    def _check_report(self, text: str, analysis: dict[str, Any]) -> None:
        body_units = _body_units(text)
        if body_units < 3000:
            self._fail(
                f"research_report.md body depth is {body_units} units; expected >=3000 Chinese chars / word-equivalent units.",
                "Step 6",
                "Return to Step 6 and expand sourced narrative analysis without padding.",
            )
        receipt = analysis.get("consulting_evidence")
        if not isinstance(receipt, dict) or receipt.get("enabled") is not True:
            return
        self._check_storyline_alternatives(text, _evidence_ids(analysis))

    def _check_storyline_alternatives(self, text: str, evidence_ids: set[str]) -> None:
        match = STORYLINE_ALTERNATIVES_RE.search(text)
        if match is None:
            self._fail(
                "consulting evidence is enabled but research_report.md lacks "
                "STORYLINE_ALTERNATIVES.",
                "Step 6",
                "Write the machine-readable block with 2-3 SCR candidates.",
            )
            return
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            self._fail(
                f"STORYLINE_ALTERNATIVES contains invalid JSON: {exc}.",
                "Step 6",
                "Rewrite the comment block as valid JSON.",
            )
            return
        if not isinstance(payload, dict) or payload.get("enabled") is not True:
            self._fail(
                "STORYLINE_ALTERNATIVES must be an enabled JSON object.",
                "Step 6",
                "Set enabled=true and provide the required candidates.",
            )
            return

        alternatives = payload.get("storyline_alternatives")
        if not isinstance(alternatives, list) or not 2 <= len(alternatives) <= 3:
            self._fail(
                "storyline_alternatives must contain exactly 2-3 candidates.",
                "Step 6",
                "Compare 2-3 real SCR options before selecting one.",
            )
            return

        recommendation = payload.get("recommended_storyline")
        if not isinstance(recommendation, dict):
            self._fail(
                "recommended_storyline is missing from STORYLINE_ALTERNATIVES.",
                "Step 6",
                "Reference exactly one candidate and state the selection rationale.",
            )
            recommendation = {}
        recommended_id = str(recommendation.get("storyline_id") or "").strip()
        if not _nonempty_string(recommendation.get("rationale")):
            self._fail(
                "recommended_storyline.rationale is missing.",
                "Step 6",
                "Explain why the selected SCR best fits the evidence, audience, and goal.",
            )

        seen_ids: set[str] = set()
        for index, candidate in enumerate(alternatives, 1):
            if not isinstance(candidate, dict):
                self._fail(
                    f"storyline candidate #{index} is not an object.",
                    "Step 6",
                    "Rewrite each candidate with the documented SCR fields.",
                )
                continue
            storyline_id = str(candidate.get("storyline_id") or "").strip()
            if STORYLINE_ID_RE.fullmatch(storyline_id) is None:
                self._fail(
                    f"storyline candidate #{index} has invalid ID {storyline_id!r}.",
                    "Step 6",
                    "Use a stable ID such as S1.",
                )
            elif storyline_id in seen_ids:
                self._fail(
                    f"storyline_alternatives repeats {storyline_id}.",
                    "Step 6",
                    "Keep storyline IDs unique.",
                )
            else:
                seen_ids.add(storyline_id)

            scr = candidate.get("scr")
            if not isinstance(scr, dict) or any(
                not _nonempty_string(scr.get(key))
                for key in ("situation", "complication", "resolution")
            ):
                self._fail(
                    f"{storyline_id or f'candidate #{index}'} lacks complete SCR statements.",
                    "Step 6",
                    "Write one non-empty sentence for situation, complication, and resolution.",
                )
            for field_name in ("management_conclusion", "audience_fit"):
                if not _nonempty_string(candidate.get(field_name)):
                    self._fail(
                        f"{storyline_id or f'candidate #{index}'} lacks {field_name}.",
                        "Step 6",
                        "Complete every decision-oriented storyline field.",
                    )

            key_evidence_ids = candidate.get("key_evidence_ids")
            if not isinstance(key_evidence_ids, list) or not key_evidence_ids or not all(
                isinstance(item, str) and item.strip() for item in key_evidence_ids
            ):
                self._fail(
                    f"{storyline_id or f'candidate #{index}'} has invalid key_evidence_ids.",
                    "Step 6",
                    "Reference at least one evidence_table ID without fabrication.",
                )
                candidate_evidence_ids: set[str] = set()
            else:
                candidate_evidence_ids = {item.strip() for item in key_evidence_ids}
                if len(key_evidence_ids) > 8:
                    self._fail(
                        f"{storyline_id or f'candidate #{index}'} uses more than 8 evidence IDs.",
                        "Step 6",
                        "Keep the strongest 5-8 IDs, or fewer with an explicit caveat.",
                    )
                unknown_ids = sorted(candidate_evidence_ids - evidence_ids)
                if unknown_ids:
                    self._fail(
                        f"{storyline_id or f'candidate #{index}'} references unknown evidence: "
                        f"{', '.join(unknown_ids)}.",
                        "Step 6",
                        "Use only IDs present in evidence_table.",
                    )

            caveats = candidate.get("caveats")
            if not isinstance(caveats, list) or not all(isinstance(item, str) for item in caveats):
                self._fail(
                    f"{storyline_id or f'candidate #{index}'} caveats must be a string array.",
                    "Step 6",
                    "Record conflicts and evidence limitations, or use an empty array.",
                )
            elif len(candidate_evidence_ids) < 5 and not any(item.strip() for item in caveats):
                self._fail(
                    f"{storyline_id or f'candidate #{index}'} has fewer than 5 evidence IDs "
                    "without a caveat.",
                    "Step 6",
                    "Keep the honest shortfall and explain it in caveats.",
                )

            page_material_pool = candidate.get("page_material_pool")
            if not isinstance(page_material_pool, list) or not page_material_pool or not all(
                isinstance(item, str) and item.strip() for item in page_material_pool
            ):
                self._fail(
                    f"{storyline_id or f'candidate #{index}'} lacks page_material_pool.",
                    "Step 6",
                    "List usable charts, tables, matrices, timelines, annotations, or sidebars.",
                )

            rejected_reason = candidate.get("rejected_reason")
            if storyline_id == recommended_id:
                if rejected_reason is not None:
                    self._fail(
                        f"Recommended storyline {storyline_id} must set rejected_reason to null.",
                        "Step 6",
                        "Reserve rejected_reason for unselected candidates.",
                    )
            elif not _nonempty_string(rejected_reason):
                self._fail(
                    f"Unselected storyline {storyline_id or f'#{index}'} lacks rejected_reason.",
                    "Step 6",
                    "State the evidence, caveat, repetition, or audience reason for rejection.",
                )

        if recommended_id not in seen_ids:
            self._fail(
                "recommended_storyline does not resolve to one candidate.",
                "Step 6",
                "Reference exactly one storyline_id from storyline_alternatives.",
            )

    def _check_visual_strategy(self, visual: dict[str, Any]) -> None:
        per_page = _as_list(visual.get("per_page_visual_strategy"))
        if not per_page:
            self._fail(
                "visual_strategy.json lacks per_page_visual_strategy.",
                "Step 7",
                "Return to Step 7 and write a per-page visual strategy before sync.",
            )
        else:
            missing_page_ids = [str(index + 1) for index, item in enumerate(per_page) if not isinstance(item, dict) or not item.get("page_id")]
            if missing_page_ids:
                self._fail(
                    f"{len(missing_page_ids)} per-page visual strategy entries lack page_id.",
                    "Step 7",
                    "Add page_id to every per_page_visual_strategy entry.",
                )

        ref_images = _as_list(visual.get("reference_images"))
        reviewed = 0
        for item in ref_images:
            if not isinstance(item, dict):
                continue
            if item.get("approved") is True or (
                "subject_match" in item and "style_match" in item and "cropping_risk" in item
            ):
                reviewed += 1
        if reviewed < 1:
            self._fail(
                "visual_strategy.json lacks reviewed reference image records.",
                "Step 7",
                "Add reference_images[] entries with path/source_url, subject_match, style_match, cropping_risk, and approved.",
            )

    def _print_result(self) -> None:
        print("=" * 72)
        print("PPT Master Research Gate")
        print("=" * 72)
        if self.issues:
            print("FAIL")
        else:
            print("PASS")

        if self.issues:
            print("\nBlocking gaps:")
            for issue in self.issues:
                print(f"  [FAIL] {issue.message}")
                print(f"         Return to: {issue.return_step}")
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  [WARN] {warning.message}")
                print(f"         Check: {warning.return_step}")
        if not self.issues:
            print("\nResearch depth contract satisfied. Proceed to sync_research_outputs.py.")


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _present_scalar(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return isinstance(value, (int, float))


def _source_registry_ids(analysis: dict[str, Any]) -> set[str]:
    return {
        str(source.get("source_id") or "").strip()
        for source in _as_list(analysis.get("sources"))
        if isinstance(source, dict) and str(source.get("source_id") or "").strip()
    }


def _evidence_ids(analysis: dict[str, Any]) -> set[str]:
    return {
        str(row.get("evidence_id") or "").strip()
        for row in _as_list(analysis.get("evidence_table"))
        if isinstance(row, dict) and str(row.get("evidence_id") or "").strip()
    }


def _has_evidence_gap_marker(row: dict[str, Any]) -> bool:
    text = json.dumps(row, ensure_ascii=False).casefold()
    return any(marker in text for marker in EVIDENCE_GAP_MARKERS)


def _planned_pages(plan: dict[str, Any]) -> list[dict[str, Any]]:
    raw = plan.get("pages", plan.get("items", []))
    return [item for item in _as_list(raw) if isinstance(item, dict)]


def _page_id(page: dict[str, Any]) -> str:
    return str(page.get("page_id") or page.get("slide") or page.get("id") or "")


def _normalize_page_id(value: str) -> str:
    value = value.strip()
    match = re.match(r"^[Pp]?0*(\d+)$", value)
    if match:
        return f"P{int(match.group(1)):02d}"
    return value.upper()


def _count_source_targets(item: dict[str, Any]) -> int:
    source_targets = item.get("source_targets")
    if isinstance(source_targets, dict):
        if isinstance(source_targets.get("tier12_min"), int):
            return int(source_targets["tier12_min"])
        lists = []
        for key in ("preferred_domains", "preferred_sources", "tier12_sources", "targets"):
            lists.extend(_as_list(source_targets.get(key)))
        return len([entry for entry in lists if entry])
    if isinstance(source_targets, list):
        return len([entry for entry in source_targets if entry])
    source_strategy = _as_list(item.get("source_strategy"))
    preferred = _as_list(item.get("preferred_sources"))
    return len([entry for entry in source_strategy + preferred if entry])


def _collect_urls(value: Any) -> set[str]:
    urls: set[str] = set()
    if isinstance(value, dict):
        for child in value.values():
            urls.update(_collect_urls(child))
    elif isinstance(value, list):
        for child in value:
            urls.update(_collect_urls(child))
    elif isinstance(value, str):
        urls.update(URL_RE.findall(value))
    return urls


def _count_records_by_key(value: Any, key_hints: tuple[str, ...]) -> int:
    count = 0
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if any(hint in key_lower for hint in key_hints):
                if isinstance(child, list):
                    count += len(child)
                elif isinstance(child, dict):
                    count += len(child)
                elif child:
                    count += 1
            count += _count_records_by_key(child, key_hints)
    elif isinstance(value, list):
        for child in value:
            count += _count_records_by_key(child, key_hints)
    return count


def _count_structured_markers(text: str) -> int:
    number_markers = re.findall(r"\d+(?:\.\d+)?\s*(?:%|万|亿|美元|年|月|x|倍|人|家|个)", text)
    quote_markers = re.findall(r"[“\"].{6,80}[”\"]", text)
    return len(number_markers) + len(quote_markers)


def _body_units(text: str) -> int:
    visible_text = HTML_COMMENT_RE.sub("", text)
    cjk_count = len(CJK_RE.findall(visible_text))
    word_count = len(WORD_RE.findall(visible_text))
    return cjk_count + word_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate deep-research artifacts before syncing to the PPT pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory containing _research/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return ResearchGate(Path(args.project_path)).run()


if __name__ == "__main__":
    raise SystemExit(main())
