"""Observe DOM mutations and network requests during user actions."""

import logging
from typing import Any

from playwright.async_api import Page, Request

from js_interaction_detector.recorder.selector_generator import generate_selector
from js_interaction_detector.recorder.test_generator import (
    CSSChange,
    DOMChange,
    NetworkRequest,
)

logger = logging.getLogger(__name__)

# JavaScript to inject MutationObserver
MUTATION_OBSERVER_SCRIPT = """
(() => {
    // Store mutations in a global array
    window.__mutations__ = [];

    // Helper to serialize element info
    function getElementInfo(el) {
        return {
            tag: el.tagName.toLowerCase(),
            id: el.id || '',
            classes: Array.from(el.classList),
            'data-testid': el.getAttribute('data-testid') || '',
            'aria-label': el.getAttribute('aria-label') || ''
        };
    }

    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        window.__mutations__.push({
                            type: 'childList',
                            action: 'added',
                            elementInfo: getElementInfo(node)
                        });
                    }
                });
                mutation.removedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        window.__mutations__.push({
                            type: 'childList',
                            action: 'removed',
                            elementInfo: getElementInfo(node)
                        });
                    }
                });
            } else if (mutation.type === 'attributes') {
                const el = mutation.target;
                window.__mutations__.push({
                    type: 'attributes',
                    attributeName: mutation.attributeName,
                    elementInfo: getElementInfo(el),
                    oldValue: mutation.oldValue,
                    newValue: el.getAttribute(mutation.attributeName)
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        attributes: true,
        attributeOldValue: true,
        subtree: true,
        attributeFilter: ['style', 'class', 'hidden']
    });
})();
"""


class ChangeObserver:
    """Observes DOM mutations and network requests during user actions."""

    def __init__(self, page: Page, settle_timeout: int = 500):
        """Initialize the change observer.

        Args:
            page: The Playwright Page to observe
            settle_timeout: Milliseconds to wait for changes to settle after action
        """
        self.page = page
        self.settle_timeout = settle_timeout
        self._network_requests: list[dict[str, str]] = []
        logger.info(
            f"ChangeObserver initialized with settle_timeout={settle_timeout}ms"
        )

    async def start(self) -> None:
        """Start observing changes by injecting the MutationObserver script."""
        await self.page.evaluate(MUTATION_OBSERVER_SCRIPT)
        logger.info("MutationObserver script injected")

        # Set up network request listener
        def on_request(request: Request) -> None:
            # Filter out static assets
            url = request.url
            if not any(
                url.endswith(ext)
                for ext in [
                    ".js",
                    ".css",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".svg",
                    ".ico",
                    ".woff",
                    ".woff2",
                    ".ttf",
                ]
            ):
                self._network_requests.append({"method": request.method, "url": url})
                logger.info(f"Network request tracked: {request.method} {url}")
            else:
                logger.debug(
                    f"Network request filtered (static asset): {request.method} {url}"
                )

        self.page.on("request", on_request)
        logger.info("Network request listener attached")

    async def before_action(self) -> None:
        """Clear mutations before performing an action."""
        await self.page.evaluate("window.__mutations__ = [];")
        self._network_requests.clear()
        logger.info("Mutations and network requests cleared before action")

    async def after_action(
        self,
    ) -> list[DOMChange | CSSChange | NetworkRequest]:
        """Collect changes after performing an action.

        Returns:
            List of detected changes (DOMChange, CSSChange, NetworkRequest)
        """
        # Wait for changes to settle
        await self.page.wait_for_timeout(self.settle_timeout)
        logger.info(f"Waited {self.settle_timeout}ms for changes to settle")

        # Collect mutations
        mutations = await self.page.evaluate("window.__mutations__")
        logger.info(f"Collected {len(mutations)} mutations")

        changes: list[DOMChange | CSSChange | NetworkRequest] = []

        # Process mutations
        for mutation in mutations:
            if mutation["type"] == "attributes":
                change = await self._process_attribute_mutation(mutation)
                if change:
                    changes.append(change)
            elif mutation["type"] == "childList":
                change = await self._process_childlist_mutation(mutation)
                if change:
                    changes.append(change)

        # Process network requests
        for req in self._network_requests:
            changes.append(NetworkRequest(method=req["method"], url_pattern=req["url"]))
            logger.info(f"Network request change: {req['method']} {req['url']}")

        logger.info(f"Total changes detected: {len(changes)}")
        return changes

    async def _process_attribute_mutation(
        self, mutation: dict[str, Any]
    ) -> CSSChange | None:
        """Process an attribute mutation into a CSSChange.

        Args:
            mutation: The mutation object from JavaScript

        Returns:
            CSSChange if relevant, None otherwise
        """
        attr_name = mutation.get("attributeName")

        # Focus on style attribute changes (inline styles)
        if attr_name == "style":
            element_info = mutation["elementInfo"]
            selector, _ = generate_selector(element_info)

            # Get the style values from mutation
            current_style = mutation.get("newValue") or ""
            old_style = mutation.get("oldValue") or ""

            # Parse style changes (simple approach: look for display property)
            current_display = self._extract_css_property(current_style, "display")
            old_display = self._extract_css_property(old_style, "display")

            if current_display != old_display:
                logger.info(
                    f"CSS change detected: {selector} display: {old_display} -> {current_display}"
                )
                return CSSChange(
                    selector=selector,
                    property="display",
                    value=current_display or "block",
                )

        return None

    async def _process_childlist_mutation(
        self, mutation: dict[str, Any]
    ) -> DOMChange | None:
        """Process a childList mutation into a DOMChange.

        Args:
            mutation: The mutation object from JavaScript

        Returns:
            DOMChange if relevant, None otherwise
        """
        element_info = mutation["elementInfo"]
        selector, _ = generate_selector(element_info)

        action = mutation.get("action")
        if action == "added":
            logger.info(f"DOM change detected: {selector} added")
            return DOMChange(change_type="added", selector=selector)
        elif action == "removed":
            logger.info(f"DOM change detected: {selector} removed")
            return DOMChange(change_type="removed", selector=selector)

        return None

    def _extract_css_property(self, style_string: str, property_name: str) -> str:
        """Extract a CSS property value from a style string.

        Args:
            style_string: The inline style string (e.g., "display: none; color: red")
            property_name: The property to extract (e.g., "display")

        Returns:
            The property value or empty string if not found
        """
        if not style_string:
            return ""

        # Parse style string
        for part in style_string.split(";"):
            if ":" in part:
                prop, value = part.split(":", 1)
                if prop.strip() == property_name:
                    return value.strip()

        return ""
