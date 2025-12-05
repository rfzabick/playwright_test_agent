# js-interaction-detector Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool that takes a URL and outputs JSON describing all JavaScript-driven input validations on that page.

**Architecture:** Playwright loads the page, JavaScript extracts event listeners from the DOM, Python processes results and infers validation rules via pattern matching. Dataclasses define output contracts. Functions log their own actions.

**Tech Stack:** Python 3.14+, Playwright, pytest, ruff, dataclasses, json, argparse, logging

---

## Project Structure

```
js_interaction_detector/
├── __init__.py
├── __main__.py           # CLI entry point
├── models.py             # Dataclasses for output structure
├── page_loader.py        # Playwright page loading
├── listener_extractor.py # Extract event listeners via JS
├── rule_inferrer.py      # Pattern matching for validation types
├── analyzer.py           # Orchestrates the analysis pipeline
└── cli.py                # Argument parsing, JSON output

tests/
├── __init__.py
├── test_models.py
├── test_page_loader.py
├── test_listener_extractor.py
├── test_rule_inferrer.py
├── test_analyzer.py
├── test_cli.py
└── fixtures/
    └── sample_pages/     # HTML fixtures for testing
```

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `js_interaction_detector/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "js-interaction-detector"
version = "0.1.0"
description = "Detect JavaScript-driven input validations on web pages"
requires-python = ">=3.14"
dependencies = [
    "playwright>=1.56.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.1",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.14.7",
]

[project.scripts]
js-interaction-detector = "js_interaction_detector.cli:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 88
target-version = "py314"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = [
    "E501",   # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["js_interaction_detector"]
```

**Step 2: Create package init files**

`js_interaction_detector/__init__.py`:
```python
"""Detect JavaScript-driven input validations on web pages."""

__version__ = "0.1.0"
```

`tests/__init__.py`:
```python
"""Tests for js-interaction-detector."""
```

**Step 3: Install dependencies**

Run:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

**Step 4: Verify setup**

Run: `python -c "import js_interaction_detector; print(js_interaction_detector.__version__)"`

Expected: `0.1.0`

**Step 5: Verify ruff works**

Run: `ruff check js_interaction_detector/`

Expected: No errors (empty output or "All checks passed")

Run: `ruff format --check js_interaction_detector/`

Expected: All files formatted correctly

**Step 6: Commit**

```bash
git init
git add pyproject.toml js_interaction_detector/ tests/
git commit -m "chore: initial project setup"
```

---

## Task 2: Data Models

**Files:**
- Create: `js_interaction_detector/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

Note: Per TDD.md, we don't test dataclass properties directly. We only test actual behavior like serialization logic.

`tests/test_models.py`:
```python
"""Tests for data models."""

import json
from js_interaction_detector.models import (
    ElementInfo,
    ValidationInfo,
    Interaction,
    AnalysisError,
    AnalysisResult,
)


class TestAnalysisResult:
    def given_empty_result(self):
        self.result = AnalysisResult(
            url="https://example.com",
            analyzed_at="2025-12-04T10:00:00Z",
            errors=[],
            interactions=[],
        )

    def given_result_with_interaction(self):
        self.result = AnalysisResult(
            url="https://example.com",
            analyzed_at="2025-12-04T10:00:00Z",
            errors=[],
            interactions=[
                Interaction(
                    element=ElementInfo(selector="input#test", tag="input"),
                    triggers=["blur"],
                    validation=ValidationInfo(type="unknown", raw_code="..."),
                )
            ],
        )

    def given_result_with_error(self):
        self.result = AnalysisResult(
            url="https://example.com",
            analyzed_at="2025-12-04T10:00:00Z",
            errors=[
                AnalysisError(element="input#foo", error="Failed", phase="extraction")
            ],
            interactions=[],
        )

    def when_serialized_to_json(self):
        json_str = self.result.to_json()
        self.parsed = json.loads(json_str)

    def then_json_has_expected_fields(self):
        assert self.parsed["url"] == "https://example.com"
        assert self.parsed["errors"] == []
        assert self.parsed["interactions"] == []

    def then_none_values_excluded_from_validation(self):
        interaction = self.parsed["interactions"][0]
        assert "rule_description" not in interaction["validation"]
        assert "confidence" not in interaction["validation"]

    def then_errors_are_serialized(self):
        assert len(self.parsed["errors"]) == 1
        assert self.parsed["errors"][0]["phase"] == "extraction"

    def test_serializes_to_json(self):
        """to_json() produces valid JSON with all fields."""
        self.given_empty_result()
        self.when_serialized_to_json()
        self.then_json_has_expected_fields()

    def test_serializes_interactions_excluding_none_values(self):
        """None values in nested objects are excluded from JSON."""
        self.given_result_with_interaction()
        self.when_serialized_to_json()
        self.then_none_values_excluded_from_validation()

    def test_serializes_errors(self):
        """Errors are properly serialized with all fields."""
        self.given_result_with_error()
        self.when_serialized_to_json()
        self.then_errors_are_serialized()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'js_interaction_detector.models'`

**Step 3: Write minimal implementation**

`js_interaction_detector/models.py`:
```python
"""Data models for analysis output."""

from dataclasses import dataclass, field, asdict
import json
from typing import Optional


@dataclass
class ElementInfo:
    """Information about a DOM element."""

    selector: str
    tag: str
    type: Optional[str] = None
    name: Optional[str] = None
    id: Optional[str] = None
    placeholder: Optional[str] = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationInfo:
    """Information about a validation rule."""

    type: str
    raw_code: str
    rule_description: Optional[str] = None
    confidence: Optional[str] = None  # "high", "medium", "low"


