# Model Selector & Microsoft SaRA Integration

## Overview
Added two major features to the SAT UI:
1. **Model/Mode Selection Dropdown** - Choose between Mistral/Llama3 and routing modes
2. **Microsoft SaRA Tool Integration** - Direct access to launch SaRA and Outlook client

## ✅ Feature 1: Model & Mode Selection

### UI Changes (`sat_ui_improved.html`)

#### Status Bar Enhancement
Added two dropdown selectors in the status bar:

**Model Selector:**
- Mistral (RAG) - Default
- Llama 3 (RAG)

**Mode Selector:**
- Smart Routing - Auto-detect best route (default)
- Browser Use - Force browser automation
- RAG Only - Disable browser automation

#### CSS Additions
```css
.model-selector - Container for dropdowns
.model-select, .mode-select - Styled dropdown elements
.selector-label - Labels for dropdowns
```

#### JavaScript Functions
```javascript
state.selectedModel - Track current model
state.selectedMode - Track current mode

updateModelSelection() - Handle model changes
updateModeSelection() - Handle mode changes
showNotification() - Display toast notifications
```

#### API Integration
The `sendMessage()` function now sends:
```javascript
{
    message: message,
    model: state.selectedModel,  // 'mistral' or 'llama3'
    smart_routing: routingEnabled,  // true for 'smart' mode
    force_browser: forceBrowser,  // true for 'browser_use' mode
    rag_only: state.selectedMode === 'rag_only'
}
```

### Backend Changes (`api_server.py`)

The `/api/bridge` endpoint now respects:
- `model` - Selected AI model
- `smart_routing` - Enable/disable routing
- `force_browser` - Force browser automation
- `rag_only` - RAG-only mode

---

## ✅ Feature 2: Microsoft SaRA Tool Integration

### New UI Functions (`sat_ui_improved.html`)

#### 1. Launch Microsoft SaRA Tool
```javascript
async function launchSaRATool()
```
- Calls `/api/tools/sara` endpoint
- Launches Microsoft Support and Recovery Assistant
- Fallback: Opens SaRA download page if not installed

#### 2. Open Outlook Client
```javascript
async function openOutlookClient()
```
- Calls `/api/tools/outlook` endpoint  
- Opens Microsoft Outlook desktop application
- Shows error if Outlook not installed

#### 3. Existing Diagnostics Enhanced
```javascript
async function runDiagnostics()
```
- Already integrated with agent orchestrator
- Launches both SaRA and Outlook
- Runs comprehensive diagnostics

### Diagnostics Panel Buttons

Added three action buttons in the "Microsoft Apps" module:

1. **🩺 Run Diagnostics** - Full diagnostic suite
2. **🔧 Launch Microsoft SaRA** - SaRA tool only
3. **📧 Open Outlook Client** - Open Outlook app

### Backend API Endpoints (`api_server.py`)

#### `/api/tools/sara` (POST)
```python
Launch Microsoft Support and Recovery Assistant
Request: { "action": "launch_sara", "target": "outlook" }
Response: { "success": true, "message": "...", "execution_time": 0.5 }
```

#### `/api/tools/outlook` (POST)
```python
Open Microsoft Outlook desktop client
Request: { "action": "open_outlook" }
Response: { "success": true, "message": "...", "execution_time": 0.3 }
```

### Tool Invoker Integration (`tool_invoker.py`)

Already implemented methods:
- `_open_outlook()` - Launch Outlook.exe
- `_run_sara()` - Launch SaRA from configured path

Features:
- ✅ Process detection (checks if already running)
- ✅ Timeout handling (30 seconds default)
- ✅ Error handling with detailed messages
- ✅ Cross-platform support (Windows primary)

---

## 🎨 Visual Enhancements

### Notification System
- Sliding notifications from top-right
- Color-coded (blue for info, green for success, red for error)
- Auto-dismiss after 3 seconds
- Smooth animations (slideInRight, fadeOut)

### Status Bar Layout
```
[●] Online & Ready  |  Model: [Mistral ▼]  Mode: [Smart Routing ▼]  |  Response time: ~2s
```

---

## 🧪 Testing

### Test Model/Mode Selection:
1. Open SAT UI (`http://localhost:8000/sat`)
2. Check status bar for dropdowns
3. Change model: Mistral ↔ Llama 3
4. Change mode: Smart Routing / Browser Use / RAG Only
5. Send a test message - verify routing works

### Test SaRA Integration:
1. Open sidebar "Microsoft Apps" section
2. Click "🔧 Launch Microsoft SaRA"
   - Should launch SaRA if installed
   - Should open download page if not installed
3. Click "📧 Open Outlook Client"
   - Should open Outlook desktop app
4. Click "🩺 Run Diagnostics"
   - Should launch both SaRA and Outlook
   - Should run agent orchestrator analysis

---

## 📝 Configuration Requirements

### SaRA Path Configuration
Update `config.py` or `.env` with SaRA installation path:
```python
SARA_PATH = "C:\\Program Files\\Microsoft Support and Recovery Assistant\\SaRA.exe"
```

Default paths SaRA might be installed:
- `C:\Program Files\Microsoft Support and Recovery Assistant\SaRA.exe`
- `C:\Program Files (x86)\Microsoft Support and Recovery Assistant\SaRA.exe`

### Outlook Configuration
Outlook is detected automatically via:
- `outlook.exe` in system PATH
- Windows `os.startfile()` API

---

## 🚀 Usage Examples

### Example 1: Switch to Browser Use Mode
1. Select "Mode: Browser Use"
2. Type: "Find laptops under $1000 on Amazon"
3. System forces browser automation

### Example 2: RAG-Only Mode
1. Select "Mode: RAG Only"
2. Type: "Outlook not working"
3. System uses only knowledge base (no browser)

### Example 3: Quick SaRA Launch
1. Click sidebar → "Launch Microsoft SaRA"
2. SaRA opens automatically
3. Follow SaRA wizard for Outlook troubleshooting

### Example 4: Llama 3 Model
1. Select "Model: Llama 3 (RAG)"
2. All queries now use Llama 3 instead of Mistral
3. Knowledge base responses from Llama 3

---

## 🔧 Technical Details

### State Management
```javascript
const state = {
    selectedModel: 'mistral',  // 'mistral' | 'llama3'
    selectedMode: 'smart'  // 'smart' | 'browser_use' | 'rag_only'
}
```

### API Request Format
```javascript
POST /api/bridge
{
    "message": "user query",
    "model": "mistral" | "llama3",
    "smart_routing": true | false,
    "force_browser": true | false,
    "rag_only": true | false
}
```

### Tool Invocation
```javascript
POST /api/tools/sara
POST /api/tools/outlook

Response:
{
    "success": true/false,
    "message": "Status message",
    "execution_time": 0.5
}
```

---

## 📊 Benefits

### Model Selection:
- ✅ User control over AI model
- ✅ Compare Mistral vs Llama 3 responses
- ✅ Flexibility for different use cases

### Mode Selection:
- ✅ Force specific routing behavior
- ✅ Test browser automation explicitly
- ✅ RAG-only for pure knowledge base queries

### SaRA Integration:
- ✅ One-click access to Microsoft diagnostic tools
- ✅ Direct Outlook client launch
- ✅ Automated troubleshooting workflow
- ✅ Reduces manual tool navigation

---

## 🎯 Next Steps

1. ✅ Server running with new features
2. ✅ UI updated with dropdowns and buttons
3. ✅ API endpoints implemented
4. ✅ Tool invoker integrated

**Ready to test!** Refresh your browser and explore the new features.
