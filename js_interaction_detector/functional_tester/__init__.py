"""Functional API tester for JavaScript library upgrades."""

from js_interaction_detector.functional_tester.instrumentation import (
    generate_instrumentation_script,
    generate_wrapper,
)
from js_interaction_detector.functional_tester.models import (
    CallSite,
    CapturedCall,
    FunctionSignature,
)
from js_interaction_detector.functional_tester.test_generator import (
    generate_test_case,
    generate_test_file,
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
    # Models
    "FunctionSignature",
    "CallSite",
    "CapturedCall",
    # Type parsing
    "parse_dts_file",
    "parse_dts_content",
    # Usage detection
    "find_imports",
    "find_call_sites",
    "detect_usage",
    # Instrumentation
    "generate_wrapper",
    "generate_instrumentation_script",
    # Test generation
    "generate_test_case",
    "generate_test_file",
]
