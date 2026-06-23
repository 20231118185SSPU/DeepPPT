#!/usr/bin/env python3
"""Memory orchestrator for PPT-master2's Select-Extract-Reconcile lifecycle.

Implements the three-phase memory lifecycle adapted from MemSlides to the
Eight Confirmations workflow:

1. **Select** -- map a PPT generation mode to the correct intent bucket.
2. **Extract** -- pull preference signals from ``confirm_ui/result.json``.
3. **Reconcile** -- merge historical profile preferences with the current
   request, where explicit current choices always win.

The high-level entry point is :func:`build_injection`, which SKILL.md calls
at Step 4 to inject a formatted preference block into the Strategist prompt.

Usage::

    from skills.ppt_master.memory.orchestrator import build_injection
    from pathlib import Path

    prompt = build_injection(Path("projects/my_deck"), mode="business")
    if prompt:
        # prepend to Strategist system prompt
        ...
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .profile_schema import (
    ContentPreference,
    LayoutPreference,
    MemoryStore,
    MODE_TO_INTENT,
    ThemePreference,
    UserProfile,
    VisualPreference,
)
from .profile_store import ProfileStore

# ---------------------------------------------------------------------------
# 1. load_memory
# ---------------------------------------------------------------------------


def load_memory(
    project_path: Path,
    intent: Optional[str] = None,
) -> Optional[MemoryStore]:
    """Load the memory store from *project_path*.

    Args:
        project_path: Root of the PPT project directory.
        intent:       If provided, the returned store will contain only
                      the single matching intent bucket (still wrapped in a
                      ``MemoryStore`` so callers can use the same API).
                      If ``None``, the full store is returned.

    Returns:
        A :class:`MemoryStore` instance, or ``None`` if no memory file
        exists on disk.
    """
    store = ProfileStore(project_path)
    if not store.exists():
        return None

    memory = store.load()

    # Empty store (file existed but had no intents)
    if not memory.intents:
        return None

    if intent is not None:
        bucket = memory.intents.get(intent)
        if bucket is None:
            return None
        narrowed = MemoryStore(
            user_id=memory.user_id,
            version=memory.version,
            intents={intent: bucket},
        )
        return narrowed

    return memory


# ---------------------------------------------------------------------------
# 2. select_intent
# ---------------------------------------------------------------------------


def select_intent(mode: str, user_id: str = "default") -> str:
    """Convert a PPT-master2 mode string to an intent bucket key.

    The mapping comes from :data:`MODE_TO_INTENT` in ``profile_schema``.
    Modes not present in the table (e.g. ``"instructional"``) fall back to
    ``"general"``.

    Args:
        mode:    The ``mode`` value from the Eight Confirmations result.
        user_id: Reserved for future per-user mapping (unused today).

    Returns:
        An intent key such as ``"business"``, ``"academic"``, or ``"general"``.
    """
    normalised = mode.strip().lower() if mode else ""
    return MODE_TO_INTENT.get(normalised, "general")


# ---------------------------------------------------------------------------
# 3. extract_preferences_from_confirmations
# ---------------------------------------------------------------------------


def extract_preferences_from_confirmations(result_path: Path) -> Dict[str, Dict[str, Any]]:
    """Read ``confirm_ui/result.json`` and extract preference signals.

    The Eight Confirmations UI writes a JSON file whose fields map to the
    profile schema categories as follows:

    +-------------------------+----------------------------------------------+
    | result.json field(s)    | Preference category / keys                   |
    +-------------------------+----------------------------------------------+
    | mode, visual_style,     | ThemePreference: visual_style, mood,         |
    | image_strategy.mood     |     background_style                         |
    +-------------------------+----------------------------------------------+
    | color, image_strategy   | ThemePreference: primary_colors, accent      |
    |                         |     colors, color_name, palette              |
    +-------------------------+----------------------------------------------+
    | typography              | ContentPreference: font_heading, font_body,  |
    |                         |     text_density (from body_size)            |
    +-------------------------+----------------------------------------------+
    | canvas                  | LayoutPreference: canvas_format              |
    +-------------------------+----------------------------------------------+
    | image_usage, icons,     | VisualPreference: image_style, icon_style,   |
    | image_strategy          |     image_rendering, image_color             |
    +-------------------------+----------------------------------------------+

    Args:
        result_path: Absolute path to ``confirm_ui/result.json``.

    Returns:
        A dict keyed by preference category name (``"theme"``, ``"content"``,
        ``"layout"``, ``"visual"``).  Each value is a dict with ``"values"``
        and ``"confidence"`` sub-keys ready to feed into a ``Preference``.
        Returns an empty dict when the file is missing or unreadable.
    """
    if not result_path.exists():
        return {}

    try:
        data: Dict[str, Any] = json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    # -- Theme ---------------------------------------------------------------
    theme_values: Dict[str, Any] = {}
    mode = data.get("mode", "")
    visual_style = data.get("visual_style", "")
    if visual_style:
        theme_values["visual_style"] = visual_style
    if mode:
        theme_values["mood"] = mode

    color_obj = data.get("color", {})
    if isinstance(color_obj, dict):
        color_name = color_obj.get("name", "")
        if color_name:
            theme_values["color_name"] = color_name
        palette = color_obj.get("palette", {})
        if isinstance(palette, dict):
            if palette.get("primary"):
                theme_values["primary_colors"] = [palette["primary"]]
            if palette.get("accent"):
                theme_values["accent_colors"] = [palette["accent"]]
            if palette.get("background"):
                theme_values["background_style"] = palette["background"]
        custom = color_obj.get("custom", "")
        if custom and not palette:
            theme_values["color_custom"] = custom

    image_strategy = data.get("image_strategy", {})
    if isinstance(image_strategy, dict):
        strat_mood = image_strategy.get("mood", "")
        if strat_mood and "mood" not in theme_values:
            theme_values["mood"] = strat_mood
        strat_color = image_strategy.get("color", "")
        if strat_color:
            theme_values["image_color_scheme"] = strat_color

    # -- Content -------------------------------------------------------------
    content_values: Dict[str, Any] = {}
    typography = data.get("typography", {})
    if isinstance(typography, dict):
        typ_name = typography.get("name", "")
        if typ_name:
            content_values["typography_name"] = typ_name
        heading = typography.get("heading", {})
        if isinstance(heading, dict):
            h_latin = heading.get("latin", "")
            if h_latin:
                content_values["font_heading_latin"] = h_latin
            h_cjk = heading.get("cjk", "")
            if h_cjk:
                content_values["font_heading_cjk"] = h_cjk
        body = typography.get("body", {})
        if isinstance(body, dict):
            b_latin = body.get("latin", "")
            if b_latin:
                content_values["font_body_latin"] = b_latin
            b_cjk = body.get("cjk", "")
            if b_cjk:
                content_values["font_body_cjk"] = b_cjk
        body_size = typography.get("body_size", "")
        if body_size:
            try:
                size_int = int(body_size)
                if size_int <= 16:
                    content_values["text_density"] = "dense"
                elif size_int <= 20:
                    content_values["text_density"] = "moderate"
                else:
                    content_values["text_density"] = "sparse"
            except (ValueError, TypeError):
                pass

    # -- Layout --------------------------------------------------------------
    layout_values: Dict[str, Any] = {}
    canvas = data.get("canvas", "")
    if canvas:
        layout_values["canvas_format"] = canvas

    # -- Visual --------------------------------------------------------------
    visual_values: Dict[str, Any] = {}
    image_usage = data.get("image_usage", "")
    if image_usage:
        visual_values["image_usage"] = image_usage
    icons = data.get("icons", "")
    if icons:
        visual_values["icon_style"] = icons
    if isinstance(image_strategy, dict):
        rendering = image_strategy.get("rendering", "")
        if rendering:
            visual_values["image_rendering"] = rendering
        strat_palette = image_strategy.get("palette", "")
        if strat_palette:
            visual_values["image_palette"] = strat_palette
        strat_visual = image_strategy.get("visual", "")
        if strat_visual:
            visual_values["image_visual_desc"] = strat_visual

    # -- Assemble result with confidence -------------------------------------
    # Confidence is set based on whether the field was explicitly chosen
    # (non-empty in result.json).  Explicitly confirmed fields get 0.9;
    # defaults / empty get nothing.
    result: Dict[str, Dict[str, Any]] = {}
    if theme_values:
        result["theme"] = {"values": theme_values, "confidence": 0.9}
    if content_values:
        result["content"] = {"values": content_values, "confidence": 0.9}
    if layout_values:
        result["layout"] = {"values": layout_values, "confidence": 0.9}
    if visual_values:
        result["visual"] = {"values": visual_values, "confidence": 0.9}

    return result


# ---------------------------------------------------------------------------
# 4. reconcile
# ---------------------------------------------------------------------------


def reconcile(
    profile_prefs: Dict[str, Dict[str, Any]],
    current_prefs: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Merge *profile_prefs* (from memory) with *current_prefs* (from this job).

    Conflict resolution rules:

    * **Overlapping keys** -- ``current_prefs`` wins (explicit request
      overrides historical inference).
    * **Non-overlapping keys** -- both are kept (union).
    * **Confidence** -- the higher of the two is retained.
    * **Sources** -- deduplicated and concatenated.

    Args:
        profile_prefs: Historical preferences from the user profile.
        current_prefs: Extracted preferences from the current confirmations.

    Returns:
        A merged dict in the same shape as the inputs (category -> values +
        confidence).
    """
    merged: Dict[str, Dict[str, Any]] = {}

    all_categories = set(profile_prefs) | set(current_prefs)

    for cat in all_categories:
        prof = profile_prefs.get(cat, {})
        curr = current_prefs.get(cat, {})

        prof_values = prof.get("values", {})
        curr_values = curr.get("values", {})
        prof_conf = prof.get("confidence", 0.0)
        curr_conf = curr.get("confidence", 0.0)

        # Start with profile values, overlay current values
        combined_values = dict(prof_values)
        combined_values.update(curr_values)  # current wins on conflict

        combined_conf = max(prof_conf, curr_conf)

        merged[cat] = {
            "values": combined_values,
            "confidence": combined_conf,
        }

    return merged


