# Recording Mode Design

## Purpose

Add a recording mode that generates Playwright TypeScript tests by observing user interactions. User opens a page, clicks around, and the tool captures what changed after each action, then outputs a ready-to-run test file.

## Scope

**v1 includes:**
- `record` subcommand for the CLI
- DOM change detection via MutationObserver
- CSS change detection via computed style diffing
- Network request logging (API calls only, not static assets)
- TypeScript Playwright test generation
- Single-page recording only
- Help output and README documentation

**Deferred to later versions:**
- Python test output
- Multi-page/spidering
- Human-guided exploration mode
- Fully automatic exploration mode
- Full request/response body capture
- Screenshot/visual diffing

---

## Architecture

Three main components:

### 1. Action Tracker

Intercepts user clicks, keypresses, and form inputs. For each action, records:
- Which element was acted upon
- Playwright action code (e.g., `await page.click('#bell-icon')`)

### 2. Change Observer

Detects what changed after each action:

**DOM Changes** (via MutationObserver):
- Elements added → assert `toBeVisible()`
- Elements removed → assert `toBeHidden()` or `not.toBeAttached()`
- Visibility toggled → assert `toBeVisible()` or `toBeHidden()`
- Text content changed → assert `toHaveText()`

**CSS Changes** (via computed style diffing):
- Track "interesting" properties: background-color, color, border-color, transform, opacity
- Only track CSS on elements that had DOM mutations or their ancestors/siblings within 2 levels

**Network Requests** (via Playwright's `page.on('request')`):
- Capture URL and method for API calls (fetch/XHR)
- Filter out static assets (images, fonts, CSS, JS, webpack HMR)
- Generate: `await page.waitForRequest(req => req.url().includes('/api/...'))`

**Settle detection:**
- Action is "settled" when network is idle and no mutations for 100ms

### 3. Test Generator

Takes the sequence of (action, changes) pairs and generates a `.spec.ts` file.

**Selector strategy** (priority order):
1. `data-testid` attribute (most stable)
2. `id` attribute
3. Unique `aria-label` or role
4. CSS selector based on class + position

---

## CLI Interface

```bash
# Existing command (detects input validations)
python -m js_interaction_detector https://example.com

# New recording command
python -m js_interaction_detector record https://example.com

# Options
python -m js_interaction_detector record https://example.com --output tests/my-test.spec.ts
python -m js_interaction_detector record https://example.com --timeout 30000
```

**Session flow:**
1. CLI prints: "Recording... interact with the page, then press Ctrl+C to finish"
2. Browser opens at the URL (headed mode)
3. User interacts with the page
4. User presses Ctrl+C
5. CLI prints summary: "Recorded 5 actions with 12 assertions"
6. Writes test file to `--output` path (default: `./recorded-test.spec.ts`)

---

## Example Output

For a session where the user clicks a notification bell, then opens settings and changes a color:

```typescript
import { test, expect } from '@playwright/test';

test('recorded interaction test', async ({ page }) => {
  await page.goto('http://localhost:8080');

  // Click notification bell
  await page.click('[data-testid="bell-icon"]');
  await expect(page.locator('.notification-dropdown')).toBeVisible();
  await expect(page.locator('.notification-dropdown .item')).toHaveCount(3);

  // Click settings wheel
  await page.click('[data-testid="settings-icon"]');
  await expect(page.locator('.settings-panel')).toBeVisible();

  // Click blue color option
  await page.click('.color-option.blue');
  await expect(page.locator('.navbar-selection-box')).toHaveCSS('background-color', 'rgb(0, 0, 255)');
});
```

---

## Error Handling

**Timeouts:**
- If a click triggers no observable changes after 2 seconds, record the action with comment: `// No observable changes detected`
- User can adjust settle timeout via `--timeout`

**Selector failures:**
- If no reliable selector available, generate best effort with warning: `// Warning: fragile selector - consider adding data-testid`

**Page navigation:**
- If an action navigates to a new page, call `page.goBack()` and add comment: `// Action triggered navigation to /new-page - skipped for single-page recording`

**Ctrl+C handling:**
- Graceful shutdown: finish current action, then generate test file
- If no actions recorded, print "No actions recorded" and exit without creating file

**Network request filtering:**
- Ignore: `*.js`, `*.css`, `*.png`, `*.jpg`, `*.gif`, `*.woff`, `*.svg`, `hot-update`
- Capture: Anything to `/api/`, or any fetch/XHR returning JSON
