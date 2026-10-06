import { expect, test } from '@playwright/test'

test('home screen renders core inspection controls', async ({ page }) => {
  await page.goto('http://localhost:5173/')

  await expect(page.getByRole('button', { name: 'SELECT IMAGE' })).toBeVisible()
})
