"""Shared XML utilities for the pptx_to_svg package."""


def xml_escape(text: str) -> str:
    """Escape special XML characters in text content."""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
