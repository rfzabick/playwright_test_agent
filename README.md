# js-interaction-detector

A Python CLI tool that detects JavaScript-driven interactions on web pages and generates Playwright tests.

## Installation

Requires Python 3.14+.

```bash
# Clone the repository
git clone https://github.com/rfzabick/playwright_test_agent.git
cd playwright_test_agent

# Create virtual environment (using conda py314 or any Python 3.14+)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium
```

## Usage

### Detect Input Validations

Analyze a page for JavaScript-driven input validations:

```bash
python -m js_interaction_detector https://example.com/form
```

Outputs JSON describing detected validations:
- Element selectors and metadata
- Event triggers (blur, input, change, etc.)
- Inferred validation rules (email, phone, required, min_length, etc.)
- Raw JavaScript code for each handler

Example with a local file:

```bash
python -m js_interaction_detector file://$(pwd)/tests/fixtures/sample_pages/form_with_validation.html
```

### Record Interactions (Coming Soon)

Record user interactions and generate Playwright tests:

```bash
python -m js_interaction_detector record https://example.com
```

Options:
- `--output FILE` - Output path for generated test (default: `./recorded-test.spec.ts`)
- `--timeout MS` - Settle timeout in milliseconds (default: 2000)

The browser opens, you interact with the page, then press Ctrl+C. The tool generates a TypeScript Playwright test with assertions for:
- DOM changes (elements appearing/disappearing)
- CSS changes (colors, visibility)
- Network requests (API calls)

## Development

Run tests:

```bash
pytest -v
```

Run linting:

```bash
ruff check js_interaction_detector/ tests/
ruff format js_interaction_detector/ tests/
```

## License

MIT
