# Quick API Key Setup

## Once you have your Gemini API key:

### Option 1: Manual Edit
1. Open `.env` file
2. Scroll to bottom
3. Add this line:
```
GOOGLE_API_KEY=AIza...your_key_here...
```
4. Save

### Option 2: PowerShell Command
Run this (replace YOUR_KEY with your actual key):
```powershell
Add-Content -Path ".env" -Value "`nGOOGLE_API_KEY=YOUR_KEY_HERE"
```

### Option 3: Quick Copy-Paste
```bash
# Add this line to .env file:
GOOGLE_API_KEY=
```

---

## Then Restart Server

```powershell
# Stop server
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Wait 2 seconds
Start-Sleep -Seconds 2

# Start server
python agent_bridge.py
```

---

## Test

In UI, type:
```
Find laptops on Amazon
```

Browser should open automatically! 🚀
