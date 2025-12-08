"""Tests for Jest test generator."""

from js_interaction_detector.functional_tester.models import CapturedCall
from js_interaction_detector.functional_tester.test_generator import (
    generate_test_case,
    generate_test_file,
)


class TestGenerateTestCase:
    """Tests for generate_test_case function."""

    def test_generates_complete_test(self):
        """Generates a complete test for a captured call."""
        call = CapturedCall(
            function_name="groupBy",
            inputs=['[{"name": "alice", "age": 30}]', '"age"'],
            output='{"30": [{"name": "alice", "age": 30}]}',
            location="src/utils.js:42",
            is_complete=True,
        )

        test_code = generate_test_case(call, "lodash")

        assert "test(" in test_code
        assert "groupBy" in test_code
        assert "expect(" in test_code
        assert "toEqual(" in test_code

    def test_generates_failing_test_for_incomplete(self):
        """Generates a failing test for incomplete captures."""
        call = CapturedCall(
            function_name="map",
            inputs=["users", "processUser"],
            output="",
            location="src/transform.js:87",
            is_complete=False,
            incomplete_reason="Could not capture 'processUser' function body",
        )

        test_code = generate_test_case(call, "lodash")

        assert "test(" in test_code
        assert "throw new Error" in test_code
        assert "src/transform.js:87" in test_code
        assert "processUser" in test_code


class TestGenerateTestFile:
    """Tests for generate_test_file function."""

    def test_generates_valid_jest_structure(self):
        """Generates a valid Jest test file structure."""
        calls = [
            CapturedCall(
                function_name="add",
                inputs=["1", "2"],
                output="3",
                location="src/math.js:10",
                is_complete=True,
            ),
        ]

        test_file = generate_test_file("my-lib", calls)

        assert "import { add } from 'my-lib'" in test_file
        assert "describe('my-lib'" in test_file
        assert "test(" in test_file

    def test_deduplicates_similar_calls(self):
        """Deduplicates calls with same function and similar inputs."""
        calls = [
            CapturedCall(
                function_name="add",
                inputs=["1", "2"],
                output="3",
                location="src/a.js:1",
                is_complete=True,
            ),
            CapturedCall(
                function_name="add",
                inputs=["1", "2"],
                output="3",
                location="src/b.js:2",
                is_complete=True,
            ),
            CapturedCall(
                function_name="add",
                inputs=["5", "10"],
                output="15",
                location="src/c.js:3",
                is_complete=True,
            ),
        ]

        test_file = generate_test_file("my-lib", calls)

        # Should have 2 tests, not 3
        assert test_file.count("test(") == 2
