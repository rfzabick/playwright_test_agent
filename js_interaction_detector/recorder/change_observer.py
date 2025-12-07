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

# Elements to ignore - these are usually noise, not user-meaningful changes
IGNORED_TAGS = frozenset({
    "script", "style", "link", "meta", "noscript",  # Document structure
    "iframe",  # Embedded content (ads, tracking)
    "time",  # Timestamps update frequently
    "hr", "br",  # Decorative elements
    "svg", "path", "g", "circle", "rect", "line", "polygon", "polyline",  # SVG internals
    "img",  # Images loading is noise
    "source", "picture",  # Media elements
    "canvas",  # Canvas elements
    "slot",  # Web components slots
    # Common loader/spinner patterns
    "faceplate-loader", "faceplate-partial", "shreddit-loading",
    "ac-track",  # Analytics
})

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

    def __init__(
        self,
        page: Page,
        settle_timeout: int = 500,
        only_stable_selectors: bool = True,
        max_changes_per_action: int = 10,
    ):
        """Initialize the change observer.

        Args:
            page: The Playwright Page to observe
            settle_timeout: Milliseconds to wait for changes to settle after action
            only_stable_selectors: If True, only report changes to elements with stable
                selectors (data-testid, id, aria-label). This filters out noise.
            max_changes_per_action: Maximum number of DOM/CSS changes to report per action.
                This prevents test bloat on complex pages.
        """
        self.page = page
        self.settle_timeout = settle_timeout
        self.only_stable_selectors = only_stable_selectors
        self.max_changes_per_action = max_changes_per_action
        self._network_requests: list[dict[str, str]] = []
        self._seen_selectors: set[str] = set()  # For DOM/CSS deduplication
        self._seen_api_patterns: set[str] = set()  # For network request deduplication
        logger.info(
            f"ChangeObserver initialized with settle_timeout={settle_timeout}ms, "
            f"only_stable_selectors={only_stable_selectors}, "
            f"max_changes_per_action={max_changes_per_action}"
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
        self._seen_selectors.clear()
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
        logger.info(f"Collected {len(mutations)} raw mutations")

        dom_css_changes: list[DOMChange | CSSChange] = []
        filtered_count = 0
        duplicate_count = 0

        # Process mutations
        for mutation in mutations:
            if mutation["type"] == "attributes":
                change = self._process_attribute_mutation(mutation)
                if change:
                    dom_css_changes.append(change)
                elif change is None:
                    filtered_count += 1
            elif mutation["type"] == "childList":
                result = self._process_childlist_mutation(mutation)
                if result == "duplicate":
                    duplicate_count += 1
                elif result == "filtered":
                    filtered_count += 1
                elif result:
                    dom_css_changes.append(result)

        # Limit DOM/CSS changes to prevent test bloat
        if len(dom_css_changes) > self.max_changes_per_action:
            logger.info(
                f"Limiting DOM/CSS changes from {len(dom_css_changes)} to {self.max_changes_per_action}"
            )
            dom_css_changes = dom_css_changes[: self.max_changes_per_action]

        # Build final changes list
        changes: list[DOMChange | CSSChange | NetworkRequest] = list(dom_css_changes)

        # Process network requests - only include API calls, not assets
        api_request_count = 0
        for req in self._network_requests:
            url = req["url"]
            # Only include requests that look like API calls
            if self._is_api_request(url):
                # Extract a reasonable URL pattern
                pattern = self._extract_api_pattern(url)
                # Deduplicate by method + pattern
                dedup_key = f"{req['method']}:{pattern}"
                if dedup_key not in self._seen_api_patterns:
                    self._seen_api_patterns.add(dedup_key)
                    changes.append(NetworkRequest(method=req["method"], url_pattern=pattern))
                    api_request_count += 1
                    logger.info(f"API request: {req['method']} {pattern}")

        logger.info(
            f"Changes: {len(dom_css_changes)} DOM/CSS (filtered {filtered_count}, "
            f"deduplicated {duplicate_count}), {len(changes) - len(dom_css_changes)} API"
        )
        return changes

    def _is_api_request(self, url: str) -> bool:
        """Check if a URL looks like an API request vs a static asset."""
        url_lower = url.lower()

        # Exclude patterns - be aggressive about filtering noise
        exclude_patterns = [
            # Static assets
            ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
            ".woff", ".woff2", ".ttf", ".eot", ".map",
            ".webp", ".avif", ".mp4", ".webm",
            "/static/", "/assets/", "/images/", "/fonts/",
            # Third-party tracking/analytics
            "google.com", "facebook.com", "twitter.com", "analytics",
            "recaptcha", "captcha", "tracking", "beacon",
            # Reddit-specific noise
            "preview.redd.it", "external-preview.redd.it",
            "styles.redditmedia.com", "www.redditstatic.com",
            "emoji.redditmedia.com",  # Emoji CDN
            "w3-reporting.reddit.com",  # W3C reporting
            "alb.reddit.com",  # Load balancer tracking
            "/svc/shreddit/events",  # Analytics events
            "/svc/shreddit/trending",  # Background data
            "/svc/shreddit/graphql",  # Background queries
        ]

        if any(pattern in url_lower for pattern in exclude_patterns):
            return False

        # Include patterns - things that look like user-triggered API calls
        include_patterns = [
            "/api/",
            "search",  # Search typeahead is user-triggered
            "httpbin.org",  # Test API endpoints
        ]

        # If URL matches an include pattern, allow it
        if any(pattern in url_lower for pattern in include_patterns):
            return True

        # Also allow any URL that contains common API path segments
        # This catches things like /json, /data, /query etc.
        api_path_patterns = ["/json", "/get", "/post", "/data", "/query"]
        return any(pattern in url_lower for pattern in api_path_patterns)

    def _extract_api_pattern(self, url: str) -> str:
        """Extract a reasonable API pattern from a URL for assertions."""
        # Remove query params for cleaner patterns
        if "?" in url:
            url = url.split("?")[0]
        # For /api/ URLs, keep just the /api/... path (common pattern)
        if "/api/" in url:
            return "/api/" + url.split("/api/")[1]
        # For external URLs, keep domain + path for clarity
        return url

    def _process_attribute_mutation(
        self, mutation: dict[str, Any]
    ) -> CSSChange | None:
        """Process an attribute mutation into a CSSChange.

        Args:
            mutation: The mutation object from JavaScript

        Returns:
            CSSChange if relevant, None otherwise
        """
        attr_name = mutation.get("attributeName")
        element_info = mutation["elementInfo"]
        tag = element_info.get("tag", "").lower()

        # Filter ignored tags
        if tag in IGNORED_TAGS:
            return None

        # Focus on style attribute changes (inline styles)
        if attr_name == "style":
            selector, is_fragile = generate_selector(element_info)

            # Filter fragile selectors if configured
            if self.only_stable_selectors and is_fragile:
                return None

            # Deduplicate
            if selector in self._seen_selectors:
                return None
            self._seen_selectors.add(selector)

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

    def _process_childlist_mutation(
        self, mutation: dict[str, Any]
    ) -> DOMChange | str | None:
        """Process a childList mutation into a DOMChange.

        Args:
            mutation: The mutation object from JavaScript

        Returns:
            DOMChange if relevant, "duplicate" if deduplicated, "filtered" if filtered, None otherwise
        """
        element_info = mutation["elementInfo"]
        tag = element_info.get("tag", "").lower()

        # Filter ignored tags
        if tag in IGNORED_TAGS:
            return "filtered"

        selector, is_fragile = generate_selector(element_info)

        # Filter fragile selectors if configured
        if self.only_stable_selectors and is_fragile:
            return "filtered"

        # Deduplicate - only report each selector once per action
        if selector in self._seen_selectors:
            return "duplicate"
        self._seen_selectors.add(selector)

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
