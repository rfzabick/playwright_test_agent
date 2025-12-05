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
