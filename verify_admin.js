const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Navigating to login page...');
    await page.goto('http://127.0.0.1:5000/');
    
    // Open login modal
    await page.click('button[data-modal="login"]');
    
    console.log('Attempting login as admin...');
    await page.fill('#login-username', 'admin');
    await page.fill('#login-password', 'Admin@123'); // Guessing based on reporter password
    await page.click('#loginForm button[type="submit"]');
    
    // Wait for navigation
    await page.waitForURL('http://127.0.0.1:5000/admin');
    console.log('Successfully logged into Admin Dashboard');
    
    // Check if table rows exist in DOM
    const rowCount = await page.locator('table.admin-table tbody tr').count();
    console.log(`Table Row Count in DOM: ${rowCount}`);
    if (rowCount > 0) {
        const firstRow = page.locator('table.admin-table tbody tr').first();
        const styles = await firstRow.evaluate(el => {
            const cs = window.getComputedStyle(el);
            return {
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                color: cs.color,
                height: cs.height,
                backgroundColor: cs.backgroundColor
            }
        });
        console.log('First Row Computed Styles:', styles);
    } else {
        const bodyContent = await page.locator('table.admin-table').innerHTML();
        console.log('Table InnerHTML:', bodyContent);
    }

    // Take screenshot of the new UI
    await page.screenshot({ path: 'C:/Users/achua/.gemini/antigravity/brain/79cea534-ceef-4730-b256-b0a874be8e28/admin_dashboard_overhaul.png', fullPage: true });
    console.log('Screenshot of overhauled dashboard saved.');

    // Click on "View & Chat" button
    // It's a modern button in the Advertisements table
    const viewChatBtn = page.locator('a.btn-modern.btn-view:has-text("View & Chat")').first();
    if (await viewChatBtn.isVisible()) {
        const href = await viewChatBtn.getAttribute('href');
        console.log(`Clicking "View & Chat" button (href: ${href})...`);
        await viewChatBtn.click();
        
        // Wait for either the URL match or a fixed time
        console.log('Waiting for navigation...');
        await page.waitForTimeout(5000); 
        console.log('Current URL:', page.url());
        
        // Take screenshot of ad details and chat widget
        await page.screenshot({ path: 'C:/Users/achua/.gemini/antigravity/brain/79cea534-ceef-4730-b256-b0a874be8e28/ad_details_chat.png', fullPage: true });
        console.log('Screenshot of ad details and chat widget saved.');
    } else {
        console.log('View & Chat button not found or no advertisements available.');
    }

  } catch (error) {
    console.error('Verification failed:', error);
    // Take error screenshot
    await page.screenshot({ path: 'C:/Users/achua/.gemini/antigravity/brain/79cea534-ceef-4730-b256-b0a874be8e28/verification_error.png' });
  } finally {
    await browser.close();
  }
})();