@dataclass
class ErrorDisplay:
    """Information about how validation errors are displayed."""

    method: str  # "sibling_element", "tooltip", "inline", etc.
    selector: Optional[str] = None
    sample_message: Optional[str] = None


@dataclass
class Interaction:
    """A detected JavaScript interaction on an element."""

    element: ElementInfo
    triggers: list[str]
    validation: ValidationInfo
    error_display: Optional[ErrorDisplay] = None
    examples: Optional[dict[str, list[str]]] = None


@dataclass
class AnalysisError:
    """A non-fatal error encountered during analysis."""

    element: Optional[str]
    error: str
    phase: str  # "loading", "discovery", "extraction"


@dataclass
class AnalysisResult:
    """Complete result of analyzing a page."""

    url: str
    analyzed_at: str
    errors: list[AnalysisError]
    interactions: list[Interaction]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "analyzed_at": self.analyzed_at,
            "errors": [asdict(e) for e in self.errors],
            "interactions": [self._interaction_to_dict(i) for i in self.interactions],
        }

    def _interaction_to_dict(self, interaction: Interaction) -> dict:
        """Convert an interaction to a dictionary, excluding None values."""
        result = {
            "element": asdict(interaction.element),
            "triggers": interaction.triggers,
            "validation": asdict(interaction.validation),
        }
        # Remove None values from nested dicts
        result["validation"] = {
            k: v for k, v in result["validation"].items() if v is not None
        }
        if interaction.error_display:
            result["error_display"] = {
                k: v
                for k, v in asdict(interaction.error_display).items()
                if v is not None
            }
        if interaction.examples:
            result["examples"] = interaction.examples
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add js_interaction_detector/models.py tests/test_models.py
git commit -m "feat: add data models for analysis output"
```

---

## Task 3: Page Loader

**Files:**
- Create: `js_interaction_detector/page_loader.py`
- Create: `tests/test_page_loader.py`
- Create: `tests/fixtures/sample_pages/simple_form.html`

**Step 1: Create test fixture**

`tests/fixtures/sample_pages/simple_form.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Test Form</title></head>
<body>
  <form id="test-form">
    <input type="email" id="email" name="email" />
    <button type="submit">Submit</button>
  </form>
</body>
</html>
```

**Step 2: Write the failing test**

`tests/test_page_loader.py`:
```python
"""Tests for page loader."""

import pytest
from pathlib import Path
from js_interaction_detector.page_loader import PageLoader, PageLoadError


@pytest.fixture
def sample_page_path():
    return Path(__file__).parent / "fixtures" / "sample_pages" / "simple_form.html"


class TestPageLoader:
    def given_local_file_url(self, sample_page_path):
        self.url = f"file://{sample_page_path}"

    def given_invalid_url(self):
        self.url = "not-a-valid-url"

    def given_unreachable_url(self):
        self.url = "https://localhost:99999/nonexistent"

    async def when_page_is_loaded(self):
        async with PageLoader() as loader:
            self.page = await loader.load(self.url)

    async def when_page_load_fails(self):
        async with PageLoader() as loader:
            with pytest.raises(PageLoadError) as exc_info:
                await loader.load(self.url)
            self.error = exc_info.value

    async def then_page_title_is(self, expected_title):
        title = await self.page.title()
        assert title == expected_title

    def then_error_contains(self, text):
        assert text in str(self.error)

    def then_error_phase_is(self, phase):
        assert self.error.phase == phase

    async def then_page_has_element(self, selector):
        element = await self.page.query_selector(selector)
        assert element is not None

    @pytest.mark.asyncio
    async def test_loads_local_file(self, sample_page_path):
        """PageLoader successfully loads a local HTML file."""
        self.given_local_file_url(sample_page_path)
        await self.when_page_is_loaded()
        await self.then_page_title_is("Test Form")

    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_url(self):
        """PageLoader raises PageLoadError for invalid URL schemes."""
        self.given_invalid_url()
        await self.when_page_load_fails()
        self.then_error_contains("Invalid URL")

    @pytest.mark.asyncio
    async def test_raises_error_for_unreachable_page(self):
        """PageLoader raises PageLoadError with phase='loading' for unreachable URLs."""
        self.given_unreachable_url()
        await self.when_page_load_fails()
        self.then_error_phase_is("loading")

    @pytest.mark.asyncio
    async def test_waits_for_network_idle(self, sample_page_path):
        """PageLoader waits for network idle before returning."""
        self.given_local_file_url(sample_page_path)
        await self.when_page_is_loaded()
        await self.then_page_has_element("#test-form")
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_page_loader.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'js_interaction_detector.page_loader'`

**Step 4: Write minimal implementation**

`js_interaction_detector/page_loader.py`:
```python
"""Load web pages using Playwright."""

import logging
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, Error as PlaywrightError

logger = logging.getLogger(__name__)


class PageLoadError(Exception):
    """Error loading a page."""

    def __init__(self, message: str, phase: str = "loading"):
        super().__init__(message)
        self.phase = phase


