#!/usr/bin/env python3
"""
Shared helpers for vision check backends.

Provides: image encoding, retry logic, response parsing, rubric loading.
"""

import sys

if __name__ == "__main__":
    print(__doc__)
    print("This is an internal helper module used by vision_check.py backends.")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import base64
import json
import os
import time
from pathlib import Path

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5
RETRY_BACKOFF = 2


def encode_image_base64(png_path: str) -> str:
    """Read a PNG file and return its base64-encoded content."""
    return base64.b64encode(Path(png_path).read_bytes()).decode("utf-8")


def detect_media_type(path: str) -> str:
    """Detect MIME type from file extension."""
    ext = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "image/png")


def retry_with_backoff(fn, max_retries=MAX_RETRIES, base_delay=RETRY_BASE_DELAY):
    """Execute fn() with exponential backoff on failure."""
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                delay = base_delay * (RETRY_BACKOFF ** attempt)
                time.sleep(delay)
    raise last_err


def parse_vision_response(raw_text: str) -> dict:
    """
    Parse the vision model's text response into structured findings.

    Expects JSON output from the model. Falls back to wrapping raw text
    as a single finding if JSON parsing fails.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "issues": [{"severity": "info", "category": "raw", "description": raw_text[:500]}],
            "overall": "needs_human_review",
            "suggestions": [],
        }


def build_rubric_prompt(rubric: str, spec_lock_excerpt: str = "", page_context: str = "") -> str:
    """
    Build the system/user prompt for vision check based on rubric type.

    Args:
        rubric: One of 'quality', 'quick', 'brand', or path to custom rubric file.
        spec_lock_excerpt: Relevant spec_lock.md content (colors, fonts, etc.)
        page_context: Optional page-specific context (core_argument, narrative_function)
    """
    base_instruction = (
        "You are a PPT slide visual quality reviewer. "
        "Analyze the provided slide PNG and return a JSON object with this exact schema:\n"
        '{"issues": [{"severity": "must_fix"|"should_fix"|"accepted", '
        '"category": "<category>", "description": "<specific issue>"}], '
        '"overall": "ready"|"acceptable"|"needs_fix", '
        '"suggestions": ["<actionable suggestion>"]}\n\n'
    )

    if rubric == "quality":
        checklist = (
            "Check ALL of the following:\n"
            "1. Text readability: font size adequate? text overflow? truncation?\n"
            "2. Visual hierarchy: clear title→subtitle→body distinction? single focal point?\n"
            "3. Spacing & alignment: elements well-spaced? no overlap? consistent margins?\n"
            "4. Color usage: colors have semantic purpose? sufficient contrast? palette consistent?\n"
            "5. Image treatment: images properly sized? no distortion? relevant to content?\n"
            "6. Layout balance: whitespace intentional? page not overly dense or empty?\n"
            "7. Brand consistency: fonts/colors match specification below?\n"
            "8. Overall professionalism: looks like a finished consulting/business slide?\n"
        )
    elif rubric == "quick":
        checklist = (
            "Quick scan only. Check:\n"
            "1. Any text overflow or truncation?\n"
            "2. Any element overlap or collision?\n"
            "3. Is visual hierarchy clear (title vs body)?\n"
            "4. Any obviously broken layout?\n"
        )
    elif rubric == "brand":
        checklist = (
            "Brand consistency check only:\n"
            "1. Do colors match the specification below?\n"
            "2. Are fonts visually consistent with the spec?\n"
            "3. Is the visual style consistent across the slide?\n"
            "4. Any off-brand elements (wrong color, wrong font weight)?\n"
        )
    else:
        rubric_path = Path(rubric)
        if rubric_path.exists():
            checklist = rubric_path.read_text(encoding="utf-8")
        else:
            checklist = f"Custom rubric: {rubric}\n"

    prompt = base_instruction + checklist

    if spec_lock_excerpt:
        prompt += f"\n--- Design Specification ---\n{spec_lock_excerpt}\n"

    if page_context:
        prompt += f"\n--- Page Context ---\n{page_context}\n"

    prompt += (
        "\n--- Instructions ---\n"
        "Be specific and actionable. Only flag real issues visible in the image. "
        "Do NOT invent issues you cannot see. Return valid JSON only, no markdown wrapping."
    )

    return prompt


def extract_spec_lock_excerpt(project_path: str) -> str:
    """Extract key visual specs from spec_lock.md for context."""
    spec_path = Path(project_path) / "spec_lock.md"
    if not spec_path.exists():
        return ""

    text = spec_path.read_text(encoding="utf-8")
    sections_to_keep = ("## colors", "## typography", "## visual_style")
    lines = text.split("\n")
    excerpt_lines = []
    in_section = False

    for line in lines:
        if line.startswith("## "):
            in_section = any(line.startswith(s) for s in sections_to_keep)
        if in_section and not line.startswith(">"):
            excerpt_lines.append(line)

    return "\n".join(excerpt_lines[:40])
