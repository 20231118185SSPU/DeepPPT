#!/usr/bin/env python3
"""User profile data model for PPT-master2's memory system.

Hierarchical preference schema adapted from MemSlides' memory architecture
to PPT-master2's file-based workflow.  Each preference carries its own
confidence score and source attribution so the system can reason about
which observations to trust.

Usage::

    from pathlib import Path
    from skills.ppt_master.memory.profile_schema import MemoryStore, MODE_TO_INTENT

    store = MemoryStore.load(Path("user_memory.json"))
    bucket = store.get_or_create_intent("business")
    bucket.profile.theme.values["primary_colors"] = ["#003366"]
    bucket.profile.theme.confidence = 0.85
    bucket.profile.theme.sources.append("job-2024-06")
    store.save(Path("user_memory.json"))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar
import json

T = TypeVar("T", bound="Preference")

# ---------------------------------------------------------------------------
# Intent mapping  (Eight Confirmations mode -> memory bucket name)
# ---------------------------------------------------------------------------

MODE_TO_INTENT: Dict[str, str] = {
    "academic": "academic",
    "business": "business",
    "consulting": "business",
    "education": "education",
    "government": "government",
    "tech": "tech",
    "narrative": "general",
    "general": "general",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Preference base
# ---------------------------------------------------------------------------

@dataclass
class Preference:
    """Base preference with confidence tracking and source attribution.

    Attributes:
        values:   Key-value pairs describing the concrete preference.
        confidence: 0.0 (no signal) to 1.0 (high confidence).
        sources:    Identifiers of jobs / documents that contributed data.
        updated_at: ISO-8601 timestamp of the last update.
    """

    values: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    updated_at: str = ""

    # -- merge ---------------------------------------------------------------

    def merge(self: T, other: T) -> T:
        """Return a new Preference whose values come from the higher-confidence side.

        If *other* has higher (or equal) confidence, its keys overwrite ours
        for any overlap.  Sources and timestamps are unioned / kept latest.
        """
        merged_values = dict(self.values)
        if other.confidence >= self.confidence:
            merged_values.update(other.values)

        merged_sources = list(dict.fromkeys(self.sources + other.sources))  # dedupe, preserve order
        merged_updated = max(self.updated_at, other.updated_at) if (self.updated_at and other.updated_at) else (other.updated_at or self.updated_at)
        merged_conf = max(self.confidence, other.confidence)

        return type(self)(
            values=merged_values,
            confidence=merged_conf,
            sources=merged_sources,
            updated_at=merged_updated,
        )

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "values": self.values,
            "confidence": self.confidence,
            "sources": self.sources,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Deserialize from a dict, ignoring unknown keys."""
        return cls(
            values=data.get("values", {}),
            confidence=data.get("confidence", 0.0),
            sources=data.get("sources", []),
            updated_at=data.get("updated_at", ""),
        )


# ---------------------------------------------------------------------------
# Specific preference types
# ---------------------------------------------------------------------------

@dataclass
class ThemePreference(Preference):
    """Visual theme preferences: colours, fonts, background, mood.

    Expected keys inside *values*:
        primary_colors, accent_colors, font_family,
        background_style, visual_style, mood.
    """


@dataclass
class ContentPreference(Preference):
    """Content / copywriting preferences.

    Expected keys inside *values*:
        text_density (sparse / moderate / dense),
        language_style, bullet_style, title_length, evidence_style.
    """


@dataclass
class LayoutPreference(Preference):
    """Slide layout preferences.

    Expected keys inside *values*:
        content_density, alignment_style, spacing,
        page_structure (two_column / centered / full_bleed / ...).
    """


@dataclass
class VisualPreference(Preference):
    """Visual asset and charting preferences.

    Expected keys inside *values*:
        image_style (photo / illustration / mixed / none),
        chart_type_priority, icon_style, animation.
    """


