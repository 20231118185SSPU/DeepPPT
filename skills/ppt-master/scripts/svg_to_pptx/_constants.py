"""Shared constants for the svg_to_pptx package."""

import re

# Tokens found in SVG element IDs that indicate "chrome" (non-content) elements.
# These are skipped by the animation system so that backgrounds, headers, footers,
# decorations etc. appear together with the slide instead of requiring presenter clicks.
CHROME_ID_TOKENS = frozenset({
    'background', 'bg',
    'decoration', 'decorations', 'decor',
    'header', 'footer',
    'chrome', 'watermark',
    'pagenumber', 'pagenum',
    'page-number',
    'nav', 'logo', 'rule',
})


def is_chrome_id(elem_id: str | None) -> bool:
    """Return True if *elem_id* looks like a chrome (non-content) element."""
    if not elem_id:
        return False
    lower = elem_id.lower()
    if lower.replace('-', '').replace('_', '') in CHROME_ID_TOKENS:
        return True
    tokens = re.split(r'[-_]', lower)
    return any(t in CHROME_ID_TOKENS for t in tokens if t)
