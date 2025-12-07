"""Extract interactive elements from the accessibility tree."""

import logging
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Roles that represent interactive elements
INTERACTIVE_ROLES = frozenset(
    {
        "button",
        "link",
        "textbox",
        "checkbox",
        "radio",
        "combobox",
        "slider",
        "switch",
        "menuitem",
        "tab",
        "searchbox",
        "spinbutton",
        "option",
    }
)


@dataclass
class AccessibilityElement:
    """Represents an interactive element from the accessibility tree.

    Attributes:
        role: The ARIA role of the element (button, textbox, etc.)
        name: The accessible name of the element
        value: Current value (for inputs)
        checked: Whether the element is checked (for checkboxes/radios)
        disabled: Whether the element is disabled
        expanded: Whether the element is expanded (for comboboxes, etc.)
    """

    role: str
    name: str
    value: str | None = None
    checked: bool | None = None
    disabled: bool = False
    expanded: bool | None = None

    def has_name(self) -> bool:
        """Check if element has a non-empty accessible name."""
        return bool(self.name and self.name.strip())


async def extract_accessibility_tree(page: Page) -> dict[str, Any] | None:
    """Extract the full accessibility tree from a page.

    Args:
        page: Playwright Page object

    Returns:
        The accessibility tree as a dict, or None if extraction fails
    """
    try:
        snapshot = await page.accessibility.snapshot()
        logger.info("Accessibility tree extracted successfully")
        return snapshot
    except Exception as e:
        logger.error(f"Failed to extract accessibility tree: {e}")
        return None


def flatten_tree(
    node: dict[str, Any] | None,
    elements: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Flatten the accessibility tree into a list of nodes.

    Args:
        node: The current node in the tree
        elements: Accumulator list for elements

    Returns:
        List of all nodes in the tree
    """
    if elements is None:
        elements = []

    if node is None:
        return elements

    elements.append(node)

    for child in node.get("children", []):
        flatten_tree(child, elements)

    return elements


def filter_interactive_elements(
    nodes: list[dict[str, Any]],
) -> list[AccessibilityElement]:
    """Filter nodes to only interactive elements with names.

    Args:
        nodes: List of accessibility tree nodes

    Returns:
        List of AccessibilityElement objects for interactive elements
    """
    elements = []

    for node in nodes:
        role = node.get("role", "").lower()

        if role not in INTERACTIVE_ROLES:
            continue

        element = AccessibilityElement(
            role=role,
            name=node.get("name", ""),
            value=node.get("value"),
            checked=node.get("checked"),
            disabled=node.get("disabled", False),
            expanded=node.get("expanded"),
        )

        elements.append(element)

    logger.info(f"Found {len(elements)} interactive elements")
    return elements


async def extract_interactive_elements(page: Page) -> list[AccessibilityElement]:
    """Extract all interactive elements from a page's accessibility tree.

    This is the main entry point for accessibility tree extraction.

    Args:
        page: Playwright Page object

    Returns:
        List of AccessibilityElement objects representing interactive elements
    """
    tree = await extract_accessibility_tree(page)

    if tree is None:
        logger.warning("No accessibility tree available")
        return []

    nodes = flatten_tree(tree)
    logger.info(f"Flattened tree contains {len(nodes)} total nodes")

    elements = filter_interactive_elements(nodes)

    # Log summary by role
    role_counts: dict[str, int] = {}
    for el in elements:
        role_counts[el.role] = role_counts.get(el.role, 0) + 1

    for role, count in sorted(role_counts.items()):
        logger.info(f"  {role}: {count}")

    return elements
