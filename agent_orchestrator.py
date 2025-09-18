# agent_orchestrator.py
import os
from tool_invoker import invoke_tool
from outlook_login import automate_outlook_login

def run_outlook_agent():
    print("🚀 Attempting to launch Outlook desktop...")

    try:
        invoke_tool("open_outlook")

        # Simulate failure detection (replace with real check later)
        # For now, we assume failure to trigger fallback
        raise Exception("Outlook desktop failed to launch")

    except Exception as e:
        print(f"⚠️ Desktop Outlook failed: {e}")
        print("🧭 Launching Outlook Web as fallback...")

        email = os.getenv("OUTLOOK_EMAIL", "240375096@aston.ac.uk")
        password = os.getenv("OUTLOOK_PASSWORD", "Den8lash618")
        automate_outlook_login(email, password)

        print("🛠️ Running SaRA diagnostics in parallel...")
        invoke_tool("run_sara")

if __name__ == "__main__":
    run_outlook_agent()
