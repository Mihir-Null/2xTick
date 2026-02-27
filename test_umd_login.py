import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def do_test():
    username = os.getenv('CANVAS_USERNAME')
    password = os.getenv('CANVAS_PASSWORD')
    
    if not username or not password:
        print("Error: Missing credentials in .env")
        return
        
    print(f"Loaded credentials. Username: {username}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://umd.instructure.com")
        
        print("Waiting for login form...")
        # Since umd.instructure.com redirects to CAS, we wait for the username input
        page.wait_for_selector('input[type="text"], input[name="username"], input[name="login_id"], #username', timeout=10000)
        
        print("Filling credentials...")
        page.fill('input[type="text"], input[name="username"], input[name="login_id"], #username', username)
        page.fill('input[type="password"], input[name="password"], #password', password)
        
        # Click the login button. The login button uses name="_eventId_proceed" on standard CAS.
        # We can also just press Enter.
        page.keyboard.press('Enter')
        
        # Give the page a moment to navigate
        page.wait_for_timeout(5000)
        
        print("Page URL after submitting credentials:", page.url)
        page.screenshot(path='umd_login_after_enter.png')
        with open('umd_login_after_enter.html', 'w') as f:
            f.write(page.content())
            
        browser.close()

if __name__ == "__main__":
    do_test()
