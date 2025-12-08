# Functional API Tester Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate regression tests for a JavaScript library's functional APIs before an upgrade.

**Architecture:** New `js_interaction_detector/functional_tester/` module with four components: type parser, usage detector, instrumentation generator, and test generator. CLI gets a new `functional` subcommand.

**Tech Stack:** Python 3.14+, TypeScript parser (tree-sitter-typescript or regex-based for v1), Jest output format.

---

## Test List (TDD Starting Point)

### Phase 1: Type Definition Parsing
- [ ] Parse simple function signature from .d.ts
- [ ] Parse function with multiple parameters
- [ ] Parse function with generic types
- [ ] Parse exported const/class with methods
- [ ] Handle @types package structure
- [ ] Handle bundled .d.ts in library package

### Phase 2: Usage Detection
- [ ] Find ES module import: `import { fn } from 'lib'`
- [ ] Find CommonJS require: `const lib = require('lib')`
- [ ] Find destructured require: `const { fn } = require('lib')`
- [ ] Find call sites of imported functions
- [ ] Extract static literal arguments
- [ ] Extract simple lambda arguments
- [ ] Track call site location (file:line)

### Phase 3: Instrumentation Generation
- [ ] Generate wrapper for single function
- [ ] Wrapper captures inputs and outputs
- [ ] Wrapper outputs executable test code
- [ ] Handle serializable inputs (primitives, objects, arrays)
- [ ] Handle simple lambdas (inline arrow functions)
- [ ] Skip non-serializable inputs with placeholder

### Phase 4: Test Generation
- [ ] Generate complete Jest test from captured data
- [ ] Generate failing test for incomplete captures
- [ ] Failure message includes location and usage info
- [ ] Deduplicate similar test cases
- [ ] Organize tests in single file per library

---

## Task 1: Create Module Structure

**Files:**
- Create: `js_interaction_detector/functional_tester/__init__.py`
- Create: `js_interaction_detector/functional_tester/models.py`
- Create: `tests/test_functional_tester/__init__.py`

**Step 1: Create the module directories and init files**

```python
# js_interaction_detector/functional_tester/__init__.py
"""Functional API tester for JavaScript library upgrades."""

from js_interaction_detector.functional_tester.models import (
    FunctionSignature,
    CallSite,
    CapturedCall,
)

__all__ = [
    "FunctionSignature",
    "CallSite",
    "CapturedCall",
]
```

```python
# js_interaction_detector/functional_tester/models.py
"""Data models for functional API testing."""

from dataclasses import dataclass, field


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
```

```python
# tests/test_functional_tester/__init__.py
"""Tests for functional API tester."""
```

**Step 2: Run tests to verify module imports work**

Run: `python -c "from js_interaction_detector.functional_tester import FunctionSignature, CallSite, CapturedCall; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add js_interaction_detector/functional_tester/ tests/test_functional_tester/
git commit -m "feat: add functional_tester module structure and models"
```

---

## Task 2: Type Definition Parser - Simple Functions

**Files:**
- Create: `js_interaction_detector/functional_tester/type_parser.py`
- Create: `tests/test_functional_tester/test_type_parser.py`
- Create: `tests/fixtures/type_definitions/simple.d.ts`

**Step 1: Create test fixture**

```typescript
// tests/fixtures/type_definitions/simple.d.ts
export function greet(name: string): string;
export function add(a: number, b: number): number;
export function identity<T>(value: T): T;
```

**Step 2: Write failing test for simple function parsing**

