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

### Enumerate Interactive Elements

Generate presence tests for all interactive elements on a page using the accessibility tree:

```bash
python -m js_interaction_detector enumerate https://example.com
```

This analyzes the page's accessibility tree and generates tests that verify each interactive element (buttons, links, inputs, etc.) is present and functional. Tests use Playwright's recommended `getByRole` locators for maximum stability.

Options:
- `--output FILE`, `-o FILE` - Output path for generated test (default: `./a11y-tests.spec.ts`)

Example:

```bash
python -m js_interaction_detector enumerate http://localhost:8080 -o tests/a11y.spec.ts
```

**Note:** This generates v1 "presence tests" - they verify elements exist and are interactive, but don't test functionality or user flows. See the [design doc](docs/plans/2025-01-06-accessibility-enumeration-design.md) for the roadmap.

### Analyze Library Usage (Functional APIs)

Analyze your source code for library usage and generate tests:

```bash
python -m js_interaction_detector functional analyze --library lodash --source ./src
```

This:
1. Scans your source for imports and calls to the specified library
2. Reports which functions are used and how often
3. Generates an instrumentation script to capture runtime values

To capture runtime values:
1. Inject the generated `instrumentation.js` into your dev environment
2. Use your app normally, triggering the library calls
3. Copy the test code from the browser console
4. Paste into your test file

Options:
- `--library`, `-l` - Library name to analyze (required)
- `--source`, `-s` - Source directory to scan (required)
- `--output`, `-o` - Output path for instrumentation script (default: `./instrumentation.js`)

**Note:** This is Tool A of the functional API tester - it focuses on pure functions with input/output relationships. Tool B (side-effect APIs) is planned for a future release.

### Record Interactions

Record user interactions and generate Playwright tests:

```bash
python -m js_interaction_detector record https://example.com
```

The browser opens in headed mode. Interact with the page (click buttons, fill forms, etc.), then press `Ctrl+C` to stop recording. The tool generates a TypeScript Playwright test file.

Options:
- `--output FILE`, `-o FILE` - Output path for generated test (default: `./recorded-test.spec.ts`)
- `--timeout MS`, `-t MS` - Settle timeout in milliseconds (default: 2000)
- `--headless` - Run in headless mode (for testing/automation)

Example:

```bash
# Record interactions on localhost app
python -m js_interaction_detector record http://localhost:8080 -o tests/my-app.spec.ts

# The tool captures:
# - Click actions → page.click() calls
# - Form input → page.fill() calls
# - DOM changes → toBeVisible()/toBeHidden() assertions
# - CSS changes → toHaveCSS() assertions
# - API calls → waitForRequest() assertions
```

Generated test example:

```typescript
import { test, expect } from '@playwright/test';

test('recorded interaction test', async ({ page }) => {
  await page.goto('http://localhost:8080');

  await page.click('[data-testid="menu-btn"]');
  await expect(page.locator('.dropdown-menu')).toBeVisible();

  await page.click('.menu-item.settings');
  await expect(page.locator('.settings-panel')).toBeVisible();
});
```

**Note:** Recording is single-page only. If you click a link that navigates away, the tool automatically goes back to the original page.

## Running Generated Tests

The generated `.spec.ts` files are Playwright tests. To run them:

```bash
# Install Playwright test runner (one-time setup)
npm init -y
npm install -D @playwright/test
npx playwright install chromium

# Run tests
npx playwright test my-tests.spec.ts

# Run with visible browser
npx playwright test my-tests.spec.ts --headed

# Generate HTML report
npx playwright test my-tests.spec.ts --reporter=html
npx playwright show-report
```

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
