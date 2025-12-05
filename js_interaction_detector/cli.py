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


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="js-interaction-detector",
        description="Detect JavaScript-driven input validations on web pages",
    )
    parser.add_argument(
        "url",
        help="URL to analyze (http, https, or file://)",
    )
    return parser.parse_args(args)


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

    logger.info(f"Analyzing URL: {parsed.url}")
    result = await analyze_page(parsed.url)

    # Output JSON to stdout
    print(result.to_json())

    # Return 0 even with partial results (per spec)
    return 0


def main():
    """Entry point for the CLI."""
    exit_code = asyncio.run(run_cli(sys.argv[1:]))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
