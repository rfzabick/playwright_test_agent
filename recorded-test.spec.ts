import { test, expect } from '@playwright/test';

test('recorded interaction test', async ({ page }) => {
  await page.goto('http://reddit.com');

});
