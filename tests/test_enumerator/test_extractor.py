"""Tests for accessibility tree extraction."""

from pathlib import Path

import pytest

from js_interaction_detector.enumerator.extractor import (
    AccessibilityElement,
    extract_interactive_elements,
    filter_interactive_elements,
    flatten_tree,
)
from js_interaction_detector.page_loader import PageLoader


@pytest.fixture
def fixtures_path():
    """Path to test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "sample_pages"


class TestAccessibilityElement:
    """Tests for AccessibilityElement dataclass."""

    def test_has_name_with_name(self):
        """Element with name returns True for has_name."""
        el = AccessibilityElement(role="button", name="Submit")
        assert el.has_name() is True

    def test_has_name_without_name(self):
        """Element without name returns False for has_name."""
        el = AccessibilityElement(role="button", name="")
        assert el.has_name() is False

    def test_has_name_with_whitespace_only(self):
        """Element with whitespace-only name returns False for has_name."""
        el = AccessibilityElement(role="button", name="   ")
        assert el.has_name() is False


class TestFlattenTree:
    """Tests for flatten_tree function."""

    def test_flattens_nested_tree(self):
        """Flattens a nested tree into a list."""
        tree = {
            "role": "WebArea",
            "name": "Page",
            "children": [
                {"role": "button", "name": "Submit"},
                {
                    "role": "form",
                    "name": "Login",
                    "children": [
                        {"role": "textbox", "name": "Email"},
                    ],
                },
            ],
        }

        nodes = flatten_tree(tree)

        assert len(nodes) == 4
        roles = [n["role"] for n in nodes]
        assert "WebArea" in roles
        assert "button" in roles
        assert "form" in roles
        assert "textbox" in roles

    def test_handles_none_input(self):
        """Returns empty list for None input."""
        nodes = flatten_tree(None)
        assert nodes == []

    def test_handles_no_children(self):
        """Handles nodes without children."""
        tree = {"role": "button", "name": "Submit"}
        nodes = flatten_tree(tree)
        assert len(nodes) == 1


class TestFilterInteractiveElements:
    """Tests for filter_interactive_elements function."""

    def test_filters_to_interactive_roles(self):
        """Only returns elements with interactive roles."""
        nodes = [
            {"role": "button", "name": "Submit"},
            {"role": "heading", "name": "Title"},
            {"role": "textbox", "name": "Email"},
            {"role": "text", "name": "Some text"},
            {"role": "link", "name": "Click here"},
        ]

        elements = filter_interactive_elements(nodes)

        roles = [el.role for el in elements]
        assert "button" in roles
        assert "textbox" in roles
        assert "link" in roles
        assert "heading" not in roles
        assert "text" not in roles

    def test_preserves_element_properties(self):
        """Preserves element properties in AccessibilityElement."""
        nodes = [
            {
                "role": "checkbox",
                "name": "Remember me",
                "checked": True,
                "disabled": False,
            },
        ]

        elements = filter_interactive_elements(nodes)

        assert len(elements) == 1
        el = elements[0]
        assert el.role == "checkbox"
        assert el.name == "Remember me"
        assert el.checked is True
        assert el.disabled is False


class TestExtractInteractiveElements:
    """Integration tests for extract_interactive_elements."""

    @pytest.fixture
    def accessible_form_url(self, fixtures_path):
        """URL to the accessible form fixture."""
        return f"file://{fixtures_path}/accessible_form.html"

    @pytest.mark.asyncio
    async def test_extracts_elements_from_form(self, accessible_form_url):
        """Extracts interactive elements from an accessible form."""
        async with PageLoader() as loader:
            page = await loader.load(accessible_form_url)
            elements = await extract_interactive_elements(page)

        # Should find: 2 textboxes, 1 checkbox, 1 button, 2 links
        roles = [el.role for el in elements]

        assert "textbox" in roles
        assert "checkbox" in roles
        assert "button" in roles
        assert "link" in roles

    @pytest.mark.asyncio
    async def test_captures_element_names(self, accessible_form_url):
        """Captures accessible names of elements."""
        async with PageLoader() as loader:
            page = await loader.load(accessible_form_url)
            elements = await extract_interactive_elements(page)

        names = [el.name for el in elements]

        assert "Email address" in names
        assert "Password" in names
        assert "Sign in" in names
        assert "Forgot password?" in names

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_interactive_elements(self, fixtures_path):
        """Returns empty list when page has no interactive elements."""
        # Create a simple page with just text
        url = f"file://{fixtures_path}/dropdown_page.html"

        async with PageLoader() as loader:
            page = await loader.load(url)
            elements = await extract_interactive_elements(page)

        # dropdown_page.html has a button, so this should have elements
        assert len(elements) > 0