@dataclass
class GeneralPreference(Preference):
    """Freeform preference notes that don't fit other categories.

    Expected keys inside *values*:
        notes (list[str]) or any ad-hoc key.
    """


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """Complete user profile for PPT generation preferences."""

    user_id: str = "default"
    version: int = 1
    created_at: str = ""
    updated_at: str = ""

    theme: ThemePreference = field(default_factory=ThemePreference)
    content: ContentPreference = field(default_factory=ContentPreference)
    layout: LayoutPreference = field(default_factory=LayoutPreference)
    visual: VisualPreference = field(default_factory=VisualPreference)
    general: GeneralPreference = field(default_factory=GeneralPreference)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "user_id": self.user_id,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "theme": self.theme.to_dict(),
            "content": self.content.to_dict(),
            "layout": self.layout.to_dict(),
            "visual": self.visual.to_dict(),
            "general": self.general.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Deserialize from a dict."""
        return cls(
            user_id=data.get("user_id", "default"),
            version=data.get("version", 1),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            theme=ThemePreference.from_dict(data.get("theme", {})),
            content=ContentPreference.from_dict(data.get("content", {})),
            layout=LayoutPreference.from_dict(data.get("layout", {})),
            visual=VisualPreference.from_dict(data.get("visual", {})),
            general=GeneralPreference.from_dict(data.get("general", {})),
        )


# ---------------------------------------------------------------------------
# IntentProfile
# ---------------------------------------------------------------------------

@dataclass
class IntentProfile:
    """Profile bucket for a specific presentation intent (academic / business / ...)."""

    intent: str = "general"
    profile: UserProfile = field(default_factory=UserProfile)
    job_count: int = 0
    last_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "profile": self.profile.to_dict(),
            "job_count": self.job_count,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentProfile":
        return cls(
            intent=data.get("intent", "general"),
            profile=UserProfile.from_dict(data.get("profile", {})),
            job_count=data.get("job_count", 0),
            last_used=data.get("last_used", ""),
        )


# ---------------------------------------------------------------------------
# MemoryStore
# ---------------------------------------------------------------------------

@dataclass
class MemoryStore:
    """Top-level memory store container.

    Stores per-intent profile buckets so that, e.g., academic decks and
    business decks accumulate separate preference histories.
    """

    user_id: str = "default"
    version: int = 1
    intents: Dict[str, IntentProfile] = field(default_factory=dict)

    # -- intent helpers ------------------------------------------------------

    def get_or_create_intent(self, intent: str) -> IntentProfile:
        """Return the IntentProfile for *intent*, creating it if absent."""
        if intent not in self.intents:
            profile = UserProfile(user_id=self.user_id, created_at=_now_iso())
            self.intents[intent] = IntentProfile(
                intent=intent,
                profile=profile,
            )
        return self.intents[intent]

    # -- persistence ---------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "version": self.version,
            "intents": {k: v.to_dict() for k, v in self.intents.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryStore":
        return cls(
            user_id=data.get("user_id", "default"),
            version=data.get("version", 1),
            intents={
                k: IntentProfile.from_dict(v)
                for k, v in data.get("intents", {}).items()
            },
        )

    def save(self, path: Path) -> None:
        """Write the store to *path* as pretty-printed JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "MemoryStore":
        """Load a store from *path*, returning an empty store if the file is missing."""
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile, os

    # Build a small store in memory
    store = MemoryStore(user_id="demo")
    bucket = store.get_or_create_intent("business")
    bucket.job_count = 3
    bucket.last_used = _now_iso()
    bucket.profile.theme.values = {"primary_colors": ["#003366", "#FF6600"], "font_family": "Helvetica Neue"}
    bucket.profile.theme.confidence = 0.82
    bucket.profile.theme.sources.append("job-2024-06-21")
    bucket.profile.content.values = {"text_density": "moderate", "bullet_style": "concise"}
    bucket.profile.content.confidence = 0.7

    # Round-trip through dict
    as_dict = store.to_dict()
    restored = MemoryStore.from_dict(as_dict)
    assert restored.user_id == "demo"
    assert restored.intents["business"].profile.theme.values["primary_colors"] == ["#003366", "#FF6600"]
    assert restored.intents["business"].profile.theme.confidence == 0.82

    # Round-trip through file
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "memory.json"
        store.save(p)
        loaded = MemoryStore.load(p)
        assert loaded.to_dict() == store.to_dict()

    # Merge test
    a = ThemePreference(values={"primary_colors": ["#AAA"]}, confidence=0.5, sources=["s1"], updated_at="2024-01-01T00:00:00+00:00")
    b = ThemePreference(values={"primary_colors": ["#BBB"], "font_family": "Arial"}, confidence=0.9, sources=["s2"], updated_at="2024-06-01T00:00:00+00:00")
    merged = a.merge(b)
    assert merged.values["primary_colors"] == ["#BBB"]  # higher confidence wins
    assert merged.values["font_family"] == "Arial"
    assert merged.confidence == 0.9
    assert set(merged.sources) == {"s1", "s2"}

    print("profile_schema.py: all smoke tests passed")
