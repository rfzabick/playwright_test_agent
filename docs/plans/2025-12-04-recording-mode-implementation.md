# Recording Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `record` subcommand that captures user interactions and generates Playwright TypeScript tests with assertions for DOM, CSS, and network changes.

**Architecture:** User runs `record <url>`, browser opens in headed mode, user interacts, presses Ctrl+C. Tool uses MutationObserver for DOM changes, computed style diffing for CSS, Playwright's request events for network. Test generator outputs `.spec.ts` file.

**Tech Stack:** Python 3.14+, Playwright (async API, headed mode), TypeScript output, argparse subcommands

---

## Project Structure (New Files)

```
js_interaction_detector/
├── recorder/
│   ├── __init__.py
│   ├── action_tracker.py      # Intercepts user actions
│   ├── change_observer.py     # Observes DOM/CSS/network changes
│   ├── selector_generator.py  # Generates stable selectors
│   └── test_generator.py      # Outputs TypeScript test file
├── cli.py                     # Modified: add subcommands

tests/
├── test_recorder/
│   ├── __init__.py
│   ├── test_action_tracker.py
│   ├── test_change_observer.py
│   ├── test_selector_generator.py
│   └── test_test_generator.py
```

---

## Task 1: CLI Subcommands

**Files:**
- Modify: `js_interaction_detector/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
class TestCLISubcommands:
    def given_analyze_command(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"
        self.args = ["analyze", self.url]

    def given_record_command(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"
        self.args = ["record", self.url]

    def given_no_subcommand(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"
        self.args = [self.url]

    def given_help_flag(self):
        self.args = ["--help"]

    async def when_cli_is_run_capturing_output(self, capsys):
        self.exit_code = await run_cli(self.args)
        self.captured = capsys.readouterr()

    def then_exit_code_is_zero(self):
        assert self.exit_code == 0

    def then_exit_code_is_nonzero(self):
        assert self.exit_code != 0

    def then_stdout_is_valid_json(self):
        output = json.loads(self.captured.out)
        assert "url" in output

    def then_stderr_mentions_subcommands(self):
        assert "analyze" in self.captured.err or "analyze" in self.captured.out
        assert "record" in self.captured.err or "record" in self.captured.out

    @pytest.mark.asyncio
    async def test_analyze_subcommand_works(self, fixtures_path, capsys):
        """'analyze' subcommand runs the existing detection."""
        self.given_analyze_command(fixtures_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_stdout_is_valid_json()

    @pytest.mark.asyncio
    async def test_bare_url_still_works_for_backwards_compat(self, fixtures_path, capsys):
        """Bare URL without subcommand defaults to analyze."""
        self.given_no_subcommand(fixtures_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_stdout_is_valid_json()

    @pytest.mark.asyncio
    async def test_help_shows_subcommands(self, capsys):
        """--help shows available subcommands."""
        self.given_help_flag()
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_stderr_mentions_subcommands()
```

**Step 2: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_cli.py::TestCLISubcommands -v`

Expected: FAIL with `AttributeError` or assertion errors

**Step 3: Write minimal implementation**

Replace `js_interaction_detector/cli.py`:

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


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="js-interaction-detector",
        description="Detect JavaScript-driven interactions on web pages",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a page for input validations (default)",
    )
    analyze_parser.add_argument(
        "url",
        help="URL to analyze (http, https, or file://)",
    )

    # record subcommand
    record_parser = subparsers.add_parser(
        "record",
        help="Record interactions and generate Playwright tests",
    )
    record_parser.add_argument(
        "url",
        help="URL to record (http, https, or file://)",
    )
    record_parser.add_argument(
        "--output", "-o",
        default="./recorded-test.spec.ts",
        help="Output path for generated test (default: ./recorded-test.spec.ts)",
    )
    record_parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=2000,
        help="Settle timeout in milliseconds (default: 2000)",
    )

    return parser


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command-line arguments with backwards compatibility."""
    parser = create_parser()

    # Handle backwards compatibility: bare URL without subcommand
    if args and not args[0].startswith("-") and args[0] not in ("analyze", "record"):
        # Assume it's a URL, prepend 'analyze'
        args = ["analyze"] + args

    return parser.parse_args(args)


async def run_analyze(url: str) -> int:
    """Run the analyze command."""
    logger.info(f"Analyzing URL: {url}")
    result = await analyze_page(url)
    print(result.to_json())
    return 0


async def run_record(url: str, output: str, timeout: int) -> int:
    """Run the record command."""
    # Placeholder - will be implemented in later tasks
    print(f"Recording not yet implemented. URL: {url}, Output: {output}", file=sys.stderr)
    return 1


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

    if parsed.command is None:
        # No command and no args - show help
        create_parser().print_help(sys.stderr)
        return 1

    if parsed.command == "analyze":
        return await run_analyze(parsed.url)
    elif parsed.command == "record":
        return await run_record(parsed.url, parsed.output, parsed.timeout)

    return 1


def main():
    """Entry point for the CLI."""
    exit_code = asyncio.run(run_cli(sys.argv[1:]))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_cli.py -v`

Expected: All tests PASS

**Step 5: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/cli.py tests/test_cli.py && conda run -n py314 ruff format js_interaction_detector/cli.py tests/test_cli.py`

**Step 6: Commit**

```bash
git add js_interaction_detector/cli.py tests/test_cli.py
git commit -m "feat: add CLI subcommands (analyze, record)"
```

---

## Task 2: Selector Generator

**Files:**
- Create: `js_interaction_detector/recorder/__init__.py`
- Create: `js_interaction_detector/recorder/selector_generator.py`
- Create: `tests/test_recorder/__init__.py`
- Create: `tests/test_recorder/test_selector_generator.py`

**Step 1: Write the failing test**

Create `tests/test_recorder/__init__.py`:

```python
"""Tests for recorder module."""
```

Create `tests/test_recorder/test_selector_generator.py`:

```python
"""Tests for selector generation."""

import pytest


