"""Data models for analysis output."""

import json
from dataclasses import asdict, dataclass, field


@dataclass
class ElementInfo:
    """Information about a DOM element."""

    selector: str
    tag: str
    type: str | None = None
    name: str | None = None
    id: str | None = None
    placeholder: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationInfo:
    """Information about a validation rule."""

    type: str
    raw_code: str
    rule_description: str | None = None
    confidence: str | None = None  # "high", "medium", "low"


@dataclass
class ErrorDisplay:
    """Information about how validation errors are displayed."""

    method: str  # "sibling_element", "tooltip", "inline", etc.
    selector: str | None = None
    sample_message: str | None = None


@dataclass
class Interaction:
    """A detected JavaScript interaction on an element."""

    element: ElementInfo
    triggers: list[str]
    validation: ValidationInfo
    error_display: ErrorDisplay | None = None
    examples: dict[str, list[str]] | None = None


@dataclass
class AnalysisError:
    """A non-fatal error encountered during analysis."""

    element: str | None
    error: str
    phase: str  # "loading", "discovery", "extraction"


@dataclass
class AnalysisResult:
    """Complete result of analyzing a page."""

    url: str
    analyzed_at: str
    errors: list[AnalysisError]
    interactions: list[Interaction]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "analyzed_at": self.analyzed_at,
            "errors": [asdict(e) for e in self.errors],
            "interactions": [self._interaction_to_dict(i) for i in self.interactions],
        }

    def _interaction_to_dict(self, interaction: Interaction) -> dict:
        """Convert an interaction to a dictionary, excluding None values."""
        result = {
            "element": asdict(interaction.element),
            "triggers": interaction.triggers,
            "validation": asdict(interaction.validation),
        }
        # Remove None values from nested dicts
        result["validation"] = {
            k: v for k, v in result["validation"].items() if v is not None
        }
        if interaction.error_display:
            result["error_display"] = {
                k: v
                for k, v in asdict(interaction.error_display).items()
                if v is not None
            }
        if interaction.examples:
            result["examples"] = interaction.examples
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
