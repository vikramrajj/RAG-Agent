# Testing Guide: Diagnostics & Agent Orchestrator Integration

## ✅ What Was Fixed

### **Problem:**
The "Run Diagnostics" button was not invoking the agent orchestrator properly.

### **Solution:**
We implemented a **dual-endpoint architecture** where clicking "Run Diagnostics" now:
1. Calls `/api/diagnostics/outlook` to launch diagnostic tools
2. Calls `/fallback/outlook` to invoke the agent orchestrator for analysis

---

## 🧪 How to Test

### **Step 1: Start the Correct Server**

You need to run `agent_bridge.py` (Flask server) because that's where the diagnostics endpoints are implemented:

```powershell
# Method 1: Using virtual environment Python (recommended)
& "C:/Users/vikra/Downloads/RAG Agent/.venv/Scripts/python.exe" agent_bridge.py

# Method 2: Using system Python
python agent_bridge.py
```

**Wait for this message:**
```
Starting RAG Agent server on http://localhost:8000
 * Running on http://localhost:8000
```

### **Step 2: Open the SAT UI**

Open your browser to: http://localhost:8000/sat

### **Step 3: Test Run Diagnostics**

**Option A: Click Button**
1. Open the side panel (if closed)
2. Scroll to "🔧 Troubleshooting" module  
3. Click "🩺 Run Diagnostics"

**Option B: Keyboard Shortcut**
- Press `Alt + D`

### **Step 4: What You Should See**

**Toast Notifications (in order):**
1. 🩺 "Running Outlook diagnostics via Agent Orchestrator..."
2. ✅ "Diagnostics tools launched"
3. 🤖 "Invoking Agent Orchestrator..."
4. ✅ "Agent Orchestrator completed analysis"

**Chat Messages (2 messages):**

**Message 1: Diagnostics Initiated**
```
🔧 Diagnostics Initiated:

✅ Outlook desktop launched successfully
✅ Microsoft Support and Recovery Assistant (SaRA) launched
ℹ️ SaRA will help diagnose Outlook issues
```

**Message 2: Agent Orchestrator Analysis**
```
🤖 Agent Orchestrator Analysis:

✅ Outlook desktop application launched successfully
✅ Microsoft Support and Recovery Assistant (SaRA) launched
📋 SaRA will perform comprehensive Outlook diagnostics

🔍 **Diagnostic Recommendations:**
1. Check Outlook is properly configured with your email account
2. Verify internet connectivity
3. Check Windows credentials are valid
4. Ensure Outlook is not in offline mode
5. Review Outlook send/receive logs
```

---

## 🔍 Verify Agent Orchestrator Invocation

### **Check Browser DevTools**

1. Press `F12` to open DevTools
2. Go to **Network** tab
3. Click "Run Diagnostics"
4. You should see TWO POST requests:

**Request 1:**
- URL: `http://localhost:8000/api/diagnostics/outlook`
- Method: POST
- Status: 200 OK
- Response contains: `{"success": true, "details": "..."}`

**Request 2:**
- URL: `http://localhost:8000/fallback/outlook`
- Method: POST
- Status: 200 OK
- Response contains: `{"status": "success", "result": {...}}`

### **Check Backend Logs**

In the terminal where `agent_bridge.py` is running, look for:

```
INFO: Running Outlook agent orchestrator with message: Run comprehensive Outlook diagnostics...
```

This confirms the `run_outlook_agent()` function was called by the agent orchestrator.

---

## 🎯 Test Other Troubleshooting Features

While testing, also verify these work:

### **Open Outlook OWA**
- Click "📧 Open Outlook OWA" OR press `Alt + O`
- Should open Outlook Web Access in new tab
- URL: https://outlook.office365.com/owa/

### **Open Teams Web**
- Click "💬 Open Teams Web" OR press `Alt + T`
- Should open Microsoft Teams in new tab
- URL: https://teams.microsoft.com

---

## 📊 Test Scenarios

### **Scenario 1: Normal Flow (Outlook & SaRA Installed)**

**Expected:**
- Both Outlook and SaRA launch successfully
- Toast notifications show success
- Chat shows "✅ launched successfully" for both tools
- Recommendations appear