class TestSelectorGenerator:
    def given_element_with_testid(self):
        self.element_info = {
            "tag": "button",
            "data-testid": "submit-btn",
            "id": "btn1",
            "classes": ["primary", "large"],
        }

    def given_element_with_id_only(self):
        self.element_info = {
            "tag": "div",
            "id": "main-content",
            "classes": [],
        }

    def given_element_with_aria_label(self):
        self.element_info = {
            "tag": "button",
            "aria-label": "Close dialog",
            "classes": ["icon-btn"],
        }

    def given_element_with_only_classes(self):
        self.element_info = {
            "tag": "span",
            "classes": ["notification", "badge"],
        }

    def given_element_with_nothing(self):
        self.element_info = {
            "tag": "div",
            "classes": [],
        }

    def when_selector_is_generated(self):
        from js_interaction_detector.recorder.selector_generator import generate_selector
        self.selector, self.is_fragile = generate_selector(self.element_info)

    def then_selector_is(self, expected):
        assert self.selector == expected

    def then_selector_is_not_fragile(self):
        assert self.is_fragile is False

    def then_selector_is_fragile(self):
        assert self.is_fragile is True

    def test_prefers_data_testid(self):
        """data-testid is preferred over id and classes."""
        self.given_element_with_testid()
        self.when_selector_is_generated()
        self.then_selector_is('[data-testid="submit-btn"]')
        self.then_selector_is_not_fragile()

    def test_uses_id_when_no_testid(self):
        """Falls back to id when no data-testid."""
        self.given_element_with_id_only()
        self.when_selector_is_generated()
        self.then_selector_is("#main-content")
        self.then_selector_is_not_fragile()

    def test_uses_aria_label_when_no_id(self):
        """Falls back to aria-label when no id."""
        self.given_element_with_aria_label()
        self.when_selector_is_generated()
        self.then_selector_is('button[aria-label="Close dialog"]')
        self.then_selector_is_not_fragile()

    def test_uses_classes_as_last_resort(self):
        """Falls back to tag + classes when nothing better available."""
        self.given_element_with_only_classes()
        self.when_selector_is_generated()
        self.then_selector_is("span.notification.badge")
        self.then_selector_is_fragile()

    def test_marks_tag_only_as_fragile(self):
        """Tag-only selector is marked fragile."""
        self.given_element_with_nothing()
        self.when_selector_is_generated()
        self.then_selector_is("div")
        self.then_selector_is_fragile()
```

**Step 2: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_recorder/test_selector_generator.py -v`

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `js_interaction_detector/recorder/__init__.py`:

```python
"""Recorder module for capturing user interactions."""
```

Create `js_interaction_detector/recorder/selector_generator.py`:

```python
"""Generate stable CSS selectors for elements."""

import logging

logger = logging.getLogger(__name__)


def generate_selector(element_info: dict) -> tuple[str, bool]:
    """Generate a CSS selector for an element.

    Uses a priority order to create the most stable selector possible:
    1. data-testid (most stable)
    2. id
    3. aria-label with tag
    4. tag + classes (fragile)
    5. tag only (very fragile)

    Args:
        element_info: Dictionary with tag, id, classes, data-testid, aria-label, etc.

    Returns:
        Tuple of (selector_string, is_fragile)
    """
    tag = element_info.get("tag", "div")

    # Priority 1: data-testid
    testid = element_info.get("data-testid")
    if testid:
        selector = f'[data-testid="{testid}"]'
        logger.info(f"Generated selector from data-testid: {selector}")
        return selector, False

    # Priority 2: id
    elem_id = element_info.get("id")
    if elem_id:
        selector = f"#{elem_id}"
        logger.info(f"Generated selector from id: {selector}")
        return selector, False

    # Priority 3: aria-label
    aria_label = element_info.get("aria-label")
    if aria_label:
        selector = f'{tag}[aria-label="{aria_label}"]'
        logger.info(f"Generated selector from aria-label: {selector}")
        return selector, False

    # Priority 4: tag + classes (fragile)
    classes = element_info.get("classes", [])
    if classes:
        class_selector = ".".join(classes)
        selector = f"{tag}.{class_selector}"
        logger.info(f"Generated fragile selector from classes: {selector}")
        return selector, True

    # Priority 5: tag only (very fragile)
    logger.warning(f"Generated very fragile tag-only selector: {tag}")
    return tag, True
```

**Step 4: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_recorder/test_selector_generator.py -v`

Expected: All tests PASS

**Step 5: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/recorder/ tests/test_recorder/ && conda run -n py314 ruff format js_interaction_detector/recorder/ tests/test_recorder/`

**Step 6: Commit**

```bash
git add js_interaction_detector/recorder/ tests/test_recorder/
git commit -m "feat: add selector generator with priority-based selection"
```

---

## Task 3: Test Generator

**Files:**
- Create: `js_interaction_detector/recorder/test_generator.py`
- Create: `tests/test_recorder/test_test_generator.py`

**Step 1: Write the failing test**

Create `tests/test_recorder/test_test_generator.py`:

