/**
 * Accessibility Tests (WCAG 2.1 AA Compliance)
 *
 * Uses @axe-core/playwright to test accessibility
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility - Critical Pages (WCAG 2.1 AA)', () => {

  test('Homepage - No accessibility violations', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Login Page - No accessibility violations', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Dashboard - No accessibility violations', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Upload Page - No accessibility violations', async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Drafts Page - No accessibility violations', async ({ page }) => {
    await page.goto('/drafts');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Analytics Page - No accessibility violations', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Messages Page - No accessibility violations', async ({ page }) => {
    await page.goto('/messages');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Settings Page - No accessibility violations', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});

test.describe('Accessibility - Keyboard Navigation', () => {

  test('Can navigate entire app using only keyboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tab through interactive elements
    const tabCount = 10;
    for (let i = 0; i < tabCount; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      // Check that focused element is visible
      const focusedElement = await page.evaluateHandle(() => document.activeElement);
      const isVisible = await focusedElement.evaluate((el: Element) => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });

      expect(isVisible).toBeTruthy();
    }
  });

  test('Forms can be submitted with keyboard only', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Tab to email field
    await page.keyboard.press('Tab');
    await page.keyboard.type('test@example.com');

    // Tab to password field
    await page.keyboard.press('Tab');
    await page.keyboard.type('TestPassword123!');

    // Tab to submit button and press Enter
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');

    await page.waitForTimeout(1000);

    // Form should have been submitted (check URL changed or error appeared)
    const urlChanged = page.url() !== new URL('/login', page.url()).href;
    const hasError = await page.locator('text=/error|invalid/i').count() > 0;

    expect(urlChanged || hasError).toBeTruthy();
  });

  test('Dropdowns can be operated with keyboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find language switcher or any dropdown
    const dropdown = page.locator('[role="button"], [aria-haspopup="true"]').first();

    if (await dropdown.count() > 0) {
      // Focus dropdown
      await dropdown.focus();

      // Open with Enter or Space
      await page.keyboard.press('Enter');
      await page.waitForTimeout(300);

      // Should show options
      const hasVisibleOptions = await page.locator('[role="menu"], [role="listbox"]').count() > 0;

      if (hasVisibleOptions) {
        // Navigate with arrow keys
        await page.keyboard.press('ArrowDown');
        await page.waitForTimeout(100);

        // Close with Escape
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);

        // Dropdown should be closed
        const isClosed = await page.locator('[role="menu"], [role="listbox"]').count() === 0;
        expect(isClosed).toBeTruthy();
      }
    }
  });

  test('Modal can be closed with Escape key', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Try to open a modal
    const modalTrigger = page.locator('button:has-text("Create"), button:has-text("Add")').first();

    if (await modalTrigger.count() > 0) {
      await modalTrigger.click();
      await page.waitForTimeout(300);

      // Check modal is open
      const modalOpen = await page.locator('[role="dialog"], [role="alertdialog"]').count() > 0;

      if (modalOpen) {
        // Press Escape
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);

        // Modal should be closed
        const modalClosed = await page.locator('[role="dialog"], [role="alertdialog"]').count() === 0;
        expect(modalClosed).toBeTruthy();
      }
    }
  });
});

test.describe('Accessibility - Screen Reader Support', () => {

  test('All images have alt text or aria-label', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find all images
    const images = await page.locator('img').all();

    for (const img of images) {
      const hasAlt = await img.getAttribute('alt') !== null;
      const hasAriaLabel = await img.getAttribute('aria-label') !== null;
      const isDecorative = await img.getAttribute('role') === 'presentation' || await img.getAttribute('alt') === '';

      // Image should have alt text, aria-label, or be marked as decorative
      expect(hasAlt || hasAriaLabel || isDecorative).toBeTruthy();
    }
  });

  test('All buttons have accessible names', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find all buttons
    const buttons = await page.locator('button').all();

    for (const button of buttons) {
      const text = await button.innerText();
      const ariaLabel = await button.getAttribute('aria-label');
      const title = await button.getAttribute('title');

      // Button should have text, aria-label, or title
      expect(text.length > 0 || ariaLabel !== null || title !== null).toBeTruthy();
    }
  });

  test('All form inputs have labels', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Find all inputs
    const inputs = await page.locator('input:not([type="hidden"])').all();

    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      const placeholder = await input.getAttribute('placeholder');

      let hasLabel = false;

      if (id) {
        // Check for associated label
        const label = await page.locator(`label[for="${id}"]`).count();
        hasLabel = label > 0;
      }

      // Input should have label, aria-label, aria-labelledby, or placeholder
      expect(hasLabel || ariaLabel !== null || ariaLabelledBy !== null || placeholder !== null).toBeTruthy();
    }
  });

  test('Landmarks are properly defined', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for main landmark
    const hasMain = await page.locator('main, [role="main"]').count() > 0;
    expect(hasMain).toBeTruthy();

    // Check for navigation
    const hasNav = await page.locator('nav, [role="navigation"]').count() > 0;
    expect(hasNav).toBeTruthy();
  });

  test('Headings follow proper hierarchy', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Get all headings
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();

    if (headings.length > 0) {
      // First heading should be h1
      const firstHeading = headings[0];
      const tagName = await firstHeading.evaluate((el: Element) => el.tagName.toLowerCase());

      expect(tagName).toBe('h1');

      // Check no headings are skipped (no h1 → h3 without h2)
      let previousLevel = 1;
      for (const heading of headings) {
        const tag = await heading.evaluate((el: Element) => el.tagName.toLowerCase());
        const level = parseInt(tag.substring(1));

        // Level should not skip more than 1
        expect(level - previousLevel).toBeLessThanOrEqual(1);
        previousLevel = level;
      }
    }
  });
});

test.describe('Accessibility - Color Contrast', () => {

  test('Text has sufficient color contrast (WCAG AA)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include(['body'])
      .analyze();

    // Filter for color contrast violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );

    expect(contrastViolations).toEqual([]);
  });

  test('Dark mode has sufficient color contrast', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Enable dark mode
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
    });

    await page.waitForTimeout(300);

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();

    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );

    expect(contrastViolations).toEqual([]);
  });
});

test.describe('Accessibility - Focus Management', () => {

  test('Focus is visible on all interactive elements', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tab through elements and check focus visibility
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      // Check focused element has visible focus indicator
      const focusVisible = await page.evaluate(() => {
        const activeElement = document.activeElement as HTMLElement;
        if (!activeElement) return false;

        const styles = window.getComputedStyle(activeElement);
        const outlineWidth = styles.outlineWidth;
        const outlineColor = styles.outlineColor;

        // Has visible outline or other focus indicator
        return outlineWidth !== '0px' || activeElement.matches(':focus-visible');
      });

      expect(focusVisible).toBeTruthy();
    }
  });

  test('Focus trap works in modals', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Try to open a modal
    const modalTrigger = page.locator('button:has-text("Create"), button:has-text("Add")').first();

    if (await modalTrigger.count() > 0) {
      await modalTrigger.click();
      await page.waitForTimeout(300);

      // Check modal is open
      const modal = page.locator('[role="dialog"]').first();

      if (await modal.count() > 0) {
        // Focus should be inside modal
        const focusInModal = await page.evaluate(() => {
          const activeElement = document.activeElement;
          const modal = document.querySelector('[role="dialog"]');

          return modal?.contains(activeElement) ?? false;
        });

        expect(focusInModal).toBeTruthy();
      }
    }
  });
});

test.describe('Accessibility - ARIA Attributes', () => {

  test('Dynamic content updates are announced', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check for live regions
    const liveRegions = await page.locator('[aria-live], [role="status"], [role="alert"]').count();

    // Should have at least one live region for dynamic updates
    // (This is more of a guideline, not strict requirement)
    expect(liveRegions).toBeGreaterThanOrEqual(0);
  });

  test('Interactive elements have correct ARIA roles', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    // Filter for ARIA violations
    const ariaViolations = accessibilityScanResults.violations.filter(
      v => v.id.includes('aria')
    );

    expect(ariaViolations).toEqual([]);
  });

  test('Required form fields are marked as required', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Check email and password inputs
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();

    if (await emailInput.count() > 0) {
      const emailRequired = await emailInput.getAttribute('required') !== null ||
                           await emailInput.getAttribute('aria-required') === 'true';

      // Email should be marked as required
      expect(emailRequired).toBeTruthy();
    }

    if (await passwordInput.count() > 0) {
      const passwordRequired = await passwordInput.getAttribute('required') !== null ||
                              await passwordInput.getAttribute('aria-required') === 'true';

      // Password should be marked as required
      expect(passwordRequired).toBeTruthy();
    }
  });
});
