const { test, expect } = require('@playwright/test');

test.describe('News & Content Tests', () => {
    test.beforeEach(async ({ page }) => {
        // News features require login
        await page.goto('/');
        await page.click('button[data-modal="login"]');
        await page.fill('#login-username', 'user_demo');
        await page.fill('#login-password', 'AuraNews2026!');
        await page.click('#loginForm button[type="submit"]');
        await expect(page).toHaveURL(/\/$/);
    });

    test('Home Page News Grid', async ({ page }) => {
        // Check for news grid
        const newsCards = page.locator('.news-grid .news-card');
        await expect(newsCards.first()).toBeVisible();

        // Verify at least some news cards exist
        const count = await newsCards.count();
        expect(count).toBeGreaterThan(0);
    });

    test('Category Filtering', async ({ page }) => {
        // Open Local News dropdown
        await page.click('.dropdown-trigger:has-text("Local News")');

        // Click Sports category
        await page.click('a:has-text("Sports")');

        // Verify URL (toHaveURL has built-in retry/wait)
        await expect(page).toHaveURL(/\/category\/sports/i);
        // Use getByRole to be more specific
        await expect(page.locator('.page-title')).toContainText('sports', { ignoreCase: true });

        // Verify news items in category
        const newsCards = page.locator('.news-grid .news-card');
        const count = await newsCards.count();
        // Assuming some sports news exists in the mock data
        if (count > 0) {
            await expect(newsCards.first()).toBeVisible();
        }
    });

    test('Live News Section', async ({ page }) => {
        await page.click('a:has-text("Live News")');

        await expect(page).toHaveURL(/\/live-news/);
        await expect(page.locator('.page-title')).toContainText('Live News', { ignoreCase: true });

        // Wait for news to fetch if spinner is visible
        const spinner = page.locator('.spinner');
        if (await spinner.isVisible()) {
            await expect(spinner).not.toBeVisible({ timeout: 15000 });
        }

        const liveCards = page.locator('.news-grid .news-card');
        await expect(liveCards.first()).toBeVisible();
    });
});
