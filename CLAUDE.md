# MISSION
Generate Playwright tests given a URL to a web app.

In order to do this, the NUMBER ONE THING is to give clarity and accurate information to the user. If we can't dosomething, it's MUCH better to be clear about that than it is to default to a message that implies that everything worked perfectly. A test generation tool that does 90% of the work and is clear about the remaining 10% is hugely useful. A tool that teaches the user to not trust the output of the tool and forces the user to become a detective to sleuth out what's actually fixed will probably not get used or have any impact at all.

# INPUTS
This application will start with a URL to a working web page. This is the page that we'll generate Playwright tests for. 


# ARCHITECTURE
The playwrite test writing agent itself is written in python, using modern, pythonic code conventions.
The agent has good unit test coverage.
When writing python code, use type hints and docstrings.


# LOGGING
Principle: Log at the Source

Functions that do work should log what they did, not rely on callers to log correctly.

DON'T do this (caller logs):

def is_buildable():
    # Check if project builds
    return check_build()

# Caller has to remember to log
if is_buildable():
    logger.info("Project is buildable!")
    # continue with work
DO this (function logs):

def is_buildable():
    # Check if project builds
    buildable = check_build()
    logger.info(f"Project buildable: {buildable}")
    return buildable

# Caller just uses the result
if is_buildable():
    # continue with work
Why?

Prevents logging drift - Caller can't forget to log or log incorrectly
Eliminates duplication - Multiple callers don't log the same thing differently
Ensures consistency - Same operation always produces same log message
Reduces knowledge pollution - Caller doesn't need to know internals to log properly
Structured Logging


# Feature Branch Workflow
When working on feature branches:

Do NOT commit until the user has tested the changes

Write the code, tests, specs, prompts, configs - everything
Leave all changes uncommitted in the working directory
Tell the user what to run to test (e.g., python -m upgrader ...)
Only commit after the user confirms it works
Keep changes reviewable

The user should be able to see what changed before committing
Use git diff to show uncommitted changes
Explain what each changed file does
This ensures the user can verify changes work in practice before they become part of the git history.

# TESTS
Follow the guidance in TDD.md 

# Component Design
Single Responsibility: Each component does one thing well
Dependency Injection: Pass dependencies via constructor (enable testing)
Dataclasses for Contracts: Use @dataclass for explicit data contracts (see CapturedState, DiffReport, ProposedFix)
Pure Functions Where Possible: Separate business logic (pure) from I/O (side effects)