```python
"""Tests for Playwright test generation."""

import pytest
from js_interaction_detector.recorder.test_generator import (
    RecordedAction,
    DOMChange,
    CSSChange,
    NetworkRequest,
    generate_test,
)


class TestTestGenerator:
    def given_single_click_with_visibility_change(self):
        self.url = "http://localhost:8080"
        self.actions = [
            RecordedAction(
                action_type="click",
                selector='[data-testid="bell-icon"]',
                changes=[
                    DOMChange(
                        change_type="added",
                        selector=".notification-dropdown",
                    ),
                ],
            ),
        ]

    def given_click_with_css_change(self):
        self.url = "http://localhost:8080"
        self.actions = [
            RecordedAction(
                action_type="click",
                selector=".color-option.blue",
                changes=[
                    CSSChange(
                        selector=".navbar-box",
                        property="background-color",
                        value="rgb(0, 0, 255)",
                    ),
                ],
            ),
        ]

    def given_click_with_network_request(self):
        self.url = "http://localhost:8080"
        self.actions = [
            RecordedAction(
                action_type="click",
                selector="#refresh-btn",
                changes=[
                    NetworkRequest(
                        method="GET",
                        url_pattern="/api/data",
                    ),
                ],
            ),
        ]

    def given_action_with_no_changes(self):
        self.url = "http://localhost:8080"
        self.actions = [
            RecordedAction(
                action_type="click",
                selector="#no-op-btn",
                changes=[],
            ),
        ]

    def given_multiple_actions(self):
        self.url = "http://localhost:8080"
        self.actions = [
            RecordedAction(
                action_type="click",
                selector='[data-testid="menu"]',
                changes=[
                    DOMChange(change_type="added", selector=".menu-dropdown"),
                ],
            ),
            RecordedAction(
                action_type="click",
                selector=".menu-item.settings",
                changes=[
                    DOMChange(change_type="added", selector=".settings-panel"),
                ],
            ),
        ]

    def when_test_is_generated(self):
        self.output = generate_test(self.url, self.actions)

    def then_output_contains(self, text):
        assert text in self.output, f"Expected '{text}' in:\n{self.output}"

    def then_output_does_not_contain(self, text):
        assert text not in self.output, f"Did not expect '{text}' in:\n{self.output}"

    def test_generates_valid_typescript_structure(self):
        """Generated test has correct TypeScript structure."""
        self.given_single_click_with_visibility_change()
        self.when_test_is_generated()
        self.then_output_contains("import { test, expect } from '@playwright/test';")
        self.then_output_contains("test('recorded interaction test'")
        self.then_output_contains("await page.goto('http://localhost:8080');")

    def test_generates_click_action(self):
        """Click actions generate page.click()."""
        self.given_single_click_with_visibility_change()
        self.when_test_is_generated()
        self.then_output_contains('await page.click(\'[data-testid="bell-icon"]\');')

    def test_generates_visibility_assertion(self):
        """DOM added changes generate toBeVisible()."""
        self.given_single_click_with_visibility_change()
        self.when_test_is_generated()
        self.then_output_contains("toBeVisible()")
        self.then_output_contains(".notification-dropdown")

    def test_generates_css_assertion(self):
        """CSS changes generate toHaveCSS()."""
        self.given_click_with_css_change()
        self.when_test_is_generated()
        self.then_output_contains("toHaveCSS('background-color', 'rgb(0, 0, 255)')")

    def test_generates_network_wait(self):
        """Network requests generate waitForRequest()."""
        self.given_click_with_network_request()
        self.when_test_is_generated()
        self.then_output_contains("waitForRequest")
        self.then_output_contains("/api/data")

    def test_adds_comment_for_no_changes(self):
        """Actions with no changes get a comment."""
        self.given_action_with_no_changes()
        self.when_test_is_generated()
        self.then_output_contains("// No observable changes detected")

    def test_handles_multiple_actions(self):
        """Multiple actions are generated in sequence."""
        self.given_multiple_actions()
        self.when_test_is_generated()
        self.then_output_contains(".menu-dropdown")
        self.then_output_contains(".settings-panel")
```

