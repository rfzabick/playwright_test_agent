"""Track user actions (clicks and input) via injected JavaScript."""

import logging
from typing import Any

from playwright.async_api import Page

from .selector_generator import generate_selector

logger = logging.getLogger(__name__)


class ActionTracker:
    """Track user interactions (clicks and input) on a page."""

    def __init__(self, page: Page):
        """Initialize the action tracker.

        Args:
            page: The Playwright page to track actions on
        """
        self._page = page
        self._actions: list[dict[str, Any]] = []

    async def start(self) -> None:
        """Start tracking actions by injecting JavaScript listeners."""
        # Inject JavaScript to track interactions
        await self._page.evaluate("""
            () => {
                // Create storage for actions
                window.__actionTracker = {
                    actions: []
                };

                // Track clicks
                document.addEventListener('click', (event) => {
                    const element = event.target;

                    // Prevent form submissions to avoid page navigation
                    if (element.tagName === 'BUTTON' && element.type === 'submit') {
                        event.preventDefault();
                    }

                    // Capture element info
                    const elementInfo = {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || '',
                        classes: Array.from(element.classList),
                        'data-testid': element.getAttribute('data-testid') || '',
                        'aria-label': element.getAttribute('aria-label') || '',
                        timestamp: Date.now()
                    };

                    window.__actionTracker.actions.push({
                        type: 'click',
                        elementInfo: elementInfo
                    });
                }, true);  // Use capture phase

                // Track input events (debounced)
                let inputDebounceMap = new Map();

                document.addEventListener('input', (event) => {
                    const element = event.target;

                    // Only track input elements
                    if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)) {
                        return;
                    }

                    // Capture element info
                    const elementInfo = {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || '',
                        classes: Array.from(element.classList),
                        'data-testid': element.getAttribute('data-testid') || '',
                        'aria-label': element.getAttribute('aria-label') || '',
                        timestamp: Date.now()
                    };

                    // Create unique key for element
                    const elementKey = element.id ||
                                     element.getAttribute('data-testid') ||
                                     element.getAttribute('name') ||
                                     JSON.stringify(elementInfo);

                    // Debounce: remove previous action for same element
                    if (inputDebounceMap.has(elementKey)) {
                        const oldIndex = inputDebounceMap.get(elementKey);
                        // Mark as removed
                        window.__actionTracker.actions[oldIndex] = null;
                    }

                    // Add new action
                    const newIndex = window.__actionTracker.actions.length;
                    window.__actionTracker.actions.push({
                        type: 'fill',
                        elementInfo: elementInfo,
                        value: element.value
                    });
                    inputDebounceMap.set(elementKey, newIndex);
                }, true);  // Use capture phase
            }
        """)
        logger.info("Action tracking started")

    async def get_actions(self) -> list[dict[str, Any]]:
        """Get all tracked actions.

        Returns:
            List of action dicts with: type, selector, is_fragile, value (optional)
        """
        # Fetch actions from browser and process them
        actions = await self._fetch_and_convert_actions()
        logger.info(f"Retrieved {len(actions)} actions")
        return actions

    async def clear(self) -> None:
        """Clear all tracked actions."""
        await self._page.evaluate("""
            () => {
                if (window.__actionTracker) {
                    window.__actionTracker.actions = [];
                }
            }
        """)
        logger.info("Action tracker cleared")

    async def _fetch_and_convert_actions(self) -> list[dict[str, Any]]:
        """Async version of syncing actions from browser."""
        # Fetch raw actions from browser
        raw_actions = await self._page.evaluate("""
            () => {
                if (!window.__actionTracker) {
                    return [];
                }
                // Filter out null entries (debounced items)
                return window.__actionTracker.actions.filter(a => a !== null);
            }
        """)

        # Convert to our format
        actions = []
        for raw_action in raw_actions:
            element_info = raw_action["elementInfo"]
            selector, is_fragile = generate_selector(element_info)

            action = {
                "type": raw_action["type"],
                "selector": selector,
                "is_fragile": is_fragile,
            }

            # Add value for fill actions
            if raw_action["type"] == "fill":
                action["value"] = raw_action.get("value", "")

            actions.append(action)

        logger.info(f"Synced {len(actions)} actions from browser")
        return actions