```python
# tests/test_functional_tester/test_type_parser.py
"""Tests for TypeScript definition parser."""

from pathlib import Path

import pytest

from js_interaction_detector.functional_tester.type_parser import parse_dts_file
from js_interaction_detector.functional_tester.models import FunctionSignature


@pytest.fixture
def fixtures_path():
    """Path to test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "type_definitions"


class TestParseDtsFile:
    """Tests for parse_dts_file function."""

    def test_parses_simple_function(self, fixtures_path):
        """Parses a simple function with one parameter."""
        dts_path = fixtures_path / "simple.d.ts"

        signatures = parse_dts_file(dts_path)

        greet = next((s for s in signatures if s.name == "greet"), None)
        assert greet is not None
        assert greet.parameters == [("name", "string")]
        assert greet.return_type == "string"

    def test_parses_function_with_multiple_params(self, fixtures_path):
        """Parses a function with multiple parameters."""
        dts_path = fixtures_path / "simple.d.ts"

        signatures = parse_dts_file(dts_path)

        add = next((s for s in signatures if s.name == "add"), None)
        assert add is not None
        assert add.parameters == [("a", "number"), ("b", "number")]
        assert add.return_type == "number"

    def test_parses_generic_function(self, fixtures_path):
        """Parses a generic function."""
        dts_path = fixtures_path / "simple.d.ts"

        signatures = parse_dts_file(dts_path)

        identity = next((s for s in signatures if s.name == "identity"), None)
        assert identity is not None
        assert identity.parameters == [("value", "T")]
        assert identity.return_type == "T"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_functional_tester/test_type_parser.py -v`
Expected: FAIL with "cannot import name 'parse_dts_file'"

**Step 4: Write minimal implementation**

```python
# js_interaction_detector/functional_tester/type_parser.py
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_functional_tester/test_type_parser.py -v`
Expected: All 3 tests PASS

**Step 6: Update module __init__.py**

```python
# js_interaction_detector/functional_tester/__init__.py
"""Functional API tester for JavaScript library upgrades."""

from js_interaction_detector.functional_tester.models import (
    CapturedCall,
    CallSite,
    FunctionSignature,
)
from js_interaction_detector.functional_tester.type_parser import (
    parse_dts_content,
    parse_dts_file,
)

__all__ = [
    "FunctionSignature",
    "CallSite",
    "CapturedCall",
    "parse_dts_file",
    "parse_dts_content",
]
```

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add type definition parser for simple functions"
```

---

## Task 3: Usage Detector - ES Module Imports

**Files:**
- Create: `js_interaction_detector/functional_tester/usage_detector.py`
- Create: `tests/test_functional_tester/test_usage_detector.py`
- Create: `tests/fixtures/sample_js/lodash_usage.js`

**Step 1: Create test fixture**

```javascript
// tests/fixtures/sample_js/lodash_usage.js
import { groupBy, map } from 'lodash';

const users = [
  { name: 'Alice', age: 30 },
  { name: 'Bob', age: 30 },
];

const byAge = groupBy(users, 'age');
const names = map(users, u => u.name);
const doubled = map([1, 2, 3], x => x * 2);
```

**Step 2: Write failing test for import detection**

```python
# tests/test_functional_tester/test_usage_detector.py
"""Tests for JavaScript usage detector."""

from pathlib import Path

import pytest

from js_interaction_detector.functional_tester.usage_detector import (
    find_imports,
    find_call_sites,
    detect_usage,
)
from js_interaction_detector.functional_tester.models import CallSite


