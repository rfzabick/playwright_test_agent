"""Tests for instrumentation code generator."""

from js_interaction_detector.functional_tester.instrumentation import (
    generate_instrumentation_script,
    generate_wrapper,
)


class TestGenerateWrapper:
    """Tests for generate_wrapper function."""

    def test_generates_wrapper_that_captures_calls(self):
        """Generates a wrapper function that captures inputs and outputs."""
        wrapper = generate_wrapper("groupBy", "lodash")

        assert "groupBy" in wrapper
        assert "JSON.stringify" in wrapper
        assert "console.log" in wrapper

    def test_wrapper_outputs_test_code(self):
        """Wrapper outputs executable test code."""
        wrapper = generate_wrapper("add", "mylib")

        # Should output expect/toEqual format
        assert "expect(" in wrapper
        assert "toEqual(" in wrapper


class TestGenerateInstrumentationScript:
    """Tests for generate_instrumentation_script function."""

    def test_generates_script_for_multiple_functions(self):
        """Generates instrumentation for multiple functions."""
        functions = ["map", "filter", "reduce"]
        script = generate_instrumentation_script("lodash", functions)

        assert "map" in script
        assert "filter" in script
        assert "reduce" in script

    def test_script_is_self_contained(self):
        """Script can be injected without dependencies."""
        functions = ["add"]
        script = generate_instrumentation_script("mathlib", functions)

        # Should wrap the original function
        assert "original" in script.lower() or "orig" in script.lower()