# ---------------------------------------------------------------------------
# 5. format_memory_prompt
# ---------------------------------------------------------------------------

# Section rendering order and labels
_SECTIONS: List[tuple[str, str]] = [
    ("theme", "主题偏好"),
    ("content", "内容偏好"),
    ("layout", "布局偏好"),
    ("visual", "视觉偏好"),
]

# Keys within each section, with display labels (order matters for output)
_SECTION_FIELDS: Dict[str, List[tuple[str, str]]] = {
    "theme": [
        ("primary_colors", "色彩"),
        ("accent_colors", "强调色"),
        ("visual_style", "视觉风格"),
        ("background_style", "背景"),
        ("mood", "氛围"),
        ("color_name", "配色方案"),
    ],
    "content": [
        ("text_density", "信息密度"),
        ("font_heading_latin", "标题字体（拉丁）"),
        ("font_heading_cjk", "标题字体（中文）"),
        ("font_body_latin", "正文字体（拉丁）"),
        ("font_body_cjk", "正文字体（中文）"),
        ("typography_name", "字体方案"),
        ("language_style", "语言风格"),
        ("title_length", "标题长度"),
    ],
    "layout": [
        ("canvas_format", "画布格式"),
        ("alignment_style", "对齐方式"),
        ("page_structure", "页面结构"),
        ("spacing", "间距"),
    ],
    "visual": [
        ("image_usage", "图片使用"),
        ("image_style", "图片风格"),
        ("image_rendering", "图片渲染"),
        ("image_palette", "图片配色"),
        ("icon_style", "图标风格"),
        ("chart_type_priority", "图表类型"),
        ("animation", "动画"),
    ],
}