@pytest.fixture
def fixtures_path():
    """Path to test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "sample_js"


class TestFindImports:
    """Tests for find_imports function."""

    def test_finds_es_module_named_imports(self, fixtures_path):
        """Finds named imports from ES modules."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        imports = find_imports(content, "lodash")

        assert "groupBy" in imports
        assert "map" in imports

    def test_returns_empty_for_no_imports(self, fixtures_path):
        """Returns empty set when library is not imported."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        imports = find_imports(content, "react")

        assert imports == set()


class TestFindCallSites:
    """Tests for find_call_sites function."""

    def test_finds_call_sites_with_literal_args(self, fixtures_path):
        """Finds call sites and extracts literal arguments."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        call_sites = find_call_sites(content, {"groupBy", "map"}, str(js_path))

        # Find the groupBy call
        groupby_calls = [c for c in call_sites if c.function_name == "groupBy"]
        assert len(groupby_calls) == 1
        assert groupby_calls[0].arguments[1] == "'age'"

    def test_finds_call_sites_with_lambda_args(self, fixtures_path):
        """Finds call sites with lambda arguments."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        call_sites = find_call_sites(content, {"map"}, str(js_path))

        # Should find two map calls
        map_calls = [c for c in call_sites if c.function_name == "map"]
        assert len(map_calls) == 2

        # One with simple lambda x => x * 2
        doubled_call = next(
            (c for c in map_calls if "x => x * 2" in c.arguments[1]),
            None
        )
        assert doubled_call is not None
        assert doubled_call.has_static_args is True

    def test_tracks_line_numbers(self, fixtures_path):
        """Tracks line numbers for call sites."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        call_sites = find_call_sites(content, {"groupBy"}, str(js_path))

        assert len(call_sites) == 1
        assert call_sites[0].line_number > 0
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_functional_tester/test_usage_detector.py -v`
Expected: FAIL with "cannot import name 'find_imports'"

**Step 4: Write minimal implementation**

```python
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_functional_tester/test_usage_detector.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add usage detector for ES module and CommonJS imports"
```

---

## Task 4: Test Generator - Complete Tests

**Files:**
- Create: `js_interaction_detector/functional_tester/test_generator.py`
- Create: `tests/test_functional_tester/test_test_generator.py`

**Step 1: Write failing test**

```python
# tests/test_functional_tester/test_test_generator.py
"""Tests for Jest test generator."""

import pytest

from js_interaction_detector.functional_tester.test_generator import (
    generate_test_case,
    generate_test_file,
)
from js_interaction_detector.functional_tester.models import CapturedCall


class TestGenerateTestCase:
    """Tests for generate_test_case function."""

    def test_generates_complete_test(self):
        """Generates a complete test for a captured call."""
        call = CapturedCall(
            function_name="groupBy",
            inputs=['[{"name": "alice", "age": 30}]', '"age"'],
            output='{"30": [{"name": "alice", "age": 30}]}',
            location="src/utils.js:42",
            is_complete=True,
        )

        test_code = generate_test_case(call, "lodash")

        assert "test(" in test_code
        assert "groupBy" in test_code
        assert "expect(" in test_code
        assert "toEqual(" in test_code

    def test_generates_failing_test_for_incomplete(self):
        """Generates a failing test for incomplete captures."""
        call = CapturedCall(
            function_name="map",
            inputs=["users", "processUser"],
            output="",
            location="src/transform.js:87",
            is_complete=False,
            incomplete_reason="Could not capture 'processUser' function body",
        )

        test_code = generate_test_case(call, "lodash")

        assert "test(" in test_code
        assert "throw new Error" in test_code
        assert "src/transform.js:87" in test_code
        assert "processUser" in test_code


class TestGenerateTestFile:
    """Tests for generate_test_file function."""

    def test_generates_valid_jest_structure(self):
        """Generates a valid Jest test file structure."""
        calls = [
            CapturedCall(
                function_name="add",
                inputs=["1", "2"],
                output="3",
                location="src/math.js:10",
                is_complete=True,
            ),
        ]

        test_file = generate_test_file("my-lib", calls)

        assert "import { add } from 'my-lib'" in test_file
        assert "describe('my-lib'" in test_file
        assert "test(" in test_file

    def test_deduplicates_similar_calls(self):
        """Deduplicates calls with same function and similar inputs."""
        calls = [
            CapturedCall(
                function_name="add",
                inputs=["1", "2"],
                output="3",
                location="src/a.js:1",
                is_complete=True,
            ),
            CapturedCall(
                function_name="add",
                inputs=["1", "2"],
                output="3",
                location="src/b.js:2",
                is_complete=True,
            ),
            CapturedCall(
                function_name="add",
                inputs=["5", "10"],
                output="15",
                location="src/c.js:3",
                is_complete=True,
            ),
        ]

        test_file = generate_test_file("my-lib", calls)

        # Should have 2 tests, not 3
        assert test_file.count("test(") == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_functional_tester/test_test_generator.py -v`
Expected: FAIL with "cannot import name 'generate_test_case'"

**Step 3: Write minimal implementation**

```python
# js_interaction_detector/functional_tester/test_generator.py
"""Generate Jest tests from captured function calls."""

