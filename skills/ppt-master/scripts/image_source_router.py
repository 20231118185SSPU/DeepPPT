#!/usr/bin/env python3
"""
PPT Master - Image Source Router

Annotate image search query manifests with domain-aware source routing fields.
The router is offline-only: it reads project metadata and JSON manifests, then
adds source-pack policy fields without searching the web or downloading assets.

Usage:
    python3 scripts/image_source_router.py <project_path> [options]

Examples:
    python3 scripts/image_source_router.py projects/demo_ppt169_20260702 --dry-run
    python3 scripts/image_source_router.py projects/demo_ppt169_20260702
    python3 scripts/image_source_router.py projects/demo_ppt169_20260702 --json --dry-run

Dependencies:
    None (only uses standard library)

See references/image-source-routing.md for the source-pack contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from json_utils import atomic_write_json  # noqa: E402


DEFAULT_QUERY_STATUS = "Pending"
SEARCH_REQUIRED_ITEM_FIELDS = ("filename", "query", "status")

GENERIC_STOCK_PROVIDERS = ["pexels", "pixabay", "unsplash"]


@dataclass
class RouteDecision:
    source_pack: str
    preferred_sources: list[str]
    preferred_providers: list[str]
    disabled_providers: list[str]
    allow_generic_stock: bool
    discovery_only: bool
    needs_manual_review: bool
    copyright_risk: str
    selection_reason: str


SOURCE_PACK_DEFAULTS: dict[str, RouteDecision] = {
    "generic_atmosphere": RouteDecision(
        source_pack="generic_atmosphere",
        preferred_sources=["pexels", "unsplash", "pixabay", "openverse"],
        preferred_providers=["pexels", "unsplash", "pixabay", "openverse", "flickr"],
        disabled_providers=[],
        allow_generic_stock=True,
        discovery_only=False,
        needs_manual_review=False,
        copyright_risk="low",
        selection_reason="Generic atmosphere/background subject; stock providers are appropriate.",
    ),
    "open_licensed_commons": RouteDecision(
        source_pack="open_licensed_commons",
        preferred_sources=["wikimedia", "openverse", "flickr_cc"],
        preferred_providers=["wikimedia", "openverse", "flickr"],
        disabled_providers=[],
        allow_generic_stock=False,
        discovery_only=False,
        needs_manual_review=False,
        copyright_risk="medium",
        selection_reason="Open-license educational/general subject; prefer Commons-style provenance.",
    ),
    "academic_science": RouteDecision(
        source_pack="academic_science",
        preferred_sources=["wikimedia", "nasa", "institutional_report", "research_institution"],
        preferred_providers=["wikimedia", "nasa", "openverse"],
        disabled_providers=GENERIC_STOCK_PROVIDERS,
        allow_generic_stock=False,
        discovery_only=False,
        needs_manual_review=False,
        copyright_risk="medium",
        selection_reason="Scientific or academic subject; prefer authoritative/open institutional sources.",
    ),
    "historical_culture": RouteDecision(
        source_pack="historical_culture",
        preferred_sources=["wikimedia", "smithsonian", "museum_open_access", "archive"],
        preferred_providers=["wikimedia", "smithsonian", "openverse"],
        disabled_providers=GENERIC_STOCK_PROVIDERS,
        allow_generic_stock=False,
        discovery_only=False,
        needs_manual_review=True,
        copyright_risk="medium",
        selection_reason="Historical/cultural subject; prefer archive, museum, or Commons provenance.",
    ),
    "anime_game_ip": RouteDecision(
        source_pack="anime_game_ip",
        preferred_sources=["official_site", "official_wiki", "publisher_press_kit", "fandom", "moegirl", "biliwiki"],
        preferred_providers=[],
        disabled_providers=GENERIC_STOCK_PROVIDERS + ["openverse"],
        allow_generic_stock=False,
        discovery_only=True,
        needs_manual_review=True,
        copyright_risk="high",
        selection_reason="IP-specific subject; generic stock cannot prove identity or usage rights.",
    ),
    "official_product": RouteDecision(
        source_pack="official_product",
        preferred_sources=["official_site", "product_docs", "press_kit", "app_store", "official_storefront"],
        preferred_providers=[],
        disabled_providers=GENERIC_STOCK_PROVIDERS,
        allow_generic_stock=False,
        discovery_only=True,
        needs_manual_review=True,
        copyright_risk="high",
        selection_reason="Specific product/software/brand asset; prefer official source pages.",
    ),
    "real_person": RouteDecision(
        source_pack="real_person",
        preferred_sources=["official_bio", "organization_newsroom", "event_organizer", "wikimedia", "authority_media"],
        preferred_providers=["wikimedia"],
        disabled_providers=GENERIC_STOCK_PROVIDERS,
        allow_generic_stock=False,
        discovery_only=True,
        needs_manual_review=True,
        copyright_risk="high",
        selection_reason="Named person or portrait; identity ambiguity requires authoritative provenance.",
    ),
    "news_recent_event": RouteDecision(
        source_pack="news_recent_event",
        preferred_sources=["official_announcement", "regulator", "primary_document", "authority_media"],
        preferred_providers=[],
        disabled_providers=GENERIC_STOCK_PROVIDERS,
        allow_generic_stock=False,
        discovery_only=True,
        needs_manual_review=True,
        copyright_risk="high",
        selection_reason="Recent/news subject; use authoritative source-page discovery and manual review.",
    ),
    "data_report_capture": RouteDecision(
        source_pack="data_report_capture",
        preferred_sources=["official_report", "data_portal", "company_ir", "institution_page"],
        preferred_providers=[],
        disabled_providers=GENERIC_STOCK_PROVIDERS,
        allow_generic_stock=False,
        discovery_only=True,
        needs_manual_review=True,
        copyright_risk="medium",
        selection_reason="Report/chart/dashboard visual should come from source report or be redrawn as SVG.",
    ),
}


SIGNALS: list[tuple[str, tuple[str, ...]]] = [
    ("anime_game_ip", (
        "anime", "game character", "official art", "key visual", "skin", "genshin",
        "原神", "角色", "二次元", "动漫", "游戏角色", "官方立绘", "设定图", "同人",
        "fandom", "moegirl", "biliwiki",
    )),
    ("official_product", (
        "product", "screenshot", "dashboard", "interface", "ui", "logo", "press kit",
        "app store", "steam", "official render", "packshot", "产品", "截图",
        "界面", "官网", "发布会", "型号", "旗舰店", "官方图", "软件",
    )),
    ("real_person", (
        "portrait", "founder", "ceo", "cto", "professor", "researcher", "headshot",
        "人物", "肖像", "创始人", "首席", "教授", "院士", "访谈", "演讲者",
    )),
    ("academic_science", (
        "paper", "research", "academic", "science", "diagram", "schema", "medical",
        "nasa", "noaa", "nih", "university", "论文", "学术", "科研", "科学",
        "医学", "实验", "示意图", "原理图", "机构", "大学",
    )),
    ("historical_culture", (
        "history", "museum", "archive", "artifact", "heritage", "portrait of",
        "painting", "historical", "smithsonian", "历史", "博物馆", "档案",
        "文物", "文化遗产", "艺术品", "古代", "馆藏",
    )),
    ("news_recent_event", (
        "latest", "recent", "breaking", "news", "policy", "launch", "incident",
        "2026", "2025", "最新", "近期", "新闻", "政策", "事故", "发布",
        "趋势", "监管",
    )),
    ("data_report_capture", (
        "report", "chart", "dashboard", "market size", "table", "figure", "pdf",
        "annual report", "报告", "图表", "柱状图", "折线图", "数据看板",
        "市场规模", "表格", "截图", "figure",
    )),
    ("generic_atmosphere", (
        "office", "meeting", "team", "workplace", "business", "background",
        "abstract", "city", "nature", "lifestyle", "mood", "atmosphere",
        "办公", "会议", "团队", "商务", "背景", "抽象", "城市", "自然",
        "氛围", "生活方式",
    )),
]


def _load_json(path: Path, *, required: bool = False) -> dict:
    if not path.exists():
        if required:
            raise FileNotFoundError(str(path))
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path}: {exc.msg} (line {exc.lineno}, col {exc.colno})"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a JSON object")
    return data


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _norm_text(*parts: Any) -> str:
    text = " ".join(str(part or "") for part in parts)
    return text.lower()


def _page_id(page: dict) -> str:
    value = page.get("page_id") or page.get("page_number") or page.get("slide") or ""
    if isinstance(value, int):
        return f"P{value:02d}"
    text = str(value).strip()
    if text and text.upper().startswith("P"):
        return text.upper()
    if text.isdigit():
        return f"P{int(text):02d}"
    return text


def _slug(text: str, fallback: str) -> str:
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", text).strip("_")
    text = text[:36].strip("_")
    return text or fallback


def _load_query_manifest(path: Path) -> dict:
    if not path.exists():
        return {"items": []}
    data = _load_json(path, required=True)
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError(f"{path}: 'items' must be an array")
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: items[{idx}] must be an object")
        for field in SEARCH_REQUIRED_ITEM_FIELDS:
            if field not in item:
                raise ValueError(f"{path}: items[{idx}] missing required field '{field}'")
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"{path}: items[{idx}].{field} must be a non-empty string")
    return data


def _brief_domain_packs(brief: dict) -> list[str]:
    material = brief.get("material_strategy") or {}
    packs = _as_list(material.get("preferred_source_packs"))
    if packs:
        return packs
    domain = str(material.get("domain") or "").strip().lower()
    if domain:
        for pack, tokens in SIGNALS:
            if any(token in domain for token in tokens):
                return [pack]
    return []


def _route_from_pack(pack: str) -> RouteDecision:
    base = SOURCE_PACK_DEFAULTS.get(pack) or SOURCE_PACK_DEFAULTS["open_licensed_commons"]
    return RouteDecision(
        source_pack=base.source_pack,
        preferred_sources=list(base.preferred_sources),
        preferred_providers=list(base.preferred_providers),
        disabled_providers=list(base.disabled_providers),
        allow_generic_stock=base.allow_generic_stock,
        discovery_only=base.discovery_only,
        needs_manual_review=base.needs_manual_review,
        copyright_risk=base.copyright_risk,
        selection_reason=base.selection_reason,
    )


def _infer_source_pack(item: dict, brief: dict, outline_page: Optional[dict]) -> str:
    explicit = str(item.get("source_pack") or "").strip()
    if explicit:
        return explicit

    visual = (outline_page or {}).get("visual_need") or {}
    explicit = str(visual.get("source_pack") or "").strip()
    if explicit:
        return explicit

    text = _norm_text(
        item.get("query"),
        item.get("purpose"),
        item.get("slide"),
        visual.get("image_type"),
        visual.get("image_description"),
        visual.get("reference_image_query"),
        (outline_page or {}).get("core_argument"),
        " ".join(_as_list((outline_page or {}).get("content_bullets"))),
    )

    for pack, tokens in SIGNALS:
        if any(token.lower() in text for token in tokens):
            return pack

    brief_packs = _brief_domain_packs(brief)
    if brief_packs:
        return brief_packs[0]

    return "open_licensed_commons"


def _apply_brief_overrides(decision: RouteDecision, brief: dict) -> None:
    material = brief.get("material_strategy") or {}
    risk = brief.get("copyright_and_risk") or {}

    generic_policy = str(material.get("generic_stock_policy") or "").strip()
    if generic_policy == "allowed_for_atmosphere" and decision.source_pack == "generic_atmosphere":
        decision.allow_generic_stock = True
    elif generic_policy in {"disabled_by_default", "fallback_only"} and decision.source_pack != "generic_atmosphere":
        decision.allow_generic_stock = False
        for provider in GENERIC_STOCK_PROVIDERS:
            if provider not in decision.disabled_providers:
                decision.disabled_providers.append(provider)

    if material.get("requires_official_assets") and decision.source_pack == "generic_atmosphere":
        official = _route_from_pack("official_product")
        decision.source_pack = official.source_pack
        decision.preferred_sources = official.preferred_sources
        decision.preferred_providers = official.preferred_providers
        decision.disabled_providers = official.disabled_providers
        decision.allow_generic_stock = official.allow_generic_stock
        decision.discovery_only = official.discovery_only
        decision.needs_manual_review = official.needs_manual_review
        decision.copyright_risk = official.copyright_risk
        decision.selection_reason = "Brief requires official assets; route away from generic stock."

    if material.get("requires_manual_asset_review"):
        decision.needs_manual_review = True
    risk_level = str(risk.get("copyright_risk_level") or "").strip()
    if risk_level in {"low", "medium", "high"}:
        if risk_level == "high" or decision.copyright_risk == "low":
            decision.copyright_risk = risk_level
    if str(risk.get("google_images_policy") or "").strip() == "discovery_only":
        if decision.source_pack in {
            "anime_game_ip",
            "official_product",
            "real_person",
            "news_recent_event",
            "data_report_capture",
        }:
            decision.discovery_only = True


def _merge_item_overrides(item: dict, decision: RouteDecision) -> RouteDecision:
    merged = RouteDecision(
        source_pack=decision.source_pack,
        preferred_sources=list(decision.preferred_sources),
        preferred_providers=list(decision.preferred_providers),
        disabled_providers=list(decision.disabled_providers),
        allow_generic_stock=decision.allow_generic_stock,
        discovery_only=decision.discovery_only,
        needs_manual_review=decision.needs_manual_review,
        copyright_risk=decision.copyright_risk,
        selection_reason=decision.selection_reason,
    )

    if item.get("preferred_sources"):
        merged.preferred_sources = _as_list(item.get("preferred_sources"))
    if item.get("preferred_providers"):
        merged.preferred_providers = _as_list(item.get("preferred_providers"))
    if item.get("disabled_providers"):
        merged.disabled_providers = _as_list(item.get("disabled_providers"))
    if "allow_generic_stock" in item:
        merged.allow_generic_stock = bool(item.get("allow_generic_stock"))
    if "discovery_only" in item:
        merged.discovery_only = bool(item.get("discovery_only"))
    if "needs_manual_review" in item:
        merged.needs_manual_review = bool(item.get("needs_manual_review"))
    if str(item.get("copyright_risk") or "").strip():
        merged.copyright_risk = str(item["copyright_risk"]).strip()
    if str(item.get("selection_reason") or "").strip():
        merged.selection_reason = str(item["selection_reason"]).strip()

    if not merged.allow_generic_stock:
        for provider in GENERIC_STOCK_PROVIDERS:
            if provider not in merged.disabled_providers:
                merged.disabled_providers.append(provider)

    return merged


def _find_outline_page(item: dict, pages_by_id: dict[str, dict]) -> Optional[dict]:
    for key in (item.get("slide"), item.get("page_id"), item.get("page_number")):
        text = str(key or "").strip()
        if not text:
            continue
        normalized = text.upper() if text.upper().startswith("P") else text
        if normalized in pages_by_id:
            return pages_by_id[normalized]
        if text.isdigit():
            pid = f"P{int(text):02d}"
            if pid in pages_by_id:
                return pages_by_id[pid]
    return None


def _generate_items_from_outline(outline: dict) -> list[dict]:
    pages = outline.get("pages") or []
    if not isinstance(pages, list):
        return []
    items: list[dict] = []
    used: set[str] = set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        visual = page.get("visual_need") or {}
        if not isinstance(visual, dict):
            continue
        image_type = str(visual.get("image_type") or "").strip()
        needs_reference = bool(visual.get("reference_image_required"))
        source_pack = str(visual.get("source_pack") or "").strip()
        should_generate = image_type in {"stock_search", "web_asset"} or (
            needs_reference and source_pack
        )
        if not should_generate:
            continue

        pid = _page_id(page) or f"P{len(items) + 1:02d}"
        query = (
            str(visual.get("reference_image_query") or "").strip()
            or str(visual.get("image_description") or "").strip()
            or str(page.get("core_argument") or "").strip()
        )
        if not query:
            continue
        stem = _slug(query, f"{pid.lower()}_image")
        filename = f"{pid.lower()}_{stem}.jpg"
        while filename in used:
            filename = f"{pid.lower()}_{stem}_{len(used) + 1}.jpg"
        used.add(filename)

        width = 0
        height = 0
        slot = visual.get("image_slot_size") or {}
        if isinstance(slot, dict):
            width = int(slot.get("width") or 0)
            height = int(slot.get("height") or 0)

        item = {
            "filename": filename,
            "query": query,
            "slide": pid,
            "purpose": f"{image_type}:{page.get('core_argument', '')}".strip(":"),
            "orientation": "any",
            "status": DEFAULT_QUERY_STATUS,
        }
        if width:
            item["min_width"] = width
        if height:
            item["min_height"] = height
        for field in (
            "source_pack",
            "preferred_sources",
            "disabled_providers",
            "allow_generic_stock",
            "discovery_only",
            "needs_manual_review",
            "copyright_risk",
            "selection_reason",
        ):
            if field in visual:
                item[field] = visual[field]
        items.append(item)
    return items


def route_item(item: dict, brief: dict, outline_page: Optional[dict]) -> RouteDecision:
    pack = _infer_source_pack(item, brief, outline_page)
    decision = _route_from_pack(pack)
    _apply_brief_overrides(decision, brief)

    visual = (outline_page or {}).get("visual_need") or {}
    for field in (
        "preferred_sources",
        "disabled_providers",
        "allow_generic_stock",
        "discovery_only",
        "needs_manual_review",
        "copyright_risk",
        "selection_reason",
    ):
        if field in visual and field not in item:
            item[field] = visual[field]

    return _merge_item_overrides(item, decision)


def _apply_route(item: dict, decision: RouteDecision) -> dict:
    updated = dict(item)
    updated["source_pack"] = decision.source_pack
    updated["preferred_sources"] = decision.preferred_sources
    updated["preferred_providers"] = decision.preferred_providers
    updated["disabled_providers"] = decision.disabled_providers
    updated["allow_generic_stock"] = decision.allow_generic_stock
    updated["discovery_only"] = decision.discovery_only
    updated["needs_manual_review"] = decision.needs_manual_review
    updated["copyright_risk"] = decision.copyright_risk
    updated["selection_reason"] = decision.selection_reason
    return updated


def _print_text_report(project: Path, output_path: Path, routed: list[dict]) -> None:
    print(f"Image source routing: {project}")
    print(f"Manifest: {output_path}")
    print()
    if not routed:
        print("No web image query rows found or generated.")
        return
    for idx, item in enumerate(routed, start=1):
        print(
            f"{idx:02d}. {item.get('filename', '')} "
            f"[{item.get('slide', '')}] {item.get('source_pack', '')}"
        )
        print(f"    query: {item.get('query', '')}")
        print(f"    preferred: {', '.join(_as_list(item.get('preferred_sources')))}")
        disabled = ", ".join(_as_list(item.get("disabled_providers"))) or "-"
        print(
            f"    disabled: {disabled}; "
            f"generic_stock={item.get('allow_generic_stock')}; "
            f"discovery_only={item.get('discovery_only')}; "
            f"manual_review={item.get('needs_manual_review')}; "
            f"risk={item.get('copyright_risk')}"
        )
        print(f"    reason: {item.get('selection_reason', '')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Annotate image_queries.json with domain-aware source routing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="PPT project directory.")
    parser.add_argument(
        "--queries",
        default=None,
        help="Input query manifest. Defaults to <project>/images/image_queries.json.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output query manifest. Defaults to the input path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print routing decisions without writing image_queries.json.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the enhanced manifest JSON to stdout.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project = Path(args.project_path)
    if not project.exists() or not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 1

    brief_path = project / "ppt_brief.json"
    outline_path = project / "detailed_outline.json"
    query_path = Path(args.queries) if args.queries else project / "images" / "image_queries.json"
    output_path = Path(args.output) if args.output else query_path

    try:
        brief = _load_json(brief_path)
        outline = _load_json(outline_path)
        manifest = _load_query_manifest(query_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    pages = outline.get("pages") or []
    pages_by_id = {
        _page_id(page): page
        for page in pages
        if isinstance(page, dict) and _page_id(page)
    }

    items = list(manifest.get("items") or [])
    if not items:
        generated = _generate_items_from_outline(outline)
        if generated:
            items = generated
            manifest["items"] = items
            manifest.setdefault("generated_by", "image_source_router.py")

    routed_items: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        outline_page = _find_outline_page(item, pages_by_id)
        decision = route_item(dict(item), brief, outline_page)
        routed_items.append(_apply_route(item, decision))

    enhanced = dict(manifest)
    enhanced["items"] = routed_items
    enhanced["routing_version"] = "source-pack-v1"
    enhanced["routing_inputs"] = {
        "ppt_brief": str(brief_path) if brief_path.exists() else "",
        "detailed_outline": str(outline_path) if outline_path.exists() else "",
    }

    if args.json:
        print(json.dumps(enhanced, indent=2, ensure_ascii=False))
    else:
        _print_text_report(project, output_path, routed_items)

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(output_path, enhanced)
        print(f"\n[OK] wrote enhanced manifest: {output_path}", file=sys.stderr)
    else:
        print("\n[dry-run] no files written", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