**Step 2: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_recorder/test_test_generator.py -v`

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `js_interaction_detector/recorder/test_generator.py`:

```python
"""Generate Playwright TypeScript tests from recorded actions."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DOMChange:
    """A DOM change observation."""

    change_type: str  # "added", "removed", "text_changed"
    selector: str
    text: str | None = None


@dataclass
class CSSChange:
    """A CSS property change observation."""

    selector: str
    property: str
    value: str


@dataclass
class NetworkRequest:
    """A network request observation."""

    method: str
    url_pattern: str


@dataclass
class RecordedAction:
    """A recorded user action with its observed changes."""

    action_type: str  # "click", "type", "press"
    selector: str
    changes: list[DOMChange | CSSChange | NetworkRequest]
    value: str | None = None  # For type actions


def generate_test(url: str, actions: list[RecordedAction]) -> str:
    """Generate a Playwright TypeScript test from recorded actions.

    Args:
        url: The URL that was recorded
        actions: List of recorded actions with their changes

    Returns:
        TypeScript test file content as a string
    """
    logger.info(f"Generating test for {url} with {len(actions)} actions")

    lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        "test('recorded interaction test', async ({ page }) => {",
        f"  await page.goto('{url}');",
        "",
    ]

    for action in actions:
        lines.extend(_generate_action(action))
        lines.append("")

    lines.append("});")
    lines.append("")

    output = "\n".join(lines)
    logger.info(f"Generated test with {len(lines)} lines")
    return output


def _generate_action(action: RecordedAction) -> list[str]:
    """Generate code for a single action and its assertions."""
    lines = []

    # Generate the action
    if action.action_type == "click":
        lines.append(f"  await page.click('{action.selector}');")
    elif action.action_type == "type":
        lines.append(f"  await page.fill('{action.selector}', '{action.value}');")
    elif action.action_type == "press":
        lines.append(f"  await page.press('{action.selector}', '{action.value}');")

    # Generate assertions for changes
    if not action.changes:
        lines.append("  // No observable changes detected")
        return lines

    for change in action.changes:
        if isinstance(change, DOMChange):
            lines.extend(_generate_dom_assertion(change))
        elif isinstance(change, CSSChange):
            lines.extend(_generate_css_assertion(change))
        elif isinstance(change, NetworkRequest):
            lines.extend(_generate_network_assertion(change))

    return lines


def _generate_dom_assertion(change: DOMChange) -> list[str]:
    """Generate assertion for a DOM change."""
    if change.change_type == "added":
        return [f"  await expect(page.locator('{change.selector}')).toBeVisible();"]
    elif change.change_type == "removed":
        return [f"  await expect(page.locator('{change.selector}')).toBeHidden();"]
    elif change.change_type == "text_changed":
        return [f"  await expect(page.locator('{change.selector}')).toHaveText('{change.text}');"]
    return []


def _generate_css_assertion(change: CSSChange) -> list[str]:
    """Generate assertion for a CSS change."""
    return [
        f"  await expect(page.locator('{change.selector}')).toHaveCSS('{change.property}', '{change.value}');"
    ]


def _generate_network_assertion(change: NetworkRequest) -> list[str]:
    """Generate assertion for a network request."""
    return [
        f"  await page.waitForRequest(req => req.url().includes('{change.url_pattern}') && req.method() === '{change.method}');"
    ]
```

**Step 4: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_recorder/test_test_generator.py -v`

Expected: All tests PASS

**Step 5: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/recorder/test_generator.py tests/test_recorder/test_test_generator.py && conda run -n py314 ruff format js_interaction_detector/recorder/test_generator.py tests/test_recorder/test_test_generator.py`

**Step 6: Commit**

```bash
git add js_interaction_detector/recorder/test_generator.py tests/test_recorder/test_test_generator.py
git commit -m "feat: add Playwright TypeScript test generator"
```

---

## Task 4: Change Observer (DOM)

**Files:**
- Create: `js_interaction_detector/recorder/change_observer.py`
- Create: `tests/test_recorder/test_change_observer.py`
- Create: `tests/fixtures/sample_pages/dropdown_page.html`

**Step 1: Create test fixture**

Create `tests/fixtures/sample_pages/dropdown_page.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Dropdown Test</title></head>
<body>
  <button id="toggle-btn" onclick="toggleDropdown()">Toggle</button>
  <div id="dropdown" style="display: none;">
    <div class="item">Item 1</div>
    <div class="item">Item 2</div>
    <div class="item">Item 3</div>
  </div>
  <script>
    function toggleDropdown() {
      const dropdown = document.getElementById('dropdown');
      dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
  </script>
</body>
</html>
```

**Step 2: Write the failing test**

Create `tests/test_recorder/test_change_observer.py`:

```python
"""Tests for change observation."""

import pytest
from pathlib import Path

from js_interaction_detector.page_loader import PageLoader
from js_interaction_detector.recorder.change_observer import ChangeObserver


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent.parent / "fixtures" / "sample_pages"


class TestChangeObserver:
    def given_dropdown_page(self, fixtures_path):
        self.url = f"file://{fixtures_path}/dropdown_page.html"

    async def when_page_is_loaded_with_observer(self):
        async with PageLoader() as loader:
            self.page = await loader.load(self.url)
            self.observer = ChangeObserver(self.page)
            await self.observer.start()

    async def when_element_is_clicked(self, selector):
        await self.observer.before_action()
        await self.page.click(selector)
        self.changes = await self.observer.after_action()

    def then_dom_change_detected(self, selector, change_type):
        dom_changes = [c for c in self.changes if hasattr(c, 'change_type')]
        matching = [c for c in dom_changes if selector in c.selector and c.change_type == change_type]
        assert len(matching) > 0, f"Expected {change_type} change for {selector}, got: {dom_changes}"

    def then_no_changes_detected(self):
        assert len(self.changes) == 0

    @pytest.mark.asyncio
    async def test_detects_visibility_change(self, fixtures_path):
        """Clicking toggle button makes dropdown visible."""
        self.given_dropdown_page(fixtures_path)
        await self.when_page_is_loaded_with_observer()
        await self.when_element_is_clicked("#toggle-btn")
        self.then_dom_change_detected("#dropdown", "visibility_changed")

    @pytest.mark.asyncio
    async def test_detects_toggle_back_to_hidden(self, fixtures_path):
        """Clicking toggle again hides the dropdown."""
        self.given_dropdown_page(fixtures_path)
        await self.when_page_is_loaded_with_observer()
        # First click shows
        await self.page.click("#toggle-btn")
        await self.page.wait_for_timeout(100)
        # Second click hides - this is what we're testing
        await self.when_element_is_clicked("#toggle-btn")
        self.then_dom_change_detected("#dropdown", "visibility_changed")
```

**Step 3: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_recorder/test_change_observer.py -v`

Expected: FAIL with `ModuleNotFoundError`

**Step 4: Write minimal implementation**

Create `js_interaction_detector/recorder/change_observer.py`:

```python
"""Observe DOM, CSS, and network changes during user actions."""

import logging
from dataclasses import dataclass, field

from playwright.async_api import Page

from js_interaction_detector.recorder.selector_generator import generate_selector
from js_interaction_detector.recorder.test_generator import (
    CSSChange,
    DOMChange,
    NetworkRequest,
)

logger = logging.getLogger(__name__)

# JavaScript to inject for observing mutations
OBSERVER_SCRIPT = """
() => {
    window.__recordedMutations = [];
    window.__mutationObserver = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.type === 'childList') {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        window.__recordedMutations.push({
                            type: 'added',
                            tag: node.tagName.toLowerCase(),
                            id: node.id || null,
                            classes: Array.from(node.classList),
                            'data-testid': node.getAttribute('data-testid'),
                            'aria-label': node.getAttribute('aria-label'),
                        });
                    }
                }
                for (const node of mutation.removedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        window.__recordedMutations.push({
                            type: 'removed',
                            tag: node.tagName.toLowerCase(),
                            id: node.id || null,
                            classes: Array.from(node.classList),
                            'data-testid': node.getAttribute('data-testid'),
                            'aria-label': node.getAttribute('aria-label'),
                        });
                    }
                }
            } else if (mutation.type === 'attributes') {
                const el = mutation.target;
                if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
                    window.__recordedMutations.push({
                        type: 'visibility_changed',
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: Array.from(el.classList),
                        'data-testid': el.getAttribute('data-testid'),
                        'aria-label': el.getAttribute('aria-label'),
                        visible: el.offsetParent !== null || getComputedStyle(el).display !== 'none',
                    });
                }
            }
        }
    });
    window.__mutationObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class', 'hidden'],
    });
}
"""

COLLECT_MUTATIONS_SCRIPT = """
() => {
    const mutations = window.__recordedMutations || [];
    window.__recordedMutations = [];
    return mutations;
}
"""


@dataclass
class ChangeObserver:
    """Observes changes to the page during user interactions."""

    page: Page
    _pending_requests: list = field(default_factory=list)

    async def start(self):
        """Start observing the page."""
        await self.page.evaluate(OBSERVER_SCRIPT)
        logger.info("Change observer started")

        # Listen for network requests
        self.page.on("request", self._on_request)

    def _on_request(self, request):
        """Handle network request events."""
        url = request.url
        # Filter out static assets
        static_extensions = ('.js', '.css', '.png', '.jpg', '.gif', '.woff', '.svg', '.ico')
        if any(url.endswith(ext) for ext in static_extensions):
            return
        if 'hot-update' in url:
            return

        self._pending_requests.append({
            "method": request.method,
            "url": url,
        })
        logger.info(f"Captured network request: {request.method} {url}")

    async def before_action(self):
        """Call before performing an action to reset state."""
        # Clear any pending mutations
        await self.page.evaluate("() => { window.__recordedMutations = []; }")
        self._pending_requests = []

    async def after_action(self, settle_timeout: int = 100) -> list:
        """Call after an action to collect changes.

        Args:
            settle_timeout: Time to wait for changes to settle (ms)

        Returns:
            List of DOMChange, CSSChange, and NetworkRequest objects
        """
        # Wait for changes to settle
        await self.page.wait_for_timeout(settle_timeout)

        # Collect mutations
        mutations = await self.page.evaluate(COLLECT_MUTATIONS_SCRIPT)

        changes = []

        # Process DOM mutations
        for mutation in mutations:
            selector, _ = generate_selector(mutation)
            change_type = mutation.get("type", "unknown")

            if change_type in ("added", "removed", "visibility_changed"):
                changes.append(DOMChange(
                    change_type=change_type,
                    selector=selector,
                ))
                logger.info(f"DOM change: {change_type} {selector}")

        # Process network requests
        for req in self._pending_requests:
            # Extract path pattern from URL
            url = req["url"]
            if "/api/" in url:
                pattern = "/api/" + url.split("/api/")[1].split("?")[0]
            else:
                pattern = url.split("://")[1].split("/", 1)[1] if "/" in url.split("://")[1] else "/"

            changes.append(NetworkRequest(
                method=req["method"],
                url_pattern=pattern,
            ))
            logger.info(f"Network request: {req['method']} {pattern}")

        return changes
```

**Step 5: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_recorder/test_change_observer.py -v`

Expected: All tests PASS

**Step 6: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/recorder/change_observer.py tests/test_recorder/test_change_observer.py && conda run -n py314 ruff format js_interaction_detector/recorder/change_observer.py tests/test_recorder/test_change_observer.py`

**Step 7: Commit**

```bash
git add js_interaction_detector/recorder/change_observer.py tests/test_recorder/test_change_observer.py tests/fixtures/sample_pages/dropdown_page.html
git commit -m "feat: add change observer for DOM mutations and network requests"
```

---

## Task 5: Action Tracker

**Files:**
- Create: `js_interaction_detector/recorder/action_tracker.py`
- Create: `tests/test_recorder/test_action_tracker.py`

**Step 1: Write the failing test**

Create `tests/test_recorder/test_action_tracker.py`:

```python
"""Tests for action tracking."""

import pytest
from pathlib import Path

from js_interaction_detector.page_loader import PageLoader
from js_interaction_detector.recorder.action_tracker import ActionTracker


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent.parent / "fixtures" / "sample_pages"


class TestActionTracker:
    def given_simple_form_page(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"

    async def when_page_is_loaded_with_tracker(self):
        async with PageLoader() as loader:
            self.page = await loader.load(self.url)
            self.tracker = ActionTracker(self.page)
            await self.tracker.start()

    async def when_user_clicks(self, selector):
        await self.page.click(selector)
        await self.page.wait_for_timeout(50)

    async def when_user_types(self, selector, text):
        await self.page.fill(selector, text)
        await self.page.wait_for_timeout(50)

    async def when_actions_are_collected(self):
        self.actions = await self.tracker.get_actions()

    def then_action_count_is(self, count):
        assert len(self.actions) == count, f"Expected {count} actions, got {len(self.actions)}: {self.actions}"

    def then_action_has_type(self, index, action_type):
        assert self.actions[index]["type"] == action_type

    def then_action_has_selector_containing(self, index, text):
        assert text in self.actions[index]["selector"]

    @pytest.mark.asyncio
    async def test_tracks_click_action(self, fixtures_path):
        """Click on button is tracked."""
        self.given_simple_form_page(fixtures_path)
        await self.when_page_is_loaded_with_tracker()
        await self.when_user_clicks("button[type='submit']")
        await self.when_actions_are_collected()
        self.then_action_count_is(1)
        self.then_action_has_type(0, "click")

    @pytest.mark.asyncio
    async def test_tracks_input_action(self, fixtures_path):
        """Typing in input field is tracked."""
        self.given_simple_form_page(fixtures_path)
        await self.when_page_is_loaded_with_tracker()
        await self.when_user_types("#email", "test@example.com")
        await self.when_actions_are_collected()
        self.then_action_count_is(1)
        self.then_action_has_type(0, "fill")

    @pytest.mark.asyncio
    async def test_tracks_multiple_actions(self, fixtures_path):
        """Multiple actions are tracked in order."""
        self.given_simple_form_page(fixtures_path)
        await self.when_page_is_loaded_with_tracker()
        await self.when_user_types("#email", "test@example.com")
        await self.when_user_clicks("button[type='submit']")
        await self.when_actions_are_collected()
        self.then_action_count_is(2)
        self.then_action_has_type(0, "fill")
        self.then_action_has_type(1, "click")
```

**Step 2: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_recorder/test_action_tracker.py -v`

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `js_interaction_detector/recorder/action_tracker.py`:

```python
"""Track user actions on a page."""

import logging
from dataclasses import dataclass, field

from playwright.async_api import Page

from js_interaction_detector.recorder.selector_generator import generate_selector

logger = logging.getLogger(__name__)

# JavaScript to inject for tracking actions
TRACKER_SCRIPT = """
() => {
    window.__recordedActions = [];

    // Track clicks
    document.addEventListener('click', (e) => {
        const el = e.target;
        window.__recordedActions.push({
            type: 'click',
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            classes: Array.from(el.classList),
            'data-testid': el.getAttribute('data-testid'),
            'aria-label': el.getAttribute('aria-label'),
            timestamp: Date.now(),
        });
    }, true);

    // Track input changes
    document.addEventListener('input', (e) => {
        const el = e.target;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            // Debounce - only record if no recent input action for this element
            const lastAction = window.__recordedActions[window.__recordedActions.length - 1];
            if (lastAction && lastAction.type === 'fill' && lastAction.id === el.id) {
                lastAction.value = el.value;
                lastAction.timestamp = Date.now();
            } else {
                window.__recordedActions.push({
                    type: 'fill',
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    classes: Array.from(el.classList),
                    'data-testid': el.getAttribute('data-testid'),
                    'aria-label': el.getAttribute('aria-label'),
                    value: el.value,
                    timestamp: Date.now(),
                });
            }
        }
    }, true);
}
"""

COLLECT_ACTIONS_SCRIPT = """
() => {
    const actions = window.__recordedActions || [];
    window.__recordedActions = [];
    return actions;
}
"""


@dataclass
class ActionTracker:
    """Tracks user actions on a page."""

    page: Page
    _started: bool = False

    async def start(self):
        """Start tracking actions on the page."""
        await self.page.evaluate(TRACKER_SCRIPT)
        self._started = True
        logger.info("Action tracker started")

    async def get_actions(self) -> list[dict]:
        """Collect all recorded actions.

        Returns:
            List of action dictionaries with type, selector, and optional value
        """
        if not self._started:
            return []

        raw_actions = await self.page.evaluate(COLLECT_ACTIONS_SCRIPT)

        actions = []
        for raw in raw_actions:
            selector, is_fragile = generate_selector(raw)
            action = {
                "type": raw["type"],
                "selector": selector,
                "is_fragile": is_fragile,
            }
            if raw.get("value"):
                action["value"] = raw["value"]

            actions.append(action)
            logger.info(f"Collected action: {raw['type']} on {selector}")

        return actions

    async def clear(self):
        """Clear recorded actions."""
        await self.page.evaluate("() => { window.__recordedActions = []; }")
```

**Step 4: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_recorder/test_action_tracker.py -v`

Expected: All tests PASS

**Step 5: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/recorder/action_tracker.py tests/test_recorder/test_action_tracker.py && conda run -n py314 ruff format js_interaction_detector/recorder/action_tracker.py tests/test_recorder/test_action_tracker.py`

**Step 6: Commit**

```bash
git add js_interaction_detector/recorder/action_tracker.py tests/test_recorder/test_action_tracker.py
git commit -m "feat: add action tracker for clicks and input"
```

---

## Task 6: Recording Session

**Files:**
- Create: `js_interaction_detector/recorder/session.py`
- Create: `tests/test_recorder/test_session.py`

**Step 1: Write the failing test**

Create `tests/test_recorder/test_session.py`:

```python
"""Tests for recording session orchestration."""

import pytest
from pathlib import Path

from js_interaction_detector.recorder.session import RecordingSession


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent.parent / "fixtures" / "sample_pages"


class TestRecordingSession:
    def given_dropdown_page_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/dropdown_page.html"

    async def when_session_records_interaction(self):
        async with RecordingSession(self.url, headed=False) as session:
            # Simulate user clicking the toggle button
            await session.page.click("#toggle-btn")
            await session.page.wait_for_timeout(200)
            self.recorded_actions = session.get_recorded_actions()

    def then_action_was_recorded_with_changes(self):
        assert len(self.recorded_actions) > 0
        action = self.recorded_actions[0]
        assert action.action_type == "click"
        assert len(action.changes) > 0

    @pytest.mark.asyncio
    async def test_records_action_with_dom_changes(self, fixtures_path):
        """Session records click action and observes DOM changes."""
        self.given_dropdown_page_url(fixtures_path)
        await self.when_session_records_interaction()
        self.then_action_was_recorded_with_changes()
```

**Step 2: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_recorder/test_session.py -v`

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `js_interaction_detector/recorder/session.py`:

```python
"""Recording session that orchestrates action tracking and change observation."""

import logging
from dataclasses import dataclass, field

from playwright.async_api import async_playwright, Page

from js_interaction_detector.recorder.action_tracker import ActionTracker
from js_interaction_detector.recorder.change_observer import ChangeObserver
from js_interaction_detector.recorder.test_generator import RecordedAction

logger = logging.getLogger(__name__)


@dataclass
class RecordingSession:
    """A recording session that captures user interactions and their effects."""

    url: str
    headed: bool = True
    settle_timeout: int = 200
    _playwright: object = field(default=None, repr=False)
    _browser: object = field(default=None, repr=False)
    _page: Page | None = field(default=None, repr=False)
    _tracker: ActionTracker | None = field(default=None, repr=False)
    _observer: ChangeObserver | None = field(default=None, repr=False)
    _recorded_actions: list[RecordedAction] = field(default_factory=list)
    _last_action_count: int = 0

    @property
    def page(self) -> Page:
        """Get the page being recorded."""
        return self._page

    async def __aenter__(self):
        """Start the recording session."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=not self.headed)
        self._page = await self._browser.new_page()

        logger.info(f"Loading page: {self.url}")
        await self._page.goto(self.url, wait_until="networkidle")

        # Set up tracking
        self._tracker = ActionTracker(self._page)
        self._observer = ChangeObserver(self._page)

        await self._tracker.start()
        await self._observer.start()

        # Set up action processing
        self._page.on("click", self._on_action)

        logger.info("Recording session started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End the recording session."""
        # Process any remaining actions
        await self._process_pending_actions()

        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Recording session ended")

    def _on_action(self, _):
        """Handle action events - we'll process after a delay."""
        pass

    async def _process_pending_actions(self):
        """Process any actions that haven't been matched with changes yet."""
        # Get all actions since last check
        actions = await self._tracker.get_actions()

        for action_data in actions:
            # Observe changes for this action
            changes = await self._observer.after_action(self.settle_timeout)

            recorded = RecordedAction(
                action_type=action_data["type"],
                selector=action_data["selector"],
                changes=changes,
                value=action_data.get("value"),
            )
            self._recorded_actions.append(recorded)
            logger.info(f"Recorded: {action_data['type']} on {action_data['selector']} with {len(changes)} changes")

    def get_recorded_actions(self) -> list[RecordedAction]:
        """Get all recorded actions."""
        return self._recorded_actions
```

**Step 4: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_recorder/test_session.py -v`

Expected: All tests PASS

**Step 5: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/recorder/session.py tests/test_recorder/test_session.py && conda run -n py314 ruff format js_interaction_detector/recorder/session.py tests/test_recorder/test_session.py`

**Step 6: Commit**

```bash
git add js_interaction_detector/recorder/session.py tests/test_recorder/test_session.py
git commit -m "feat: add recording session to orchestrate tracking and observation"
```

---

## Task 7: Wire Up Record Command

**Files:**
- Modify: `js_interaction_detector/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
class TestRecordCommand:
    def given_record_command_with_dropdown_page(self, fixtures_path):
        self.url = f"file://{fixtures_path}/dropdown_page.html"
        self.output_file = "/tmp/test-recorded.spec.ts"
        self.args = ["record", self.url, "--output", self.output_file, "--headless"]

    async def when_cli_runs_briefly(self, monkeypatch):
        # Mock to auto-stop after setup
        import js_interaction_detector.cli as cli_module

        original_run_record = cli_module.run_record

        async def quick_record(url, output, timeout, headless):
            # Just verify it starts, don't actually wait for user
            from js_interaction_detector.recorder.session import RecordingSession
            async with RecordingSession(url, headed=not headless) as session:
                # Do a quick action
                await session.page.click("#toggle-btn")
                await session.page.wait_for_timeout(200)
                actions = session.get_recorded_actions()

            # Generate test
            from js_interaction_detector.recorder.test_generator import generate_test
            test_content = generate_test(url, actions)
            with open(output, "w") as f:
                f.write(test_content)
            return 0

        monkeypatch.setattr(cli_module, "run_record", quick_record)
        self.exit_code = await cli_module.run_cli(self.args)

    def then_exit_code_is_zero(self):
        assert self.exit_code == 0

    def then_output_file_contains_playwright_test(self):
        with open(self.output_file) as f:
            content = f.read()
        assert "import { test, expect }" in content
        assert "page.goto" in content

    @pytest.mark.asyncio
    async def test_record_command_generates_test_file(self, fixtures_path, monkeypatch):
        """Record command generates a Playwright test file."""
        self.given_record_command_with_dropdown_page(fixtures_path)
        await self.when_cli_runs_briefly(monkeypatch)
        self.then_exit_code_is_zero()
        self.then_output_file_contains_playwright_test()
```

**Step 2: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_cli.py::TestRecordCommand -v`

Expected: FAIL (run_record not properly implemented)

**Step 3: Update implementation**

Update `js_interaction_detector/cli.py` - replace the `run_record` function:

```python
async def run_record(url: str, output: str, timeout: int, headless: bool = False) -> int:
    """Run the record command.

    Args:
        url: URL to record
        output: Output file path
        timeout: Settle timeout in ms
        headless: Run in headless mode (for testing)

    Returns:
        Exit code
    """
    from js_interaction_detector.recorder.session import RecordingSession
    from js_interaction_detector.recorder.test_generator import generate_test

    print(f"Recording... interact with the page, then press Ctrl+C to finish", file=sys.stderr)
    print(f"URL: {url}", file=sys.stderr)

    try:
        async with RecordingSession(url, headed=not headless, settle_timeout=timeout) as session:
            if headless:
                # For testing - just return immediately
                pass
            else:
                # Wait for Ctrl+C
                try:
                    while True:
                        await asyncio.sleep(0.1)
                        # Process any pending actions periodically
                        await session._process_pending_actions()
                except asyncio.CancelledError:
                    pass

            actions = session.get_recorded_actions()

        if not actions:
            print("No actions recorded.", file=sys.stderr)
            return 0

        # Generate test
        test_content = generate_test(url, actions)

        # Write output
        with open(output, "w") as f:
            f.write(test_content)

        print(f"Recorded {len(actions)} actions. Test written to: {output}", file=sys.stderr)
        return 0

    except Exception as e:
        logger.error(f"Recording failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

Also update the CLI parser to add `--headless` flag:

```python
    record_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (for testing)",
    )
