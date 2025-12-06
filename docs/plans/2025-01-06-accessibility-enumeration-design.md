# Accessibility Tree Enumeration Test Generation

## Problem

Developers upgrading JavaScript libraries (e.g., Vue 2 to Vue 3) need confidence that their application still works after the upgrade. Manually writing tests is tedious, and recording-based approaches are noisy and brittle.

## Solution

Generate Playwright tests by analyzing the accessibility tree of a running web page. The accessibility tree provides a semantic view of interactive elements that remains stable across framework upgrades.

## Scope and Limitations

**This is v1 - presence testing only.** These tests verify that interactive elements exist and respond to basic interaction. They do NOT verify that functionality works correctly.

**What v1 tests catch:**
- Missing UI elements after upgrade
- Elements that become disabled or non-interactive
- Broken element accessibility (missing labels, roles)

**What v1 tests do NOT catch:**
- Broken form submissions
- Incorrect data processing
- Navigation failures
- Business logic errors

**v1 alone does not provide confidence that an upgrade works.** It is a foundation layer. A development team needs v2 (flow-based testing with outcome assertions) to have real upgrade confidence. Think of v1 as "smoke tests" - they catch obvious breakage but not subtle bugs.

## Why Accessibility Tree?

- **Semantic**: A button is a button, regardless of whether it's `<button>`, `<div role="button">`, or a framework component
- **Stable**: Designed to represent what users interact with, not implementation details
- **Framework-agnostic**: Works for Vue, React, Angular, or any web application
- **Playwright-aligned**: Maps directly to Playwright's recommended `getByRole` locators

## CLI Interface

```bash
js-interaction-detector enumerate <url> --output ./a11y-tests.spec.ts
```

**Output:**
```
Analyzing http://localhost:8080...
Found 12 interactive elements:
  - 3 buttons
  - 4 textboxes
  - 2 checkboxes
  - 3 links

Generated 12 tests in ./a11y-tests.spec.ts

Warnings:
  - 2 buttons have no accessible name (skipped)
```

## Interactive Element Types

We generate tests for these roles:
- `button`
- `link`
- `textbox`
- `checkbox`
- `radio`
- `combobox`
- `slider`
- `switch`
- `menuitem`
- `tab`

Non-interactive elements (headings, images, static text) are skipped.

## Generated Tests

### Buttons
```typescript
test('button "Submit" is interactive', async ({ page }) => {
  await page.goto(url);
  const button = page.getByRole('button', { name: 'Submit' });
  await expect(button).toBeVisible();
  await expect(button).toBeEnabled();
});
```

### Text Inputs
```typescript
test('textbox "Email address" accepts input', async ({ page }) => {
  await page.goto(url);
  const input = page.getByRole('textbox', { name: 'Email address' });
  await expect(input).toBeVisible();
  await expect(input).toBeEditable();
  await input.fill('test@example.com');
  await expect(input).toHaveValue('test@example.com');
});
```

### Links
```typescript
test('link "Forgot password?" is present', async ({ page }) => {
  await page.goto(url);
  const link = page.getByRole('link', { name: 'Forgot password?' });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute('href', /.+/);
});
```

### Checkboxes
```typescript
test('checkbox "Remember me" is toggleable', async ({ page }) => {
  await page.goto(url);
  const checkbox = page.getByRole('checkbox', { name: 'Remember me' });
  await expect(checkbox).toBeVisible();
  await checkbox.check();
  await expect(checkbox).toBeChecked();
});
```

## Test File Structure

```typescript
import { test, expect } from '@playwright/test';

const url = 'http://localhost:8080';

test.describe('Accessibility Elements', () => {

  test.describe('Buttons', () => {
    test('button "Submit" is interactive', async ({ page }) => {
      // ...
    });
  });

  test.describe('Text Inputs', () => {
    test('textbox "Email address" accepts input', async ({ page }) => {
      // ...
    });
  });

  test.describe('Links', () => {
    // ...
  });

});
```

## Edge Cases

### Duplicate Names
Multiple elements with the same role and name are numbered:
```typescript
test('button "Submit" (1 of 2) is interactive', ...)
test('button "Submit" (2 of 2) is interactive', ...)
```

### Unnamed Elements
Elements without accessible names are skipped with a warning. This surfaces accessibility issues as a side benefit.

### Iframes
Content inside iframes is not captured in v1. A warning is shown if iframes are detected.

## Known Limitations (v1)

- **Static snapshot only**: Only captures elements present at page load. Dynamic content (modals, lazy-loaded sections) requires user interaction to appear.
- **No outcome assertions**: Tests verify elements exist and respond to interaction, but not what happens after (e.g., form submission results).
- **No flow testing**: Each element is tested in isolation, not as part of user journeys.

## Roadmap

### v1: Presence Testing (this document)
Verify elements exist and are interactive. Smoke test level.

### v2: Flow-Based Testing (required for upgrade confidence)
- Identify related elements (form inputs + submit button)
- Generate complete user flow tests
- Assert on outcomes: form submission results, navigation, API calls
- This is where real upgrade confidence comes from

### v3: Dynamic Content Discovery
- Interact with elements to reveal hidden content (modals, dropdowns)
- Enumerate newly visible elements
- Generate tests for complete UI surface area

### Future Considerations
- Visual regression testing
- API contract verification
- Performance regression detection

## Implementation Notes

### Accessibility Tree Extraction
```python
snapshot = await page.accessibility.snapshot()
# Returns tree structure with role, name, children, etc.
```

### Flattening the Tree
Recursively walk the tree and collect all nodes with interactive roles.

### Generating Locators
Map accessibility tree entries directly to Playwright locators:
```python
role = element["role"]  # "button"
name = element["name"]  # "Submit"
# -> page.getByRole('button', { name: 'Submit' })
```
