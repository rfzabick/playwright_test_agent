"""Tests for enumeration test generator."""

import pytest

from js_interaction_detector.enumerator.extractor import AccessibilityElement
from js_interaction_detector.enumerator.test_generator import (
    escape_string,
    generate_button_test,
    generate_checkbox_test,
    generate_enumeration_tests,
    generate_link_test,
    generate_textbox_test,
)


class TestEscapeString:
    """Tests for escape_string function."""

    def test_escapes_single_quotes(self):
        """Escapes single quotes for TypeScript strings."""
        result = escape_string("Don't click")
        assert result == "Don\\'t click"

    def test_escapes_backslashes(self):
        """Escapes backslashes for TypeScript strings."""
        result = escape_string("path\\to\\file")
        assert result == "path\\\\to\\\\file"

    def test_handles_empty_string(self):
        """Handles empty string."""
        result = escape_string("")
        assert result == ""


class TestGenerateButtonTest:
    """Tests for generate_button_test function."""

    def test_generates_button_test(self):
        """Generates test code for a button."""
        el = AccessibilityElement(role="button", name="Submit")
        code = generate_button_test(el)

        assert "button \"Submit\" is interactive" in code
        assert "getByRole('button', { name: 'Submit' })" in code
        assert "toBeVisible()" in code
        assert "toBeEnabled()" in code

    def test_handles_quotes_in_name(self):
        """Escapes quotes in button name."""
        el = AccessibilityElement(role="button", name="Don't submit")
        code = generate_button_test(el)

        assert "Don\\'t submit" in code

    def test_includes_index_for_duplicates(self):
        """Includes index when there are duplicate names."""
        el = AccessibilityElement(role="button", name="Submit")
        code = generate_button_test(el, index=2)

        assert "button \"Submit\" (2)" in code


class TestGenerateLinkTest:
    """Tests for generate_link_test function."""

    def test_generates_link_test(self):
        """Generates test code for a link."""
        el = AccessibilityElement(role="link", name="Click here")
        code = generate_link_test(el)

        assert "link \"Click here\" is present" in code
        assert "getByRole('link', { name: 'Click here' })" in code
        assert "toHaveAttribute('href'" in code


class TestGenerateTextboxTest:
    """Tests for generate_textbox_test function."""

    def test_generates_textbox_test(self):
        """Generates test code for a textbox."""
        el = AccessibilityElement(role="textbox", name="Email")
        code = generate_textbox_test(el)

        assert "textbox \"Email\" accepts input" in code
        assert "getByRole('textbox', { name: 'Email' })" in code
        assert "toBeEditable()" in code
        assert "fill('test input')" in code
        assert "toHaveValue('test input')" in code

    def test_handles_searchbox_role(self):
        """Uses searchbox role when specified."""
        el = AccessibilityElement(role="searchbox", name="Search")
        code = generate_textbox_test(el)

        assert "searchbox \"Search\" accepts input" in code
        assert "getByRole('searchbox', { name: 'Search' })" in code


class TestGenerateCheckboxTest:
    """Tests for generate_checkbox_test function."""

    def test_generates_checkbox_test(self):
        """Generates test code for a checkbox."""
        el = AccessibilityElement(role="checkbox", name="Remember me")
        code = generate_checkbox_test(el)

        assert "checkbox \"Remember me\" is toggleable" in code
        assert "getByRole('checkbox', { name: 'Remember me' })" in code
        assert "check()" in code
        assert "toBeChecked()" in code


class TestGenerateEnumerationTests:
    """Tests for generate_enumeration_tests function."""

    def test_generates_complete_test_file(self):
        """Generates a complete TypeScript test file."""
        elements = [
            AccessibilityElement(role="button", name="Submit"),
            AccessibilityElement(role="textbox", name="Email"),
        ]

        content, warnings = generate_enumeration_tests("http://example.com", elements)

        assert "import { test, expect } from '@playwright/test'" in content
        assert "test.describe('Accessibility Elements'" in content
        assert "page.goto('http://example.com')" in content
        assert "Buttons" in content
        assert "Text Inputs" in content

    def test_groups_elements_by_role(self):
        """Groups tests by element role."""
        elements = [
            AccessibilityElement(role="button", name="Submit"),
            AccessibilityElement(role="button", name="Cancel"),
            AccessibilityElement(role="link", name="Home"),
        ]

        content, warnings = generate_enumeration_tests("http://example.com", elements)

        # Should have describe blocks for Buttons and Links
        assert "test.describe('Buttons'" in content
        assert "test.describe('Links'" in content

    def test_warns_about_unnamed_elements(self):
        """Generates warnings for elements without names."""
        elements = [
            AccessibilityElement(role="button", name="Submit"),
            AccessibilityElement(role="button", name=""),  # No name
            AccessibilityElement(role="textbox", name=""),  # No name
        ]

        content, warnings = generate_enumeration_tests("http://example.com", elements)

        # Should warn about unnamed elements
        assert len(warnings) == 2
        assert any("button" in w for w in warnings)
        assert any("textbox" in w for w in warnings)

    def test_handles_duplicate_names(self):
        """Adds indices for elements with duplicate names."""
        elements = [
            AccessibilityElement(role="button", name="Submit"),
            AccessibilityElement(role="button", name="Submit"),
        ]

        content, warnings = generate_enumeration_tests("http://example.com", elements)

        assert "button \"Submit\" (1)" in content
        assert "button \"Submit\" (2)" in content

    def test_returns_empty_tests_for_no_named_elements(self):
        """Returns minimal test file when no named elements."""
        elements = [
            AccessibilityElement(role="button", name=""),
        ]

        content, warnings = generate_enumeration_tests("http://example.com", elements)

        # Should still have the test structure
        assert "test.describe('Accessibility Elements'" in content
        # But no actual test blocks for buttons
        assert "test.describe('Buttons'" not in content