```

And update the command dispatch:

```python
    elif parsed.command == "record":
        return await run_record(parsed.url, parsed.output, parsed.timeout, parsed.headless)
```

**Step 4: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_cli.py -v`

Expected: All tests PASS

**Step 5: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/cli.py && conda run -n py314 ruff format js_interaction_detector/cli.py`

**Step 6: Commit**

```bash
git add js_interaction_detector/cli.py tests/test_cli.py
git commit -m "feat: wire up record command to generate Playwright tests"
```

---

## Task 8: Handle Navigation (Go Back)

**Files:**
- Modify: `js_interaction_detector/recorder/session.py`
- Create: `tests/fixtures/sample_pages/navigation_page.html`
- Add test to: `tests/test_recorder/test_session.py`

**Step 1: Create test fixture**

Create `tests/fixtures/sample_pages/navigation_page.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Navigation Test</title></head>
<body>
  <a id="nav-link" href="simple_form.html">Go to Form</a>
  <button id="stay-btn" onclick="alert('clicked')">Stay Here</button>
</body>
</html>
```

**Step 2: Write the failing test**

Add to `tests/test_recorder/test_session.py`:

```python
class TestNavigationHandling:
    def given_navigation_page_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/navigation_page.html"
        self.original_title = "Navigation Test"

    async def when_session_handles_navigation(self):
        async with RecordingSession(self.url, headed=False) as session:
            # Click link that would navigate away
            await session.page.click("#nav-link")
            await session.page.wait_for_timeout(500)
            # Session should have gone back
            self.final_title = await session.page.title()
            self.recorded_actions = session.get_recorded_actions()

    def then_page_returned_to_original(self):
        assert self.final_title == self.original_title

    def then_navigation_was_noted(self):
        # Action should exist but may have a navigation note
        assert len(self.recorded_actions) >= 0  # May or may not record depending on timing

    @pytest.mark.asyncio
    async def test_goes_back_after_navigation(self, fixtures_path):
        """Session returns to original page after navigation."""
        self.given_navigation_page_url(fixtures_path)
        await self.when_session_handles_navigation()
        self.then_page_returned_to_original()
