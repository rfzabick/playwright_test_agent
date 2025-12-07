"""Tests for selector generation."""

from js_interaction_detector.recorder.selector_generator import generate_selector


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

    def given_element_with_quoted_testid(self):
        self.element_info = {
            "tag": "button",
            "data-testid": 'test"quote',
        }

    def test_escapes_quotes_in_testid(self):
        """Quotes in data-testid are properly escaped."""
        self.given_element_with_quoted_testid()
        self.when_selector_is_generated()
        self.then_selector_is('[data-testid="test\\"quote"]')
        self.then_selector_is_not_fragile()

    def given_element_with_empty_id(self):
        self.element_info = {
            "tag": "div",
            "id": "",
            "classes": ["container"],
        }

    def test_empty_id_falls_back_to_classes(self):
        """Empty string id should fall back to next priority."""
        self.given_element_with_empty_id()
        self.when_selector_is_generated()
        self.then_selector_is("div.container")
        self.then_selector_is_fragile()

    def given_element_with_whitespace_classes(self):
        self.element_info = {
            "tag": "div",
            "classes": ["  ", "valid", "", "  another  "],
        }

    def test_filters_whitespace_only_classes(self):
        """Whitespace-only class names are filtered out."""
        self.given_element_with_whitespace_classes()
        self.when_selector_is_generated()
        self.then_selector_is("div.valid.another")
        self.then_selector_is_fragile()
