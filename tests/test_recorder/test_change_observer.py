"""Tests for change observer."""

from pathlib import Path

import pytest


@pytest.fixture
def dropdown_page_url():
    """Return the URL for the dropdown test page."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
    return f"file://{fixtures_path}/dropdown_page.html"


class TestChangeObserver:
    """Test the ChangeObserver detects DOM changes."""

    @pytest.mark.asyncio
    async def given_page_loaded(self, dropdown_page_url):
        """Load the dropdown page."""
        from js_interaction_detector.page_loader import PageLoader

        self.loader = PageLoader()
        await self.loader.__aenter__()
        self.page = await self.loader.load(dropdown_page_url)

    @pytest.mark.asyncio
    async def given_observer_started(self):
        """Start the change observer."""
        from js_interaction_detector.recorder.change_observer import ChangeObserver

        self.observer = ChangeObserver(self.page)
        await self.observer.start()

    @pytest.mark.asyncio
    async def when_dropdown_is_toggled_to_show(self):
        """Click the toggle button to show dropdown."""
        await self.observer.before_action()
        await self.page.click("#toggle-btn")
        self.changes = await self.observer.after_action()

    @pytest.mark.asyncio
    async def when_dropdown_is_toggled_to_hide(self):
        """Click the toggle button to hide dropdown."""
        await self.observer.before_action()
        await self.page.click("#toggle-btn")
        self.changes = await self.observer.after_action()

    @pytest.mark.asyncio
    async def cleanup(self):
        """Close the browser."""
        await self.page.close()
        await self.loader.close()

    def then_visibility_change_detected(self):
        """Verify visibility change was detected."""
        # Should have detected a CSS change (display: none -> block or vice versa)
        from js_interaction_detector.recorder.test_generator import CSSChange

        css_changes = [c for c in self.changes if isinstance(c, CSSChange)]
        assert len(css_changes) > 0, "Expected CSS changes to be detected"

        # Should be a display or visibility change on the dropdown
        display_changes = [
            c
            for c in css_changes
            if c.property == "display" and "dropdown" in c.selector
        ]
        assert len(display_changes) > 0, "Expected display change on dropdown element"

    @pytest.mark.asyncio
    async def test_detects_dropdown_shown(self, dropdown_page_url):
        """Detects when dropdown is shown."""
        await self.given_page_loaded(dropdown_page_url)
        await self.given_observer_started()
        await self.when_dropdown_is_toggled_to_show()
        self.then_visibility_change_detected()
        await self.cleanup()

    @pytest.mark.asyncio
    async def test_detects_dropdown_hidden(self, dropdown_page_url):
        """Detects when dropdown is hidden (toggled back)."""
        await self.given_page_loaded(dropdown_page_url)
        await self.given_observer_started()

        # First toggle to show
        await self.observer.before_action()
        await self.page.click("#toggle-btn")
        await self.observer.after_action()

        # Then toggle to hide (this is what we're testing)
        await self.when_dropdown_is_toggled_to_hide()
        self.then_visibility_change_detected()
        await self.cleanup()