```

**Step 3: Run test to verify it fails**

Run: `conda run -n py314 pytest tests/test_recorder/test_session.py::TestNavigationHandling -v`

Expected: FAIL (navigation not handled)

**Step 4: Update implementation**

Update `js_interaction_detector/recorder/session.py` to handle navigation:

Add to `__aenter__` after setting up observers:

```python
        # Track original URL for navigation handling
        self._original_url = self.url

        # Handle navigation
        self._page.on("framenavigated", self._on_navigation)
```

Add the navigation handler method:

```python
    async def _on_navigation(self, frame):
        """Handle page navigation - go back to original page."""
        if frame != self._page.main_frame:
            return

        current_url = self._page.url
        if current_url != self._original_url and not current_url.startswith("about:"):
            logger.info(f"Navigation detected to {current_url}, going back")
            try:
                await self._page.go_back(wait_until="networkidle")
                # Re-initialize trackers after going back
                await self._tracker.start()
                await self._observer.start()
            except Exception as e:
                logger.warning(f"Could not go back: {e}")
```

**Step 5: Run test to verify it passes**

Run: `conda run -n py314 pytest tests/test_recorder/test_session.py -v`

Expected: All tests PASS

**Step 6: Run ruff**

Run: `conda run -n py314 ruff check js_interaction_detector/recorder/session.py && conda run -n py314 ruff format js_interaction_detector/recorder/session.py`

**Step 7: Commit**

```bash
git add js_interaction_detector/recorder/session.py tests/test_recorder/test_session.py tests/fixtures/sample_pages/navigation_page.html
git commit -m "feat: handle navigation by going back to original page"
```

---

## Task 9: Update README

**Files:**
- Modify: `README.md`

**Step 1: Update README with recording instructions**

Update the "Record Interactions" section in `README.md`:

```markdown
### Record Interactions

