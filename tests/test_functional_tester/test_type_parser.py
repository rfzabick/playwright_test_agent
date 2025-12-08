"""Tests for TypeScript definition parser."""

from pathlib import Path

import pytest

from js_interaction_detector.functional_tester.type_parser import parse_dts_file


@pytest.fixture
def fixtures_path():
    """Path to test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "type_definitions"


class TestParseDtsFile:
    """Tests for parse_dts_file function."""

    def test_parses_simple_function(self, fixtures_path):
        """Parses a simple function with one parameter."""
        dts_path = fixtures_path / "simple.d.ts"

        signatures = parse_dts_file(dts_path)

        greet = next((s for s in signatures if s.name == "greet"), None)
        assert greet is not None
        assert greet.parameters == [("name", "string")]
        assert greet.return_type == "string"

    def test_parses_function_with_multiple_params(self, fixtures_path):
        """Parses a function with multiple parameters."""
        dts_path = fixtures_path / "simple.d.ts"

        signatures = parse_dts_file(dts_path)

        add = next((s for s in signatures if s.name == "add"), None)
        assert add is not None
        assert add.parameters == [("a", "number"), ("b", "number")]
        assert add.return_type == "number"

    def test_parses_generic_function(self, fixtures_path):
        """Parses a generic function."""
        dts_path = fixtures_path / "simple.d.ts"

        signatures = parse_dts_file(dts_path)

        identity = next((s for s in signatures if s.name == "identity"), None)
        assert identity is not None
        assert identity.parameters == [("value", "T")]
        assert identity.return_type == "T"
