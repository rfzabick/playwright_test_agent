"""Tests for CLI interface."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from js_interaction_detector.cli import run_cli


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures" / "sample_pages"


class TestCLI:
    def given_valid_url(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"
        self.args = [self.url]

    def given_unreachable_url(self):
        self.args = ["https://localhost:99999/nope"]

    def given_no_args(self):
        self.args = []

    async def when_cli_is_run(self):
        self.exit_code = await run_cli(self.args)

    async def when_cli_is_run_capturing_output(self, capsys):
        self.exit_code = await run_cli(self.args)
        self.captured = capsys.readouterr()

    def then_exit_code_is_zero(self):
        assert self.exit_code == 0

    def then_exit_code_is_nonzero(self):
        assert self.exit_code != 0

    def then_stdout_is_valid_json_with_url(self):
        output = json.loads(self.captured.out)
        assert output["url"] == self.url
        assert "interactions" in output

    def then_stderr_mentions_usage(self):
        assert (
            "usage" in self.captured.err.lower()
            or "required" in self.captured.err.lower()
        )

    @pytest.mark.asyncio
    async def test_outputs_json_to_stdout(self, fixtures_path, capsys):
        """CLI outputs valid JSON to stdout."""
        self.given_valid_url(fixtures_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_stdout_is_valid_json_with_url()

    @pytest.mark.asyncio
    async def test_returns_zero_on_success(self, fixtures_path):
        """CLI returns exit code 0 on successful analysis."""
        self.given_valid_url(fixtures_path)
        await self.when_cli_is_run()
        self.then_exit_code_is_zero()

    @pytest.mark.asyncio
    async def test_returns_zero_with_partial_results(self):
        """CLI returns exit code 0 even with errors (partial results strategy)."""
        self.given_unreachable_url()
        await self.when_cli_is_run()
        self.then_exit_code_is_zero()

    @pytest.mark.asyncio
    async def test_returns_nonzero_for_missing_url(self, capsys):
        """CLI returns non-zero exit code when URL argument is missing."""
        self.given_no_args()
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_nonzero()
        self.then_stderr_mentions_usage()

    @pytest.mark.asyncio
    async def test_errors_go_to_stderr(self):
        """CLI sends logging/errors to stderr, not stdout."""
        self.given_unreachable_url()
        with patch("sys.stderr", new_callable=StringIO):
            await self.when_cli_is_run()
        self.then_exit_code_is_zero()


class TestCLISubcommands:
    def given_analyze_command(self, fixtures_path):
        self.url = f"file://{fixtures_path}/form_with_validation.html"
        self.args = ["analyze", self.url]

    def given_record_command(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"
        self.args = ["record", self.url]

    def given_no_subcommand(self, fixtures_path):
        self.url = f"file://{fixtures_path}/simple_form.html"
        self.args = [self.url]

    def given_help_flag(self):
        self.args = ["--help"]

    async def when_cli_is_run_capturing_output(self, capsys):
        self.exit_code = await run_cli(self.args)
        self.captured = capsys.readouterr()

    def then_exit_code_is_zero(self):
        assert self.exit_code == 0

    def then_exit_code_is_nonzero(self):
        assert self.exit_code != 0

    def then_stdout_is_valid_json(self):
        output = json.loads(self.captured.out)
        assert "url" in output

    def then_stderr_mentions_subcommands(self):
        assert "analyze" in self.captured.err or "analyze" in self.captured.out
        assert "record" in self.captured.err or "record" in self.captured.out

    @pytest.mark.asyncio
    async def test_analyze_subcommand_works(self, fixtures_path, capsys):
        """'analyze' subcommand runs the existing detection."""
        self.given_analyze_command(fixtures_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_stdout_is_valid_json()

    @pytest.mark.asyncio
    async def test_bare_url_still_works_for_backwards_compat(
        self, fixtures_path, capsys
    ):
        """Bare URL without subcommand defaults to analyze."""
        self.given_no_subcommand(fixtures_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_stdout_is_valid_json()

    @pytest.mark.asyncio
    async def test_help_shows_subcommands(self, capsys):
        """--help shows available subcommands."""
        self.given_help_flag()
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_stderr_mentions_subcommands()


class TestRecordCommand:
    """Test the record command that generates Playwright tests."""

    def given_record_command_with_simple_page(self, fixtures_path, tmp_path):
        """Set up record command with simple page."""
        self.url = f"file://{fixtures_path}/simple_form.html"
        self.output_file = str(tmp_path / "test-recorded.spec.ts")
        self.args = ["record", self.url, "--output", self.output_file, "--headless"]

    async def when_cli_is_run_capturing_output(self, capsys):
        """Run the CLI and capture output."""
        self.exit_code = await run_cli(self.args)
        self.captured = capsys.readouterr()

    def then_exit_code_is_zero(self):
        """Verify exit code is 0."""
        assert self.exit_code == 0

    def then_output_file_exists(self):
        """Verify output file was created."""
        assert Path(self.output_file).exists()

    def then_output_is_valid_playwright_test(self):
        """Verify output contains valid Playwright test structure."""
        content = Path(self.output_file).read_text()
        assert "import { test, expect }" in content
        assert "test('recorded interaction test'" in content
        assert "await page.goto(" in content

    def then_stderr_mentions_recording(self):
        """Verify stderr mentions recording."""
        assert "recording" in self.captured.err.lower()

    @pytest.mark.asyncio
    async def test_record_command_generates_test_file(
        self, fixtures_path, tmp_path, capsys
    ):
        """Record command in headless mode creates output file."""
        self.given_record_command_with_simple_page(fixtures_path, tmp_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_exit_code_is_zero()
        self.then_output_file_exists()
        self.then_output_is_valid_playwright_test()

    @pytest.mark.asyncio
    async def test_record_command_outputs_to_stderr(
        self, fixtures_path, tmp_path, capsys
    ):
        """Record command outputs status messages to stderr."""
        self.given_record_command_with_simple_page(fixtures_path, tmp_path)
        await self.when_cli_is_run_capturing_output(capsys)
        self.then_stderr_mentions_recording()


class TestFunctionalCommand:
    """Tests for the functional API testing command."""

    @pytest.fixture
    def sample_js_dir(self, tmp_path):
        """Create a sample JS directory with lodash usage."""
        js_file = tmp_path / "src" / "utils.js"
        js_file.parent.mkdir(parents=True)
        js_file.write_text("""
import { groupBy } from 'lodash';

const users = [{ name: 'alice', age: 30 }];
const byAge = groupBy(users, 'age');
""")
        return tmp_path

    async def test_functional_analyze_finds_usage(self, sample_js_dir, capsys):
        """functional analyze command finds library usage."""
        exit_code = await run_cli(
            [
                "functional",
                "analyze",
                "--library",
                "lodash",
                "--source",
                str(sample_js_dir / "src"),
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "groupBy" in captured.err  # Summary goes to stderr
