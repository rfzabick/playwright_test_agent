"""Recording session that orchestrates action tracking and change observation."""

import logging
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Browser, Page, Playwright, async_playwright

from js_interaction_detector.recorder.action_tracker import ActionTracker
from js_interaction_detector.recorder.change_observer import ChangeObserver
from js_interaction_detector.recorder.test_generator import RecordedAction

logger = logging.getLogger(__name__)


@dataclass
class RecordingSession:
    """Orchestrates ActionTracker and ChangeObserver to record user interactions.

    This session manages the full recording lifecycle:
    - Launches browser and navigates to URL
    - Sets up action tracking and change observation
    - Processes pending actions to match them with changes
    - Returns list of recorded actions with their effects

    Usage:
        async with RecordingSession(url, headed=False) as session:
            await session.page.click("#button")
            actions = session.get_recorded_actions()
    """

    url: str
    headed: bool = True
    settle_timeout: int = 200

    # Private fields (not part of constructor args)
    _playwright: Playwright | None = field(default=None, init=False, repr=False)
    _browser: Browser | None = field(default=None, init=False, repr=False)
    _page: Page | None = field(default=None, init=False, repr=False)
    _tracker: ActionTracker | None = field(default=None, init=False, repr=False)
    _observer: ChangeObserver | None = field(default=None, init=False, repr=False)
    _recorded_actions: list[RecordedAction] = field(
        default_factory=list, init=False, repr=False
    )

    @property
    def page(self) -> Page:
        """Get the Playwright page object for interaction.

        Returns:
            The Playwright Page object

        Raises:
            RuntimeError: If accessed outside of async context manager
        """
        if self._page is None:
            raise RuntimeError("Page not available outside of session context")
        return self._page

    async def __aenter__(self) -> RecordingSession:
        """Enter the async context manager and set up recording.

        Returns:
            The RecordingSession instance
        """
        logger.info(f"Starting recording session for {self.url}")

        # Launch Playwright browser
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=not self.headed)
        self._page = await self._browser.new_page()

        # Navigate to URL
        await self._page.goto(self.url, wait_until="networkidle")
        logger.info(f"Navigated to {self.url}")

        # Set up action tracking and change observation
        self._tracker = ActionTracker(self._page)
        self._observer = ChangeObserver(self._page, settle_timeout=self.settle_timeout)

        await self._tracker.start()
        await self._observer.start()

        logger.info("Recording session started")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context manager and clean up.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        # Process any pending actions before cleanup
        await self._process_pending_actions()

        # Close browser and stop playwright
        if self._browser:
            await self._browser.close()
            logger.info("Browser closed")

        if self._playwright:
            await self._playwright.stop()
            logger.info("Playwright stopped")

        logger.info("Recording session ended")

    async def _process_pending_actions(self) -> None:
        """Process pending actions by matching them with observed changes.

        This method:
        1. Retrieves all tracked actions from the ActionTracker
        2. For each action, gets the corresponding changes from ChangeObserver
        3. Creates RecordedAction objects combining actions with their changes
        4. Stores them in _recorded_actions list
        """
        if not self._tracker or not self._observer:
            logger.warning("Tracker or observer not initialized")
            return

        actions = await self._tracker.get_actions()
        logger.info(f"Processing {len(actions)} pending actions")

        for action_data in actions:
            # Get changes for this action
            changes = await self._observer.after_action()

            # Create RecordedAction
            recorded = RecordedAction(
                action_type=action_data["type"],
                selector=action_data["selector"],
                changes=changes,
                value=action_data.get("value"),
            )

            self._recorded_actions.append(recorded)
            logger.info(
                f"Recorded {action_data['type']} action on {action_data['selector']} "
                f"with {len(changes)} changes"
            )

    def get_recorded_actions(self) -> list[RecordedAction]:
        """Get the list of recorded actions with their changes.

        Returns:
            List of RecordedAction objects
        """
        logger.info(f"Returning {len(self._recorded_actions)} recorded actions")
        return self._recorded_actions