import logging
from collections import defaultdict

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
Issue: {call.incomplete_reason or 'Unknown'}
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
    function_names = sorted(set(c.function_name for c in unique_calls))
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_functional_tester/test_test_generator.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Jest test generator for captured calls"
```

---

## Task 5: Instrumentation Generator

**Files:**
- Create: `js_interaction_detector/functional_tester/instrumentation.py`
- Create: `tests/test_functional_tester/test_instrumentation.py`

**Step 1: Write failing test**

```python
# tests/test_functional_tester/test_instrumentation.py
"""Tests for instrumentation code generator."""

import pytest

from js_interaction_detector.functional_tester.instrumentation import (
    generate_wrapper,
    generate_instrumentation_script,
)


class TestGenerateWrapper:
    """Tests for generate_wrapper function."""

    def test_generates_wrapper_that_captures_calls(self):
        """Generates a wrapper function that captures inputs and outputs."""
        wrapper = generate_wrapper("groupBy", "lodash")

        assert "groupBy" in wrapper
        assert "JSON.stringify" in wrapper
        assert "console.log" in wrapper

    def test_wrapper_outputs_test_code(self):
        """Wrapper outputs executable test code."""
        wrapper = generate_wrapper("add", "mylib")

        # Should output expect/toEqual format
        assert "expect(" in wrapper
        assert "toEqual(" in wrapper


class TestGenerateInstrumentationScript:
    """Tests for generate_instrumentation_script function."""

    def test_generates_script_for_multiple_functions(self):
        """Generates instrumentation for multiple functions."""
        functions = ["map", "filter", "reduce"]
        script = generate_instrumentation_script("lodash", functions)

        assert "map" in script
        assert "filter" in script
        assert "reduce" in script

    def test_script_is_self_contained(self):
        """Script can be injected without dependencies."""
        functions = ["add"]
        script = generate_instrumentation_script("mathlib", functions)

        # Should wrap the original function
        assert "original" in script.lower() or "orig" in script.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_functional_tester/test_instrumentation.py -v`
Expected: FAIL with "cannot import name 'generate_wrapper'"

**Step 3: Write minimal implementation**

```python
# js_interaction_detector/functional_tester/instrumentation.py
"""Generate instrumentation code to capture function calls at runtime."""

import logging

logger = logging.getLogger(__name__)


def generate_wrapper(function_name: str, library: str) -> str:
    """Generate a wrapper function that captures inputs/outputs.

    The wrapper logs executable test code to the console.

    Args:
        function_name: Name of the function to wrap
        library: The library name

    Returns:
        JavaScript code for the wrapper
    """
    return f"""
(function() {{
  const originalFn = {function_name};
  {function_name} = function(...args) {{
    const result = originalFn.apply(this, args);

    try {{
      const serializedArgs = args.map(arg => {{
        if (typeof arg === 'function') {{
          // Try to capture simple arrow functions
          const fnStr = arg.toString();
          if (fnStr.includes('=>') && !fnStr.includes('{{')) {{
            return fnStr;
          }}
          return '/* function: ' + (arg.name || 'anonymous') + ' */';
        }}
        return JSON.stringify(arg);
      }});

      const serializedResult = JSON.stringify(result);
      const argsStr = serializedArgs.join(', ');

      console.log('// Test captured from runtime:');
      console.log(`expect({function_name}(${{argsStr}})).toEqual(${{serializedResult}});`);
    }} catch (e) {{
      console.log('// Could not serialize call to {function_name}:', e.message);
    }}

    return result;
  }};
}})();
"""


