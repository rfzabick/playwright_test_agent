"""Infer validation rules from JavaScript code via pattern matching."""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InferredRule:
    """Result of validation rule inference."""

    type: str
    description: str
    confidence: str | None  # "high", "medium", "low", or None for unknown


# Patterns ordered by specificity (most specific first)
PATTERNS = [
    # Email patterns
    {
        "type": "email",
        "patterns": [
            r"@.*\.",  # Common email regex fragment
            r"email",  # Variable/function name hint
            r"\\.+@\\.+",  # Escaped regex
        ],
        "description": "Must be a valid email address",
        "confidence": "high",
    },
    # URL patterns
    {
        "type": "url",
        "patterns": [
            r"https\?:",  # URL scheme (escaped question mark to match literal ?)
        ],
        "description": "Must be a valid URL",
        "confidence": "high",
    },
    # Phone patterns
    {
        "type": "phone",
        "patterns": [
            r"\\d\{3\}[-.]\\d\{3\}[-.]\\d\{4\}",  # US phone with escaped braces
            r"\d{3}[-]\d{3}[-]\d{4}",  # US phone pattern
            r"phone",  # Variable name hint
        ],
        "description": "Must be a valid phone number",
        "confidence": "medium",
    },
    # Numeric patterns
    {
        "type": "numeric",
        "patterns": [
            r"isNaN\s*\(",
            r"Number\s*\(",
            r"parseInt\s*\(",
            r"parseFloat\s*\(",
            r"\^\\d\+\$",  # Digits only regex
        ],
        "description": "Must be a number",
        "confidence": "high",
    },
    # Min length patterns
    {
        "type": "min_length",
        "patterns": [
            r"\.length\s*<\s*(\d+)",
            r"\.length\s*>=\s*(\d+)",
            r"minlength",
        ],
        "description_template": "Must be at least {0} characters",
        "confidence": "high",
    },
    # Max length patterns
    {
        "type": "max_length",
        "patterns": [
            r"\.length\s*>\s*(\d+)",
            r"\.length\s*<=\s*(\d+)",
            r"maxlength",
        ],
        "description_template": "Must be at most {0} characters",
        "confidence": "high",
    },
    # Required patterns
    {
        "type": "required",
        "patterns": [
            r"===?\s*['\"][\s]*['\"]",  # Empty string check
            r"===?\s*null",
            r"===?\s*undefined",
            r"\.length\s*===?\s*0",
            r"!value",
            r"required",
        ],
        "description": "Field is required",
        "confidence": "high",
    },
    # Custom pattern (catch-all for regexes we don't recognize)
    {
        "type": "pattern",
        "patterns": [
            r"/\^.*\$/",  # Anchored regex
            r"\.test\s*\(",
            r"\.match\s*\(",
            r"RegExp\s*\(",
        ],
        "description": "Must match a specific pattern",
        "confidence": "low",
    },
]


def infer_validation_rule(code: str) -> InferredRule:
    """Infer the validation rule type from JavaScript code.

    Args:
        code: The JavaScript validation function code

    Returns:
        InferredRule with type, description, and confidence
    """
    if not code or not code.strip():
        logger.info("Empty code, returning unknown")
        return InferredRule(
            type="unknown",
            description="Could not determine validation rule",
            confidence=None,
        )

    # Try each pattern in order of specificity
    for pattern_def in PATTERNS:
        for pattern in pattern_def["patterns"]:
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                # Build description
                if "description_template" in pattern_def:
                    # Extract captured group for parameterized descriptions
                    try:
                        param = match.group(1)
                        description = pattern_def["description_template"].format(param)
                    except (IndexError, AttributeError):
                        description = pattern_def.get(
                            "description", f"Validation rule: {pattern_def['type']}"
                        )
                else:
                    description = pattern_def.get(
                        "description", f"Validation rule: {pattern_def['type']}"
                    )

                logger.info(
                    f"Inferred rule type '{pattern_def['type']}' "
                    f"with confidence '{pattern_def['confidence']}'"
                )
                return InferredRule(
                    type=pattern_def["type"],
                    description=description,
                    confidence=pattern_def["confidence"],
                )

    # No pattern matched
    logger.info("No pattern matched, returning unknown")
    return InferredRule(
        type="unknown",
        description="Could not determine validation rule",
        confidence=None,
    )
