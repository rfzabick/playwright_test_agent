"""Tests for recording session."""

from pathlib import Path

import pytest

from js_interaction_detector.recorder.session import RecordingSession


@pytest.fixture
def dropdown_page_url():
    """Return the URL for the dropdown test page."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
    return f"file://{fixtures_path}/dropdown_page.html"


class TestRecordingSession:
    """Test the RecordingSession orchestrates action tracking and change observation."""

    def given_dropdown_page_url(self, fixtures_path):
        """Set up the URL for dropdown test page."""
        self.url = f"file://{fixtures_path}/dropdown_page.html"

    async def when_session_records_interaction(self):
        """Record a click interaction on the dropdown toggle button."""
        async with RecordingSession(self.url, headed=False) as session:
            # Simulate user clicking the toggle button
            await session.page.click("#toggle-btn")
            await session.page.wait_for_timeout(200)
            self.recorded_actions = session.get_recorded_actions()

    def then_action_was_recorded_with_changes(self):
        """Verify that the action was recorded with changes."""
        assert len(self.recorded_actions) > 0, "Expected at least one recorded action"
        action = self.recorded_actions[0]
        assert action.action_type == "click", (
            f"Expected click, got {action.action_type}"
        )
        assert len(action.changes) > 0, "Expected changes to be recorded"

    @pytest.mark.asyncio
    async def test_records_action_with_dom_changes(self, dropdown_page_url):
        """Records click action and observes DOM changes."""
        # Given: A dropdown page URL
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
        self.given_dropdown_page_url(fixtures_path)

        # When: Session records interaction
        await self.when_session_records_interaction()

        # Then: Action was recorded with changes
        self.then_action_was_recorded_with_changes()

    @pytest.mark.asyncio
    async def test_session_provides_page_property(self, dropdown_page_url):
        """Session provides access to the page object."""
        # Given: A dropdown page URL
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
        url = f"file://{fixtures_path}/dropdown_page.html"

        # When: Session is entered
        async with RecordingSession(url, headed=False) as session:
            # Then: Page property is accessible
            assert session.page is not None
            # Then: Page can be interacted with
            title = await session.page.title()
            assert title == "Dropdown Test"

    @pytest.mark.asyncio
    async def test_empty_session_returns_no_actions(self, dropdown_page_url):
        """Session with no interactions returns empty action list."""
        # Given: A dropdown page URL
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
        url = f"file://{fixtures_path}/dropdown_page.html"

        # When: Session is entered but no interactions are performed
        async with RecordingSession(url, headed=False) as session:
            recorded_actions = session.get_recorded_actions()

        # Then: No actions are recorded
        assert len(recorded_actions) == 0, (
            "Expected no actions without user interaction"
        )

    @pytest.mark.asyncio
    async def test_records_multiple_actions(self, dropdown_page_url):
        """Records multiple actions in sequence.

        Note: Due to v1 batch processing limitation, all changes are attributed
        to the first action. This test verifies both actions are recorded, but
        change attribution is not tested here.
        """
        # Given: A dropdown page URL
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
        url = f"file://{fixtures_path}/dropdown_page.html"

        # When: Multiple interactions are performed
        async with RecordingSession(url, headed=False) as session:
            # Click toggle button twice
            await session.page.click("#toggle-btn")
            await session.page.wait_for_timeout(200)
            await session.page.click("#toggle-btn")
            await session.page.wait_for_timeout(200)
            recorded_actions = session.get_recorded_actions()

        # Then: Multiple actions are recorded
        assert len(recorded_actions) == 2, (
            f"Expected 2 actions, got {len(recorded_actions)}"
        )
        assert all(action.action_type == "click" for action in recorded_actions)
        # Note: In v1, first action gets all changes, second gets none
        # This is a known limitation documented in _process_pending_actions

    @pytest.mark.asyncio
    async def test_page_property_raises_outside_context(self, dropdown_page_url):
        """Accessing page property outside context raises RuntimeError."""
        # Given: A recording session (not entered)
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_pages"
        url = f"file://{fixtures_path}/dropdown_page.html"
        session = RecordingSession(url, headed=False)

        # When: Attempting to access page property
        # Then: RuntimeError is raised
        with pytest.raises(
            RuntimeError, match="Page not available outside of session context"
        ):
            _ = session.page
