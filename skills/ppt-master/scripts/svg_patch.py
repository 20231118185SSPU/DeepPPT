#!/usr/bin/env python3
"""
PPT Master - SVG Patch Engine

Applies localized edits to SVG files without regenerating them from scratch.
Implements the "Act" phase of the Plan-Act-Guard pipeline.

All editable elements MUST have ``id`` attributes (enforced by
svg_quality_checker.py).  Operations target elements by id and modify
attributes, text content, or tree structure.

Usage:
    # Single patch operation via CLI
    python3 svg_patch.py apply <svg_path> \\
        --ops '[{"op":"update_text","target":"title","params":{"text":"Hello"}}]' \\
        --hash <expected_sha256>

    # Batch fill update
    python3 svg_patch.py batch-fill <svg_path> \\
        --ids title,subtitle --fill '#FF0000'

    # Batch font-size update
    python3 svg_patch.py batch-font-size <svg_path> \\
        --ids title,subtitle --size 24

    # Library usage
    from svg_patch import apply_patch, batch_update_fill
    result = apply_patch(Path("page.svg"), [
        {"op": "update_text", "target": "title", "params": {"text": "New Title"}},
        {"op": "update_fill", "target": "bg",   "params": {"fill": "#222"}},
    ])
"""

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Register namespaces so output does not use ns0:/ns1: prefixes.
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

PATCH_OPS: Dict[str, str] = {
    "update_text": "Change text content of a text element",
    "update_fill": "Change fill color",
    "update_font_size": "Change font-size attribute",
    "update_font_family": "Change font-family attribute",
    "update_transform": "Change transform attribute",
    "update_attribute": "Change any arbitrary attribute",
    "replace_image_href": "Change image href/src",
    "delete_element": "Remove an element by id",
    "insert_after": "Insert SVG fragment after a target element",
}

