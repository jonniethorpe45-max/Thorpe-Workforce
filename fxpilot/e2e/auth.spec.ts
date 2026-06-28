import { expect, test } from '@playwright/test'

test('auth page allows mock login flow', async ({ page }) => {
  await page.goto('/auth')

  await page.getByLabel('Email').fill('trader@example.com')
  await page.getByLabel('Password').fill('StrongPass123')
  await page.getByRole('button', { name: 'Login to FXPilot' }).click()

  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByText('Broker Connection')).toBeVisible()
})
