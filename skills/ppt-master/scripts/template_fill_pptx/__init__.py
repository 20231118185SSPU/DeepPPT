"""PPTX template-fill package.

Direct OOXML editing for reusable slide libraries and native template-filled
PPTX output.

Public API: analyze_pptx(), scaffold_plan(), check_plan(), print_check_report(),
apply_plan(), main().
"""

from .analyzer import analyze_pptx
from .applier import apply_plan
from .checker import check_plan, print_check_report
from .cli import main
from .scaffolder import scaffold_plan

__all__ = [
    "analyze_pptx",
    "scaffold_plan",
    "check_plan",
    "print_check_report",
    "apply_plan",
    "main",
]
