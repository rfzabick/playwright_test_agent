"""Tests for change observer."""

from pathlib import Path

import pytest

from js_interaction_detector.page_loader import PageLoader
from js_interaction_detector.recorder.change_observer import ChangeObserver
from js_interaction_detector.recorder.test_generator import (
    CSSChange,
    NetworkRequest,
)


@pytest.fixture
def dropdown_page_url():
    """Return the URL for the dropdown test page."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
    return f"file://{fixtures_path}/dropdown_page.html"


@pytest.fixture
def api_call_page_url():
    """Return the URL for the API call test page."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
    return f"file://{fixtures_path}/api_call_page.html"


class TestChangeObserver:
    """Test the ChangeObserver detects DOM changes."""

    @pytest.mark.asyncio
    async def test_detects_dropdown_shown(self, dropdown_page_url):
        """Detects when dropdown is shown."""
        # Given: A page with a dropdown is loaded
        async with PageLoader() as loader:
            page = await loader.load(dropdown_page_url)

            # Given: A change observer is started
            observer = ChangeObserver(page)
            await observer.start()

            # When: The dropdown is toggled to show
            await observer.before_action()
            await page.click("#toggle-btn")
            changes = await observer.after_action()

            # Then: Visibility change should be detected
            css_changes = [c for c in changes if isinstance(c, CSSChange)]
            assert len(css_changes) > 0, "Expected CSS changes to be detected"

            # Then: Should be a display or visibility change on the dropdown
            display_changes = [
                c
                for c in css_changes
                if c.property == "display" and "dropdown" in c.selector
            ]
            assert len(display_changes) > 0, (
                "Expected display change on dropdown element"
            )

    @pytest.mark.asyncio
    async def test_detects_dropdown_hidden(self, dropdown_page_url):
        """Detects when dropdown is hidden (toggled back)."""
        # Given: A page with a dropdown is loaded
        async with PageLoader() as loader:
            page = await loader.load(dropdown_page_url)

            # Given: A change observer is started
            observer = ChangeObserver(page)
            await observer.start()

            # Given: The dropdown is shown first
            await observer.before_action()
            await page.click("#toggle-btn")
            await observer.after_action()

            # When: The dropdown is toggled to hide
            await observer.before_action()
            await page.click("#toggle-btn")
            changes = await observer.after_action()

            # Then: Visibility change should be detected
            css_changes = [c for c in changes if isinstance(c, CSSChange)]
            assert len(css_changes) > 0, "Expected CSS changes to be detected"

            # Then: Should be a display or visibility change on the dropdown
            display_changes = [
                c
                for c in css_changes
                if c.property == "display" and "dropdown" in c.selector
            ]
            assert len(display_changes) > 0, (
                "Expected display change on dropdown element"
            )

    @pytest.mark.asyncio
    async def test_detects_network_requests(self, api_call_page_url):
        """Detects network requests made during user actions."""
        # Given: A page with API call functionality is loaded
        async with PageLoader() as loader:
            page = await loader.load(api_call_page_url)

            # Given: A change observer is started
            observer = ChangeObserver(page)
            await observer.start()

            # When: A button is clicked that triggers an API call
            await observer.before_action()
            await page.click("#fetch-btn")
            changes = await observer.after_action()

            # Then: Network request should be detected
            network_requests = [c for c in changes if isinstance(c, NetworkRequest)]
            assert len(network_requests) > 0, "Expected network request to be detected"

            # Then: Request should be to httpbin.org
            httpbin_requests = [
                r for r in network_requests if "httpbin.org" in r.url_pattern
            ]
            assert len(httpbin_requests) > 0, (
                "Expected request to httpbin.org to be detected"
            )
