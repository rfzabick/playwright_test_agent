"""Load web pages using Playwright."""

import logging
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, async_playwright

logger = logging.getLogger(__name__)


class PageLoadError(Exception):
    """Error loading a page."""

    def __init__(self, message: str, phase: str = "loading"):
        super().__init__(message)
        self.phase = phase


class PageLoader:
    """Load pages using Playwright with network idle wait."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._pages = []

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch()
        logger.info("Browser launched")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Keep browser and playwright alive - pages may still be in use
        # Caller must explicitly close pages when done
        pass

    async def close(self):
        """Close the browser and cleanup resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    async def load(self, url: str) -> Page:
        """Load a page and wait for network idle.

        Args:
            url: The URL to load (http, https, or file://)

        Returns:
            The loaded Playwright Page object

        Raises:
            PageLoadError: If the URL is invalid or page fails to load
        """
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ("http", "https", "file"):
            logger.error(f"Invalid URL scheme: {url}")
            raise PageLoadError(f"Invalid URL: {url}")

        page = await self._browser.new_page()
        try:
            logger.info(f"Loading page: {url}")
            await page.goto(url, wait_until="networkidle")
            logger.info(f"Page loaded successfully: {url}")
            return page
        except PlaywrightError as e:
            await page.close()
            logger.error(f"Failed to load page: {e}")
            raise PageLoadError(str(e), phase="loading") from e