def generate_instrumentation_script(
    library: str,
    function_names: list[str],
) -> str:
    """Generate a complete instrumentation script for multiple functions.

    Args:
        library: The library name
        function_names: List of function names to instrument

    Returns:
        JavaScript code that can be injected into a page
    """
    logger.info(f"Generating instrumentation for {len(function_names)} functions")

    wrappers = []
    for fn in function_names:
        wrappers.append(generate_wrapper(fn, library))

    header = f"""
// Instrumentation for {library}
// Paste this into your browser console or inject into your dev environment
// Then interact with your app - test code will be logged to the console

console.log('=== {library} Instrumentation Active ===');
console.log('Interact with your app. Test code will appear below.');
console.log('');
"""

    return header + "\n".join(wrappers)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_functional_tester/test_instrumentation.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add instrumentation generator for runtime capture"
```

---

## Task 6: CLI Integration

**Files:**
- Modify: `js_interaction_detector/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing test**

Add to `tests/test_cli.py`:

```python
class TestFunctionalCommand:
    """Tests for the functional API testing command."""

    @pytest.fixture
    def sample_js_dir(self, tmp_path):
        """Create a sample JS directory with lodash usage."""
        js_file = tmp_path / "src" / "utils.js"
        js_file.parent.mkdir(parents=True)
        js_file.write_text("""
import { groupBy } from 'lodash';

const users = [{ name: 'alice', age: 30 }];
const byAge = groupBy(users, 'age');
""")
        return tmp_path

    @pytest.mark.asyncio
    async def test_functional_analyze_finds_usage(self, sample_js_dir, capsys):
        """functional analyze command finds library usage."""
        from js_interaction_detector.cli import run_cli

        exit_code = await run_cli([
            "functional", "analyze",
            "--library", "lodash",
            "--source", str(sample_js_dir / "src"),
        ])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "groupBy" in captured.err  # Summary goes to stderr
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::TestFunctionalCommand -v`
Expected: FAIL

**Step 3: Add functional subcommand to CLI**

Add to `js_interaction_detector/cli.py` in `create_parser()`:

```python
    # functional subcommand group
    functional_parser = subparsers.add_parser(
        "functional",
        help="Analyze and test functional library APIs",
    )
    functional_subparsers = functional_parser.add_subparsers(
        dest="functional_command",
        help="Functional testing commands",
    )

    # functional analyze
    func_analyze = functional_subparsers.add_parser(
        "analyze",
        help="Analyze source code for library usage",
    )
    func_analyze.add_argument(
        "--library", "-l",
        required=True,
        help="Library name to analyze (e.g., 'lodash')",
    )
    func_analyze.add_argument(
        "--source", "-s",
        required=True,
        help="Source directory to analyze",
    )
    func_analyze.add_argument(
        "--output", "-o",
        default="./instrumentation.js",
        help="Output path for instrumentation script",
    )
```

Add the handler function:

```python
async def run_functional_analyze(library: str, source: str, output: str) -> int:
    """Run the functional analyze command.

    Args:
        library: Library name to analyze
        source: Source directory path
        output: Output path for instrumentation script

    Returns:
        Exit code
    """
    from pathlib import Path

    from js_interaction_detector.functional_tester.usage_detector import detect_usage
    from js_interaction_detector.functional_tester.instrumentation import (
        generate_instrumentation_script,
    )

    source_path = Path(source)
    if not source_path.exists():
        print(f"Error: Source directory not found: {source}", file=sys.stderr)
        return 1

    print(f"Analyzing {source} for {library} usage...", file=sys.stderr)

    # Detect usage
    call_sites = detect_usage(source_path, library)

    if not call_sites:
        print(f"No usage of {library} found in {source}", file=sys.stderr)
        return 0

    # Summarize findings
    function_names = sorted(set(cs.function_name for cs in call_sites))
    print(f"\nFound {len(call_sites)} call sites:", file=sys.stderr)
    for fn in function_names:
        count = sum(1 for cs in call_sites if cs.function_name == fn)
        print(f"  - {fn}: {count} calls", file=sys.stderr)

    # Count static vs dynamic
    static_count = sum(1 for cs in call_sites if cs.has_static_args)
    dynamic_count = len(call_sites) - static_count
    print(f"\nStatic arguments: {static_count}", file=sys.stderr)
    print(f"Dynamic arguments: {dynamic_count}", file=sys.stderr)

    # Generate instrumentation script
    script = generate_instrumentation_script(library, function_names)
    with open(output, "w") as f:
        f.write(script)

    print(f"\nInstrumentation script written to: {output}", file=sys.stderr)
    print("Inject this into your dev environment to capture runtime values.", file=sys.stderr)

    return 0
```

