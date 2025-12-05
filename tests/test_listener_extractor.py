"""Tests for event listener extraction."""

from pathlib import Path

import pytest

from js_interaction_detector.listener_extractor import extract_listeners
from js_interaction_detector.page_loader import PageLoader


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
        listener = next(
            item for item in self.listeners if selector_fragment in item.selector
        )
        assert event in listener.events

    def then_listener_code_contains(self, selector_fragment, text):
        listener = next(
            item for item in self.listeners if selector_fragment in item.selector
        )
        assert text in listener.code or text.lower() in listener.code.lower()

    def then_listener_has_element_info(self, selector_fragment, tag, input_type, name):
        listener = next(
            item for item in self.listeners if selector_fragment in item.selector
        )
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
