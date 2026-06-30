#!/usr/bin/env python3
"""
PPT Master - Research Asset Gate

Checks that image and visual asset manifests satisfy layout and semantic
requirements before the Executor starts SVG generation.

Usage:
    python3 scripts/research/asset_gate.py <project_path>

Examples:
    python3 skills/ppt-master/scripts/research/asset_gate.py projects/my_deck

Dependencies:
    Pillow
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None


URL_RE = re.compile(r"^https?://", re.IGNORECASE)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
INFO_PAGE_TYPES = {"deep_dive", "comparison", "data", "timeline"}


@dataclass
class Issue:
    severity: str
    message: str
    return_step: str


class AssetGate:
    """Run schema, file, dimension, and reference checks for image assets."""

    def __init__(self, project_path: Path):
        self.project = project_path.resolve()
        self.errors: list[Issue] = []
        self.warnings: list[Issue] = []
        self._planned_files: set[str] = set()

    def run(self) -> int:
        if Image is None:
            print("ERROR: Pillow is not installed. Fix: run `pip install Pillow`.", file=sys.stderr)
            return 2
        if not self.project.is_dir():
            print(f"ERROR: project directory not found: {self.project}", file=sys.stderr)
            print("Fix: pass the canonical project folder created by project_manager.py.", file=sys.stderr)
            return 2

        outline = self._load_json("detailed_outline.json", "Detailed Outline")
        visual = self._load_json("analysis/visual_strategy.json", "deep-research Step 7", required=False)
        if visual is None:
            visual = self._load_json("_research/step7_visual/visual_strategy.json", "deep-research Step 7", required=False)
        prompts = self._load_json("images/image_prompts.json", "Step 5", required=False)
        queries = self._load_json("images/image_queries.json", "Step 5", required=False)
        sources = self._load_json("images/image_sources.json", "Step 5", required=False)
        search_manifest = self._load_json("_research/step3_search/search_manifest.json", "deep-research Step 3", required=False)

        if isinstance(outline, dict):
            self._check_outline(outline, visual if isinstance(visual, dict) else {})
        elif outline is None:
            self._error(
                "Missing detailed_outline.json.",
                "Detailed Outline",
                "Run the detailed-outline workflow before image acquisition / Executor.",
            )

        if isinstance(prompts, dict):
            self._check_ai_prompts(prompts)
        if isinstance(queries, dict):
            self._check_web_queries(queries)
        if isinstance(sources, dict) or isinstance(sources, list):
            self._check_image_sources(sources)
        if isinstance(search_manifest, dict):
            self._check_search_assets(search_manifest)

        self._check_orphan_web_assets()
        self._print_result()
        return 1 if self.errors else 0

    def _load_json(self, rel_path: str, return_step: str, *, required: bool = True) -> Any:
        path = self.project / rel_path
        if not path.exists():
            if required:
                self._error(f"Missing {rel_path}.", return_step, f"Create {rel_path} before continuing.")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._error(f"Invalid JSON in {rel_path}: {exc}.", return_step, "Rewrite this file as valid JSON.")
            return None

    def _error(self, message: str, return_step: str, fix: str) -> None:
        self.errors.append(Issue("FAIL", f"{message} Fix: {fix}", return_step))

    def _warn(self, message: str, return_step: str, fix: str) -> None:
        self.warnings.append(Issue("WARN", f"{message} Fix: {fix}", return_step))

    def _check_outline(self, outline: dict[str, Any], visual: dict[str, Any]) -> None:
        visual_by_page = _visual_by_page(visual)
        for page in _as_list(outline.get("pages")):
            if not isinstance(page, dict):
                continue
            page_id = _page_id(page)
            page_type = str(page.get("page_type") or "").lower()
            visual_need = page.get("visual_need") if isinstance(page.get("visual_need"), dict) else {}
            layout_plan = page.get("layout_plan") if isinstance(page.get("layout_plan"), dict) else {}
            image_type = str(visual_need.get("image_type") or "").lower()
            needs_image = image_type in {"ai_generated", "stock_search"} or bool(visual_need.get("image_description"))
            slot = _slot_size(visual_need.get("image_slot_size")) or _slot_size(layout_plan.get("image_area"))

            if needs_image and slot is None:
                self._error(
                    f"{page_id} needs an image but lacks visual_need.image_slot_size.",
                    "Detailed Outline",
                    "Fill image_slot_size from the intended layout slot before writing prompts or queries.",
                )

            if visual_need.get("reference_image_required") and not _valid_ref_value(visual_need.get("reference_image"), self.project):
                self._error(
                    f"{page_id} requires a reference image but visual_need.reference_image is missing or invalid.",
                    "deep-research Step 7",
                    "Collect a vetted local reference under images/ref or use an HTTP(S) URL.",
                )

            if page_type in INFO_PAGE_TYPES:
                if not self._has_information_asset(page, visual_by_page.get(_normalize_page_id(page_id), {})):
                    self._error(
                        f"{page_id} is a {page_type} page without a web asset, AI Type B fallback, or svg-native card declaration.",
                        "Step 5",
                        "Acquire a web asset, declare image_strategy=ai_type_b, or mark svg_native_card/svg-native information card.",
                    )

            asset_file = str(visual_need.get("asset_file") or "")
            if asset_file:
                self._planned_files.add(_basename(asset_file))

    def _has_information_asset(self, page: dict[str, Any], visual: dict[str, Any]) -> bool:
        visual_need = page.get("visual_need") if isinstance(page.get("visual_need"), dict) else {}
        fields = [
            visual_need.get("asset_file"),
            visual_need.get("web_asset"),
            visual.get("asset_file"),
            visual.get("web_asset"),
        ]
        for value in fields:
            if value:
                self._planned_files.add(_basename(str(value)))
                return True

        strategy = " ".join(
            str(value).lower()
            for value in [
                visual.get("image_strategy"),
                visual.get("fallback"),
                visual.get("asset_strategy"),
                visual_need.get("fallback"),
                visual_need.get("image_strategy"),
            ]
            if value
        )
        if "ai_type_b" in strategy or "type b" in strategy:
            return True
        if "svg-native" in strategy or "svg_native" in strategy or "information card" in strategy:
            return True
        return bool(visual.get("svg_native_card") or visual_need.get("svg_native_card"))

    def _check_ai_prompts(self, prompts: dict[str, Any]) -> None:
        for item in _manifest_items(prompts):
            filename = str(item.get("filename") or item.get("output") or "")
            if filename:
                self._planned_files.add(_basename(filename))
            label = filename or str(item.get("id") or item.get("page_id") or "AI prompt")
            target = _target_size(item)
            if not target:
                self._error(
                    f"{label} lacks target_width/target_height.",
                    "Step 5",
                    "Write layout-derived target dimensions into image_prompts.json.",
                )
            if item.get("reference_image_required") or item.get("concrete_subject") or item.get("requires_reference"):
                if not _valid_ref_value(item.get("reference_image"), self.project):
                    self._error(
                        f"{label} requires reference_image but none is valid.",
                        "Step 5",
                        "Provide a local reference file or HTTP(S) URL before generation.",
                    )
            elif _looks_concrete_subject(item) and not _valid_ref_value(item.get("reference_image"), self.project):
                self._error(
                    f"{label} appears to depict a concrete subject but lacks reference_image.",
                    "Step 5",
                    "Add reference_image or explicitly mark concrete_subject=false for abstract concept art.",
                )
            self._check_file_against_slot(filename, target, label, "Step 5")

    def _check_web_queries(self, queries: dict[str, Any]) -> None:
        for item in _manifest_items(queries):
            filename = str(item.get("filename") or "")
            if filename:
                self._planned_files.add(_basename(filename))
            label = filename or str(item.get("slide") or item.get("page_id") or "web query")
            target = _target_size(item, width_keys=("min_width", "target_width", "width"), height_keys=("min_height", "target_height", "height"))
            status = str(item.get("status") or "")
            if filename and status in {"Sourced", "Generated", ""}:
                self._check_file_against_slot(filename, target, label, "Step 5")

    def _check_image_sources(self, sources: Any) -> None:
        for item in _manifest_items(sources):
            filename = str(item.get("filename") or item.get("file") or item.get("path") or "")
            if not filename:
                continue
            self._planned_files.add(_basename(filename))
            target = _target_size(item)
            label = filename
            self._check_file_against_slot(filename, target, label, "Step 5")

    def _check_search_assets(self, manifest: dict[str, Any]) -> None:
        for item in _as_list(manifest.get("asset_manifest")):
            if not isinstance(item, dict):
                continue
            filename = str(item.get("file") or item.get("filename") or "")
            if not filename:
                continue
            self._planned_files.add(_basename(filename))
            target = _slot_size(item.get("planned_slot")) or _target_size(item)
            self._check_file_against_slot(filename, target, filename, "deep-research Step 3")

    def _check_file_against_slot(
        self,
        filename: str,
        target: tuple[int, int] | None,
        label: str,
        return_step: str,
    ) -> None:
        if not filename or not target:
            return
        path = _resolve_project_path(filename, self.project)
        if path is None or not path.exists():
            status_hint = " If this is an AI row in Needs-Manual, place the generated file before Executor."
            self._error(
                f"{label} points to missing file {filename}.",
                return_step,
                f"Download/generate it into project/images or update the manifest path.{status_hint}",
            )
            return
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            return
        try:
            with Image.open(path) as img:
                width, height = img.size
        except OSError as exc:
            self._error(
                f"{label} cannot be opened as an image: {exc}.",
                return_step,
                "Replace the file with a readable bitmap or update the manifest path.",
            )
            return

        target_w, target_h = target
        if width < target_w * 0.8 or height < target_h * 0.8:
            self._error(
                f"{label} is {width}x{height}, below 80% of target slot {target_w}x{target_h}.",
                return_step,
                "Acquire a larger image or reduce the planned image slot before Executor.",
            )
        actual_ratio = width / height if height else 0
        target_ratio = target_w / target_h if target_h else 0
        if actual_ratio and target_ratio:
            deviation = abs(actual_ratio - target_ratio) / target_ratio
            if deviation > 0.15:
                self._error(
                    f"{label} aspect ratio {actual_ratio:.2f} deviates {deviation:.0%} from target {target_ratio:.2f}.",
                    return_step,
                    "Re-crop/re-source the image, mark the row Needs-Manual, or revise the layout slot.",
                )

    def _check_orphan_web_assets(self) -> None:
        web_dir = self.project / "images" / "web_assets"
        if not web_dir.is_dir():
            return
        referenced = {name.lower() for name in self._planned_files}
        svg_refs = self._svg_references()
        referenced.update(name.lower() for name in svg_refs)
        for path in web_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.name.lower() not in referenced:
                self._warn(
                    f"images/web_assets/{path.name} is not referenced by any plan, manifest, or SVG.",
                    "Step 5",
                    "Remove it if unused, or add it to detailed_outline/image_sources/SVG usage.",
                )

    def _svg_references(self) -> set[str]:
        refs: set[str] = set()
        svg_dir = self.project / "svg_output"
        if not svg_dir.is_dir():
            return refs
        for svg_file in svg_dir.glob("*.svg"):
            try:
                text = svg_file.read_text(encoding="utf-8")
            except OSError:
                continue
            for match in re.findall(r"(?:href|xlink:href)=[\"']([^\"']+)[\"']", text):
                refs.add(_basename(match))
        return refs

    def _print_result(self) -> None:
        print("=" * 72)
        print("PPT Master Asset Gate")
        print("=" * 72)
        print("FAIL" if self.errors else "PASS")
        if self.errors:
            print("\nBlocking gaps:")
            for issue in self.errors:
                print(f"  [FAIL] {issue.message}")
                print(f"         Return to: {issue.return_step}")
        if self.warnings:
            print("\nWarnings:")
            for issue in self.warnings:
                print(f"  [WARN] {issue.message}")
                print(f"         Check: {issue.return_step}")
        if not self.errors:
            print("\nAsset contract satisfied. Proceed to Executor.")


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _manifest_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        raw = value.get("items", value.get("assets", value.get("sources", [])))
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _page_id(page: dict[str, Any]) -> str:
    raw = page.get("page_id") or page.get("id")
    if raw:
        return str(raw)
    number = page.get("page_number")
    if isinstance(number, int):
        return f"P{number:02d}"
    return "unknown page"


def _normalize_page_id(value: str) -> str:
    match = re.match(r"^[Pp]?0*(\d+)$", str(value).strip())
    if match:
        return f"P{int(match.group(1)):02d}"
    return str(value).strip().upper()


def _visual_by_page(visual: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in _as_list(visual.get("per_page_visual_strategy")):
        if not isinstance(item, dict):
            continue
        page_id = item.get("page_id")
        if page_id:
            result[_normalize_page_id(str(page_id))] = item
    return result


def _slot_size(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, dict):
        return None
    width = _positive_int(value.get("width"))
    height = _positive_int(value.get("height"))
    if width and height:
        return width, height
    return None


def _target_size(
    item: dict[str, Any],
    *,
    width_keys: tuple[str, ...] = ("target_width", "min_width", "width"),
    height_keys: tuple[str, ...] = ("target_height", "min_height", "height"),
) -> tuple[int, int] | None:
    nested = _slot_size(item.get("target_slot")) or _slot_size(item.get("planned_slot")) or _slot_size(item.get("image_slot_size"))
    if nested:
        return nested
    width = next((_positive_int(item.get(key)) for key in width_keys if _positive_int(item.get(key))), None)
    height = next((_positive_int(item.get(key)) for key in height_keys if _positive_int(item.get(key))), None)
    if width and height:
        return width, height
    return None


def _positive_int(value: Any) -> int | None:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _valid_ref_value(value: Any, project: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    value = value.strip()
    if URL_RE.match(value):
        return True
    path = _resolve_project_path(value, project)
    return bool(path and path.exists() and path.is_file())


def _resolve_project_path(value: str, project: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    candidates = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.extend([
            project / value,
            project / "images" / value,
            project / "images" / "web_assets" / value,
            project / "images" / "ref" / value,
        ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def _basename(value: str) -> str:
    clean = value.split("#", 1)[0].split("?", 1)[0]
    return Path(clean).name


def _looks_concrete_subject(item: dict[str, Any]) -> bool:
    text = " ".join(str(item.get(key) or "") for key in ("prompt", "subject", "purpose", "description"))
    concrete_terms = [
        "person",
        "people",
        "portrait",
        "product",
        "object",
        "place",
        "character",
        "ip",
        "人物",
        "产品",
        "物品",
        "地点",
        "角色",
        "真实场景",
    ]
    return any(term.lower() in text.lower() for term in concrete_terms)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate image assets before Executor SVG generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return AssetGate(Path(args.project_path)).run()


if __name__ == "__main__":
    raise SystemExit(main())
