# 💻 Windows Use Mode Guide

## ✅ FEATURE ADDED: Windows Use Mode

**Date:** October 9, 2025  
**Status:** 🟢 **ACTIVE**

---

## 🎯 What's New?

Added a dedicated **"Windows Use"** mode option in the SAT UI, similar to the existing "Browser Use" mode. This allows users to explicitly force Windows desktop automation for any command.

---

## 🔧 Mode Options Available

### Mode Dropdown (Top-Right Corner):

| Mode | Icon | Description | Use When |
|------|------|-------------|----------|
| **Smart Routing** | 🧠 | Auto-detects best route | Default - let AI decide |
| **Browser Use** | 🌐 | Forces browser automation | Web searches, shopping, browsing |
| **Windows Use** | 💻 | Forces Windows automation | Desktop apps, settings, file operations |
| **RAG Only** | 📚 | Uses only knowledge base | Technical docs, Outlook help |

---

## 🚀 How to Use Windows Use Mode

### Method 1: Select Mode First

1. **Open SAT UI** at http://localhost:8000/sat
2. **Click Mode dropdown** (top-right, next to Model selector)
3. **Select "Windows Use"** from dropdown
4. **Type any command** - it will always use Windows automation

### Method 2: Use Quick Action Cards

- Click any of the 4 Windows automation cards:
  - 🧮 **Calculator**
  - 📝 **Notepad**
  - 📁 **File Explorer**
  - ⚙️ **Settings**

### Method 3: Smart Routing (Auto-detect)

- Keep mode on **"Smart Routing"**
- Type keywords like:
  - "Open Calculator"
  - "Launch Notepad"
  - "Open File Explorer"
  - "Open Settings"

---

## 💡 Example Commands for Windows Use Mode

### When "Windows Use" Mode is Selected:

**Basic Commands:**
```
Open Notepad
Launch Calculator
Open File Explorer
Open Settings
Open Control Panel
Open Task Manager
```

**Advanced Commands:**
```
Open Notepad and type Hello World
Open File Explorer and go to Downloads
Open Settings and go to System
Open Calculator and minimize it
Launch Paint
Open Device Manager
```

**System Commands:**
```
Change to dark mode in settings
Open display settings
Open network settings
Open sound settings
Show desktop
Minimize all windows
```

---

## 📊 Mode Comparison

### Smart Routing (Default)
```
You: "Open Notepad"
SAT: [Detects Windows keyword] → Uses Windows automation ✅
```

### Windows Use Mode (Forced)
```
You: "notepad"
SAT: [Forced Windows mode] → Uses Windows automation ✅
```

```
You: "search for laptops"
SAT: [Forced Windows mode] → Tries Windows automation ⚠️
     (Better to use Browser Use mode for web searches)
```

### Browser Use Mode (Forced)
```
You: "Open Notepad"
SAT: [Forced Browser mode] → Searches Google for "Open Notepad" ❌
     (Wrong - should use Windows Use mode)
```

---

## 🎨 UI Changes

### Before (Old):
```
Mode: [Smart Routing ▼]
      - Smart Routing
      - Browser Use
      - RAG Only
```

### After (New):
```
Mode: [Smart Routing ▼]
      - Smart Routing
      - Browser Use
      - Windows Use  ← NEW!
      - RAG Only
```

### Notification Messages:
- **Smart Routing:** "Mode: Smart Routing (Auto-detect)"
- **Browser Use:** "Mode: Browser Automation Mode"
- **Windows Use:** "Mode: Windows Automation Mode" ← NEW!
- **RAG Only:** "Mode: RAG-only Mode"

---

## 🔍 Behind the Scenes

### Frontend (sat_ui_improved.html):

**1. Mode Dropdown:**
```html
<select class="mode-select" id="modeSelect">
    <option value="smart">Smart Routing</option>
    <option value="browser_use">Browser Use</option>
    <option value="windows_use">Windows Use</option>  ← NEW!
    <option value="rag_only">RAG Only</option>
</select>
```

**2. API Request:**
```javascript
body: JSON.stringify({
    message: message,
    model: state.selectedModel,
    smart_routing: routingEnabled,
    force_browser: forceBrowser,
    force_windows: forceWindows,  ← NEW!
    rag_only: state.selectedMode === 'rag_only'
})
```

### Backend (agent_bridge.py):

**1. Parse Parameter:**
```python
force_browser = data.get('force_browser', False)
force_windows = data.get('force_windows', False)  ← NEW!
```

**2. Force Windows Mode Logic:**
```python
if force_windows and WINDOWS_AUTOMATION_AVAILABLE:
    logger.info("Force Windows mode enabled")
    windows_wrapper = get_windows_wrapper()
    result = windows_wrapper.execute_task(message)
    return jsonify({
        'route': 'windows_use',
        'confidence': 1.0,  # Max confidence for forced mode
        'forced_mode': True
    })
```

---

## ✅ Testing Checklist

### Test 1: Mode Selection
- [ ] Select "Windows Use" from dropdown
- [ ] Notification shows "Mode: Windows Automation Mode"
- [ ] Mode persists across messages

