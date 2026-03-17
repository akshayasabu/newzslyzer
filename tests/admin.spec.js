const { test, expect } = require('@playwright/test');

test.describe('Admin Workflow Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Admin tasks require login
        await page.goto('/');
        await page.click('button[data-modal="login"]');
        await page.fill('#login-username', 'admin');
        await page.fill('#login-password', 'Admin@123');
        await page.click('#loginForm button[type="submit"]');
        await expect(page).toHaveURL(/\/admin/);
    });

    test('User Management - View User Info', async ({ page }) => {
        // Click View on the first reporter
        const viewButton = page.locator('button:has-text("View")').first();
        await viewButton.click();

        // Verify Modal is visible
        const modal = page.locator('#viewReporterModal');
        await expect(modal).toBeVisible();
        await expect(modal.locator('h2')).not.toBeEmpty();

        // Close modal
        await page.click('button:has-text("Close")');
        await expect(modal).not.toBeVisible();
    });

    test('Admin Header Brand Logic', async ({ page }) => {
        // According to branding requirements, Admin dashboard should just show "JANAVAAKYA – Voice of the People"
        // Wait, let's check base.html logic:
        // {% if request.path == '/' and session.get('user') and session.get('role') == 'user' %}
        //   h1: User Dashboard, subtitle: JANAVAAKYA – Voice of the People
        // {% else %}
        //   h1: JANAVAAKYA – Voice of the People
        // {% endif %}

        const brand = page.locator('.header-brand-group h1');
        await expect(brand).toHaveText('JANAVAAKYA – Voice of the People');
    });
});