### **Scenario 2: Outlook Not Installed**

**Expected:**
- Toast: "Running diagnostics..."
- Chat Message 1: "⚠️ Could not launch Outlook desktop - may already be running or not installed"
- Chat Message 2: Still shows recommendations
- No crash or error

### **Scenario 3: SaRA Not Installed**

**Expected:**
- Outlook launches
- Chat shows: "⚠️ SaRA not available - Install from: https://aka.ms/SaRA-OutlookSetupAssist"
- Provides link to download SaRA
- Still shows recommendations

### **Scenario 4: Both Not Available**

**Expected:**
- Warnings for both tools
- Fallback recommendations still displayed
- No JavaScript errors in console

---

## 🐛 Troubleshooting

### **Problem: "Connection Refused"**

**Solution:**
- Server isn't running
- Start `agent_bridge.py` as shown in Step 1

### **Problem: "404 Not Found" or "Detail: Not Found"**

**Solution:**
- You're running `api_server.py` instead of `agent_bridge.py`
- Stop the current server: `Get-Process python | Stop-Process`
- Start `agent_bridge.py` instead

### **Problem: Only ONE chat message appears**

**Solution:**
- Check browser console (F12) for JavaScript errors
- Check Network tab - one of the two API calls might be failing
- Verify both endpoints exist in `agent_bridge.py`:
  - `/api/diagnostics/outlook` (line ~640)
  - `/fallback/outlook` (line ~865)

### **Problem: No toast notifications**

**Solution:**
- Check browser console for JavaScript errors
- Verify `showToast()` function exists in `sat_ui_improved.html`
- Hard refresh: `Ctrl + F5`

### **Problem: Server won't start**

**Solution:**
- Port 8000 might be in use
- Check: `Get-NetTCPConnection -LocalPort 8000`
- Kill process: `Get-Process python | Stop-Process -Force`
- Try again

---

## ✅ Success Criteria Checklist

Use this checklist to verify everything works:

- [ ] Server starts without errors on port 8000
- [ ] Can access http://localhost:8000/sat
- [ ] Side panel shows three troubleshooting buttons
- [ ] Clicking "Run Diagnostics" shows 4 toast notifications
- [ ] Two chat messages appear (Diagnostics + Orchestrator)
- [ ] DevTools Network tab shows 2 successful POST requests
- [ ] Backend logs show "Running Outlook agent orchestrator"
- [ ] Recommendations are displayed in chat
- [ ] No JavaScript errors in browser console
- [ ] No Python errors in terminal
- [ ] `Alt + D` keyboard shortcut works
- [ ] `Alt + O` opens Outlook OWA
- [ ] `Alt + T` opens Teams Web

---

## 📝 What to Report

### **If It Works:**
✅ Take a screenshot showing:
- Toast notifications
- Both chat messages
- DevTools Network tab with both successful requests

### **If It Doesn't Work:**
❌ Provide:
- Screenshot of error
- Browser console output (F12 → Console tab)
- Terminal output where server is running
- Which step failed

---

## 🔗 Related Documentation

- **DIAGNOSTICS_ORCHESTRATOR_INTEGRATION.md** - Technical implementation details
- **LEGACY_FEATURES_INTEGRATED.md** - All integrated features
- **API_DOCUMENTATION.md** - Full API reference

---

## 📞 Quick Test Command

If you want to test the endpoints directly without the UI:

```powershell
# Test diagnostics endpoint
curl -X POST http://localhost:8000/api/diagnostics/outlook `
  -H "Content-Type: application/json" `
  -d '{"action": "run_diagnostics"}'

# Test orchestrator endpoint  
curl -X POST http://localhost:8000/fallback/outlook `
  -H "Content-Type: application/json" `
  -d '{"message": "Run diagnostics"}'
```

Both should return JSON responses without errors.

---

## Summary

**The fix is complete and ready for testing!** 

The diagnostics functionality now properly invokes the agent orchestrator through a two-step process:
1. Launch diagnostic tools (Outlook + SaRA)
2. Run orchestrator analysis and provide recommendations

Follow this guide to test the implementation and verify everything works as expected.

**Status:** ✅ **Implementation Complete** - Ready for User Testing
