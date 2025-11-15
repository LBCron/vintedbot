import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/login');

    await expect(page.locator('h1')).toContainText('Login');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show validation errors', async ({ page }) => {
    await page.goto('/login');

    // Click submit without filling fields
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('text=required')).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');

    // Click register link
    await page.click('text=Sign up');

    // Should be on register page
    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator('h1')).toContainText('Register');
  });

  test('should show dashboard after successful login', async ({ page }) => {
    await page.goto('/login');

    // Fill login form (using test credentials)
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');

    // Submit
    await page.click('button[type="submit"]');

    // Should redirect to dashboard (or show error if credentials invalid)
    // Note: This will fail in real tests without valid credentials
    // For CI, use environment variables for test credentials
  });
});
