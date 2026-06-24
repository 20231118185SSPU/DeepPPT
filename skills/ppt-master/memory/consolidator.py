#!/usr/bin/env python3
"""Consolidate PPT generation results into long-term user memory.

At the end of a PPT generation job, compares what the user actually chose
(in Eight Confirmations) with their existing profile and updates the profile
with stability-weighted merging.  Prevents transient / one-off preferences
from polluting long-term memory.

Usage::

    from pathlib import Path
    from skills.ppt_master.memory.consolidator import consolidate, generate_report

    # Basic — infers intent from confirm_ui/result.json
    report = consolidate(Path("projects/my_deck"))
    print(report["summary"])

    # With explicit intent override
    report = consolidate(Path("projects/my_deck"), intent="academic")

    # Standalone report (no side-effects)
    from skills.ppt_master.memory.profile_store import ProfileStore
    store = ProfileStore(Path("projects/my_deck"))
    old = store.get_profile("business")
    new = store.get_profile("business")   # after consolidate()
    # generate_report(old, new)
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .profile_schema import (
    MODE_TO_INTENT,
    ContentPreference,
    LayoutPreference,
    MemoryStore,
    Preference,
    ThemePreference,
    UserProfile,
    VisualPreference,
)
from .profile_store import ProfileStore

# ---------------------------------------------------------------------------
# Signal extraction mapping
# ---------------------------------------------------------------------------

# Maps result.json keys to (preference_attr, preference_values_key) pairs.
# A single confirmation key may fan out to multiple preference entries.
_SIGNAL_MAP: Dict[str, List[tuple]] = {
    "d_style": [
        ("content", "language_style"),       # d_style.mode
        ("theme", "visual_style"),           # d_style.visual_style
    ],
    "e_colors": [
        ("theme", "primary_colors"),         # hex list
    ],
    "f_icons": [
        ("visual", "icon_style"),
    ],
    "g_typography": [
        ("content", "font_family"),
        ("theme", "font_family"),
    ],
    "h_images": [
        ("visual", "image_style"),           # h_images.value
        ("visual", "image_rendering"),       # h_images.rendering
        ("theme", "color_palette"),          # h_images.palette
    ],
    "a_canvas": [
        ("layout", "page_structure"),        # 16:9 -> wide, 4:3 -> standard
    ],
}

# Mapping from raw canvas value to layout terminology
_CANVAS_MAP: Dict[str, str] = {
    "ppt169": "wide",
    "16:9": "wide",
    "ppt43": "standard",
    "4:3": "standard",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def consolidate(
    project_path: Path,
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    """Consolidate Eight Confirmations results into the user's long-term profile.

    Steps:
        a. Read ``confirm_ui/result.json`` to get the user's actual choices.
        b. Determine intent (from ``mode`` in result.json, or *intent* override).
        c. Load existing profile via :class:`ProfileStore`.
        d. Extract preference signals from confirmations.
        e. Compare each signal with existing profile.
        f. Update profile with stability-weighted merging.
        g. Save updated profile.
        h. Return consolidation report.

    Args:
        project_path: Root of the PPT project.
        intent:       Explicit intent override.  When ``None`` the intent is
                      inferred from ``result.json["d_style"]["mode"]``.

    Returns:
        A consolidation report dict with keys ``intent``, ``job_count``,
        ``updated``, ``unchanged``, ``new_intents``, and ``summary``.

    Raises:
        FileNotFoundError: If ``confirm_ui/result.json`` does not exist.
    """
    project_path = Path(project_path)
    result_path = project_path / "confirm_ui" / "result.json"

    # -- step a: read confirmations ------------------------------------------
    if not result_path.exists():
        raise FileNotFoundError(
            f"Confirm UI result not found: {result_path}. "
            "Run Eight Confirmations before consolidation."
        )
    result = json.loads(result_path.read_text(encoding="utf-8"))

    # -- step b: determine intent --------------------------------------------
    if intent is None:
        mode = ""
        d_style = result.get("d_style", {})
        if isinstance(d_style, dict):
            mode = d_style.get("mode", "")
        intent = MODE_TO_INTENT.get(mode, "general")

    # -- step c: load existing profile ---------------------------------------
    store = ProfileStore(project_path)
    existing_profile = store.get_profile(intent)

    # Deep-copy the "before" snapshot for the report (first-time users have
    # an empty profile, so synthesise one).
    if existing_profile is not None:
        old_snapshot = copy.deepcopy(existing_profile)
    else:
        old_snapshot = UserProfile(user_id="consolidator-placeholder")

    # -- step d: extract signals ---------------------------------------------
    signals = _extract_signals(result)

    # -- step e + f: compare and update with stability weighting -------------
    new_profile = copy.deepcopy(old_snapshot)
    now = datetime.now(timezone.utc).isoformat()

    # Determine how many jobs the bucket has seen so far (for weight calc).
    memory: MemoryStore = store.load()
    bucket = memory.intents.get(intent)
    job_count = bucket.job_count if bucket is not None else 0

    for category, field_signals in signals.items():
        pref: Preference = getattr(new_profile, category)
        # Snapshot the pre-consolidation confidence so that sequential field
        # updates within the same category do not artificially inflate or
        # deflate each other's weight calculation.
        original_conf = pref.confidence
        for field_name, field_value in field_signals.items():
            old_val = pref.values.get(field_name)
            is_agreement = old_val is not None and old_val == field_value
            is_new = old_val is None

            new_conf = _stability_weight(
                original_conf,
                new_signal_agrees=is_agreement,
                new_signal_exists=not is_new or True,
                is_brand_new=is_new and original_conf == 0.0,
                job_count=job_count,
            )

            # Apply update
            pref.values[field_name] = field_value
            pref.confidence = new_conf  # last field's confidence is kept
            if project_path.name not in pref.sources:
                pref.sources.append(project_path.name)
            pref.updated_at = now

        setattr(new_profile, category, pref)

    # -- step g: save via ProfileStore ---------------------------------------
    store.update_profile(intent, new_profile, source=project_path.name)

    # -- step h: build report ------------------------------------------------
    report = generate_report(old_snapshot, new_profile)
    report["intent"] = intent
    report["job_count"] = job_count + 1
    changed = len(report["updated"])
    report["summary"] = (
        f"Consolidated {changed} preference(s) into '{intent}' "
        f"bucket (job #{report['job_count']})."
    )
    return report


def _extract_signals(result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Parse Eight Confirmations ``result.json`` into preference signals.

    Args:
        result: Raw dict read from ``confirm_ui/result.json``.

    Returns:
        Nested dict keyed by preference category (``theme``, ``content``,
        ``layout``, ``visual``) whose values map field names to concrete
        preference values.  For example::

            {
                "theme": {"primary_colors": ["#005587", "#F5A623"], "visual_style": "corporate-clean"},
                "content": {"language_style": "consulting", "font_family": "Microsoft YaHei"},
                "layout": {"page_structure": "wide"},
                "visual": {"icon_style": "tabler-filled", "image_style": "ai"},
            }
    """
    out: Dict[str, Dict[str, Any]] = {
        "theme": {},
        "content": {},
        "layout": {},
        "visual": {},
    }

    for conf_key, mappings in _SIGNAL_MAP.items():
        entry = result.get(conf_key)
        if entry is None:
            continue

        # Normalise: some entries are bare values, others are dicts.
        raw_val: Any = entry.get("value", entry) if isinstance(entry, dict) else entry

        for category, field_name in mappings:
            value: Any = raw_val  # default

            # -- per-key special extraction ---------------------------------
            if conf_key == "d_style" and isinstance(entry, dict):
                if field_name == "language_style":
                    value = entry.get("mode", raw_val)
                elif field_name == "visual_style":
                    value = entry.get("visual_style", raw_val)

            elif conf_key == "e_colors" and isinstance(raw_val, str):
                # Split comma-separated hex colours
                colors = [c.strip() for c in raw_val.split(",") if c.strip()]
                if len(colors) > 2:
                    value = colors  # primary set
                elif len(colors) == 2:
                    value = colors

            elif conf_key == "h_images" and isinstance(entry, dict):
                if field_name == "image_style":
                    value = entry.get("value", raw_val)
                elif field_name == "image_rendering":
                    value = entry.get("rendering", "")
                elif field_name == "color_palette":
                    value = entry.get("palette", "")
                # Skip empty values
                if not value:
                    continue

            elif conf_key == "a_canvas":
                value = _CANVAS_MAP.get(str(raw_val), str(raw_val))

            # Skip empty / None values
            if value is None or value == "":
                continue

            out[category][field_name] = value

    return out


