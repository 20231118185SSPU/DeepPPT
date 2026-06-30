"""Shared JSON I/O helpers — load, save, and atomic write."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def load_json(path: str | Path, *, default=None):
    """Read and parse a JSON file.  Returns *default* on missing file or bad JSON."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


def save_json(path: str | Path, data, *, indent: int = 2) -> None:
    """Write *data* as pretty-printed JSON (UTF-8, trailing newline)."""
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )


def atomic_write_json(path: str | Path, data, *, indent: int = 2) -> None:
    """Atomically write JSON via tmp-file + rename.

    On success the target is replaced in one ``os.replace`` call.
    On failure the tmp file is cleaned up and the exception re-raised.
    """
    target = Path(path)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.stem + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.write("\n")
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
