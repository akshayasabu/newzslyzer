const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        permissions: ['microphone']
    });
    const page = await context.newPage();

    // Create screenshots directory
    const screenshotDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir);
    }

    console.log("Starting browser for search test...");
    await page.goto('http://127.0.0.1:5000');

    // Accept cookie prompt if it exists to clean up UI
    try {
        const acceptBtn = await page.$('text="Accept"');
        if (acceptBtn) await acceptBtn.click();
    } catch (e) { }

    // Login to access the dashboard where search is
    console.log("Logging into dashboard...");
    await page.click('text="SIGN IN"');
    await page.waitForSelector('#loginForm');
    await page.fill('#login-username', 'user_demo');
    await page.fill('#login-password', 'AuraNews2026!'); // Updated to strong password from app initalization
    await page.click('#loginForm button[type="submit"]');

    await page.waitForTimeout(5000); // Give the dashboard more time to load and render
    console.log("Logged in. Taking screenshot of search UI...");
    await page.screenshot({ path: path.join(screenshotDir, 'search_ui.png') });

    // Test 1: Text Search
    console.log("Testing text search...");
    await page.waitForSelector('#homeSearchInput', { timeout: 30000 });
    await page.fill('#homeSearchInput', 'technology');
    await page.click('.search-submit-btn');
    await page.waitForSelector('.news-grid', { timeout: 30000 }); // Wait for results
    await page.screenshot({ path: path.join(screenshotDir, 'search_results_text.png') });

    // Go back home
    await page.goto('http://127.0.0.1:5000/');
    await page.waitForLoadState('networkidle');


    // Test 2: Image Search
    console.log("Testing image upload search...");
    const sampleImagePath = path.join(__dirname, 'static', 'img', 'news_placeholder.jpg');

    // Ensure the fake file exists for testing
    if (fs.existsSync(sampleImagePath)) {
        // Set the hidden input file and trigger the form submission via Playwright
        const fileInput = await page.$('#imageSearchInput');
        await fileInput.setInputFiles(sampleImagePath);
        await page.waitForSelector('.news-grid'); // Wait for simulated results redirect
        await page.screenshot({ path: path.join(screenshotDir, 'search_results_image.png') });
    } else {
        console.log("Skipping image search test, no placeholder image found to upload.");
    }

    console.log("Search screenshots captured.");

    await browser.close();
})();
