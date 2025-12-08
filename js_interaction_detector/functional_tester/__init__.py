"""Functional API tester for JavaScript library upgrades."""

from js_interaction_detector.functional_tester.models import (
    CallSite,
    CapturedCall,
    FunctionSignature,
)
from js_interaction_detector.functional_tester.type_parser import (
    parse_dts_content,
    parse_dts_file,
)
from js_interaction_detector.functional_tester.usage_detector import (
    detect_usage,
    find_call_sites,
    find_imports,
)

__all__ = [
    "FunctionSignature",
    "CallSite",
    "CapturedCall",
    "parse_dts_file",
    "parse_dts_content",
    "find_imports",
    "find_call_sites",
    "detect_usage",
]