# ---------------------------------------------------------------------------
# Stability weighting
# ---------------------------------------------------------------------------

def _stability_weight(
    existing_confidence: float,
    new_signal_agrees: bool,
    new_signal_exists: bool,
    is_brand_new: bool,
    job_count: int,
) -> float:
    """Calculate updated confidence after observing a new signal.

    The formula biases toward stability: agreeing signals gently boost
    confidence (diminishing returns), while disagreeing signals cause a
    moderate decrease that protects well-established preferences from
    being wiped by a single outlier job.

    Args:
        existing_confidence: Current confidence of the preference (0.0-1.0).
        new_signal_agrees:   ``True`` when the new observation matches what
                             the profile already stores.
        new_signal_exists:   ``True`` when there *is* a new signal (always
                             ``True`` in normal use; parameter exists for
                             symmetry / future use).
        is_brand_new:        ``True`` when the preference has never been seen
                             before (confidence is 0.0).
        job_count:           Number of completed jobs for this intent bucket.

    Returns:
        Updated confidence float, always in ``[0.1, 1.0]``.
    """
    if is_brand_new:
        return 0.5

    if new_signal_agrees:
        # Agree: gentle boost with diminishing returns
        return min(1.0, existing_confidence + 0.1 * (1.0 - existing_confidence))
    else:
        # Disagree: moderate decrease, floor at 0.1
        return max(0.1, existing_confidence * 0.9)