Add to the command dispatcher in `run_cli()`:

```python
    elif parsed.command == "functional":
        if parsed.functional_command == "analyze":
            return await run_functional_analyze(
                parsed.library, parsed.source, parsed.output
            )
        else:
            print("Unknown functional command", file=sys.stderr)
            return 1
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::TestFunctionalCommand -v`
Expected: PASS

**Step 5: Run all tests**

Run: `pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add functional analyze CLI command"
```

---

## Task 7: Update Module Exports and Documentation

**Files:**
- Modify: `js_interaction_detector/functional_tester/__init__.py`
- Modify: `README.md`

**Step 1: Update module __init__.py with all exports**

```python
# js_interaction_detector/functional_tester/__init__.py
"""Functional API tester for JavaScript library upgrades."""

from js_interaction_detector.functional_tester.models import (
    CapturedCall,
    CallSite,
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
from js_interaction_detector.functional_tester.instrumentation import (
    generate_instrumentation_script,
    generate_wrapper,
)
from js_interaction_detector.functional_tester.test_generator import (
    generate_test_case,
    generate_test_file,
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
```

**Step 2: Add documentation to README**

Add to `README.md` after the enumerate section:

```markdown
### Analyze Library Usage (Functional APIs)

Analyze your source code for library usage and generate tests:

```bash
python -m js_interaction_detector functional analyze --library lodash --source ./src
```

This:
1. Scans your source for imports and calls to the specified library
2. Reports which functions are used and how often
3. Generates an instrumentation script to capture runtime values

To capture runtime values:
1. Inject the generated `instrumentation.js` into your dev environment
2. Use your app normally, triggering the library calls
3. Copy the test code from the browser console
4. Paste into your test file

Options:
- `--library`, `-l` - Library name to analyze (required)
- `--source`, `-s` - Source directory to scan (required)
- `--output`, `-o` - Output path for instrumentation script (default: `./instrumentation.js`)

**Note:** This is Tool A of the functional API tester - it focuses on pure functions with input/output relationships. Tool B (side-effect APIs) is planned for a future release.
```

**Step 3: Run linting**

Run: `ruff check . && ruff format .`
Expected: No errors

**Step 4: Commit**

```bash
git add -A
git commit -m "docs: add functional API tester documentation and exports"
```

---

## Summary

This plan implements the core of Tool A (Functional API Tester) with:

1. **Type Definition Parser** - Parses `.d.ts` files to understand library APIs
2. **Usage Detector** - Finds library imports and call sites in source code
3. **Instrumentation Generator** - Creates JavaScript to capture runtime values
4. **Test Generator** - Produces Jest tests from captured data
5. **CLI Integration** - `functional analyze` command

### What's Deferred to Future Tasks

- Fetching types from npm (`@types/xxx`)
- Documentation scraping
- `functional generate` command (to create tests from captured traces)
- More sophisticated deduplication
- CommonJS default import handling (e.g., `const _ = require('lodash')`)

### Test Commands

Run all tests:
```bash
pytest -v
```

Run only functional tester tests:
```bash
pytest tests/test_functional_tester/ -v
```
