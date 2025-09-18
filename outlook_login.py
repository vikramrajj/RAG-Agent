# outlook_login.py
import os
from playwright.sync_api import sync_playwright

def automate_outlook_login(email, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Step 1: Go to Microsoft login
        page.goto("https://login.microsoftonline.com/")

        # Step 2: Fill in email
        page.get_by_placeholder("Email, phone, or Skype").fill(email)
        page.get_by_role("button", name="Next").click()

        # Step 3: Wait for Aston login redirect
        page.wait_for_selector("input[type='password']", timeout=10000)

        # Step 4: Fill in password
        page.fill("input[type='password']", password)

        # Step 5: Click "Sign in"
        try:
            page.get_by_role("button", name="Sign in").click()
        except:
            page.locator("input[type='submit']").click()

        # Step 6: Check for login error
        if page.locator("text=The password is incorrect").is_visible():
            print("❌ Login failed: Incorrect password.")
            page.screenshot(path="login_error.png")
            return

        # Step 7: Wait for login to complete
        page.wait_for_timeout(5000)

        # Step 8: Force navigation to Outlook inbox
        page.goto("https://outlook.office.com/mail/")
        page.wait_for_selector("text=Inbox", timeout=10000)
        page.screenshot(path="inbox_forced.png")
        print("✅ Outlook inbox loaded at:", page.url)

        # ✅ Keep browser open by pausing the script
        input("🟢 Browser will remain open. Press Enter to close...")

        # Optional: close browser only after manual confirmation
        browser.close()

if __name__ == "__main__":
    email = os.getenv("OUTLOOK_EMAIL", "240375096@aston.ac.uk")
    password = os.getenv("OUTLOOK_PASSWORD", "Den8lash618")
    automate_outlook_login(email, password)
