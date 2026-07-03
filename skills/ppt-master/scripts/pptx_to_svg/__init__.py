"""PPTX to SVG semantic conversion package.

Reads OOXML (DrawingML) directly from a .pptx zip archive and emits SVG with
shape-level fidelity.

Public API: convert_pptx_to_svg().
"""

from .converter import convert_pptx_to_svg

__all__ = ["convert_pptx_to_svg"]