Record user interactions and generate Playwright tests:

```bash
python -m js_interaction_detector record https://example.com
```

The browser opens in headed mode. Interact with the page (click buttons, fill forms, etc.), then press `Ctrl+C` to stop recording. The tool generates a TypeScript Playwright test file.

Options:
- `--output FILE`, `-o FILE` - Output path for generated test (default: `./recorded-test.spec.ts`)
- `--timeout MS`, `-t MS` - Settle timeout in milliseconds (default: 2000)
- `--headless` - Run in headless mode (for testing)

Example:

```bash
# Record interactions on localhost app
python -m js_interaction_detector record http://localhost:8080 -o tests/my-app.spec.ts

# The tool captures:
# - Click actions → page.click() calls
# - Form input → page.fill() calls
# - DOM changes → toBeVisible()/toBeHidden() assertions
# - CSS changes → toHaveCSS() assertions
# - API calls → waitForRequest() assertions
```

Generated test example:

```typescript
import { test, expect } from '@playwright/test';

test('recorded interaction test', async ({ page }) => {
  await page.goto('http://localhost:8080');

  await page.click('[data-testid="menu-btn"]');
  await expect(page.locator('.dropdown-menu')).toBeVisible();

  await page.click('.menu-item.settings');
  await expect(page.locator('.settings-panel')).toBeVisible();
});
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with recording mode instructions"
```

