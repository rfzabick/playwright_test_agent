"""Generate Playwright tests from accessibility elements."""

import logging
from collections import defaultdict

from js_interaction_detector.enumerator.extractor import AccessibilityElement

logger = logging.getLogger(__name__)


def escape_string(s: str) -> str:
    """Escape a string for use in TypeScript single-quoted strings."""
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _get_nth_selector(index: int | None, total: int | None) -> str:
    """Get the .first()/.nth() selector suffix for duplicate elements.

    Args:
        index: 1-based index of this element among duplicates
        total: Total number of duplicates

    Returns:
        Selector suffix like ".first()" or ".nth(1)" or empty string
    """
    if index is None or total is None or total <= 1:
        return ""
    if index == 1:
        return ".first()"
    # nth() is 0-based, so index 2 becomes nth(1)
    return f".nth({index - 1})"


def generate_button_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a button element.

    Args:
        element: The button element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"button \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is interactive', async ({{ page }}) => {{
    const button = page.getByRole('button', {{ name: '{name}' }}){nth};
    await expect(button).toBeVisible();
    await expect(button).toBeEnabled();
  }});"""


def generate_link_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a link element.

    Args:
        element: The link element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"link \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is present', async ({{ page }}) => {{
    const link = page.getByRole('link', {{ name: '{name}' }}){nth};
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', /.+/);
  }});"""


def generate_textbox_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a textbox element.

    Args:
        element: The textbox element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    role = element.role  # Could be 'textbox' or 'searchbox'
    test_name = f"{role} \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} accepts input', async ({{ page }}) => {{
    const input = page.getByRole('{role}', {{ name: '{name}' }}){nth};
    await expect(input).toBeVisible();
    await expect(input).toBeEditable();
    await input.fill('test input');
    await expect(input).toHaveValue('test input');
  }});"""


def generate_checkbox_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a checkbox element.

    Args:
        element: The checkbox element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"checkbox \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is toggleable', async ({{ page }}) => {{
    const checkbox = page.getByRole('checkbox', {{ name: '{name}' }}){nth};
    await expect(checkbox).toBeVisible();
    await checkbox.check();
    await expect(checkbox).toBeChecked();
  }});"""


def generate_radio_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a radio button element.

    Args:
        element: The radio element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"radio \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    # Note: Many UI frameworks hide the actual radio input and style a wrapper.
    # We just verify the radio exists in the accessibility tree - interaction testing
    # would require framework-specific knowledge of the wrapper structure.
    return f"""  test('{escape_string(test_name)} exists', async ({{ page }}) => {{
    const radio = page.getByRole('radio', {{ name: '{name}' }}){nth};
    await expect(radio).toBeAttached();
  }});"""


def generate_combobox_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a combobox element.

    Args:
        element: The combobox element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"combobox \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is interactive', async ({{ page }}) => {{
    const combobox = page.getByRole('combobox', {{ name: '{name}' }}){nth};
    await expect(combobox).toBeVisible();
    await expect(combobox).toBeEnabled();
  }});"""


def generate_slider_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a slider element.

    Args:
        element: The slider element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"slider \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is adjustable', async ({{ page }}) => {{
    const slider = page.getByRole('slider', {{ name: '{name}' }}){nth};
    await expect(slider).toBeVisible();
    await expect(slider).toBeEnabled();
  }});"""


def generate_switch_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a switch element.

    Args:
        element: The switch element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"switch \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is toggleable', async ({{ page }}) => {{
    const switchEl = page.getByRole('switch', {{ name: '{name}' }}){nth};
    await expect(switchEl).toBeVisible();
    await switchEl.click();
  }});"""


def generate_tab_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for a tab element.

    Args:
        element: The tab element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    test_name = f"tab \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is selectable', async ({{ page }}) => {{
    const tab = page.getByRole('tab', {{ name: '{name}' }}){nth};
    await expect(tab).toBeVisible();
    await tab.click();
  }});"""


