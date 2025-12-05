"""Command-line interface for js-interaction-detector."""

import argparse
import asyncio
import logging
import sys

from js_interaction_detector.analyzer import analyze_page

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging to stderr."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="js-interaction-detector",
        description="Detect JavaScript-driven interactions on web pages",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a page for input validations (default)",
    )
    analyze_parser.add_argument(
        "url",
        help="URL to analyze (http, https, or file://)",
    )

    # record subcommand
    record_parser = subparsers.add_parser(
        "record",
        help="Record interactions and generate Playwright tests",
    )
    record_parser.add_argument(
        "url",
        help="URL to record (http, https, or file://)",
    )
    record_parser.add_argument(
        "--output",
        "-o",
        default="./recorded-test.spec.ts",
        help="Output path for generated test (default: ./recorded-test.spec.ts)",
    )
    record_parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=2000,
        help="Settle timeout in milliseconds (default: 2000)",
    )

    return parser


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command-line arguments with backwards compatibility."""
    parser = create_parser()

    # Handle backwards compatibility: bare URL without subcommand
    if args and not args[0].startswith("-") and args[0] not in ("analyze", "record"):
        # Assume it's a URL, prepend 'analyze'
        args = ["analyze"] + args

    return parser.parse_args(args)


async def run_analyze(url: str) -> int:
    """Run the analyze command."""
    logger.info(f"Analyzing URL: {url}")
    result = await analyze_page(url)
    print(result.to_json())
    return 0


async def run_record(url: str, output: str, timeout: int) -> int:
    """Run the record command."""
    # Placeholder - will be implemented in later tasks
    print(
        f"Recording not yet implemented. URL: {url}, Output: {output}", file=sys.stderr
    )
    return 1


async def run_cli(args: list[str]) -> int:
    """Run the CLI with the given arguments.

    Args:
        args: Command-line arguments (without program name)

    Returns:
        Exit code (0 for success, non-zero for fatal errors)
    """
    setup_logging()

    try:
        parsed = parse_args(args)
    except SystemExit as e:
        return e.code if e.code else 1

    if parsed.command is None:
        # No command and no args - show help
        create_parser().print_help(sys.stderr)
        return 1

    if parsed.command == "analyze":
        return await run_analyze(parsed.url)
    elif parsed.command == "record":
        return await run_record(parsed.url, parsed.output, parsed.timeout)

    return 1


def main():
    """Entry point for the CLI."""
    exit_code = asyncio.run(run_cli(sys.argv[1:]))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