# Operations that require a target element to exist.
_OPS_NEED_TARGET = {
    "update_text", "update_fill", "update_font_size", "update_font_family",
    "update_transform", "update_attribute", "replace_image_href",
    "delete_element", "insert_after",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_hash(svg_path: Path) -> str:
    """Return the SHA-256 hex digest of *svg_path*."""
    h = hashlib.sha256()
    h.update(svg_path.read_bytes())
    return h.hexdigest()


def _find_element(root: ET.Element, element_id: str) -> Optional[ET.Element]:
    """Find an element by its ``id`` attribute in the SVG tree.

    Searches all descendants (including *root* itself).  Handles elements
    that live inside the SVG namespace (tag like ``{http://...}rect``) as
    well as namespace-free tags.

    Returns:
        The matching :class:`ET.Element`, or ``None`` when no element has
        the requested id.
    """
    for elem in root.iter():
        if elem.get("id") == element_id:
            return elem
    return None


def _local_tag(elem: ET.Element) -> str:
    """Return the element tag without namespace prefix."""
    tag = elem.tag
    return tag.split("}", 1)[1] if "}" in tag else tag


def _success(applied: int, errors: List[Dict[str, str]], svg_path: Path) -> Dict[str, Any]:
    """Build a success result dict."""
    return {
        "success": True,
        "applied": applied,
        "errors": errors,
        "new_hash": _compute_hash(svg_path),
    }


def _fail(error: str, **extra: Any) -> Dict[str, Any]:
    """Build a failure result dict."""
    result: Dict[str, Any] = {"success": False, "error": error}
    result.update(extra)
    return result


# ---------------------------------------------------------------------------
# Per-operation appliers
# ---------------------------------------------------------------------------


def _apply_update_text(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Update the text content of a ``<text>`` element.

    * If the element contains ``<tspan>`` children, the *first* tspan's
      text is updated (matching the common single-line title pattern).
    * If there are multiple tspans and the caller needs per-tspan control,
      they should target each tspan by its own id.
    * Otherwise the element's direct ``.text`` is set.

    Params::

        {"text": "new text"}
    """
    new_text = str(params.get("text", ""))

    # Check for tspan children.
    tspans = [
        child for child in elem
        if _local_tag(child) == "tspan"
    ]
    if tspans:
        tspans[0].text = new_text
    else:
        elem.text = new_text


def _apply_update_fill(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Update the ``fill`` attribute.

    Params::

        {"fill": "#FF0000"}
    """
    fill = params.get("fill", "none")
    elem.set("fill", str(fill))


def _apply_update_font_size(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Update the ``font-size`` attribute.

    Params::

        {"font_size": "24"}  or  {"font_size": 24}
    """
    size = params.get("font_size", "")
    elem.set("font-size", str(size))


def _apply_update_font_family(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Update the ``font-family`` attribute.

    Params::

        {"font_family": "Arial"}
    """
    family = params.get("font_family", "")
    elem.set("font-family", str(family))


def _apply_update_transform(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Update the ``transform`` attribute.

    Params::

        {"transform": "translate(10, 20)"}
    """
    transform = params.get("transform", "")
    elem.set("transform", str(transform))


def _apply_update_attribute(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Update any arbitrary attribute on the element.

    Params::

        {"attr": "rx", "value": "10"}
    """
    attr_name = params.get("attr", "")
    value = params.get("value", "")
    if not attr_name:
        raise ValueError("update_attribute requires 'attr' in params")
    elem.set(str(attr_name), str(value))


def _apply_replace_image_href(elem: ET.Element, params: Dict[str, Any]) -> None:
    """Replace ``href`` or ``xlink:href`` on an ``<image>`` element.

    Updates whichever variant is already present, or sets plain ``href``
    if neither exists.

    Params::

        {"href": "images/new_image.png"}
    """
    new_href = str(params.get("href", ""))
    xlink_key = f"{{{XLINK_NS}}}href"

    # Prefer updating whichever form is already set.
    if elem.get(xlink_key) is not None:
        elem.set(xlink_key, new_href)
    elif elem.get("href") is not None:
        elem.set("href", new_href)
    else:
        # Neither present yet -- default to plain href.
        elem.set("href", new_href)


def _apply_delete_element(
    root: ET.Element,
    elem: ET.Element,
    params: Dict[str, Any],
) -> None:
    """Remove *elem* from its parent in *root*.

    Params::

        {}  (empty)
    """
    # Walk tree to find the parent.
    for parent in root.iter():
        children = list(parent)
        if elem in children:
            parent.remove(elem)
            return

    # If we get here, element is root or orphan -- cannot delete.
    raise ValueError(
        f"Cannot delete element with id '{elem.get('id')}': "
        "no parent found (cannot delete root)"
    )


def _apply_insert_after(
    root: ET.Element,
    elem: ET.Element,
    params: Dict[str, Any],
) -> None:
    """Insert an SVG fragment (from a string) immediately after *elem*.

    The fragment is parsed as an XML snippet and appended as a sibling
    right after the target element in its parent's child list.

    Params::

        {"svg_fragment": "<rect id='new' .../>"}
    """
    fragment_xml = params.get("svg_fragment", "")
    if not fragment_xml:
        raise ValueError("insert_after requires 'svg_fragment' in params")

    # Parse fragment.  Wrap in a dummy root so ElementTree can parse it.
    wrapped = f'<svg xmlns="{SVG_NS}">{fragment_xml}</svg>'
    try:
        frag_root = ET.fromstring(wrapped)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid SVG fragment: {exc}") from exc

    # Find parent of elem.
    for parent in root.iter():
        children = list(parent)
        if elem in children:
            idx = children.index(elem)
            # Insert each child of the wrapper after elem.
            insert_pos = idx + 1
            for new_child in list(frag_root):
                parent.insert(insert_pos, new_child)
                insert_pos += 1
            return

    raise ValueError(
        f"Cannot insert after element with id '{elem.get('id')}': "
        "no parent found"
    )


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

# Maps operation name to (handler_callable, needs_root, needs_elem).
_HANDLERS: Dict[str, Tuple[Any, bool, bool]] = {
    "update_text":        (_apply_update_text,        False, True),
    "update_fill":        (_apply_update_fill,        False, True),
    "update_font_size":   (_apply_update_font_size,   False, True),
    "update_font_family": (_apply_update_font_family, False, True),
    "update_transform":   (_apply_update_transform,   False, True),
    "update_attribute":   (_apply_update_attribute,   False, True),
    "replace_image_href": (_apply_replace_image_href, False, True),
    "delete_element":     (_apply_delete_element,     True,  True),
    "insert_after":       (_apply_insert_after,       True,  True),
}


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------


def apply_patch(
    svg_path: Path,
    operations: List[Dict[str, Any]],
    expected_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply a sequence of patch operations to an SVG file.

    Args:
        svg_path: Path to the SVG file to modify (modified in-place).
        operations: List of operation dicts, each with keys ``op``,
            ``target``, and ``params``.
        expected_hash: If provided, the current file's SHA-256 hash must
            match this value.  When stale, the file is not modified and
            an error result is returned.

    Returns:
        A result dict::

            {"success": True,  "applied": N, "errors": [...], "new_hash": "..."}
            {"success": False, "error": "...", "current_hash": "..."}
    """
    svg_path = Path(svg_path)
    if not svg_path.is_file():
        return _fail("file_not_found", detail=str(svg_path))

    # -- Staleness check ---------------------------------------------------
    if expected_hash is not None:
        current_hash = _compute_hash(svg_path)
        if current_hash != expected_hash:
            return _fail(
                "snapshot_stale",
                current_hash=current_hash,
            )

    # -- Parse SVG ---------------------------------------------------------
    try:
        tree = ET.parse(str(svg_path))
    except ET.ParseError as exc:
        return _fail("parse_error", detail=str(exc))

    root = tree.getroot()

    # -- Apply operations in order -----------------------------------------
    applied = 0
    errors: List[Dict[str, str]] = []

    for i, op_desc in enumerate(operations):
        op_name = op_desc.get("op", "")
        target_id = op_desc.get("target", "")
        params = op_desc.get("params", {})

        if op_name not in _HANDLERS:
            errors.append({"index": i, "op": op_name, "error": "unknown_operation"})
            continue

        handler, needs_root, needs_elem = _HANDLERS[op_name]

        # Resolve target element.
        elem: Optional[ET.Element] = None
        if needs_elem:
            if not target_id:
                errors.append({"index": i, "op": op_name, "error": "missing_target"})
                continue
            elem = _find_element(root, target_id)
            if elem is None:
                errors.append({
                    "index": i,
                    "op": op_name,
                    "target": target_id,
                    "error": "element_not_found",
                })
                continue

        try:
            if needs_root:
                handler(root, elem, params)  # type: ignore[misc]
            else:
                handler(elem, params)  # type: ignore[misc]
            applied += 1
        except Exception as exc:
            errors.append({
                "index": i,
                "op": op_name,
                "target": target_id,
                "error": str(exc),
            })

    # -- Write back --------------------------------------------------------
    tree.write(str(svg_path), encoding="unicode", xml_declaration=False)

    return _success(applied, errors, svg_path)


# ---------------------------------------------------------------------------
# Batch convenience helpers
# ---------------------------------------------------------------------------


def batch_update_fill(
    svg_path: Path,
    element_ids: List[str],
    fill: str,
    expected_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Update the ``fill`` attribute on multiple elements at once.

    Args:
        svg_path: Path to the SVG file.
        element_ids: List of element id strings.
        fill: The fill value (e.g. ``"#FF0000"``).
        expected_hash: Optional SHA-256 for staleness checking.

    Returns:
        Same shape as :func:`apply_patch`.
    """
    operations = [
        {"op": "update_fill", "target": eid, "params": {"fill": fill}}
        for eid in element_ids
    ]
    return apply_patch(svg_path, operations, expected_hash=expected_hash)


def batch_update_font_size(
    svg_path: Path,
    element_ids: List[str],
    font_size: str,
    expected_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Update the ``font-size`` attribute on multiple elements at once.

    Args:
        svg_path: Path to the SVG file.
        element_ids: List of element id strings.
        font_size: The font-size value (e.g. ``"24"``).
        expected_hash: Optional SHA-256 for staleness checking.

    Returns:
        Same shape as :func:`apply_patch`.
    """
    operations = [
        {"op": "update_font_size", "target": eid, "params": {"font_size": font_size}}
        for eid in element_ids
    ]
    return apply_patch(svg_path, operations, expected_hash=expected_hash)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli_apply(args: argparse.Namespace) -> None:
    """Handle the ``apply`` subcommand."""
    ops_raw: str = args.ops
    try:
        operations = json.loads(ops_raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"success": False, "error": f"invalid JSON: {exc}"}, indent=2))
        sys.exit(1)

    if not isinstance(operations, list):
        print(json.dumps({"success": False, "error": "--ops must be a JSON array"}, indent=2))
        sys.exit(1)

    result = apply_patch(
        Path(args.svg_path),
        operations,
        expected_hash=args.hash,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


def _cli_batch_fill(args: argparse.Namespace) -> None:
    """Handle the ``batch-fill`` subcommand."""
    ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    if not ids:
        print(json.dumps({"success": False, "error": "no element ids provided"}, indent=2))
        sys.exit(1)

    result = batch_update_fill(
        Path(args.svg_path),
        ids,
        args.fill,
        expected_hash=args.hash,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


def _cli_batch_font_size(args: argparse.Namespace) -> None:
    """Handle the ``batch-font-size`` subcommand."""
    ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    if not ids:
        print(json.dumps({"success": False, "error": "no element ids provided"}, indent=2))
        sys.exit(1)

    result = batch_update_font_size(
        Path(args.svg_path),
        ids,
        args.size,
        expected_hash=args.hash,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success") else 1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PPT Master SVG Patch Engine",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- apply -------------------------------------------------------------
    sp_apply = subparsers.add_parser(
        "apply",
        help="Apply a JSON list of patch operations to an SVG file",
    )
    sp_apply.add_argument("svg_path", help="Path to SVG file")
    sp_apply.add_argument(
        "--ops", required=True,
        help="JSON array of operations",
    )
    sp_apply.add_argument(
        "--hash", default=None,
        help="Expected SHA-256 hash for staleness check",
    )

    # -- batch-fill --------------------------------------------------------
    sp_bfill = subparsers.add_parser(
        "batch-fill",
        help="Update fill color on multiple elements",
    )
    sp_bfill.add_argument("svg_path", help="Path to SVG file")
    sp_bfill.add_argument(
        "--ids", required=True,
        help="Comma-separated element ids",
    )
    sp_bfill.add_argument(
        "--fill", required=True,
        help="Fill value (e.g. '#FF0000')",
    )
    sp_bfill.add_argument(
        "--hash", default=None,
        help="Expected SHA-256 hash for staleness check",
    )

    # -- batch-font-size ---------------------------------------------------
    sp_bfs = subparsers.add_parser(
        "batch-font-size",
        help="Update font-size on multiple elements",
    )
    sp_bfs.add_argument("svg_path", help="Path to SVG file")
    sp_bfs.add_argument(
        "--ids", required=True,
        help="Comma-separated element ids",
    )
    sp_bfs.add_argument(
        "--size", required=True,
        help="Font-size value (e.g. '24')",
    )
    sp_bfs.add_argument(
        "--hash", default=None,
        help="Expected SHA-256 hash for staleness check",
    )

    args = parser.parse_args()

    dispatch = {
        "apply": _cli_apply,
        "batch-fill": _cli_batch_fill,
        "batch-font-size": _cli_batch_font_size,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
