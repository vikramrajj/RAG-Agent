# agent_orchestrator.py
import os
import logging
from tool_invoker import invoke_tool
from outlook_login import OutlookLogin
from config import ConfigManager

logger = logging.getLogger(__name__)

def try_open_desktop_outlook():
    print("[LAUNCH] Attempting to launch Outlook desktop...")
    try:
        result = invoke_tool("open_outlook")
        if result:
            print("[OK] Outlook desktop launched successfully")
            return True
        else:
            print("[WARNING] Desktop Outlook launch returned False")
            return False
    except Exception as e:
        print(f"[WARNING] Desktop Outlook failed: {e}")
        logger.error(f"Failed to launch Outlook desktop: {e}")
        return False

def fallback_to_web_outlook():
    print("[FALLBACK] Launching Outlook Web as fallback...")
    try:
        # Get credentials through ConfigManager
        config = ConfigManager.get_config()
        email, password = config.get_credentials()
        
        # Initialize and use OutlookLogin class
        outlook = OutlookLogin()
        outlook.login(email, password)
        
    except ValueError as e:
        logger.error(f"Failed to retrieve Outlook credentials: {e}")
        print(f"[ERROR] Credential error: {e}")
        print("Please check your .env file and ensure OUTLOOK_EMAIL and OUTLOOK_PASSWORD are set correctly.")
    except Exception as e:
        logger.error(f"Unexpected error in fallback_to_web_outlook: {e}")
        print(f"[ERROR] Unexpected error: {e}")

def run_sara_diagnostics():
    print("[DIAGNOSTICS] Running SaRA diagnostics in parallel...")
    invoke_tool("run_sara")

def run_outlook_agent():
    if not try_open_desktop_outlook():
        fallback_to_web_outlook()
        run_sara_diagnostics()

if __name__ == "__main__":
    run_outlook_agent()
