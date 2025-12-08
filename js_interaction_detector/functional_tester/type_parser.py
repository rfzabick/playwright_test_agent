"""Parse TypeScript definition files (.d.ts) to extract function signatures."""

import logging
import re
from pathlib import Path

from js_interaction_detector.functional_tester.models import FunctionSignature

logger = logging.getLogger(__name__)

# Regex to match: export function name<T>(param: type, ...): returnType;
FUNCTION_PATTERN = re.compile(
    r"export\s+function\s+(\w+)"  # function name
    r"(?:<[^>]+>)?"  # optional generic params
    r"\s*\(([^)]*)\)"  # parameters
    r"\s*:\s*([^;]+)"  # return type
    r"\s*;",
    re.MULTILINE,
)

# Regex to match individual parameters: name: type
PARAM_PATTERN = re.compile(r"(\w+)\s*:\s*([^,]+)")


def parse_dts_file(path: Path) -> list[FunctionSignature]:
    """Parse a .d.ts file and extract function signatures.

    Args:
        path: Path to the .d.ts file

    Returns:
        List of FunctionSignature objects
    """
    logger.info(f"Parsing type definitions from {path}")
    content = path.read_text()
    return parse_dts_content(content, module=path.stem)


def parse_dts_content(content: str, module: str = "") -> list[FunctionSignature]:
    """Parse .d.ts content and extract function signatures.

    Args:
        content: The .d.ts file content
        module: The module name for these signatures

    Returns:
        List of FunctionSignature objects
    """
    signatures = []

    for match in FUNCTION_PATTERN.finditer(content):
        name = match.group(1)
        params_str = match.group(2).strip()
        return_type = match.group(3).strip()

        # Parse parameters
        parameters = []
        if params_str:
            for param_match in PARAM_PATTERN.finditer(params_str):
                param_name = param_match.group(1)
                param_type = param_match.group(2).strip()
                parameters.append((param_name, param_type))

        sig = FunctionSignature(
            name=name,
            parameters=parameters,
            return_type=return_type,
            module=module,
        )
        signatures.append(sig)
        logger.debug(f"Parsed function: {name}({params_str}) -> {return_type}")

    logger.info(f"Found {len(signatures)} function signatures")
    return signatures
