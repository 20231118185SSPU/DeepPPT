#!/usr/bin/env python3
"""
PPT Master - Memory Manager CLI

Manage user profile memory for PPT generation preferences.

Usage:
    python3 scripts/memory_manager.py show <project_path>
    python3 scripts/memory_manager.py load <project_path> --intent academic
    python3 scripts/memory_manager.py consolidate <project_path>
    python3 scripts/memory_manager.py reset <project_path> --intent academic
    python3 scripts/memory_manager.py reset <project_path> --force
    python3 scripts/memory_manager.py export <project_path> -o output.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup -- allow importing the sibling ``memory`` package
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPTS_DIR.parent
sys.path.insert(0, str(_SKILL_DIR))

from memory.profile_schema import MemoryStore, MODE_TO_INTENT  # noqa: E402
from memory.profile_store import ProfileStore  # noqa: E402


# ── helpers ─────────────────────────────────────────────────────────────────

def _load_store(project_path: Path) -> MemoryStore | None:
    """Attempt to load the memory store; return *None* if absent."""
    return ProfileStore.load(project_path)


def _ts_display(ts: str | None) -> str:
    """Format an ISO-ish timestamp for table display."""
    if not ts:
        return '-'
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return ts[:16] if len(ts) > 16 else ts


def _confirm_reset_all() -> None:
    """Print guidance when --force is missing for a full reset."""
    print(
        'Error: resetting ALL intents requires the --force flag.\n'
        '  python3 scripts/memory_manager.py reset <project_path> --force',
        file=sys.stderr,
    )


# ── subcommand implementations ─────────────────────────────────────────────

def _cmd_show(args: argparse.Namespace) -> int:
    """Display all intent profiles in the memory store."""
    project_path = Path(args.project_path)
    store = _load_store(project_path)
    if store is None or not store.profiles:
        print('No memory found. Run a PPT generation first.')
        return 0

    # Header
    header = f'{"Intent":<20} {"Jobs":>5}  {"Last Used":<16}  Top Preferences'
    sep = '-' * len(header)
    print(header)
    print(sep)

    # Sort by last_used descending (most recent first)
    sorted_profiles = sorted(
        store.profiles.values(),
        key=lambda p: p.last_used or '',
        reverse=True,
    )
    for profile in sorted_profiles:
        job_count = len(profile.jobs)
        last = _ts_display(profile.last_used)
        # Collect top 3 preference keys from the most recent job (if any)
        top_prefs = ''
        if profile.preferences:
            keys = list(profile.preferences.keys())[:3]
            top_prefs = ', '.join(keys)
        print(f'{profile.intent:<20} {job_count:>5}  {last:<16}  {top_prefs}')

    print(sep)
    total = sum(len(p.jobs) for p in store.profiles.values())
    print(f'Total intents: {len(store.profiles)}, total jobs: {total}')
    return 0


def _cmd_load(args: argparse.Namespace) -> int:
    """Load and display a specific intent profile and its memory prompt."""
    project_path = Path(args.project_path)
    store = _load_store(project_path)
    if store is None or not store.profiles:
        print('No memory found. Run a PPT generation first.')
        return 0

    intent = args.intent
    if not intent:
        # Pick the most recently used profile
        sorted_profiles = sorted(
            store.profiles.values(),
            key=lambda p: p.last_used or '',
            reverse=True,
        )
        if not sorted_profiles:
            print('No memory found. Run a PPT generation first.')
            return 0
        intent = sorted_profiles[0].intent
        print(f'(No --intent specified; showing most recent: {intent})\n')

    profile = store.profiles.get(intent)
    if profile is None:
        available = ', '.join(sorted(store.profiles.keys())) or '(none)'
        print(f'No profile found for intent "{intent}".', file=sys.stderr)
        print(f'Available intents: {available}', file=sys.stderr)
        return 1

    # Print profile details
    print(f'Intent:     {profile.intent}')
    print(f'Last used:  {_ts_display(profile.last_used)}')
    print(f'Jobs:       {len(profile.jobs)}')
    print(f'Preferences ({len(profile.preferences)}):')
    for key, pref in profile.preferences.items():
        val = pref.value if hasattr(pref, 'value') else pref
        conf = pref.confidence if hasattr(pref, 'confidence') else ''
        conf_str = f'  (confidence: {conf})' if conf else ''
        print(f'  {key}: {val}{conf_str}')

    # Print the memory prompt
    try:
        from memory.orchestrator import format_memory_prompt  # noqa: E402
        prompt = format_memory_prompt(store, intent)
        if prompt:
            print('\n--- Memory Prompt (injected into Strategist) ---')
            print(prompt)
            print('--- End ---')
        else:
            print('\n(No memory prompt generated for this intent.)')
    except ImportError:
        print(
            '\nNote: orchestrator module not available; '
            'cannot display memory prompt.',
            file=sys.stderr,
        )

    return 0


def _cmd_consolidate(args: argparse.Namespace) -> int:
    """Manually trigger profile consolidation from the latest Eight Confirmations."""
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f'Error: project path does not exist: {project_path}', file=sys.stderr)
        return 1

    result_path = project_path / 'confirm_ui' / 'result.json'
    if not result_path.exists():
        print(
            f'Error: {result_path} not found.\n'
            'Run a PPT generation (at least through the Eight Confirmations) first.',
            file=sys.stderr,
        )
        return 1

    try:
        from memory.consolidator import consolidate  # noqa: E402
    except ImportError:
        print(
            'Error: memory.consolidator module could not be imported. '
            'Ensure the memory package is complete.',
            file=sys.stderr,
        )
        return 1

    try:
        with open(result_path, encoding='utf-8') as fh:
            confirmations = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f'Error reading {result_path}: {exc}', file=sys.stderr)
        return 1

    # Derive intent from the confirmations (fall back to "general")
    intent = confirmations.get('intent') or confirmations.get('mode') or 'general'

    try:
        updated = consolidate(project_path, intent, confirmations)
    except Exception as exc:
        print(f'Error during consolidation: {exc}', file=sys.stderr)
        return 1

    if updated:
        print(f'Memory consolidated for intent "{intent}".')
        print(f'Updated keys: {", ".join(updated)}')
    else:
        print('No new preferences to consolidate.')

    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    """Reset one intent bucket or the entire memory store."""
    project_path = Path(args.project_path)
    store = _load_store(project_path)

    if store is None or not store.profiles:
        print('No memory found. Nothing to reset.')
        return 0

    intent = args.intent

    # Full reset -- require --force
    if not intent:
        if not args.force:
            _confirm_reset_all()
            return 1
        store.profiles.clear()
        store.version = 1
        ProfileStore.save(project_path, store)
        print('All memory profiles have been reset.')
        return 0

    # Single-intent reset
    if intent not in store.profiles:
        available = ', '.join(sorted(store.profiles.keys())) or '(none)'
        print(f'No profile found for intent "{intent}".', file=sys.stderr)
        print(f'Available intents: {available}', file=sys.stderr)
        return 1

    del store.profiles[intent]
    ProfileStore.save(project_path, store)
    print(f'Profile for intent "{intent}" has been reset.')
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    """Export the memory store to a JSON file."""
    project_path = Path(args.project_path)
    store = _load_store(project_path)

    if store is None or not store.profiles:
        print('No memory found. Nothing to export.')
        return 0

    output_path = Path(args.output) if args.output else project_path / 'memory' / 'export.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Serialise via the schema's own method when available, else dict fallback
    if hasattr(store, 'to_dict'):
        data = store.to_dict()
    elif hasattr(store, 'model_dump'):
        data = store.model_dump()
    else:
        # Last resort: build a plain dict manually
        data = {
            'version': store.version,
            'profiles': {
                intent: _profile_to_dict(p)
                for intent, p in store.profiles.items()
            },
        }

    with open(output_path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    print(f'Memory exported to {output_path}')
    return 0


def _profile_to_dict(profile: object) -> dict:
    """Best-effort conversion of a profile object to a plain dict."""
    if hasattr(profile, 'model_dump'):
        return profile.model_dump()
    if hasattr(profile, 'to_dict'):
        return profile.to_dict()
    if hasattr(profile, '__dict__'):
        return profile.__dict__
    return {'repr': repr(profile)}


# ── CLI construction ───────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Manage user profile memory for PPT generation preferences.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # show
    show = subparsers.add_parser(
        'show',
        help='display all intent profiles in the memory store',
    )
    show.add_argument('project_path', help='Project directory')

    # load
    load = subparsers.add_parser(
        'load',
        help='load and display a specific intent profile',
    )
    load.add_argument('project_path', help='Project directory')
    load.add_argument(
        '--intent',
        default=None,
        help='Intent to load (e.g. academic, business). Default: most recent',
    )

    # consolidate
    consolidate = subparsers.add_parser(
        'consolidate',
        help='trigger profile consolidation from Eight Confirmations',
    )
    consolidate.add_argument('project_path', help='Project directory')

    # reset
    reset = subparsers.add_parser(
        'reset',
        help='reset one intent profile or all profiles',
    )
    reset.add_argument('project_path', help='Project directory')
    reset.add_argument(
        '--intent',
        default=None,
        help='Reset only this intent. Omit to reset all (requires --force)',
    )
    reset.add_argument(
        '--force',
        action='store_true',
        help='Required when resetting all intents (no --intent given)',
    )

    # export
    export = subparsers.add_parser(
        'export',
        help='export memory store to JSON',
    )
    export.add_argument('project_path', help='Project directory')
    export.add_argument(
        '-o', '--output',
        default=None,
        help='Output file path. Default: <project>/memory/export.json',
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Validate project path exists for commands that need it
    if args.command in ('show', 'load', 'export'):
        project_path = Path(args.project_path)
        if not project_path.exists():
            print(f'Error: project path does not exist: {project_path}', file=sys.stderr)
            return 1

    dispatch = {
        'show': _cmd_show,
        'load': _cmd_load,
        'consolidate': _cmd_consolidate,
        'reset': _cmd_reset,
        'export': _cmd_export,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == '__main__':
    raise SystemExit(main())