def generate_generic_test(
    element: AccessibilityElement, index: int | None = None, total: int | None = None
) -> str:
    """Generate test code for other interactive elements.

    Args:
        element: The element
        index: Optional index if there are duplicates (1-based)
        total: Total number of elements with same name

    Returns:
        TypeScript test code
    """
    name = escape_string(element.name)
    role = element.role
    test_name = f"{role} \"{element.name}\""
    if index is not None:
        test_name += f" ({index})"

    nth = _get_nth_selector(index, total)

    return f"""  test('{escape_string(test_name)} is interactive', async ({{ page }}) => {{
    const el = page.getByRole('{role}', {{ name: '{name}' }}){nth};
    await expect(el).toBeVisible();
  }});"""


# Map roles to their test generators
TEST_GENERATORS = {
    "button": generate_button_test,
    "link": generate_link_test,
    "textbox": generate_textbox_test,
    "searchbox": generate_textbox_test,
    "checkbox": generate_checkbox_test,
    "radio": generate_radio_test,
    "combobox": generate_combobox_test,
    "slider": generate_slider_test,
    "switch": generate_switch_test,
    "tab": generate_tab_test,
}


def generate_enumeration_tests(
    url: str,
    elements: list[AccessibilityElement],
) -> tuple[str, list[str]]:
    """Generate a complete Playwright test file from accessibility elements.

    Args:
        url: The URL of the page being tested
        elements: List of AccessibilityElement objects

    Returns:
        Tuple of (test file content, list of warning messages)
    """
    warnings: list[str] = []

    # Separate elements with and without names
    named_elements: list[AccessibilityElement] = []
    unnamed_counts: dict[str, int] = defaultdict(int)

    for el in elements:
        if el.has_name():
            named_elements.append(el)
        else:
            unnamed_counts[el.role] += 1

    # Generate warnings for unnamed elements
    for role, count in sorted(unnamed_counts.items()):
        warnings.append(
            f"Skipped {count} {role}(s) without accessible name. "
            "Consider adding aria-label attributes."
        )
        logger.warning(warnings[-1])

    # Group elements by role
    by_role: dict[str, list[AccessibilityElement]] = defaultdict(list)
    for el in named_elements:
        by_role[el.role].append(el)

    # Track duplicate names within each role
    def get_name_indices(
        elements: list[AccessibilityElement],
    ) -> dict[str, list[int]]:
        """Get indices of elements with duplicate names."""
        name_indices: dict[str, list[int]] = defaultdict(list)
        for i, el in enumerate(elements):
            name_indices[el.name].append(i)
        return name_indices

    # Generate test sections
    test_sections: list[str] = []

    # Define order of roles for consistent output
    role_order = [
        "button",
        "link",
        "textbox",
        "searchbox",
        "checkbox",
        "radio",
        "combobox",
        "slider",
        "switch",
        "tab",
        "menuitem",
        "option",
        "spinbutton",
    ]

    for role in role_order:
        if role not in by_role:
            continue

        role_elements = by_role[role]
        name_indices = get_name_indices(role_elements)

        # Determine display name for the role in describe block
        role_display = {
            "textbox": "Text Inputs",
            "searchbox": "Search Inputs",
            "checkbox": "Checkboxes",
            "radio": "Radio Buttons",
            "combobox": "Comboboxes",
            "slider": "Sliders",
            "switch": "Switches",
            "tab": "Tabs",
            "menuitem": "Menu Items",
            "option": "Options",
            "spinbutton": "Spin Buttons",
        }.get(role, f"{role.title()}s")

        tests: list[str] = []
        generator = TEST_GENERATORS.get(role, generate_generic_test)

        for i, el in enumerate(role_elements):
            # Determine if we need to add index for duplicates
            indices = name_indices[el.name]
            if len(indices) > 1:
                # Find position within duplicates (1-based)
                pos = indices.index(i) + 1
                total = len(indices)
                test_code = generator(el, index=pos, total=total)
            else:
                test_code = generator(el)

            tests.append(test_code)

        if tests:
            section = f"""  test.describe('{role_display}', () => {{
{chr(10).join(tests)}
  }});"""
            test_sections.append(section)

    # Assemble complete test file
    test_content = f"""import {{ test, expect }} from '@playwright/test';

test.describe('Accessibility Elements', () => {{
  test.beforeEach(async ({{ page }}) => {{
    await page.goto('{url}');
  }});

{chr(10).join(test_sections)}
}});
"""

    logger.info(f"Generated tests for {len(named_elements)} elements")
    return test_content, warnings