def _update_preference(
    existing: Preference,
    signal_values: Dict[str, Any],
    source: str,
    confidence: float,
) -> Preference:
    """Update a single :class:`Preference` with new signal data.

    New values override existing values for the same keys.  Confidence is
    set to *confidence* (caller is expected to pass in the output of
    :func:`_stability_weight`).  Source is appended if not already present.

    Args:
        existing:      The preference to update (mutated in place *and* returned).
        signal_values: New key-value pairs to merge in.
        source:        Attribution tag for this observation.
        confidence:    New confidence value.

    Returns:
        The updated preference (same object as *existing*).
    """
    existing.values.update(signal_values)
    existing.confidence = confidence
    if source not in existing.sources:
        existing.sources.append(source)
    existing.updated_at = datetime.now(timezone.utc).isoformat()
    return existing


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    old_profile: UserProfile,
    new_profile: UserProfile,
) -> Dict[str, Any]:
    """Compare old and new profiles, returning a structured change report.

    Args:
        old_profile: Snapshot of the profile *before* consolidation.
        new_profile: Profile *after* consolidation.

    Returns:
        Dict with keys:

        - ``updated``   -- list of changed preference entries, each a dict
          with ``category``, ``field``, ``old``, ``new``, ``confidence``.
        - ``unchanged`` -- list of field descriptors that did not change.
        - ``new_intents`` -- list of category.field strings that were freshly
          added (did not exist in the old profile).
    """
    updated: List[Dict[str, Any]] = []
    unchanged: List[str] = []
    new_fields: List[str] = []

    categories = ("theme", "content", "layout", "visual", "general")

    for cat in categories:
        old_pref: Preference = getattr(old_profile, cat)
        new_pref: Preference = getattr(new_profile, cat)

        # All keys present in either old or new
        all_keys = set(old_pref.values.keys()) | set(new_pref.values.keys())

        for key in sorted(all_keys):
            old_val = old_pref.values.get(key)
            new_val = new_pref.values.get(key)

            if old_val is None and new_val is not None:
                new_fields.append(f"{cat}.{key}")
                updated.append({
                    "category": cat,
                    "field": key,
                    "old": None,
                    "new": new_val,
                    "confidence": new_pref.confidence,
                })
            elif old_val != new_val:
                updated.append({
                    "category": cat,
                    "field": key,
                    "old": old_val,
                    "new": new_val,
                    "confidence": new_pref.confidence,
                })
            else:
                unchanged.append(f"{cat}.{key}")

    return {
        "updated": updated,
        "unchanged": unchanged,
        "new_intents": new_fields,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import tempfile

    # -- offline smoke test --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "test_project"
        confirm_dir = proj / "confirm_ui"
        confirm_dir.mkdir(parents=True)

        # Simulate a result.json
        result_data = {
            "a_canvas": {"value": "ppt169"},
            "b_pages": {"value": 12},
            "c_audience": {"value": "business professionals"},
            "d_style": {"mode": "consulting", "visual_style": "corporate-clean"},
            "e_colors": {"value": "#005587, #F5A623, #333333"},
            "f_icons": {"value": "tabler-filled"},
            "g_typography": {"value": "Microsoft YaHei"},
            "h_images": {"value": "ai", "rendering": "watercolor", "palette": "warm"},
        }
        (confirm_dir / "result.json").write_text(
            json.dumps(result_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # First consolidation (empty memory)
        report1 = consolidate(proj)
        assert report1["intent"] == "business"  # consulting -> business
        assert report1["job_count"] == 1
        assert len(report1["updated"]) > 0
        print(f"Pass 1: {report1['summary']}")

        # Second consolidation (same choices — should boost confidence)
        report2 = consolidate(proj)
        assert report2["job_count"] == 2
        print(f"Pass 2: {report2['summary']}")

        # Verify profile persisted
        ps = ProfileStore(proj)
        bp = ps.get_profile("business")
        assert bp is not None
        assert bp.theme.values.get("visual_style") == "corporate-clean"
        assert bp.theme.confidence > 0.5
        assert bp.layout.values.get("page_structure") == "wide"
        assert bp.visual.values.get("icon_style") == "tabler-filled"
        assert bp.visual.values.get("image_rendering") == "watercolor"
        assert bp.theme.values.get("color_palette") == "warm"
        print(f"  theme confidence: {bp.theme.confidence}")
        print(f"  theme values: {bp.theme.values}")
        print(f"  content values: {bp.content.values}")
        print(f"  layout values: {bp.layout.values}")
        print(f"  visual values: {bp.visual.values}")

    # -- _stability_weight unit checks ---------------------------------------
    # Use approximate comparison for floats to avoid IEEE-754 rounding.
    def _approx(a: float, b: float, tol: float = 1e-9) -> bool:
        return abs(a - b) < tol

    assert _approx(_stability_weight(0.0, False, True, True, 0), 0.5)
    assert _approx(_stability_weight(0.8, True, True, False, 3), 0.82)
    assert _approx(_stability_weight(0.8, False, True, False, 3), 0.72)
    assert _approx(_stability_weight(0.1, False, True, False, 1), 0.1)   # floor
    assert _approx(_stability_weight(1.0, True, True, False, 5), 1.0)   # cap

    # -- CLI mode ------------------------------------------------------------
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        intent_arg = sys.argv[2] if len(sys.argv) > 2 else None
        r = consolidate(path, intent=intent_arg)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print("consolidator.py: all smoke tests passed")