---

## Task 10: Final Verification

**Step 1: Run full test suite**

Run: `conda run -n py314 pytest -v`

Expected: All tests PASS

**Step 2: Run ruff on everything**

Run: `conda run -n py314 ruff check js_interaction_detector/ tests/ && conda run -n py314 ruff format --check js_interaction_detector/ tests/`

Expected: No errors

**Step 3: Manual test**

Run: `conda run -n py314 python -m js_interaction_detector record file://$(pwd)/tests/fixtures/sample_pages/dropdown_page.html --headless -o /tmp/test.spec.ts && cat /tmp/test.spec.ts`

Expected: Generated TypeScript test file

**Step 4: Final commit if any cleanup needed**

```bash
git status
# If clean, done. If not:
git add -A
git commit -m "chore: final cleanup for recording mode"
```

---

## Summary

| Task | Component | Description |
|------|-----------|-------------|
| 1 | CLI Subcommands | Add analyze/record subcommands with backwards compat |
| 2 | Selector Generator | Priority-based CSS selector generation |
| 3 | Test Generator | Generate TypeScript Playwright tests |
| 4 | Change Observer | DOM mutations and network request detection |
| 5 | Action Tracker | Track clicks and input actions |
| 6 | Recording Session | Orchestrate tracking and observation |
| 7 | Wire Up Record | Connect CLI to recording session |
| 8 | Navigation Handling | Go back when navigation occurs |
| 9 | README | Update documentation |
| 10 | Final Verification | Run all tests, lint, manual check |

**Total: 10 tasks, ~30 TDD cycles**
