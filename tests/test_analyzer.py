"""Tests for the main analyzer."""

import json
from pathlib import Path

import pytest

from js_interaction_detector.analyzer import analyze_page
from js_interaction_detector.models import AnalysisResult


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestAnalyzer:
    def given_form_with_validation_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"

    def given_invalid_url(self):
        self.url = "not-a-url"

    async def when_page_is_analyzed(self):
        self.result = await analyze_page(self.url)

    def then_result_is_valid(self):
        assert isinstance(self.result, AnalysisResult)
        assert self.result.url == self.url
        assert self.result.analyzed_at is not None
        assert isinstance(self.result.interactions, list)

    def then_email_validation_detected(self):
        email_interaction = next(
            (i for i in self.result.interactions if "email" in i.element.selector), None
        )
        assert email_interaction is not None
        assert email_interaction.validation.type == "email"

    def then_email_has_blur_trigger(self):
        email_interaction = next(
            (i for i in self.result.interactions if "email" in i.element.selector), None
        )
        assert "blur" in email_interaction.triggers

    def then_result_has_errors(self):
        assert len(self.result.errors) > 0
        assert self.result.errors[0].phase == "loading"
        assert self.result.interactions == []

    def then_result_serializes_to_json(self):
        json_str = self.result.to_json()
        parsed = json.loads(json_str)
        assert parsed["url"] == self.url

    @pytest.mark.asyncio
    async def test_analyzes_page_and_returns_result(self, fixtures_path):
        """analyze_page returns an AnalysisResult with expected fields."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_result_is_valid()

    @pytest.mark.asyncio
    async def test_finds_email_validation(self, fixtures_path):
        """analyze_page detects email validation on email input."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_email_validation_detected()

    @pytest.mark.asyncio
    async def test_captures_triggers(self, fixtures_path):
        """analyze_page captures which events trigger validation."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_email_has_blur_trigger()

    @pytest.mark.asyncio
    async def test_returns_error_for_invalid_url(self):
        """analyze_page returns errors array for invalid URLs."""
        self.given_invalid_url()
        await self.when_page_is_analyzed()
        self.then_result_has_errors()

    @pytest.mark.asyncio
    async def test_result_serializes_to_valid_json(self, fixtures_path):
        """analyze_page result can be serialized to valid JSON."""
        self.given_form_with_validation_url(fixtures_path)
        await self.when_page_is_analyzed()
        self.then_result_serializes_to_json()
