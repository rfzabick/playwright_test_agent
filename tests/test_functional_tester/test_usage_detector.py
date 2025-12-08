# tests/test_functional_tester/test_usage_detector.py
"""Tests for JavaScript usage detector."""

from pathlib import Path

import pytest

from js_interaction_detector.functional_tester.usage_detector import (
    find_call_sites,
    find_imports,
)


@pytest.fixture
def fixtures_path():
    """Path to test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "sample_js"


class TestFindImports:
    """Tests for find_imports function."""

    def test_finds_es_module_named_imports(self, fixtures_path):
        """Finds named imports from ES modules."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        imports = find_imports(content, "lodash")

        assert "groupBy" in imports
        assert "map" in imports

    def test_returns_empty_for_no_imports(self, fixtures_path):
        """Returns empty set when library is not imported."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        imports = find_imports(content, "react")

        assert imports == set()


class TestFindCallSites:
    """Tests for find_call_sites function."""

    def test_finds_call_sites_with_literal_args(self, fixtures_path):
        """Finds call sites and extracts literal arguments."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        call_sites = find_call_sites(content, {"groupBy", "map"}, str(js_path))

        # Find the groupBy call
        groupby_calls = [c for c in call_sites if c.function_name == "groupBy"]
        assert len(groupby_calls) == 1
        assert groupby_calls[0].arguments[1] == "'age'"

    def test_finds_call_sites_with_lambda_args(self, fixtures_path):
        """Finds call sites with lambda arguments."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        call_sites = find_call_sites(content, {"map"}, str(js_path))

        # Should find two map calls
        map_calls = [c for c in call_sites if c.function_name == "map"]
        assert len(map_calls) == 2

        # One with simple lambda x => x * 2
        doubled_call = next(
            (c for c in map_calls if "x => x * 2" in c.arguments[1]), None
        )
        assert doubled_call is not None
        assert doubled_call.has_static_args is True

    def test_tracks_line_numbers(self, fixtures_path):
        """Tracks line numbers for call sites."""
        js_path = fixtures_path / "lodash_usage.js"
        content = js_path.read_text()

        call_sites = find_call_sites(content, {"groupBy"}, str(js_path))

        assert len(call_sites) == 1
        assert call_sites[0].line_number > 0
