"""Integration tests for end-to-end functionality."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestEndToEnd:
    def given_form_with_validation_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"

    def given_simple_form_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"

    def given_unreachable_url(self):
        self.url = "https://localhost:99999/nope"

    def when_cli_is_executed(self):
        self.result = subprocess.run(
            [sys.executable, "-m", "js_interaction_detector", self.url],
            capture_output=True,
            text=True,
        )
        self.output = json.loads(self.result.stdout)

    def then_exit_code_is_zero(self):
        assert self.result.returncode == 0

    def then_output_has_expected_structure(self):
        assert self.output["url"] == self.url
        assert "analyzed_at" in self.output
        assert "interactions" in self.output
        assert "errors" in self.output

    def then_email_validation_is_detected(self):
        email_interactions = [
            i
            for i in self.output["interactions"]
            if "email" in i["element"]["selector"]
        ]
        assert len(email_interactions) > 0
        assert email_interactions[0]["validation"]["type"] == "email"

    def then_interactions_are_empty(self):
        assert self.output["interactions"] == []

    def then_errors_are_present(self):
        assert len(self.output["errors"]) > 0

    def test_cli_produces_valid_json(self, fixtures_path):
        """CLI produces valid JSON with expected structure."""
        self.given_form_with_validation_url(fixtures_path)
        self.when_cli_is_executed()
        self.then_exit_code_is_zero()
        self.then_output_has_expected_structure()

    def test_detects_email_validation_end_to_end(self, fixtures_path):
        """Full pipeline detects email validation correctly."""
        self.given_form_with_validation_url(fixtures_path)
        self.when_cli_is_executed()
        self.then_email_validation_is_detected()

    def test_handles_page_without_validation(self, fixtures_path):
        """Page with no JS validation returns empty interactions."""
        self.given_simple_form_url(fixtures_path)
        self.when_cli_is_executed()
        self.then_exit_code_is_zero()
        self.then_interactions_are_empty()

    def test_handles_unreachable_url_gracefully(self):
        """Unreachable URL returns errors array, not crash."""
        self.given_unreachable_url()
        self.when_cli_is_executed()
        self.then_exit_code_is_zero()
        self.then_errors_are_present()
        self.then_interactions_are_empty()
