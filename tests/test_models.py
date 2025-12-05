"""Tests for data models."""

import json

from js_interaction_detector.models import (
    AnalysisError,
    AnalysisResult,
    ElementInfo,
    Interaction,
    ValidationInfo,
)


class TestAnalysisResult:
    def given_empty_result(self):
        self.result = AnalysisResult(
            url="https://example.com",
            analyzed_at="2025-12-04T10:00:00Z",
            errors=[],
            interactions=[],
        )

    def given_result_with_interaction(self):
        self.result = AnalysisResult(
            url="https://example.com",
            analyzed_at="2025-12-04T10:00:00Z",
            errors=[],
            interactions=[
                Interaction(
                    element=ElementInfo(selector="input#test", tag="input"),
                    triggers=["blur"],
                    validation=ValidationInfo(type="unknown", raw_code="..."),
                )
            ],
        )

    def given_result_with_error(self):
        self.result = AnalysisResult(
            url="https://example.com",
            analyzed_at="2025-12-04T10:00:00Z",
            errors=[
                AnalysisError(element="input#foo", error="Failed", phase="extraction")
            ],
            interactions=[],
        )

    def when_serialized_to_json(self):
        json_str = self.result.to_json()
        self.parsed = json.loads(json_str)

    def then_json_has_expected_fields(self):
        assert self.parsed["url"] == "https://example.com"
        assert self.parsed["errors"] == []
        assert self.parsed["interactions"] == []

    def then_none_values_excluded_from_validation(self):
        interaction = self.parsed["interactions"][0]
        assert "rule_description" not in interaction["validation"]
        assert "confidence" not in interaction["validation"]

    def then_errors_are_serialized(self):
        assert len(self.parsed["errors"]) == 1
        assert self.parsed["errors"][0]["phase"] == "extraction"

    def test_serializes_to_json(self):
        """to_json() produces valid JSON with all fields."""
        self.given_empty_result()
        self.when_serialized_to_json()
        self.then_json_has_expected_fields()

    def test_serializes_interactions_excluding_none_values(self):
        """None values in nested objects are excluded from JSON."""
        self.given_result_with_interaction()
        self.when_serialized_to_json()
        self.then_none_values_excluded_from_validation()

    def test_serializes_errors(self):
        """Errors are properly serialized with all fields."""
        self.given_result_with_error()
        self.when_serialized_to_json()
        self.then_errors_are_serialized()
