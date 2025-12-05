"""Generate Playwright TypeScript tests from recorded actions."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _escape_typescript_string(value: str) -> str:
    """Escape a string for use in TypeScript single-quoted string."""
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


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
        f"  await page.goto('{_escape_typescript_string(url)}');",
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
        lines.append(
            f"  await page.click('{_escape_typescript_string(action.selector)}');"
        )
    elif action.action_type == "type":
        escaped_selector = _escape_typescript_string(action.selector)
        escaped_value = _escape_typescript_string(action.value or "")
        lines.append(f"  await page.fill('{escaped_selector}', '{escaped_value}');")
    elif action.action_type == "press":
        escaped_selector = _escape_typescript_string(action.selector)
        escaped_value = _escape_typescript_string(action.value or "")
        lines.append(f"  await page.press('{escaped_selector}', '{escaped_value}');")
    else:
        lines.append(f"  // WARNING: Unknown action type '{action.action_type}'")

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
    escaped_selector = _escape_typescript_string(change.selector)
    if change.change_type == "added":
        return [f"  await expect(page.locator('{escaped_selector}')).toBeVisible();"]
    elif change.change_type == "removed":
        return [f"  await expect(page.locator('{escaped_selector}')).toBeHidden();"]
    elif change.change_type == "text_changed":
        escaped_text = _escape_typescript_string(change.text or "")
        return [
            f"  await expect(page.locator('{escaped_selector}')).toHaveText('{escaped_text}');"
        ]
    return []


def _generate_css_assertion(change: CSSChange) -> list[str]:
    """Generate assertion for a CSS change."""
    escaped_selector = _escape_typescript_string(change.selector)
    escaped_property = _escape_typescript_string(change.property)
    escaped_value = _escape_typescript_string(change.value)
    return [
        f"  await expect(page.locator('{escaped_selector}')).toHaveCSS('{escaped_property}', '{escaped_value}');"
    ]


def _generate_network_assertion(change: NetworkRequest) -> list[str]:
    """Generate assertion for a network request."""
    escaped_url_pattern = _escape_typescript_string(change.url_pattern)
    escaped_method = _escape_typescript_string(change.method)
    return [
        f"  await page.waitForRequest(req => req.url().includes('{escaped_url_pattern}') && req.method() === '{escaped_method}');"
    ]
