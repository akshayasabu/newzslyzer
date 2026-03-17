from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    
    print('Navigating to landing page to login...')
    page.goto('http://127.0.0.1:5000/landing')
    
    page.fill('#login-username', 'user_demo')
    page.fill('#login-password', 'AuraNews2026!')
    page.click('#loginForm button[type="submit"]')
    page.wait_for_timeout(2000)
    
    print('Taking screenshot of Home Page...')
    page.screenshot(path='/tmp/home_after_fix.png', full_page=False)
    
    print('Clicking SECTIONS menu...')
    page.click('#sidebarToggle')
    page.wait_for_timeout(1000)
    
    print('Taking screenshot of Mega Menu...')
    page.screenshot(path='/tmp/mega_menu_after_fix.png', full_page=False)
    
    print('Success! Screenshots saved to /tmp')
    browser.close()
