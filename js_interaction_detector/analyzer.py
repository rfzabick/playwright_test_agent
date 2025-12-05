"""Main analyzer that orchestrates the analysis pipeline."""

import logging
from datetime import UTC, datetime

from js_interaction_detector.listener_extractor import extract_listeners
from js_interaction_detector.models import (
    AnalysisError,
    AnalysisResult,
    ElementInfo,
    Interaction,
    ValidationInfo,
)
from js_interaction_detector.page_loader import PageLoader, PageLoadError
from js_interaction_detector.rule_inferrer import infer_validation_rule

logger = logging.getLogger(__name__)


async def analyze_page(url: str) -> AnalysisResult:
    """Analyze a page for JavaScript-driven input validations.

    Args:
        url: The URL to analyze

    Returns:
        AnalysisResult containing all detected interactions and any errors
    """
    logger.info(f"Starting analysis of {url}")
    errors: list[AnalysisError] = []
    interactions: list[Interaction] = []
    analyzed_at = datetime.now(UTC).isoformat()

    try:
        async with PageLoader() as loader:
            page = await loader.load(url)

            # Extract event listeners
            listeners = await extract_listeners(page)
            logger.info(f"Found {len(listeners)} elements with listeners")

            # Process each listener
            for listener_info in listeners:
                try:
                    # Infer validation rule
                    rule = infer_validation_rule(listener_info.code)

                    # Build element info
                    element = ElementInfo(
                        selector=listener_info.selector,
                        tag=listener_info.tag,
                        type=listener_info.input_type,
                        name=listener_info.name,
                        id=listener_info.id,
                        placeholder=listener_info.placeholder,
                        attributes=listener_info.attributes or {},
                    )

                    # Build validation info
                    validation = ValidationInfo(
                        type=rule.type,
                        raw_code=listener_info.code,
                        rule_description=rule.description
                        if rule.type != "unknown"
                        else None,
                        confidence=rule.confidence,
                    )

                    # Create interaction
                    interaction = Interaction(
                        element=element,
                        triggers=listener_info.events,
                        validation=validation,
                    )
                    interactions.append(interaction)
                    logger.info(f"Processed {listener_info.selector}: {rule.type}")

                except Exception as e:
                    logger.warning(f"Error processing {listener_info.selector}: {e}")
                    errors.append(
                        AnalysisError(
                            element=listener_info.selector,
                            error=str(e),
                            phase="extraction",
                        )
                    )

    except PageLoadError as e:
        logger.error(f"Page load error: {e}")
        errors.append(
            AnalysisError(
                element=None,
                error=str(e),
                phase=e.phase,
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        errors.append(
            AnalysisError(
                element=None,
                error=str(e),
                phase="discovery",
            )
        )

    result = AnalysisResult(
        url=url,
        analyzed_at=analyzed_at,
        errors=errors,
        interactions=interactions,
    )
    logger.info(
        f"Analysis complete: {len(interactions)} interactions, {len(errors)} errors"
    )
    return result
