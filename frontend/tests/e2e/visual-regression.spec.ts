/**
 * Visual Regression Tests
 *
 * Captures screenshots and compares them to detect visual changes
 */
import { test, expect } from '@playwright/test';

test.describe('Visual Regression - Critical Pages', () => {

  // Configure for visual testing
  test.use({
    viewport: { width: 1280, height: 720 }
  });

  test('Homepage - Desktop', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for any animations to complete
    await page.waitForTimeout(500);

    // Take screenshot
    await expect(page).toHaveScreenshot('homepage-desktop.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Login Page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Dashboard - Empty State', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('dashboard-empty.png', {
      fullPage: true,
      animations: 'disabled',
      mask: [
        // Mask dynamic content (dates, times, user-specific data)
        page.locator('text=/\\d{4}-\\d{2}-\\d{2}|\\d{2}:\\d{2}/').first()
      ]
    });
  });

  test('Upload Page', async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('upload-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Drafts Page', async ({ page }) => {
    await page.goto('/drafts');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('drafts-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Analytics Page', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Charts may take longer to render

    await expect(page).toHaveScreenshot('analytics-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Messages Page', async ({ page }) => {
    await page.goto('/messages');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('messages-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Automation Page', async ({ page }) => {
    await page.goto('/automation');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('automation-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Settings Page', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('settings-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });
});

test.describe('Visual Regression - Mobile', () => {

  test.use({
    viewport: { width: 375, height: 667 } // iPhone SE
  });

  test('Homepage - Mobile', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('homepage-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Dashboard - Mobile', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('dashboard-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Upload - Mobile', async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('upload-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });
});

test.describe('Visual Regression - Dark Mode', () => {

  test.use({
    viewport: { width: 1280, height: 720 },
    colorScheme: 'dark'
  });

  test('Homepage - Dark Mode', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Ensure dark mode is active
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
    });

    await expect(page).toHaveScreenshot('homepage-dark.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Dashboard - Dark Mode', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
    });

    await expect(page).toHaveScreenshot('dashboard-dark.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });
});

test.describe('Visual Regression - Component States', () => {

  test.use({
    viewport: { width: 1280, height: 720 }
  });

  test('Modal - Open State', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Try to trigger a modal (if exists)
    const modalTrigger = page.locator('button:has-text("Create"), button:has-text("Add")').first();

    if (await modalTrigger.count() > 0) {
      await modalTrigger.click();
      await page.waitForTimeout(300);

      await expect(page).toHaveScreenshot('modal-open.png', {
        animations: 'disabled'
      });
    }
  });

  test('Dropdown - Expanded', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Try to open language switcher or user menu
    const dropdown = page.locator('[aria-label*="language"], [aria-haspopup="true"]').first();

    if (await dropdown.count() > 0) {
      await dropdown.click();
      await page.waitForTimeout(200);

      await expect(page).toHaveScreenshot('dropdown-expanded.png', {
        animations: 'disabled'
      });
    }
  });

  test('Form - Validation State', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Submit empty form to trigger validation
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    await page.waitForTimeout(300);

    await expect(page).toHaveScreenshot('form-validation.png', {
      animations: 'disabled'
    });
  });

  test('Loading State', async ({ page }) => {
    await page.goto('/dashboard');

    // Capture loading state (before networkidle)
    await page.waitForTimeout(100);

    await expect(page).toHaveScreenshot('loading-state.png', {
      animations: 'disabled'
    });
  });
});

test.describe('Visual Regression - Language Variants', () => {

  test('French Language - Homepage', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Set French language
    await page.evaluate(() => {
      localStorage.setItem('vintedbot_language', 'fr');
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('homepage-fr.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('English Language - Homepage', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Set English language
    await page.evaluate(() => {
      localStorage.setItem('vintedbot_language', 'en');
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('homepage-en.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });
});

test.describe('Visual Regression - Responsive Breakpoints', () => {

  const breakpoints = [
    { name: 'mobile-sm', width: 320, height: 568 },    // iPhone SE (old)
    { name: 'mobile-md', width: 375, height: 667 },    // iPhone SE
    { name: 'mobile-lg', width: 414, height: 896 },    // iPhone XR
    { name: 'tablet', width: 768, height: 1024 },      // iPad
    { name: 'laptop', width: 1366, height: 768 },      // Laptop
    { name: 'desktop', width: 1920, height: 1080 }     // Desktop
  ];

  for (const breakpoint of breakpoints) {
    test(`Dashboard - ${breakpoint.name} (${breakpoint.width}x${breakpoint.height})`, async ({ page }) => {
      await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot(`dashboard-${breakpoint.name}.png`, {
        fullPage: false, // Only visible area
        animations: 'disabled'
      });
    });
  }
});

test.describe('Visual Regression - Error States', () => {

  test('404 Page', async ({ page }) => {
    await page.goto('/this-does-not-exist');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('404-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Network Error State', async ({ page }) => {
    // Simulate offline mode
    await page.context().setOffline(true);

    await page.goto('/dashboard');
    await page.waitForTimeout(1000);

    await expect(page).toHaveScreenshot('network-error.png', {
      fullPage: true,
      animations: 'disabled'
    });

    await page.context().setOffline(false);
  });
});
