const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    // Create screenshots directory
    const screenshotDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir);
    }

    console.log("Starting browser for validation test...");
    await page.goto('http://127.0.0.1:5000');
    console.log("Page loaded.");

    // Open login modal
    await page.waitForLoadState('networkidle');
    await page.click('text="SIGN IN"');
    await page.waitForSelector('#loginForm');

    // Switch to Register modal
    console.log("Switching to Create Account...");
    await page.click('a[data-switch="register"]');
    await page.waitForSelector('#registerForm', { state: 'visible' });

    // Test 1: Username already taken ('admin')
    console.log("Testing duplicate username...");
    await page.fill('#reg-username', 'admin');
    await page.evaluate(() => document.getElementById('reg-username').blur());
    await page.waitForTimeout(1000); // Wait for API response
    await page.screenshot({ path: path.join(screenshotDir, 'validation_username.png') });

    // Test 2: Email already taken ('admin@auranews.com')
    console.log("Testing duplicate email...");
    await page.fill('#reg-email', 'admin@auranews.com');
    await page.evaluate(() => document.getElementById('reg-email').blur());
    await page.waitForTimeout(1000); // Wait for API response
    await page.screenshot({ path: path.join(screenshotDir, 'validation_email.png') });

    console.log("Validation screenshots captured.");

    await browser.close();
})();
