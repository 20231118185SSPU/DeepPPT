#!/usr/bin/env python3
"""JSON-file-backed user profile storage with intent bucketing.

Provides :class:`ProfileStore`, a high-level facade over the low-level
:class:`~profile_schema.MemoryStore` data model.  Each PPT project gets its
own ``memory/user_profiles.json`` file so profiles never bleed across projects.

Usage::

    from pathlib import Path
    from skills.ppt_master.memory.profile_store import ProfileStore

    store = ProfileStore(Path("projects/my_deck"))

    # Record a completed job
    store.update_profile("business", user_profile, source="job-abc")

    # Read back
    profile = store.get_profile("business")

    # CLI-friendly summary
    for row in store.get_intent_summary():
        print(row)

    # Housekeeping
    store.reset("academic")   # drop one bucket
    store.export(Path("backup.json"))
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .profile_schema import (
    IntentProfile,
    MemoryStore,
    UserProfile,
)


class ProfileStore:
    """JSON-file-backed user profile storage with intent bucketing.

    Each project directory owns a ``memory/user_profiles.json`` file.
    The store delegates serialization to :class:`MemoryStore` and adds
    convenience methods for intent-level queries and merges.
    """

    MEMORY_FILENAME = "user_profiles.json"

    def __init__(self, project_path: Path) -> None:
        """Initialize store for a project.

        Args:
            project_path: Root of the PPT project (e.g. ``projects/my_deck``).
        """
        self.project_path = Path(project_path)
        self.memory_dir = self.project_path / "memory"
        self.memory_file = self.memory_dir / self.MEMORY_FILENAME

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def load(self) -> MemoryStore:
        """Load the memory store from disk.

        Returns the parsed :class:`MemoryStore` if the file exists and is
        valid JSON, or an empty store when the file is missing or corrupt.
        """
        if not self.memory_file.exists():
            return MemoryStore()
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
            return MemoryStore.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"[profile_store] WARNING: corrupt memory file, "
                  f"starting fresh ({exc})")
            return MemoryStore()

    def save(self, store: MemoryStore) -> None:
        """Persist *store* to disk.

        Creates the ``memory/`` directory if it does not yet exist.
        Updates ``updated_at`` on every intent bucket touched.
        """
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat()
        for bucket in store.intents.values():
            bucket.profile.updated_at = stamp
        self.memory_file.write_text(
            json.dumps(store.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def exists(self) -> bool:
        """Return ``True`` if the memory file already exists on disk."""
        return self.memory_file.exists()

    # ------------------------------------------------------------------
    # Profile accessors
    # ------------------------------------------------------------------

    def get_profile(self, intent: str) -> Optional[UserProfile]:
        """Return the :class:`UserProfile` for *intent*, or ``None``.

        Args:
            intent: Bucket name (e.g. ``"academic"``, ``"business"``).
        """
        store = self.load()
        bucket = store.intents.get(intent)
        if bucket is None:
            return None
        return bucket.profile

    def update_profile(
        self,
        intent: str,
        profile: UserProfile,
        source: str = "consolidation",
    ) -> None:
        """Merge *profile* into the existing bucket for *intent*.

        If the bucket does not exist yet it is created.  Each preference
        category is merged via :pymethod:`Preference.merge` so higher-confidence
        values win.  ``job_count`` is incremented and ``last_used`` refreshed.

        Args:
            intent:  Bucket name (e.g. ``"business"``).
            profile: New observations to merge in.
            source:  Attribution tag recorded on changed preferences.
        """
        store = self.load()
        bucket = store.get_or_create_intent(intent)

        stamp = datetime.now(timezone.utc).isoformat()

        # Merge each preference category ----------------------------------
        for attr in ("theme", "content", "layout", "visual", "general"):
            new_pref = getattr(profile, attr)
            old_pref = getattr(bucket.profile, attr)
            if new_pref.values:
                new_pref.sources.append(source)
                new_pref.updated_at = stamp
                setattr(bucket.profile, attr, old_pref.merge(new_pref))

        # Bookkeeping ------------------------------------------------------
        bucket.job_count += 1
        bucket.last_used = stamp

        self.save(store)

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    def get_intent_summary(self) -> List[Dict[str, object]]:
        """Return a CLI-friendly summary of every intent bucket.

        Each entry contains::

            {
                "intent": "business",
                "job_count": 3,
                "last_used": "2026-06-23T12:00:00+00:00",
                "top_prefs": ["dark theme", "dense layout"],
            }
        """
        store = self.load()
        rows: List[Dict[str, object]] = []
        for name, bucket in sorted(store.intents.items()):
            top = self._top_preferences(bucket.profile)
            rows.append({
                "intent": name,
                "job_count": bucket.job_count,
                "last_used": bucket.last_used,
                "top_prefs": top,
            })
        return rows

    @staticmethod
    def _top_preferences(profile: UserProfile, limit: int = 3) -> List[str]:
        """Extract up to *limit* human-readable preference snippets."""
        snippets: List[str] = []
        for attr in ("theme", "content", "layout", "visual", "general"):
            pref = getattr(profile, attr)
            if not pref.values:
                continue
            for key, val in pref.values.items():
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                snippets.append(f"{key}: {val}")
        return snippets[:limit]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def reset(self, intent: Optional[str] = None) -> str:
        """Remove a single intent bucket or the entire memory file.

        Args:
            intent: Bucket to remove, or ``None`` to wipe everything.

        Returns:
            A short description of what was reset (for logging / CLI output).
        """
        if intent is None:
            if self.memory_file.exists():
                self.memory_file.unlink()
            return f"all profiles deleted ({self.memory_file})"

        store = self.load()
        if intent in store.intents:
            del store.intents[intent]
            self.save(store)
            return f"intent '{intent}' reset"
        return f"intent '{intent}' not found -- nothing to reset"

    def export(self, output_path: Path) -> Path:
        """Copy the memory file to *output_path*.

        Args:
            output_path: Destination file or directory.  If a directory,
                the file keeps its original name.

        Returns:
            The resolved path of the exported file.

        Raises:
            FileNotFoundError: If the memory file does not exist yet.
        """
        if not self.memory_file.exists():
            raise FileNotFoundError(
                f"No memory file to export: {self.memory_file}"
            )
        dest = Path(output_path)
        if dest.is_dir():
            dest = dest / self.MEMORY_FILENAME
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.memory_file, dest)
        return dest


# ------------------------------------------------------------------
# Smoke test
# ------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "demo_project"
        ps = ProfileStore(proj)

        # 1. Empty state
        assert ps.exists() is False
        assert ps.get_profile("business") is None
        assert ps.get_intent_summary() == []

        # 2. Write a profile
        p = UserProfile(
            user_id="demo",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        p.theme.values = {"primary_colors": ["#003366"], "font_family": "Arial"}
        p.theme.confidence = 0.8
        p.layout.values = {"content_density": "dense"}
        p.layout.confidence = 0.7
        ps.update_profile("business", p, source="job-test-1")

        # 3. Read it back
        assert ps.exists()
        got = ps.get_profile("business")
        assert got is not None
        assert got.theme.values["primary_colors"] == ["#003366"]

        # 4. Merge a second observation
        p2 = UserProfile(user_id="demo")
        p2.theme.values = {"primary_colors": ["#FF6600"], "visual_style": "modern"}
        p2.theme.confidence = 0.9
        ps.update_profile("business", p2, source="job-test-2")

        got2 = ps.get_profile("business")
        assert got2 is not None
        assert got2.theme.values["primary_colors"] == ["#FF6600"]  # higher conf wins
        assert got2.theme.values["visual_style"] == "modern"

        # 5. Intent summary
        summary = ps.get_intent_summary()
        assert len(summary) == 1
        assert summary[0]["intent"] == "business"
        assert summary[0]["job_count"] == 2

        # 6. Reset one intent
        msg = ps.reset("business")
        assert "reset" in msg
        assert ps.get_profile("business") is None

        # 7. Write again, then reset all
        ps.update_profile("academic", p)
        ps.reset()
        assert ps.exists() is False

        # 8. Export
        ps.update_profile("tech", p)
        out = Path(tmp) / "export_backup.json"
        exported = ps.export(out)
        assert exported.exists()
        assert exported.stat().st_size > 0

    print("profile_store.py: all smoke tests passed")
