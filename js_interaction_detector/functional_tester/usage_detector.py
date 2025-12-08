# js_interaction_detector/functional_tester/usage_detector.py
"""Detect library usage in JavaScript/TypeScript source files."""

import logging
import re
from pathlib import Path

from js_interaction_detector.functional_tester.models import CallSite

logger = logging.getLogger(__name__)

# ES module import: import { a, b } from 'library'
ES_IMPORT_PATTERN = re.compile(
    r"import\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)

# CommonJS require: const x = require('library') or const { a } = require('library')
COMMONJS_PATTERN = re.compile(
    r"(?:const|let|var)\s+(?:(\w+)|{([^}]+)})\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.MULTILINE,
)


def find_imports(content: str, library: str) -> set[str]:
    """Find all function names imported from a library.

    Args:
        content: JavaScript/TypeScript source code
        library: The library name to search for

    Returns:
        Set of imported function names
    """
    imports = set()

    # Check ES module imports
    for match in ES_IMPORT_PATTERN.finditer(content):
        import_names = match.group(1)
        from_lib = match.group(2)

        if from_lib == library or from_lib.startswith(f"{library}/"):
            # Parse the imported names
            for name in import_names.split(","):
                name = name.strip()
                # Handle "original as alias" syntax
                if " as " in name:
                    name = name.split(" as ")[0].strip()
                if name:
                    imports.add(name)

    # Check CommonJS requires
    for match in COMMONJS_PATTERN.finditer(content):
        default_import = match.group(1)
        destructured = match.group(2)
        from_lib = match.group(3)

        if from_lib == library or from_lib.startswith(f"{library}/"):
            if default_import:
                imports.add(default_import)
            if destructured:
                for name in destructured.split(","):
                    name = name.strip()
                    if " as " in name:
                        name = name.split(" as ")[0].strip()
                    if name:
                        imports.add(name)

    logger.info(f"Found {len(imports)} imports from {library}: {imports}")
    return imports


def find_call_sites(
    content: str,
    function_names: set[str],
    file_path: str,
) -> list[CallSite]:
    """Find call sites for specific functions.

    Args:
        content: JavaScript/TypeScript source code
        function_names: Set of function names to find
        file_path: Path to the source file (for location tracking)

    Returns:
        List of CallSite objects
    """
    call_sites = []
    lines = content.split("\n")

    for func_name in function_names:
        # Pattern to match function call: funcName(...)
        # This is simplified - a real parser would handle nested parens better
        call_pattern = re.compile(
            rf"\b{re.escape(func_name)}\s*\(([^)]*(?:\([^)]*\)[^)]*)*)\)",
            re.MULTILINE,
        )

        for line_num, line in enumerate(lines, start=1):
            for match in call_pattern.finditer(line):
                args_str = match.group(1)
                arguments = _parse_arguments(args_str)

                # Determine if args are static (literals or simple lambdas)
                has_static = _are_args_static(arguments)

                call_site = CallSite(
                    function_name=func_name,
                    file_path=file_path,
                    line_number=line_num,
                    arguments=arguments,
                    has_static_args=has_static,
                )
                call_sites.append(call_site)
                logger.debug(f"Found call: {func_name} at {file_path}:{line_num}")

    logger.info(f"Found {len(call_sites)} call sites in {file_path}")
    return call_sites


def _parse_arguments(args_str: str) -> list[str]:
    """Parse argument string into individual arguments.

    Handles nested structures and arrow functions.
    """
    if not args_str.strip():
        return []

    arguments = []
    current = ""
    depth = 0
    in_string = False
    string_char = None

    for char in args_str:
        if in_string:
            current += char
            if char == string_char and current[-2:] != f"\\{char}":
                in_string = False
        elif char in "\"'`":
            in_string = True
            string_char = char
            current += char
        elif char in "([{":
            depth += 1
            current += char
        elif char in ")]}":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            if current.strip():
                arguments.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        arguments.append(current.strip())

    return arguments


def _are_args_static(arguments: list[str]) -> bool:
    """Check if all arguments are static (literals or simple lambdas)."""
    for arg in arguments:
        arg = arg.strip()
        # Skip empty args
        if not arg:
            continue
        # String literals
        if arg.startswith(("'", '"', "`")):
            continue
        # Number literals
        if re.match(r"^-?\d+\.?\d*$", arg):
            continue
        # Boolean/null literals
        if arg in ("true", "false", "null", "undefined"):
            continue
        # Array literals
        if arg.startswith("[") and arg.endswith("]"):
            continue
        # Object literals
        if arg.startswith("{") and arg.endswith("}"):
            continue
        # Simple arrow functions (single expression)
        if "=>" in arg and "{" not in arg:
            continue
        # Variable reference - not static
        return False

    return True


def detect_usage(
    source_dir: Path,
    library: str,
    extensions: tuple[str, ...] = (".js", ".ts", ".jsx", ".tsx"),
) -> list[CallSite]:
    """Detect all usage of a library in a source directory.

    Args:
        source_dir: Directory to search
        library: Library name to find
        extensions: File extensions to search

    Returns:
        List of CallSite objects
    """
    all_call_sites = []

    for file_path in source_dir.rglob("*"):
        if file_path.suffix not in extensions:
            continue
        if "node_modules" in str(file_path):
            continue

        try:
            content = file_path.read_text()
            imports = find_imports(content, library)
            if imports:
                call_sites = find_call_sites(content, imports, str(file_path))
                all_call_sites.extend(call_sites)
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

    logger.info(f"Found {len(all_call_sites)} total call sites for {library}")
    return all_call_sites
