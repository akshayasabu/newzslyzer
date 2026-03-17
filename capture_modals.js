const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
    let browser;
    try {
        console.log('Starting browser...');
        // Launch in headless mode for capturing screenshots
        browser = await chromium.launch({ headless: true });
        const context = await browser.newContext({
            viewport: { width: 1280, height: 800 }
        });
        const page = await context.newPage();

        console.log('Navigating to local server...');
        await page.goto('http://127.0.0.1:5000', { waitUntil: 'load', timeout: 30000 });
        console.log('Page loaded.');

        // Ensure screenshots directory exists
        const outDir = path.join(__dirname, 'screenshots');
        if (!fs.existsSync(outDir)) {
            fs.mkdirSync(outDir, { recursive: true });
        }

        console.log('Clicking the SIGN IN button...');
        // Click the 'SIGN IN' button
        await page.click('button[data-modal="login"]');

        // Wait for the modal login form to be visible
        await page.waitForSelector('#loginForm:visible', { timeout: 10000 });
        console.log('Login form is visible. Taking screenshot...');
        await page.screenshot({ path: path.join(outDir, 'login_modal.png') });

        console.log('Clicking "Create an Account"...');
        // Click "Create an Account" link
        await page.click('a[data-switch="register"]');

        // Wait for register form to become visible
        await page.waitForSelector('#registerForm:visible', { timeout: 10000 });
        console.log('Register form is visible. Taking screenshot...');
        await page.screenshot({ path: path.join(outDir, 'register_modal.png') });

        console.log('Success! Screenshots saved to "screenshots" directory.');
    } catch (error) {
        console.error('An error occurred:', error);
    } finally {
        if (browser) {
            console.log('Closing browser...');
            await browser.close();
        }
    }
})();
