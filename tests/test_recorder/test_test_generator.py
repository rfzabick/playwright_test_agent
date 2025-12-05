"""Tests for Playwright test generation."""

from js_interaction_detector.recorder.test_generator import (
    CSSChange,
    DOMChange,
    NetworkRequest,
    RecordedAction,
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
        self.then_output_contains("await page.click('[data-testid=\"bell-icon\"]');")

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
