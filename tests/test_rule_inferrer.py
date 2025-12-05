"""Tests for validation rule inference."""

from js_interaction_detector.rule_inferrer import infer_validation_rule


class TestRuleInferrer:
    def given_code(self, code):
        self.code = code

    def when_rule_is_inferred(self):
        self.rule = infer_validation_rule(self.code)

    def then_rule_type_is(self, expected_type):
        assert self.rule.type == expected_type

    def then_confidence_is(self, expected_confidence):
        assert self.rule.confidence == expected_confidence

    def then_confidence_is_one_of(self, *expected_confidences):
        assert self.rule.confidence in expected_confidences

    def then_confidence_is_none(self):
        assert self.rule.confidence is None

    def then_description_contains(self, text):
        assert (
            text in self.rule.description
            or text.lower() in self.rule.description.lower()
        )

    def test_infers_email_from_regex(self):
        """Code with email regex pattern is recognized as email validation."""
        self.given_code(
            "if (!/.+@.+\\..+/.test(value)) { showError('Invalid email'); }"
        )
        self.when_rule_is_inferred()
        self.then_rule_type_is("email")
        self.then_confidence_is("high")
        self.then_description_contains("email")

    def test_infers_phone_from_digit_pattern(self):
        """Code with phone number regex is recognized as phone validation."""
        self.given_code("if (!/^\\d{3}-\\d{3}-\\d{4}$/.test(value)) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("phone")
        self.then_confidence_is_one_of("high", "medium")

    def test_infers_required_from_empty_check(self):
        """Code checking for empty string or null is recognized as required."""
        self.given_code(
            "if (value === '' || value === null) { showError('Required'); }"
        )
        self.when_rule_is_inferred()
        self.then_rule_type_is("required")

    def test_infers_required_from_length_zero_check(self):
        """Code checking length === 0 is recognized as required."""
        self.given_code("if (value.length === 0) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("required")

    def test_infers_min_length(self):
        """Code with length < N check is recognized as min_length."""
        self.given_code("if (value.length < 8) { showError('Too short'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("min_length")
        self.then_description_contains("8")

    def test_infers_max_length(self):
        """Code with length > N check is recognized as max_length."""
        self.given_code("if (value.length > 100) { showError('Too long'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("max_length")
        self.then_description_contains("100")

    def test_infers_numeric(self):
        """Code with isNaN check is recognized as numeric validation."""
        self.given_code("if (isNaN(value)) { showError('Must be a number'); }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("numeric")

    def test_infers_numeric_from_digit_regex(self):
        """Code with digits-only regex is recognized as numeric validation."""
        self.given_code("if (!/^\\d+$/.test(value)) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("numeric")

    def test_infers_url_pattern(self):
        """Code with URL regex is recognized as url validation."""
        self.given_code(
            "if (!/^https?:\\/\\/.+/.test(value)) { showError('Invalid URL'); }"
        )
        self.when_rule_is_inferred()
        self.then_rule_type_is("url")

    def test_returns_unknown_for_unrecognized_code(self):
        """Unrecognized validation code returns type='unknown'."""
        self.given_code("customValidator.check(value, options);")
        self.when_rule_is_inferred()
        self.then_rule_type_is("unknown")
        self.then_confidence_is_none()

    def test_captures_custom_regex_pattern(self):
        """Custom regex patterns are recognized as type='pattern'."""
        self.given_code("if (!/^[A-Z]{2}\\d{6}$/.test(value)) { return false; }")
        self.when_rule_is_inferred()
        self.then_rule_type_is("pattern")

    def test_handles_empty_code(self):
        """Empty code returns type='unknown'."""
        self.given_code("")
        self.when_rule_is_inferred()
        self.then_rule_type_is("unknown")

    def test_handles_multiple_patterns_takes_most_specific(self):
        """When multiple patterns match, the most specific one wins."""
        self.given_code("""
        if (value.length < 5) { showError('Too short'); }
        if (!/.+@.+/.test(value)) { showError('Invalid email'); }
        """)
        self.when_rule_is_inferred()
        self.then_rule_type_is("email")
