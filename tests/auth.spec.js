const { test, expect } = require('@playwright/test');

test.describe('Authentication Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('Reporter Login', async ({ page }) => {
        // Click Sign In button and wait for modal
        await page.click('button[data-modal="login"]');
        await expect(page.locator('#authModal')).toBeVisible();

        // Fill in credentials
        await page.fill('#login-username', 'reporter');
        await page.fill('#login-password', 'Reporter@123');

        // Submit form and wait for navigation
        await Promise.all([
            page.waitForNavigation(),
            page.click('#loginForm button[type="submit"]')
        ]);

        // Verify redirection to Reporter Dashboard
        await expect(page).toHaveURL(/\/reporter/);
        await expect(page.locator('h1')).toContainText('Reporter Workspace');
    });

    test('Admin Login', async ({ page }) => {
        await page.click('button[data-modal="login"]');
        await expect(page.locator('#authModal')).toBeVisible();

        await page.fill('#login-username', 'admin');
        await page.fill('#login-password', 'Admin@123');

        // Submit form and wait for navigation
        await page.click('#loginForm button[type="submit"]');

        // Verify redirection to Admin Dashboard
        await expect(page).toHaveURL(/\/admin/);
        await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();
    });

    test('Logout Flow', async ({ page }) => {
        // Login as admin first
        await page.click('button[data-modal="login"]');
        await page.fill('#login-username', 'admin');
        await page.fill('#login-password', 'Admin@123');
        await page.click('#loginForm button[type="submit"]');
        await expect(page).toHaveURL(/\/admin/);

        // Logout via profile page
        await page.goto('/profile');
        // The button might be hidden until hover or just needs a force click due to layout
        await page.click('text=Logout', { force: true });

        await expect(page).toHaveURL(/\/$/);
        await expect(page.locator('button[data-modal="login"]')).toBeVisible();
    });
});