def _format_value(value: Any) -> str:
    """Render a preference value as a readable string."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def format_memory_prompt(profile: UserProfile, intent: str) -> Optional[str]:
    """Format a :class:`UserProfile` into a prompt injection block.

    The output is designed to be prepended to the Strategist system prompt
    at Step 4 (Eight Confirmations).  Missing or empty sections are skipped.

    Args:
        profile: The user's accumulated preference profile.
        intent:  The current intent bucket name (for display).

    Returns:
        A Markdown-formatted string, or ``None`` if the profile has no
        usable preferences at all.
    """
    # Collect preference data from each category
    category_data: Dict[str, Dict[str, Any]] = {}
    attr_map = {
        "theme": profile.theme,
        "content": profile.content,
        "layout": profile.layout,
        "visual": profile.visual,
    }
    for cat, pref in attr_map.items():
        if pref.values:
            category_data[cat] = pref.values

    if not category_data:
        return None

    lines: List[str] = [
        "## 用户画像偏好（自动加载，用户显式指令优先级更高）",
        "",
        f"意图类型：{intent}",
        "",
    ]

    for cat_key, section_title in _SECTIONS:
        values = category_data.get(cat_key)
        if not values:
            continue

        fields = _SECTION_FIELDS.get(cat_key, [])
        field_lines: List[str] = []
        for val_key, label in fields:
            if val_key in values and values[val_key]:
                field_lines.append(
                    f"- {label}：{_format_value(values[val_key])}"
                )

        if field_lines:
            lines.append(f"### {section_title}")
            lines.extend(field_lines)
            lines.append("")

    # Only return if we produced at least one section
    if len(lines) <= 4:
        return None

    lines.append(
        "以上偏好基于历史生成记录自动推荐，用户显式指令始终优先。"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. build_injection  (high-level entry point for SKILL.md)
# ---------------------------------------------------------------------------


def build_injection(project_path: Path, mode: str) -> Optional[str]:
    """Load memory, select intent, and return a formatted prompt block.

    This is the single function that SKILL.md calls at Step 4.  It combines
    load, select, and format into one call.

    Args:
        project_path: Root of the PPT project directory.
        mode:         The ``mode`` value from the Eight Confirmations.

    Returns:
        A Markdown string to inject into the Strategist prompt, or ``None``
        when no memory is available for the derived intent.
    """
    intent = select_intent(mode)
    store = load_memory(project_path, intent=intent)
    if store is None:
        return None

    bucket = store.intents.get(intent)
    if bucket is None:
        return None

    return format_memory_prompt(bucket.profile, intent)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    # -- select_intent tests -------------------------------------------------
    assert select_intent("business") == "business"
    assert select_intent("consulting") == "business"
    assert select_intent("academic") == "academic"
    assert select_intent("narrative") == "general"
    assert select_intent("unknown_mode") == "general"
    assert select_intent("") == "general"
    print("select_intent: OK")

    # -- extract_preferences_from_confirmations tests ------------------------
    with tempfile.TemporaryDirectory() as tmp:
        # No file -> empty dict
        missing = Path(tmp) / "no_such.json"
        assert extract_preferences_from_confirmations(missing) == {}

        # Full result.json
        result_path = Path(tmp) / "result.json"
        result_path.write_text(json.dumps({
            "mode": "business",
            "visual_style": "dark-tech",
            "canvas": "ppt169",
            "color": {
                "name": "Cyber Glow",
                "palette": {
                    "primary": "#00D4FF",
                    "accent": "#FF6B6B",
                    "background": "#0A0E1A",
                },
            },
            "typography": {
                "name": "Inter + YaHei",
                "heading": {"latin": "Inter", "cjk": "Microsoft YaHei"},
                "body": {"latin": "Inter", "cjk": "Microsoft YaHei"},
                "body_size": "18",
            },
            "image_usage": "ai",
            "icons": "tabler-outline",
            "image_strategy": {
                "rendering": "flat",
                "palette": "cool-tech",
                "visual": "flat vectors",
                "color": "dark 70% + blue 20%",
                "mood": "modern, professional",
            },
        }, ensure_ascii=False), encoding="utf-8")

        prefs = extract_preferences_from_confirmations(result_path)
        assert "theme" in prefs
        assert prefs["theme"]["values"]["visual_style"] == "dark-tech"
        assert prefs["theme"]["values"]["primary_colors"] == ["#00D4FF"]
        assert prefs["content"]["values"]["text_density"] == "moderate"
        assert prefs["layout"]["values"]["canvas_format"] == "ppt169"
        assert prefs["visual"]["values"]["icon_style"] == "tabler-outline"
        print("extract_preferences_from_confirmations: OK")

    # -- reconcile tests -----------------------------------------------------
    profile = {
        "theme": {
            "values": {"primary_colors": ["#003366"], "mood": "professional"},
            "confidence": 0.7,
        },
    }
    current = {
        "theme": {
            "values": {"primary_colors": ["#00D4FF"]},
            "confidence": 0.9,
        },
        "layout": {
            "values": {"canvas_format": "ppt169"},
            "confidence": 0.9,
        },
    }
    merged = reconcile(profile, current)
    # current wins on primary_colors
    assert merged["theme"]["values"]["primary_colors"] == ["#00D4FF"]
    # profile-only key is preserved
    assert merged["theme"]["values"]["mood"] == "professional"
    # current-only category is added
    assert merged["layout"]["values"]["canvas_format"] == "ppt169"
    assert merged["theme"]["confidence"] == 0.9
    print("reconcile: OK")

    # -- format_memory_prompt tests ------------------------------------------
    profile_obj = UserProfile(user_id="test")
    profile_obj.theme.values = {
        "primary_colors": ["#003366"],
        "accent_colors": ["#FF6600"],
        "visual_style": "modern",
        "background_style": "#FFFFFF",
    }
    profile_obj.content.values = {
        "text_density": "moderate",
        "font_heading_latin": "Inter",
        "font_body_latin": "Inter",
    }
    profile_obj.layout.values = {"canvas_format": "ppt169"}
    profile_obj.visual.values = {"image_style": "mixed", "icon_style": "tabler-outline"}

    result = format_memory_prompt(profile_obj, "business")
    assert result is not None
    assert "主题偏好" in result
    assert "内容偏好" in result
    assert "布局偏好" in result
    assert "视觉偏好" in result
    assert "用户显式指令始终优先" in result
    assert "#003366" in result
    print("format_memory_prompt: OK")

    # Empty profile returns None
    empty = UserProfile(user_id="empty")
    assert format_memory_prompt(empty, "general") is None
    print("format_memory_prompt (empty): OK")

    # -- build_injection with no memory returns None -------------------------
    with tempfile.TemporaryDirectory() as tmp:
        result = build_injection(Path(tmp), "business")
        assert result is None
    print("build_injection (no memory): OK")

    print("\norchestrator.py: all smoke tests passed")
