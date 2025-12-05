"""Generate stable CSS selectors for elements."""

import logging

logger = logging.getLogger(__name__)


def generate_selector(element_info: dict) -> tuple[str, bool]:
    """Generate a CSS selector for an element.

    Uses a priority order to create the most stable selector possible:
    1. data-testid (most stable)
    2. id
    3. aria-label with tag
    4. tag + classes (fragile)
    5. tag only (very fragile)

    Args:
        element_info: Dictionary with tag, id, classes, data-testid, aria-label, etc.

    Returns:
        Tuple of (selector_string, is_fragile)
    """
    tag = element_info.get("tag", "div")

    # Priority 1: data-testid
    testid = element_info.get("data-testid")
    if testid:
        selector = f'[data-testid="{testid}"]'
        logger.info(f"Generated selector from data-testid: {selector}")
        return selector, False

    # Priority 2: id
    elem_id = element_info.get("id")
    if elem_id:
        selector = f"#{elem_id}"
        logger.info(f"Generated selector from id: {selector}")
        return selector, False

    # Priority 3: aria-label
    aria_label = element_info.get("aria-label")
    if aria_label:
        selector = f'{tag}[aria-label="{aria_label}"]'
        logger.info(f"Generated selector from aria-label: {selector}")
        return selector, False

    # Priority 4: tag + classes (fragile)
    classes = element_info.get("classes", [])
    if classes:
        class_selector = ".".join(classes)
        selector = f"{tag}.{class_selector}"
        logger.info(f"Generated fragile selector from classes: {selector}")
        return selector, True

    # Priority 5: tag only (very fragile)
    logger.warning(f"Generated very fragile tag-only selector: {tag}")
    return tag, True