### Test 2: Basic Windows Commands
- [ ] Type "Open Notepad" → Notepad opens ✅
- [ ] Type "Launch Calculator" → Calculator opens ✅
- [ ] Type "Open File Explorer" → File Explorer opens ✅
- [ ] Type "Open Settings" → Settings opens ✅

### Test 3: Advanced Commands
- [ ] "Open Notepad and type Hello" → Types text ✅
- [ ] "Open File Explorer and go to Downloads" → Navigates ✅

### Test 4: Mode Switching
- [ ] Switch to "Smart Routing" → Auto-detection works
- [ ] Switch to "Browser Use" → Uses browser automation
- [ ] Switch to "Windows Use" → Forces Windows automation
- [ ] Switch to "RAG Only" → Uses knowledge base only

### Test 5: Quick Action Cards
- [ ] Click Calculator card (any mode) → Opens Calculator
- [ ] Click Notepad card (any mode) → Opens Notepad
- [ ] Click File Explorer card (any mode) → Opens File Explorer
- [ ] Click Settings card (any mode) → Opens Settings

---

## 🎯 When to Use Each Mode

### Use "Smart Routing" When:
✅ You want AI to decide the best route  
✅ You're not sure which system to use  
✅ General technical support questions  
✅ Mixed commands (some Windows, some web)

### Use "Browser Use" When:
✅ Web searches ("search Google for...")  
✅ Online shopping ("find laptops on Amazon")  
✅ Web navigation ("go to website...")  
✅ Research tasks ("research topic...")

### Use "Windows Use" When:
✅ Opening desktop applications  
✅ Changing system settings  
✅ File operations  
✅ Window management (minimize, maximize)  
✅ Control Panel tasks  
✅ Any Windows OS automation

### Use "RAG Only" When:
✅ Technical documentation queries  
✅ Outlook/Teams/network troubleshooting  
✅ Knowledge base searches  
✅ Historical context questions

---

## ⚠️ Important Notes

### Limitations:

1. **API Quota Shared:**
   - Windows Use and Browser Use share the same Gemini API quota
   - Free tier: 50 requests/day
   - If quota exceeded: "⚠️ Daily API quota reached"

2. **Mode Override:**
   - Quick action cards always use Windows automation
   - Regardless of selected mode
   - This is intentional for consistency

3. **Smart Routing Priority:**
   - When "Smart Routing" is enabled:
     - Force Windows check happens FIRST
     - Then Windows keyword detection
     - Then Browser Use routing
     - Then RAG routing
     - Finally Mistral fallback

4. **Windows Version:**
   - Requires Windows 7, 8, 10, or 11
   - Some features may vary by version

---

## 🐛 Troubleshooting

### Issue 1: "Windows Use" Not in Dropdown
**Solution:** Refresh browser (Ctrl+F5) to clear cache

### Issue 2: Mode Doesn't Change
**Solution:** Check browser console for errors, restart server

### Issue 3: Windows Commands Still Use Browser
**Solution:**
1. Verify mode is set to "Windows Use"
2. Check notification message confirms mode
3. Check server logs: `Get-Content logs\app.log -Tail 20`

### Issue 4: Error "Windows automation not available"
**Solution:**
```powershell
# Check if windows-use is installed
.\.venv\Scripts\python.exe -c "import windows_use; print('OK')"

# Reinstall if needed
.\.venv\Scripts\pip.exe install windows-use
```

---

## 📝 Files Modified

### Frontend:
- ✅ `sat_ui_improved.html`
  - Added "Windows Use" option to mode dropdown
  - Updated `updateModeSelection()` function
  - Added `force_windows` parameter in API request

### Backend:
- ✅ `agent_bridge.py`
  - Added `force_windows` parameter parsing
  - Added force Windows mode logic (before smart routing)
  - Returns JSON with `forced_mode: True` metadata

---

## 🎉 Success!

**You now have full control over Windows automation!**

**3 ways to trigger Windows automation:**
1. ✅ **Smart Routing** - Auto-detects keywords
2. ✅ **Quick Action Cards** - Click pre-defined tasks
3. ✅ **Windows Use Mode** - Force all commands to Windows ← NEW!

---

## 🚀 Next Steps

### Try These Commands in Windows Use Mode:

**Beginner:**
- "Open Notepad"
- "Launch Calculator"
- "Open Settings"

**Intermediate:**
- "Open Notepad and type my first automation"
- "Open File Explorer and go to Documents"
- "Launch Paint"

**Advanced:**
- "Open Settings and go to display settings"
- "Open Device Manager"
- "Change to dark mode in settings"

---

## 📊 Server Status

**Current Status:** 🟢 **RUNNING**  
**PID:** 21392  
**Port:** 8000  
**URL:** http://localhost:8000/sat

**Features Active:**
- ✅ Smart Routing
- ✅ Browser Use (forced mode)
- ✅ Windows Use (forced mode) ← NEW!
- ✅ RAG Only (forced mode)
- ✅ Quick Action Cards
- ✅ Text-to-Speech

---

**Enjoy your new Windows Use mode!** 💪💻

**Need help? Just ask!**
