# outlook_login.py
import os
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from credential_manager import get_outlook_credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutlookLoginError(Exception):
    """Custom exception for Outlook login failures"""
    pass

class OutlookLogin:
    """Class to handle Outlook automation"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def handle_request(self, message: str, action: str = None) -> dict:
        """Handle incoming requests for Outlook operations"""
        try:
            if action == "login":
                success = self.login()
                return {
                    "response": "Login successful" if success else "Login failed",
                    "available_actions": ["check_emails", "send_email", "logout"]
                }
            elif action == "check_emails":
                return {
                    "response": "Email check not implemented yet",
                    "available_actions": ["login", "send_email", "logout"]
                }
            elif action == "send_email":
                return {
                    "response": "Email sending not implemented yet",
                    "available_actions": ["login", "check_emails", "logout"]
                }
            elif action == "logout":
                return {
                    "response": "Logout not implemented yet",
                    "available_actions": ["login"]
                }
            else:
                return {
                    "response": "Unknown action",
                    "available_actions": ["login", "check_emails", "send_email", "logout"]
                }
        except Exception as e:
            return {"response": f"Error: {str(e)}", "available_actions": ["login"]}

    def login(self, email=None, password=None) -> bool:
        """Login to Outlook Web Access"""
        if email is None or password is None:
            email, password = get_outlook_credentials()
        
        if not email or not password:
            raise OutlookLoginError("Missing credentials")
        
        try:
            with sync_playwright() as p:
                self.browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                self.context = self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                self.page = self.context.new_page()
                
                # Navigate to login page
                try:
                    self.page.goto("https://login.microsoftonline.com/", wait_until="networkidle", timeout=30000)
                except PlaywrightTimeoutError:
                    raise OutlookLoginError("Failed to load login page")
                
                # Enter email
                email_input = self.page.get_by_placeholder("Email, phone, or Skype")
                email_input.fill(email)
                self.page.get_by_role("button", name="Next").click()
                
                # Wait for password field
                try:
                    self.page.wait_for_selector("input[type='password']", timeout=15000)
                except PlaywrightTimeoutError:
                    if "outlook.office.com" in self.page.url:
                        return True
                    raise OutlookLoginError("Password field not found")
                
                # Enter password
                password_input = self.page.locator("input[type='password']")
                password_input.fill(password)
                
                # Try different sign-in buttons
                for selector in ["button:has-text('Sign in')", "input[type='submit']", "input[value='Sign in']"]:
                    try:
                        self.page.locator(selector).click(timeout=2000)
                        break
                    except:
                        continue
                else:
                    raise OutlookLoginError("Could not find sign-in button")
                
                # Check for errors
                self.page.wait_for_timeout(3000)
                error_selectors = [
                    "text=incorrect", "text=Sign-in error", "[data-testid='error']"
                ]
                for selector in error_selectors:
                    if self.page.locator(selector).is_visible():
                        raise OutlookLoginError("Login failed: Incorrect credentials")
                
                # Handle MFA if needed
                self.page.wait_for_timeout(5000)
                mfa_selectors = [
                    "text=Verify your identity",
                    "text=More information required",
                    "text=Help us protect your account"
                ]
                for selector in mfa_selectors:
                    if self.page.locator(selector).is_visible():
                        input("Complete MFA verification and press Enter...")
                        break
                
                # Navigate to Outlook
                try:
                    self.page.goto("https://outlook.office.com/mail/", wait_until="networkidle", timeout=30000)
                    self.page.wait_for_selector("text=Inbox", timeout=15000)
                    return True
                except:
                    raise OutlookLoginError("Failed to load Outlook inbox")
                
        except Exception as e:
            raise OutlookLoginError(f"Login failed: {str(e)}")
        finally:
            if self.browser:
                self.browser.close()

def test_login():
    """Test function to verify login functionality"""
    outlook = OutlookLogin()
    try:
        result = outlook.login()
        if result:
            print("Login test successful")
        return result
    except OutlookLoginError as e:
        print(f"Login test failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in test: {e}")
        return False

if __name__ == "__main__":
    try:
        outlook = OutlookLogin()
        outlook.login()
    except OutlookLoginError as e:
        logger.error(f"Login failed: {e}")
        exit(1)