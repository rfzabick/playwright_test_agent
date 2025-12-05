"""Extract event listeners from page elements."""

import logging
from dataclasses import dataclass

from playwright.async_api import Page

logger = logging.getLogger(__name__)


@dataclass
class ListenerInfo:
    """Information about an element's event listeners."""

    selector: str
    tag: str
    events: list[str]
    code: str
    input_type: str | None = None
    name: str | None = None
    id: str | None = None
    placeholder: str | None = None
    attributes: dict[str, str] | None = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


async def extract_listeners(page: Page) -> list[ListenerInfo]:
    """Extract event listeners from all input elements on the page.

    Uses Chrome DevTools Protocol to access getEventListeners.

    Args:
        page: A loaded Playwright Page object

    Returns:
        List of ListenerInfo objects for elements with event listeners
    """
    logger.info("Extracting event listeners from page")

    # Get all input elements
    input_selectors = 'input, textarea, select, [contenteditable="true"]'
    elements = await page.query_selector_all(input_selectors)

    results = []
    client = await page.context.new_cdp_session(page)

    # Enable Debugger to access script sources
    try:
        await client.send("Debugger.enable")
    except Exception as e:
        logger.warning(f"Could not enable Debugger: {e}")

    for element in elements:
        try:
            # Get element info
            info = await element.evaluate("""
                (el) => ({
                    tag: el.tagName.toLowerCase(),
                    inputType: el.type || null,
                    name: el.name || null,
                    id: el.id || null,
                    placeholder: el.placeholder || null,
                    attributes: Object.fromEntries(
                        Array.from(el.attributes)
                            .filter(a => !['id', 'name', 'type', 'placeholder', 'class'].includes(a.name))
                            .map(a => [a.name, a.value])
                    )
                })
            """)

            # Build selector
            selector = info["tag"]
            if info["id"]:
                selector += f"#{info['id']}"
            elif info["name"]:
                selector += f'[name="{info["name"]}"]'

            # Get event listeners via CDP
            # Use Runtime.evaluate to get the element and its objectId directly
            try:
                # Evaluate a script that returns the specific element
                result = await client.send(
                    "Runtime.evaluate",
                    {
                        "expression": f"document.querySelector('{selector.replace(chr(39), chr(92) + chr(39))}')",
                        "returnByValue": False,
                    },
                )

                if "result" not in result or "objectId" not in result["result"]:
                    continue

                object_id = result["result"]["objectId"]

                listeners_response = await client.send(
                    "DOMDebugger.getEventListeners", {"objectId": object_id}
                )
            except Exception as e:
                logger.debug(f"Could not get listeners via CDP for {selector}: {e}")
                continue

            listeners = listeners_response.get("listeners", [])
            if not listeners:
                continue

            # Extract event types and code
            events = []
            code_parts = []
            for listener in listeners:
                event_type = listener.get("type", "")
                if event_type:
                    events.append(event_type)

                # Get the script source using scriptId
                script_id = listener.get("scriptId")

                if script_id:
                    try:
                        # Get the full script source
                        script_response = await client.send(
                            "Debugger.getScriptSource", {"scriptId": script_id}
                        )
                        script_source = script_response.get("scriptSource", "")

                        if script_source:
                            # The lineNumber from CDP is relative to the start of the HTML document
                            # We need to adjust it to be relative to the script
                            # Find where the script tag starts in the HTML
                            lines = script_source.split("\n")

                            # The line_number from CDP is relative to the entire HTML document
                            # but the script_source only contains the script content
                            # We need to find the line in the script that contains 'addEventListener'
                            # and matches our event type

                            # Simple approach: find all addEventListener calls in the script
                            # and match by event type
                            for script_line_idx, line in enumerate(lines):
                                if (
                                    f"addEventListener('{event_type}'" in line
                                    or f'addEventListener("{event_type}"' in line
                                ):
                                    # Found the addEventListener line, now extract the function body
                                    function_code = []
                                    brace_count = 0
                                    in_function = False

                                    for i in range(script_line_idx, len(lines)):
                                        curr_line = lines[i]
                                        if not in_function:
                                            if "{" in curr_line:
                                                in_function = True
                                                brace_count = curr_line.count(
                                                    "{"
                                                ) - curr_line.count("}")
                                                function_code.append(curr_line)
                                                if brace_count == 0:
                                                    break
                                        else:
                                            function_code.append(curr_line)
                                            brace_count += curr_line.count(
                                                "{"
                                            ) - curr_line.count("}")
                                            if brace_count == 0:
                                                break

                                    if function_code:
                                        code_parts.append("\n".join(function_code))
                                        break  # Found this listener, stop searching
                    except Exception as e:
                        logger.debug(
                            f"Could not extract code from script {script_id}: {e}"
                        )

            if events:
                results.append(
                    ListenerInfo(
                        selector=selector,
                        tag=info["tag"],
                        events=list(set(events)),  # dedupe
                        code="\n\n".join(code_parts)
                        if code_parts
                        else "[code not extractable]",
                        input_type=info["inputType"],
                        name=info["name"],
                        id=info["id"],
                        placeholder=info["placeholder"],
                        attributes=info["attributes"],
                    )
                )
                logger.info(f"Found listeners on {selector}: {events}")

        except Exception as e:
            logger.warning(f"Error extracting listeners from element: {e}")
            continue

    await client.detach()
    logger.info(f"Extracted {len(results)} elements with event listeners")
    return results
