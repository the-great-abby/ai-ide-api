import { test, expect } from '@playwright/test';

test('Enhancements Details Button and User Story', async ({ page }) => {
  await page.goto('http://frontend:80');
  await page.getByRole('heading', { name: /Suggested Enhancements/i }).waitFor();

  // Find all enhancement rows
  const tables = await page.locator('table');
  // The enhancements table is usually the last one on the page
  const enhancementsTable = tables.nth(await tables.count() - 1);
  const rows = enhancementsTable.locator('tbody tr');
  const rowCount = await rows.count();

  if (rowCount === 0) {
    // If no enhancements, check for the empty state message
    await expect(page.getByText(/No enhancements submitted yet\./i)).toBeVisible();
    return;
  }

  // For each row, check for a Details button
  for (let i = 0; i < rowCount; i++) {
    const detailsButton = rows.nth(i).getByRole('button', { name: /Details/i });
    await expect(detailsButton).toBeVisible();
  }

  // Click the Details button for the first enhancement
  const firstDetailsButton = rows.nth(0).getByRole('button', { name: /Details/i });
  await firstDetailsButton.click();

  // Check that a details panel appears
  const detailsPanel = page.locator('tr').filter({ hasText: 'Full Enhancement:' });
  await expect(detailsPanel).toBeVisible();

  // If user story is present, check for its text
  const userStory = detailsPanel.locator('strong', { hasText: 'User Story:' });
  if (await userStory.count() > 0) {
    await expect(userStory).toBeVisible();
  }
}); 