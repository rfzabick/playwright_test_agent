"""Tests for action tracker."""

from pathlib import Path

import pytest

from js_interaction_detector.page_loader import PageLoader
from js_interaction_detector.recorder.action_tracker import ActionTracker


@pytest.fixture
def simple_form_url():
    """Return the URL for the simple form test page."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
    return f"file://{fixtures_path}/simple_form.html"


class TestActionTracker:
    """Test the ActionTracker tracks user interactions."""

    @pytest.mark.asyncio
    async def test_tracks_click_action(self, simple_form_url):
        """Tracks click on button."""
        # Given: A page with a form is loaded
        async with PageLoader() as loader:
            page = await loader.load(simple_form_url)

            # Given: An action tracker is started
            tracker = ActionTracker(page)
            await tracker.start()

            # When: A button is clicked
            await page.click('button[type="submit"]', no_wait_after=True)
            # Give JS time to process the click event
            await page.wait_for_timeout(100)

            # Then: Click action should be tracked
            actions = await tracker.get_actions()
            assert len(actions) == 1, "Expected one action to be tracked"

            # Then: Action should be a click
            action = actions[0]
            assert action["type"] == "click"
            assert "button" in action["selector"].lower()

    @pytest.mark.asyncio
    async def test_tracks_input_action(self, simple_form_url):
        """Tracks typing in input field."""
        # Given: A page with a form is loaded
        async with PageLoader() as loader:
            page = await loader.load(simple_form_url)

            # Given: An action tracker is started
            tracker = ActionTracker(page)
            await tracker.start()

            # When: Text is typed into an input field
            await page.fill("#email", "test@example.com")

            # Then: Fill action should be tracked
            actions = await tracker.get_actions()
            assert len(actions) == 1, "Expected one action to be tracked"

            # Then: Action should be a fill with value
            action = actions[0]
            assert action["type"] == "fill"
            assert action["value"] == "test@example.com"
            assert "#email" in action["selector"]

    @pytest.mark.asyncio
    async def test_tracks_multiple_actions_in_order(self, simple_form_url):
        """Tracks multiple actions in the order they occurred."""
        # Given: A page with a form is loaded
        async with PageLoader() as loader:
            page = await loader.load(simple_form_url)

            # Given: An action tracker is started
            tracker = ActionTracker(page)
            await tracker.start()

            # When: Multiple actions are performed
            await page.fill("#email", "test@example.com")
            await page.click('button[type="submit"]', no_wait_after=True)
            # Give JS time to process the click event
            await page.wait_for_timeout(100)

            # Then: Both actions should be tracked in order
            actions = await tracker.get_actions()
            assert len(actions) == 2, "Expected two actions to be tracked"

            # Then: First action should be fill
            assert actions[0]["type"] == "fill"
            assert actions[0]["value"] == "test@example.com"

            # Then: Second action should be click
            assert actions[1]["type"] == "click"

    @pytest.mark.asyncio
    async def test_debounces_input_actions(self, simple_form_url):
        """Debounces input events - updates value of existing fill action."""
        # Given: A page with a form is loaded
        async with PageLoader() as loader:
            page = await loader.load(simple_form_url)

            # Given: An action tracker is started
            tracker = ActionTracker(page)
            await tracker.start()

            # When: Text is typed into same field multiple times
            await page.fill("#email", "test")
            await page.fill("#email", "test@example.com")

            # Then: Only one fill action should exist with final value
            actions = await tracker.get_actions()
            assert len(actions) == 1, "Expected one action (debounced)"

            # Then: Action should have the final value
            action = actions[0]
            assert action["type"] == "fill"
            assert action["value"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_clear_actions(self, simple_form_url):
        """Clear actions removes all tracked actions."""
        # Given: A page with a form is loaded
        async with PageLoader() as loader:
            page = await loader.load(simple_form_url)

            # Given: An action tracker is started with some actions
            tracker = ActionTracker(page)
            await tracker.start()
            await page.click('button[type="submit"]')

            # When: Actions are cleared
            await tracker.clear()

            # Then: No actions should be tracked
            actions = await tracker.get_actions()
            assert len(actions) == 0, "Expected no actions after clear"

    @pytest.mark.asyncio
    async def test_selector_stability_marked(self, simple_form_url):
        """Actions include is_fragile flag for selector stability."""
        # Given: A page with a form is loaded
        async with PageLoader() as loader:
            page = await loader.load(simple_form_url)

            # Given: An action tracker is started
            tracker = ActionTracker(page)
            await tracker.start()

            # When: An element with id is clicked
            await page.click("#email")

            # Then: Action should be marked as stable (not fragile)
            actions = await tracker.get_actions()
            assert len(actions) == 1
            assert "is_fragile" in actions[0]
            # ID selectors should not be fragile
            assert actions[0]["is_fragile"] is False
