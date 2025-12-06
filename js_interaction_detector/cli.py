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
    record_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (for testing)",
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


async def run_record(
    url: str, output: str, timeout: int, headless: bool = False
) -> int:
    """Run the record command.

    Args:
        url: URL to record
        output: Output path for generated test
        timeout: Settle timeout in milliseconds
        headless: Run in headless mode (for testing)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    import signal

    from js_interaction_detector.recorder.session import RecordingSession
    from js_interaction_detector.recorder.test_generator import generate_test

    print(
        "Recording... interact with the page, then press Ctrl+C to finish",
        file=sys.stderr,
    )
    print(f"URL: {url}", file=sys.stderr)
    logger.info(
        f"Starting recording session: url={url}, output={output}, timeout={timeout}, headless={headless}"
    )

    actions = []
    session = None

    # Use an event to signal stop instead of a flag
    stop_event = asyncio.Event()

    def handle_sigint(signum, frame):
        # Just set the event, don't print yet (will print after loop exits)
        stop_event.set()

    try:
        session = RecordingSession(url, headed=not headless, settle_timeout=timeout)
        await session.__aenter__()

        if headless:
            # For testing - just return immediately after page loads
            logger.info("Running in headless mode - returning immediately")
        else:
            # Set up signal handler
            signal.signal(signal.SIGINT, handle_sigint)

            try:
                # Wait for stop event in headed mode
                while not stop_event.is_set():
                    # Use wait with timeout instead of sleep to check the event
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=0.1)
                    except TimeoutError:
                        # Timeout is expected - process pending actions
                        try:
                            await session.process_pending_actions()
                        except Exception:
                            pass  # Ignore errors during periodic processing
            finally:
                # Restore original signal handler and ignore further interrupts during cleanup
                signal.signal(signal.SIGINT, signal.SIG_IGN)

        print("\nStopping recording...", file=sys.stderr)

        # Process final pending actions and get results BEFORE closing
        try:
            await session.process_pending_actions()
        except Exception as e:
            logger.warning(f"Could not process final actions: {e}")

        # Get recorded actions (this doesn't need page.evaluate)
        actions = session.get_recorded_actions()
        logger.info(f"Retrieved {len(actions)} recorded actions")

        # Now close the session - ignore any errors
        try:
            if session._browser:
                await session._browser.close()
        except Exception:
            pass
        try:
            if session._playwright:
                await session._playwright.stop()
        except Exception:
            pass

        # Generate test even if no actions (creates basic test structure)
        logger.info(f"Generating test with {len(actions)} actions")
        test_content = generate_test(url, actions)

        # Write output
        with open(output, "w") as f:
            f.write(test_content)
        logger.info(f"Test written to {output}")

        if not actions:
            print(
                f"No actions recorded. Basic test structure written to: {output}",
                file=sys.stderr,
            )
        else:
            print(
                f"Recorded {len(actions)} actions. Test written to: {output}",
                file=sys.stderr,
            )

        return 0

    except Exception as e:
        logger.error(f"Recording failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
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
        return await run_record(
            parsed.url, parsed.output, parsed.timeout, parsed.headless
        )

    return 1


def main():
    """Entry point for the CLI."""
    exit_code = asyncio.run(run_cli(sys.argv[1:]))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