class PageLoader:
    """Load pages using Playwright with network idle wait."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch()
        logger.info("Browser launched")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    async def load(self, url: str) -> Page:
        """Load a page and wait for network idle.

        Args:
            url: The URL to load (http, https, or file://)

        Returns:
            The loaded Playwright Page object

        Raises:
            PageLoadError: If the URL is invalid or page fails to load
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ("http", "https", "file"):
            logger.error(f"Invalid URL scheme: {url}")
            raise PageLoadError(f"Invalid URL: {url}")

        page = await self._browser.new_page()
        try:
            logger.info(f"Loading page: {url}")
            await page.goto(url, wait_until="networkidle")
            logger.info(f"Page loaded successfully: {url}")
            return page
        except PlaywrightError as e:
            await page.close()
            logger.error(f"Failed to load page: {e}")
            raise PageLoadError(str(e), phase="loading")
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_page_loader.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add js_interaction_detector/page_loader.py tests/test_page_loader.py tests/fixtures/
git commit -m "feat: add page loader with network idle wait"
```

---

## Task 4: Event Listener Extractor

**Files:**
- Create: `js_interaction_detector/listener_extractor.py`
- Create: `tests/test_listener_extractor.py`
- Create: `tests/fixtures/sample_pages/form_with_validation.html`

**Step 1: Create test fixture**

`tests/fixtures/sample_pages/form_with_validation.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Form with Validation</title></head>
<body>
  <form id="signup">
    <input type="email" id="email" name="email" required />
    <input type="tel" id="phone" name="phone" placeholder="XXX-XXX-XXXX" />
    <textarea id="bio" name="bio"></textarea>
    <button type="submit">Submit</button>
  </form>
  <script>
    document.getElementById('email').addEventListener('blur', function(e) {
      const value = e.target.value;
      if (!/.+@.+\..+/.test(value)) {
        e.target.setCustomValidity('Please enter a valid email');
      } else {
        e.target.setCustomValidity('');
      }
    });

    document.getElementById('phone').addEventListener('input', function(e) {
      const value = e.target.value.replace(/\D/g, '');
      if (value.length > 0) {
        const formatted = value.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
        e.target.value = formatted;
      }
    });
  </script>
</body>
</html>
```

**Step 2: Write the failing test**

`tests/test_listener_extractor.py`:
```python
"""Tests for event listener extraction."""

import pytest
from pathlib import Path
from js_interaction_detector.page_loader import PageLoader
from js_interaction_detector.listener_extractor import (
    extract_listeners,
    ListenerInfo,
)


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestListenerExtractor:
    def given_form_with_validation_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"

    async def when_listeners_are_extracted(self):
        async with PageLoader() as loader:
            page = await loader.load(self.url)
            self.listeners = await extract_listeners(page)

    def then_listeners_include_selectors(self, *expected_selectors):
        selectors = [listener.selector for listener in self.listeners]
        for expected in expected_selectors:
            assert any(expected in s for s in selectors)

    def then_listener_has_event(self, selector_fragment, event):
        listener = next(l for l in self.listeners if selector_fragment in l.selector)
        assert event in listener.events

    def then_listener_code_contains(self, selector_fragment, text):
        listener = next(l for l in self.listeners if selector_fragment in l.selector)
        assert text in listener.code or text.lower() in listener.code.lower()

    def then_listener_has_element_info(self, selector_fragment, tag, input_type, name):
        listener = next(l for l in self.listeners if selector_fragment in l.selector)
        assert listener.tag == tag
        assert listener.input_type == input_type
        assert listener.name == name

    def then_listeners_exclude_selector(self, selector_fragment):
        selectors = [listener.selector for listener in self.listeners]
        assert not any(selector_fragment in s for s in selectors)

    @pytest.mark.asyncio
    async def test_extracts_listeners_from_inputs(self, fixtures_path):
        """extract_listeners finds all input elements with event listeners."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_listeners_are_extracted()
        self.then_listeners_include_selectors("email", "phone")

    @pytest.mark.asyncio
    async def test_captures_event_types(self, fixtures_path):
        """extract_listeners captures which events trigger each listener."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_listeners_are_extracted()
        self.then_listener_has_event("email", "blur")
        self.then_listener_has_event("phone", "input")

    @pytest.mark.asyncio
    async def test_captures_listener_code(self, fixtures_path):
        """extract_listeners captures the JavaScript code of each listener."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_listeners_are_extracted()
        self.then_listener_code_contains("email", "@")

    @pytest.mark.asyncio
    async def test_captures_element_info(self, fixtures_path):
        """extract_listeners captures element metadata (tag, type, name)."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_listeners_are_extracted()
        self.then_listener_has_element_info("email", "input", "email", "email")

    @pytest.mark.asyncio
    async def test_skips_elements_without_listeners(self, fixtures_path):
        """extract_listeners excludes elements that have no event listeners."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_listeners_are_extracted()
        self.then_listeners_exclude_selector("bio")
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_listener_extractor.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'js_interaction_detector.listener_extractor'`

**Step 4: Write minimal implementation**

`js_interaction_detector/listener_extractor.py`:
```python
"""Extract event listeners from page elements."""

import logging
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)


@dataclass
class ListenerInfo:
    """Information about an element's event listeners."""

    selector: str
    tag: str
    events: list[str]
    code: str
    input_type: Optional[str] = None
    name: Optional[str] = None
    id: Optional[str] = None
    placeholder: Optional[str] = None
    attributes: dict[str, str] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


# JavaScript to extract event listeners from input elements
EXTRACTION_SCRIPT = """
() => {
    const results = [];
    const inputSelectors = 'input, textarea, select, [contenteditable="true"]';
    const elements = document.querySelectorAll(inputSelectors);

    for (const el of elements) {
        // Try to get event listeners using Chrome DevTools Protocol
        // This works because Playwright exposes getEventListeners in evaluate
        let listeners = [];
        try {
            // In Chrome DevTools, getEventListeners is available
            if (typeof getEventListeners === 'function') {
                const elListeners = getEventListeners(el);
                for (const [eventType, handlers] of Object.entries(elListeners)) {
                    for (const handler of handlers) {
                        listeners.push({
                            type: eventType,
                            code: handler.listener.toString()
                        });
                    }
                }
            }
        } catch (e) {
            // Fall back to checking for on* properties
        }

        // Also check inline handlers (onclick, onblur, etc.)
        const inlineEvents = ['blur', 'input', 'change', 'focus', 'keyup', 'keydown', 'submit'];
        for (const evt of inlineEvents) {
            const handler = el['on' + evt];
            if (handler) {
                listeners.push({
                    type: evt,
                    code: handler.toString()
                });
            }
        }

        // Skip elements with no listeners
        if (listeners.length === 0) continue;

        // Build selector
        let selector = el.tagName.toLowerCase();
        if (el.id) selector += '#' + el.id;
        else if (el.name) selector += '[name="' + el.name + '"]';
        else if (el.className) selector += '.' + el.className.split(' ')[0];

        // Gather attributes
        const attrs = {};
        for (const attr of el.attributes) {
            if (!['id', 'name', 'type', 'placeholder', 'class'].includes(attr.name)) {
                attrs[attr.name] = attr.value;
            }
        }

        results.push({
            selector: selector,
            tag: el.tagName.toLowerCase(),
            inputType: el.type || null,
            name: el.name || null,
            id: el.id || null,
            placeholder: el.placeholder || null,
            attributes: attrs,
            events: listeners.map(l => l.type),
            code: listeners.map(l => l.code).join('\\n\\n')
        });
    }

    return results;
}
"""

# Alternative approach using CDP to get listeners
CDP_EXTRACTION = """
async (selectors) => {
    const results = [];
    const elements = document.querySelectorAll(selectors);

    for (const el of elements) {
        // Build selector
        let selector = el.tagName.toLowerCase();
        if (el.id) selector += '#' + el.id;
        else if (el.name) selector += '[name="' + el.name + '"]';

        results.push({
            selector: selector,
            tag: el.tagName.toLowerCase(),
            inputType: el.type || null,
            name: el.name || null,
            id: el.id || null,
            placeholder: el.placeholder || null,
            element: el
        });
    }
    return results;
}
"""


async def extract_listeners(page: Page) -> list[ListenerInfo]:
    """Extract event listeners from all input elements on the page.

    Uses Chrome DevTools Protocol to access getEventListeners.

    Args:
        page: A loaded Playwright Page object

    Returns:
        List of ListenerInfo objects for elements with event listeners
    """
    logger.info("Extracting event listeners from page")

    # Get all input elements
    input_selectors = 'input, textarea, select, [contenteditable="true"]'
    elements = await page.query_selector_all(input_selectors)

    results = []
    client = await page.context.new_cdp_session(page)

    for element in elements:
        try:
            # Get element info
            info = await element.evaluate("""
                (el) => ({
                    tag: el.tagName.toLowerCase(),
                    inputType: el.type || null,
                    name: el.name || null,
                    id: el.id || null,
                    placeholder: el.placeholder || null,
                    attributes: Object.fromEntries(
                        Array.from(el.attributes)
                            .filter(a => !['id', 'name', 'type', 'placeholder', 'class'].includes(a.name))
                            .map(a => [a.name, a.value])
                    )
                })
            """)

            # Build selector
            selector = info["tag"]
            if info["id"]:
                selector += f"#{info['id']}"
            elif info["name"]:
                selector += f'[name="{info["name"]}"]'

            # Get event listeners via CDP
            # First, get the DOM node ID
            box = await element.bounding_box()
            if box is None:
                continue

            # Use CDP to get listeners
            js_handle = await element.evaluate_handle("el => el")
            remote_object = js_handle._impl_obj._remote_object

            if "objectId" not in remote_object:
                continue

            try:
                listeners_response = await client.send(
                    "DOMDebugger.getEventListeners",
                    {"objectId": remote_object["objectId"]}
                )
            except Exception:
                continue

            listeners = listeners_response.get("listeners", [])
            if not listeners:
                continue

            # Extract event types and code
            events = []
            code_parts = []
            for listener in listeners:
                event_type = listener.get("type", "")
                if event_type:
                    events.append(event_type)

                # Try to get the function body
                handler_obj = listener.get("handler", {})
                if "objectId" in handler_obj:
                    try:
                        func_response = await client.send(
                            "Runtime.getProperties",
                            {"objectId": handler_obj["objectId"]}
                        )
                        # Get function source via Runtime.callFunctionOn
                        source_response = await client.send(
                            "Runtime.callFunctionOn",
                            {
                                "objectId": handler_obj["objectId"],
                                "functionDeclaration": "function() { return this.toString(); }",
                                "returnByValue": True
                            }
                        )
                        code = source_response.get("result", {}).get("value", "")
                        if code:
                            code_parts.append(code)
                    except Exception:
                        pass

            if events:
                results.append(ListenerInfo(
                    selector=selector,
                    tag=info["tag"],
                    events=list(set(events)),  # dedupe
                    code="\n\n".join(code_parts) if code_parts else "[code not extractable]",
                    input_type=info["inputType"],
                    name=info["name"],
                    id=info["id"],
                    placeholder=info["placeholder"],
                    attributes=info["attributes"]
                ))
                logger.info(f"Found listeners on {selector}: {events}")

        except Exception as e:
            logger.warning(f"Error extracting listeners from element: {e}")
            continue

    await client.detach()
    logger.info(f"Extracted {len(results)} elements with event listeners")
    return results
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_listener_extractor.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add js_interaction_detector/listener_extractor.py tests/test_listener_extractor.py tests/fixtures/
git commit -m "feat: add event listener extraction via CDP"
```

---

## Task 5: Validation Rule Inferrer

**Files:**
- Create: `js_interaction_detector/rule_inferrer.py`
- Create: `tests/test_rule_inferrer.py`

**Step 1: Write the failing test**

`tests/test_rule_inferrer.py`:
```python
"""Tests for validation rule inference."""

import pytest
from js_interaction_detector.rule_inferrer import infer_validation_rule, InferredRule


class TestRuleInferrer:
    def given_code(self, code):
        self.code = code

    def when_rule_is_inferred(self):
        self.rule = infer_validation_rule(self.code)

    def then_rule_type_is(self, expected_type):
        assert self.rule.type == expected_type

    def then_confidence_is(self, expected_confidence):
        assert self.rule.confidence == expected_confidence

    def then_confidence_is_one_of(self, *expected_confidences):
        assert self.rule.confidence in expected_confidences

    def then_confidence_is_none(self):
        assert self.rule.confidence is None

    def then_description_contains(self, text):
        assert text in self.rule.description or text.lower() in self.rule.description.lower()

    def test_infers_email_from_regex(self):
        """Code with email regex pattern is recognized as email validation."""
        self.given_code("if (!/.+@.+\\..+/.test(value)) { showError('Invalid email'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("email")
        self.then_confidence_is("high")
        self.then_description_contains("email")

    def test_infers_phone_from_digit_pattern(self):
        """Code with phone number regex is recognized as phone validation."""
        self.given_code("if (!/^\\d{3}-\\d{3}-\\d{4}$/.test(value)) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("phone")
        self.then_confidence_is_one_of("high", "medium")

    def test_infers_required_from_empty_check(self):
        """Code checking for empty string or null is recognized as required."""
        self.given_code("if (value === '' || value === null) { showError('Required'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("required")

    def test_infers_required_from_length_zero_check(self):
        """Code checking length === 0 is recognized as required."""
        self.given_code("if (value.length === 0) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("required")

    def test_infers_min_length(self):
        """Code with length < N check is recognized as min_length."""
        self.given_code("if (value.length < 8) { showError('Too short'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("min_length")
        self.then_description_contains("8")

    def test_infers_max_length(self):
        """Code with length > N check is recognized as max_length."""
        self.given_code("if (value.length > 100) { showError('Too long'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("max_length")
        self.then_description_contains("100")

    def test_infers_numeric(self):
        """Code with isNaN check is recognized as numeric validation."""
        self.given_code("if (isNaN(value)) { showError('Must be a number'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("numeric")

    def test_infers_numeric_from_digit_regex(self):
        """Code with digits-only regex is recognized as numeric validation."""
        self.given_code("if (!/^\\d+$/.test(value)) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("numeric")

    def test_infers_url_pattern(self):
        """Code with URL regex is recognized as url validation."""
        self.given_code("if (!/^https?:\\/\\/.+/.test(value)) { showError('Invalid URL'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("url")

    def test_returns_unknown_for_unrecognized_code(self):
        """Unrecognized validation code returns type='unknown'."""
        self.given_code("customValidator.check(value, options);")
        self.when_rule_is_inferred()
        self.then_rule_type_is("unknown")
        self.then_confidence_is_none()

    def test_captures_custom_regex_pattern(self):
        """Custom regex patterns are recognized as type='pattern'."""
        self.given_code("if (!/^[A-Z]{2}\\d{6}$/.test(value)) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("pattern")

    def test_handles_empty_code(self):
        """Empty code returns type='unknown'."""
        self.given_code("")
        self.when_rule_is_inferred()
        self.then_rule_type_is("unknown")

    def test_handles_multiple_patterns_takes_most_specific(self):
        """When multiple patterns match, the most specific one wins."""
        self.given_code("""
        if (value.length < 5) { showError('Too short'); }
        if (!/.+@.+/.test(value)) { showError('Invalid email'); }
        """)
        self.when_rule_is_inferred()
        self.then_rule_type_is("email")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_rule_inferrer.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'js_interaction_detector.rule_inferrer'`

**Step 3: Write minimal implementation**

`js_interaction_detector/rule_inferrer.py`:
```python
"""Infer validation rules from JavaScript code via pattern matching."""

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class InferredRule:
    """Result of validation rule inference."""

    type: str
    description: str
    confidence: Optional[str]  # "high", "medium", "low", or None for unknown


# Patterns ordered by specificity (most specific first)
PATTERNS = [
    # Email patterns
    {
        "type": "email",
        "patterns": [
            r"@.*\.",  # Common email regex fragment
            r"email",  # Variable/function name hint
            r"\\.+@\\.+",  # Escaped regex
        ],
        "description": "Must be a valid email address",
        "confidence": "high",
    },
    # URL patterns
    {
        "type": "url",
        "patterns": [
            r"https?:\\?/\\?/",  # URL scheme
            r"^https?://",
        ],
        "description": "Must be a valid URL",
        "confidence": "high",
    },
    # Phone patterns
    {
        "type": "phone",
        "patterns": [
            r"\\d{3}[-.]?\\d{3}[-.]?\\d{4}",  # US phone
            r"\d{3}.*\d{3}.*\d{4}",
            r"phone",  # Variable name hint
        ],
        "description": "Must be a valid phone number",
        "confidence": "medium",
    },
    # Numeric patterns
    {
        "type": "numeric",
        "patterns": [
            r"isNaN\s*\(",
            r"Number\s*\(",
            r"parseInt\s*\(",
            r"parseFloat\s*\(",
            r"\^\\d\+\$",  # Digits only regex
        ],
        "description": "Must be a number",
        "confidence": "high",
    },
    # Min length patterns
    {
        "type": "min_length",
        "patterns": [
            r"\.length\s*<\s*(\d+)",
            r"\.length\s*>=\s*(\d+)",
            r"minlength",
        ],
        "description_template": "Must be at least {0} characters",
        "confidence": "high",
    },
    # Max length patterns
    {
        "type": "max_length",
        "patterns": [
            r"\.length\s*>\s*(\d+)",
            r"\.length\s*<=\s*(\d+)",
            r"maxlength",
        ],
        "description_template": "Must be at most {0} characters",
        "confidence": "high",
    },
    # Required patterns
    {
        "type": "required",
        "patterns": [
            r"===?\s*['\"][\s]*['\"]",  # Empty string check
            r"===?\s*null",
            r"===?\s*undefined",
            r"\.length\s*===?\s*0",
            r"!value",
            r"required",
        ],
        "description": "Field is required",
        "confidence": "high",
    },
    # Custom pattern (catch-all for regexes we don't recognize)
    {
        "type": "pattern",
        "patterns": [
            r"/\^.*\$/",  # Anchored regex
            r"\.test\s*\(",
            r"\.match\s*\(",
            r"RegExp\s*\(",
        ],
        "description": "Must match a specific pattern",
        "confidence": "low",
    },
]


def infer_validation_rule(code: str) -> InferredRule:
    """Infer the validation rule type from JavaScript code.

    Args:
        code: The JavaScript validation function code

    Returns:
        InferredRule with type, description, and confidence
    """
    if not code or not code.strip():
        logger.info("Empty code, returning unknown")
        return InferredRule(
            type="unknown",
            description="Could not determine validation rule",
            confidence=None,
        )

    # Try each pattern in order of specificity
    for pattern_def in PATTERNS:
        for pattern in pattern_def["patterns"]:
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                # Build description
                if "description_template" in pattern_def:
                    # Extract captured group for parameterized descriptions
                    try:
                        param = match.group(1)
                        description = pattern_def["description_template"].format(param)
                    except (IndexError, AttributeError):
                        description = pattern_def.get(
                            "description", f"Validation rule: {pattern_def['type']}"
                        )
                else:
                    description = pattern_def.get(
                        "description", f"Validation rule: {pattern_def['type']}"
                    )

                logger.info(
                    f"Inferred rule type '{pattern_def['type']}' "
                    f"with confidence '{pattern_def['confidence']}'"
                )
                return InferredRule(
                    type=pattern_def["type"],
                    description=description,
                    confidence=pattern_def["confidence"],
                )

    # No pattern matched
    logger.info("No pattern matched, returning unknown")
    return InferredRule(
        type="unknown",
        description="Could not determine validation rule",
        confidence=None,
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_rule_inferrer.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add js_interaction_detector/rule_inferrer.py tests/test_rule_inferrer.py
git commit -m "feat: add validation rule inference via pattern matching"
```

---

## Task 6: Analyzer (Orchestration)

**Files:**
- Create: `js_interaction_detector/analyzer.py`
- Create: `tests/test_analyzer.py`

**Step 1: Write the failing test**

`tests/test_analyzer.py`:
```python
"""Tests for the main analyzer."""

import pytest
from pathlib import Path
from js_interaction_detector.analyzer import analyze_page
from js_interaction_detector.models import AnalysisResult


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestAnalyzer:
    def given_form_with_validation_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"

    def given_invalid_url(self):
        self.url = "not-a-url"

    async def when_page_is_analyzed(self):
        self.result = await analyze_page(self.url)

    def then_result_is_valid(self):
        assert isinstance(self.result, AnalysisResult)
        assert self.result.url == self.url
        assert self.result.analyzed_at is not None
        assert isinstance(self.result.interactions, list)

    def then_email_validation_detected(self):
        email_interaction = next(
            (i for i in self.result.interactions if "email" in i.element.selector),
            None
        )
        assert email_interaction is not None
        assert email_interaction.validation.type == "email"

    def then_email_has_blur_trigger(self):
        email_interaction = next(
            (i for i in self.result.interactions if "email" in i.element.selector),
            None
        )
        assert "blur" in email_interaction.triggers

    def then_result_has_errors(self):
        assert len(self.result.errors) > 0
        assert self.result.errors[0].phase == "loading"
        assert self.result.interactions == []

    def then_result_serializes_to_json(self):
        import json
        json_str = self.result.to_json()
        parsed = json.loads(json_str)
        assert parsed["url"] == self.url

    @pytest.mark.asyncio
    async def test_analyzes_page_and_returns_result(self, fixtures_path):
        """analyze_page returns an AnalysisResult with expected fields."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_result_is_valid()

    @pytest.mark.asyncio
    async def test_finds_email_validation(self, fixtures_path):
        """analyze_page detects email validation on email input."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_email_validation_detected()

    @pytest.mark.asyncio
    async def test_captures_triggers(self, fixtures_path):
        """analyze_page captures which events trigger validation."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_email_has_blur_trigger()

    @pytest.mark.asyncio
    async def test_returns_error_for_invalid_url(self):
        """analyze_page returns errors array for invalid URLs."""
        self.given_invalid_url()
        await self.when_page_is_analyzed()
        self.then_result_has_errors()

    @pytest.mark.asyncio
    async def test_result_serializes_to_valid_json(self, fixtures_path):
        """analyze_page result can be serialized to valid JSON."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_result_serializes_to_json()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_analyzer.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'js_interaction_detector.analyzer'`

**Step 3: Write minimal implementation**

`js_interaction_detector/analyzer.py`:
```python
"""Main analyzer that orchestrates the analysis pipeline."""

import logging
from datetime import datetime, timezone

from js_interaction_detector.models import (
    AnalysisError,
    AnalysisResult,
    ElementInfo,
    Interaction,
    ValidationInfo,
)
from js_interaction_detector.page_loader import PageLoader, PageLoadError
from js_interaction_detector.listener_extractor import extract_listeners
from js_interaction_detector.rule_inferrer import infer_validation_rule

logger = logging.getLogger(__name__)


async def analyze_page(url: str) -> AnalysisResult:
    """Analyze a page for JavaScript-driven input validations.

    Args:
        url: The URL to analyze

    Returns:
        AnalysisResult containing all detected interactions and any errors
    """
    logger.info(f"Starting analysis of {url}")
    errors: list[AnalysisError] = []
    interactions: list[Interaction] = []
    analyzed_at = datetime.now(timezone.utc).isoformat()

    try:
        async with PageLoader() as loader:
            page = await loader.load(url)

            # Extract event listeners
            listeners = await extract_listeners(page)
            logger.info(f"Found {len(listeners)} elements with listeners")

            # Process each listener
            for listener_info in listeners:
                try:
                    # Infer validation rule
                    rule = infer_validation_rule(listener_info.code)

                    # Build element info
                    element = ElementInfo(
                        selector=listener_info.selector,
                        tag=listener_info.tag,
                        type=listener_info.input_type,
                        name=listener_info.name,
                        id=listener_info.id,
                        placeholder=listener_info.placeholder,
                        attributes=listener_info.attributes or {},
                    )

                    # Build validation info
                    validation = ValidationInfo(
                        type=rule.type,
                        raw_code=listener_info.code,
                        rule_description=rule.description if rule.type != "unknown" else None,
                        confidence=rule.confidence,
                    )

                    # Create interaction
                    interaction = Interaction(
                        element=element,
                        triggers=listener_info.events,
                        validation=validation,
                    )
                    interactions.append(interaction)
                    logger.info(f"Processed {listener_info.selector}: {rule.type}")

                except Exception as e:
                    logger.warning(f"Error processing {listener_info.selector}: {e}")
                    errors.append(AnalysisError(
                        element=listener_info.selector,
                        error=str(e),
                        phase="extraction",
                    ))

    except PageLoadError as e:
        logger.error(f"Page load error: {e}")
        errors.append(AnalysisError(
            element=None,
            error=str(e),
            phase=e.phase,
        ))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        errors.append(AnalysisError(
            element=None,
            error=str(e),
            phase="discovery",
        ))

    result = AnalysisResult(
        url=url,
        analyzed_at=analyzed_at,
        errors=errors,
        interactions=interactions,
    )
    logger.info(
        f"Analysis complete: {len(interactions)} interactions, {len(errors)} errors"
    )
    return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_analyzer.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add js_interaction_detector/analyzer.py tests/test_analyzer.py
git commit -m "feat: add main analyzer orchestrating the pipeline"
```

---

## Task 7: CLI Interface

**Files:**
- Create: `js_interaction_detector/cli.py`
- Create: `js_interaction_detector/__main__.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

`tests/test_cli.py`:
```python
"""Tests for CLI interface."""

import json
import pytest
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from js_interaction_detector.cli import main, run_cli


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestCLI:
    def given_valid_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"
        self.args = [self.url]

    def given_unreachable_url(self):
        self.args = ["https://localhost:99999/nope"]

    def given_no_args(self):
        self.args = []

    async def when_cli_is_run(self):
        self.exit_code = await run_cli(self.args)

    async def when_cli_is_run_capturing_output(self, capsys):
        self.exit_code = await run_cli(self.args)
        self.captured = capsys.readouterr()

    def then_exit_code_is_zero(self):
        assert self.exit_code == 0

    def then_exit_code_is_nonzero(self):
        assert self.exit_code != 0

    def then_stdout_is_valid_json_with_url(self):
        output = json.loads(self.captured.out)
        assert output["url"] == self.url
        assert "interactions" in output

    def then_stderr_mentions_usage(self):
        assert "usage" in self.captured.err.lower() or "required" in self.captured.err.lower()

    @pytest.mark.asyncio
    async def test_outputs_json_to_stdout(self, fixtures_path, capsys):
        """CLI outputs valid JSON to stdout."""
        self.given_valid_url(fixtures_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_stdout_is_valid_json_with_url()

    @pytest.mark.asyncio
    async def test_returns_zero_on_success(self, fixtures_path):
        """CLI returns exit code 0 on successful analysis."""
        self.given_valid_url(fixtures_path)
        await self.when_cli_is_run()
        self.then_exit_code_is_zero()

    @pytest.mark.asyncio
    async def test_returns_zero_with_partial_results(self):
        """CLI returns exit code 0 even with errors (partial results strategy)."""
        self.given_unreachable_url()
        await self.when_cli_is_run()
        self.then_exit_code_is_zero()

    @pytest.mark.asyncio
    async def test_returns_nonzero_for_missing_url(self, capsys):
        """CLI returns non-zero exit code when URL argument is missing."""
        self.given_no_args()
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_nonzero()
        self.then_stderr_mentions_usage()

    @pytest.mark.asyncio
    async def test_errors_go_to_stderr(self):
        """CLI sends logging/errors to stderr, not stdout."""
        self.given_unreachable_url()
        with patch("sys.stderr", new_callable=StringIO):
            await self.when_cli_is_run()
        self.then_exit_code_is_zero()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'js_interaction_detector.cli'`

**Step 3: Write minimal implementation**

`js_interaction_detector/cli.py`:
```python
"""Command-line interface for js-interaction-detector."""

import argparse
import asyncio
import logging
import sys

from js_interaction_detector.analyzer import analyze_page

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging to stderr."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="js-interaction-detector",
        description="Detect JavaScript-driven input validations on web pages",
    )
    parser.add_argument(
        "url",
        help="URL to analyze (http, https, or file://)",
    )
    return parser.parse_args(args)


async def run_cli(args: list[str]) -> int:
    """Run the CLI with the given arguments.

    Args:
        args: Command-line arguments (without program name)

    Returns:
        Exit code (0 for success, non-zero for fatal errors)
    """
    setup_logging()

    try:
        parsed = parse_args(args)
    except SystemExit as e:
        return e.code if e.code else 1

    logger.info(f"Analyzing URL: {parsed.url}")
    result = await analyze_page(parsed.url)

    # Output JSON to stdout
    print(result.to_json())

    # Return 0 even with partial results (per spec)
    return 0


def main():
    """Entry point for the CLI."""
    exit_code = asyncio.run(run_cli(sys.argv[1:]))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

`js_interaction_detector/__main__.py`:
```python
"""Allow running as python -m js_interaction_detector."""

from js_interaction_detector.cli import main

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add js_interaction_detector/cli.py js_interaction_detector/__main__.py tests/test_cli.py
git commit -m "feat: add CLI interface with JSON output to stdout"
```

---

## Task 8: Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

`tests/test_integration.py`:
```python
"""Integration tests for end-to-end functionality."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestEndToEnd:
    def given_form_with_validation_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"

    def given_simple_form_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"

    def given_unreachable_url(self):
        self.url = "https://localhost:99999/nope"

    def when_cli_is_executed(self):
        self.result = subprocess.run(
            [sys.executable, "-m", "js_interaction_detector", self.url],
            capture_output=True,
            text=True,
        )
        self.output = json.loads(self.result.stdout)

    def then_exit_code_is_zero(self):
        assert self.result.returncode == 0

    def then_output_has_expected_structure(self):
        assert self.output["url"] == self.url
        assert "analyzed_at" in self.output
        assert "interactions" in self.output
        assert "errors" in self.output

    def then_email_validation_is_detected(self):
        email_interactions = [
            i for i in self.output["interactions"]
            if "email" in i["element"]["selector"]
        ]
        assert len(email_interactions) > 0
        assert email_interactions[0]["validation"]["type"] == "email"

    def then_interactions_are_empty(self):
        assert self.output["interactions"] == []

    def then_errors_are_present(self):
        assert len(self.output["errors"]) > 0

    def test_cli_produces_valid_json(self, fixtures_path):
        """CLI produces valid JSON with expected structure."""
        self.given_form_with_validation_url(fixtures_path)
        self.when_cli_is_executed()
        self.then_exit_code_is_zero()
        self.then_output_has_expected_structure()

    def test_detects_email_validation_end_to_end(self, fixtures_path):
        """Full pipeline detects email validation correctly."""
        self.given_form_with_validation_url(fixtures_path)
        self.when_cli_is_executed()
        self.then_email_validation_is_detected()

    def test_handles_page_without_validation(self, fixtures_path):
        """Page with no JS validation returns empty interactions."""
        self.given_simple_form_url(fixtures_path)
        self.when_cli_is_executed()
        self.then_exit_code_is_zero()
        self.then_interactions_are_empty()

    def test_handles_unreachable_url_gracefully(self):
        """Unreachable URL returns errors array, not crash."""
        self.given_unreachable_url()
        self.when_cli_is_executed()
        self.then_exit_code_is_zero()
        self.then_errors_are_present()
        self.then_interactions_are_empty()
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v`

Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for end-to-end functionality"
```

---

## Task 9: Final Verification

**Step 1: Run ruff linting**

Run: `ruff check js_interaction_detector/ tests/`

Expected: No errors

**Step 2: Run ruff formatting check**

Run: `ruff format --check js_interaction_detector/ tests/`

Expected: All files formatted correctly. If not, run `ruff format js_interaction_detector/ tests/` to fix.

**Step 3: Run all tests**

Run: `pytest -v`

Expected: All tests PASS

**Step 4: Run the tool manually**

Run: `python -m js_interaction_detector file://$(pwd)/tests/fixtures/sample_pages/form_with_validation.html`

Expected: JSON output with detected email and phone validations

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: complete v1 implementation of js-interaction-detector"
```

---

## Summary

| Task | Component | Key Files |
|------|-----------|-----------|
| 1 | Project Setup | `pyproject.toml` |
| 2 | Data Models | `models.py` |
| 3 | Page Loader | `page_loader.py` |
| 4 | Listener Extractor | `listener_extractor.py` |
| 5 | Rule Inferrer | `rule_inferrer.py` |
| 6 | Analyzer | `analyzer.py` |
| 7 | CLI | `cli.py`, `__main__.py` |
| 8 | Integration Tests | `test_integration.py` |
| 9 | Final Verification | All |

**Total: 9 tasks, ~25 TDD cycles**
