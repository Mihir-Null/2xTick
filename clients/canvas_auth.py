from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)

def login_and_save_state(url: str, username: str = None, password: str = None, state_file: str = 'canvas_state.json'):
    """
    Launches a browser for the user to log in,
    then saves the session cookies to a state file.
    If username and password are provided, it runs headlessly and automates the login form,
    pausing for the user to accept a Duo push or other 2FA via their device.
    """
    is_headless = bool(username and password)
    logger.info(f"Launching {'headless ' if is_headless else ''}browser for Canvas authentication...")
    
    with sync_playwright() as p:
        # Launch headed if no credentials, headless if we have them
        browser = p.chromium.launch(headless=is_headless)
        context = browser.new_context()
        page = context.new_page()
        
        logger.info(f"Navigating to {url}")
        page.goto(url)
        
        if is_headless:
            logger.info("Automating login with provided credentials...")
            try:
                # Wait for username and password fields (these selectors cover many common CAS setups, including UMD)
                page.wait_for_selector('input[type="text"], input[name="username"], input[name="login_id"], #username', timeout=10000)
                page.fill('input[type="text"], input[name="username"], input[name="login_id"], #username', username)
                page.fill('input[type="password"], input[name="password"], #password', password)
                
                # Press enter or click submit
                page.keyboard.press('Enter')
                
                # Duo Universal Prompt sometimes requires selecting the push method
                # or clicking through a "Trust this browser" prompt.
                logger.info("Credentials submitted. Waiting for navigation...")
                try:
                    # Wait for either the dashboard to load OR a Duo prompt to appear
                    page.wait_for_load_state('networkidle', timeout=10000)
                except Exception:
                    pass

                # If we are on Duo, we might need to click "Duo Push" or "Trust browser"
                if "duosecurity.com" in page.url or "CAS" in page.content():
                    logger.info("Duo/CAS prompt detected. Attempting to click 'Duo Push' if present...")
                    try:
                        # Sometimes Duo asks which method to use
                        push_btn = page.locator("text='Duo Push'").first
                        if push_btn.is_visible(timeout=3000):
                            push_btn.click()
                            logger.info("Clicked 'Duo Push' button.")
                    except Exception:
                        pass
                        
                    try:
                        # Sometimes Duo Universal asks if you want to trust the browser
                        trust_btn = page.locator("text='Yes, trust browser'").first
                        if trust_btn.is_visible(timeout=3000):
                            trust_btn.click()
                            logger.info("Clicked 'Trust browser' button.")
                    except Exception:
                        pass

                logger.info("Waiting for Duo push approval (please check your device)...")
            except Exception as e:
                logger.error(f"Failed to auto-fill credentials: {e}")
                logger.info("Please run without CANVAS_USERNAME and CANVAS_PASSWORD for fully interactive login.")
        else:
            logger.info("Please log in using the popup browser window.")
            
        logger.info("Waiting for the Canvas dashboard to load... (Waiting up to 2 minutes)")
        
        try:
            # Polling loop to handle Duo "Trust Browser" prompts that appear AFTER approval
            # and to wait for the Canvas dashboard to signify completion.
            dashboard_locator = page.locator('#global_nav_dashboard_link')
            
            for _ in range(120): # 120 seconds timeout
                if dashboard_locator.is_visible():
                    logger.info("Dashboard detected!")
                    break
                
                # If headless, attempt to click Duo buttons that might appear
                if is_headless:
                    try:
                        # Sometimes Duo Universal asks if you want to trust the browser
                        trust_btn = page.locator("text='Yes, trust browser'").first
                        if trust_btn.is_visible(timeout=500):
                            logger.info("Clicking 'Trust browser' button...")
                            trust_btn.click()
                            
                        # If Duo asks to Push, click it
                        push_btn = page.locator("text='Send Me a Push', text='Duo Push'").first
                        if push_btn.is_visible(timeout=500):
                            logger.info("Clicking 'Duo Push' button...")
                            push_btn.click()
                    except Exception:
                        pass
                
                page.wait_for_timeout(1000)
            
            # Final check to ensure dashboard is loaded
            page.wait_for_selector('#global_nav_dashboard_link', timeout=10000)
            
            # Additional small wait to ensure cookies are fully set
            page.wait_for_load_state('networkidle', timeout=5000)
            
            logger.info("Saving session state...")
            
            # Save the full browser context state (including all cookies)
            context.storage_state(path=state_file)
            logger.info(f"Session state saved successfully to {state_file}")
            
        except Exception as e:
            logger.error(f"Error during login or state save. You may have timed out or hit an unexpected page: {e}")
        finally:
            browser.close()
