import { expect, test } from '@playwright/test'

test('trade panel opens confirmation dialog', async ({ page }) => {
  await page.goto('/auth')

  await page.getByLabel('Email').fill('trader@example.com')
  await page.getByLabel('Password').fill('StrongPass123')
  await page.getByRole('button', { name: 'Login to FXPilot' }).click()
  await page.goto('/dashboard/trade')

  await page.getByLabel('Units').fill('7000')
  await page.getByRole('button', { name: 'Review order' }).click()

  await expect(page.getByText('Confirm trade execution')).toBeVisible()
})
