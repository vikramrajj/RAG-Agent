# tool_invoker.py
import subprocess
import os

def open_outlook():
    print("🚀 Launching Outlook desktop...")
    try:
        subprocess.run(["start", "outlook.exe"], shell=True)
    except Exception as e:
        print("❌ Failed to launch Outlook:", e)

def run_sara():
    print("🧪 Launching Microsoft Support and Recovery Assistant...")
    try:
        # Use default install path or environment override
        sara_path = os.getenv("SARA_PATH", r"C:\Program Files\Microsoft Support and Recovery Assistant\SaRA.exe")
        subprocess.run([sara_path], shell=True)
    except Exception as e:
        print("❌ Failed to launch SaRA:", e)

def invoke_tool(tool_name):
    tool_map = {
        "open_outlook": open_outlook,
        "run_sara": run_sara
    }

    if tool_name in tool_map:
        tool_map[tool_name]()
    else:
        print(f"❌ Tool '{tool_name}' not found.")
