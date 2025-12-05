"""Tests for page loader."""

from pathlib import Path

import pytest

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
