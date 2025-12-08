"""Data models for functional API testing."""

from dataclasses import dataclass


@dataclass
class FunctionSignature:
    """A function signature from type definitions."""

    name: str
    parameters: list[tuple[str, str]]  # [(name, type), ...]
    return_type: str
    module: str  # e.g., "lodash", "lodash/groupBy"


@dataclass
class CallSite:
    """A location where a library function is called."""

    function_name: str
    file_path: str
    line_number: int
    arguments: list[str]  # String representations of arguments
    has_static_args: bool  # True if all args are literals


@dataclass
class CapturedCall:
    """A captured function call with inputs and outputs."""

    function_name: str
    inputs: list[str]  # JSON-serialized inputs
    output: str  # JSON-serialized output
    location: str  # file:line where originally called
    is_complete: bool  # False if some inputs couldn't be captured
    incomplete_reason: str | None = None
