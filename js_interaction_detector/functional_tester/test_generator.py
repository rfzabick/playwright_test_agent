"""Generate Jest tests from captured function calls."""

import logging

from js_interaction_detector.functional_tester.models import CapturedCall

logger = logging.getLogger(__name__)


def generate_test_case(call: CapturedCall, library: str) -> str:
    """Generate a single Jest test case from a captured call.

    Args:
        call: The captured function call
        library: The library name

    Returns:
        Jest test code as a string
    """
    if call.is_complete:
        return _generate_complete_test(call, library)
    else:
        return _generate_incomplete_test(call, library)


def _generate_complete_test(call: CapturedCall, library: str) -> str:
    """Generate a complete, passing test."""
    inputs_str = ", ".join(call.inputs)
    test_name = f"{call.function_name} returns expected output"

    return f"""  test('{test_name}', () => {{
    expect({call.function_name}({inputs_str})).toEqual({call.output});
  }});"""


def _generate_incomplete_test(call: CapturedCall, library: str) -> str:
    """Generate a failing test with details in error message."""
    inputs_str = ", ".join(call.inputs)
    test_name = f"{call.function_name} - requires manual input"

    error_message = f"""
Unable to generate complete test for {call.function_name}

Location: {call.location}
Issue: {call.incomplete_reason or "Unknown"}
Original usage: {call.function_name}({inputs_str})

To fix: Replace this test with concrete inputs and expected output
"""

    # Escape backticks and backslashes in the error message
    error_message = error_message.replace("\\", "\\\\").replace("`", "\\`")

    return f"""  test('{test_name}', () => {{
    throw new Error(`{error_message}`);
  }});"""


def generate_test_file(library: str, calls: list[CapturedCall]) -> str:
    """Generate a complete Jest test file from captured calls.

    Args:
        library: The library name
        calls: List of captured function calls

    Returns:
        Complete Jest test file as a string
    """
    # Deduplicate calls
    unique_calls = _deduplicate_calls(calls)
    logger.info(f"Deduplicated {len(calls)} calls to {len(unique_calls)} unique tests")

    # Collect function names for imports
    function_names = sorted({c.function_name for c in unique_calls})
    imports_str = ", ".join(function_names)

    # Generate test cases
    test_cases = []
    for call in unique_calls:
        test_cases.append(generate_test_case(call, library))

    tests_str = "\n\n".join(test_cases)

    return f"""import {{ {imports_str} }} from '{library}';

describe('{library}', () => {{
{tests_str}
}});
"""


def _deduplicate_calls(calls: list[CapturedCall]) -> list[CapturedCall]:
    """Remove duplicate calls with same function and inputs.

    Keeps the first occurrence of each unique (function, inputs) pair.
    """
    seen: dict[tuple, CapturedCall] = {}

    for call in calls:
        key = (call.function_name, tuple(call.inputs))
        if key not in seen:
            seen[key] = call

    return list(seen.values())
