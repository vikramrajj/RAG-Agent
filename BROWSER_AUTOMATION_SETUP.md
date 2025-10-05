# 🚀 Browser Automation Setup - Complete Guide

## Status: Dependencies Installing...

---

## 📦 What's Being Installed

### 1. Core Packages
- ✅ `browser-use` - Browser automation framework
- ✅ `playwright` - Browser control library  
- ✅ `gradio` - UI components
- ✅ `langchain-google-genai` - Gemini AI integration

### 2. Browser
- ✅ Chromium browser (via Playwright)

**Installation time:** ~5-10 minutes (depending on internet speed)

---

## 🔑 Get Your Gemini API Key

### Quick Steps:
1. **Go to:** https://aistudio.google.com/app/apikey
2. **Sign in** with Google account
3. **Click "Get API Key"** or "Create API Key"
4. **Copy the key** (starts with `AIza...`)

### Add to .env:
Open `c:\Users\vikra\Downloads\RAG Agent\.env` and add:

```bash
# Google Gemini API for browser-use (add at the end of file)
GOOGLE_API_KEY=AIza...paste_your_key_here...
```

**Full guide:** See `GEMINI_API_KEY_GUIDE.md`

---

## 🧪 Test After Setup

### Once API key is added:

1. **Restart server:**
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
python agent_bridge.py
```

2. **Test in UI:**
- Type: "Find laptop on Amazon"
- **Expected:** Browser window opens automatically
- Amazon search page loads with laptop results
- Results returned to chat

---

## 🎯 What Browser Automation Will Do

### Before (Current):
```
You: "Find laptop"
System: Smart routes to BROWSER_USE ✅
Response: Generic advice from Mistral
```

### After (With Browser Automation):
```
You: "Find laptop on Amazon"  
System: Smart routes to BROWSER_USE ✅
Action: Opens Chrome browser
Action: Navigates to Amazon.com
Action: Searches for "laptop"
Action: Scrapes top results
Response: Real product links and prices!
```

---

## 🌐 Supported Actions

Once configured, you can do:

### Shopping Queries:
- ✅ "Find laptops on Amazon"
- ✅ "Search for headphones under $100"
- ✅ "Compare laptop prices"
- ✅ "Show me the best deals"

### Web Navigation:
- ✅ "Open Amazon"
- ✅ "Go to Best Buy"
- ✅ "Search Google for Python tutorials"

### Automated Tasks:
- ✅ "Find the cheapest iPhone"
- ✅ "Check if MacBook is in stock"
- ✅ "Get me laptop reviews"

---

## ⚙️ Configuration Options

### In browser_use_wrapper.py:

```python
# Model: Gemini 2.0 Flash (fastest, free)
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=api_key
)

# Browser settings
agent = Agent(
    task=task,
    llm=model,
    max_actions=10  # Max steps to complete task
)
```

### Customization:
- Change `max_actions` for longer/shorter sessions
- Add custom instructions in task prompt
- Configure headless vs visible browser

---

## 🔒 Security & Privacy

### API Key Safety:
- ✅ Stored in `.env` (not in Git)
- ✅ Never shared or logged
- ✅ Only used for AI requests

### Browser Privacy:
- Session is isolated
- No cookies/history saved
- Runs in incognito mode
- Closes after task completion

---

## 💰 Cost Estimate

### Gemini 2.0 Flash Pricing:
- **Free tier:** 1M tokens/month
- **After:** $0.075 per 1M tokens

### Typical Usage:
- One shopping search: ~500-1000 tokens
- **Free tier allows:** ~1000-2000 searches/month
- **Cost per search:** $0.00004 (effectively free!)

---

## 🐛 Troubleshooting

### Issue: "API key not working"
**Solution:**
1. Check for typos in `.env`
2. Verify key starts with `AIza`
3. No extra spaces around the key
4. Restart server after adding key

### Issue: "Browser doesn't open"
**Solution:**
1. Check Playwright installation: `playwright install chromium`
2. Verify browser-use package: `pip list | grep browser-use`
3. Check server logs for errors

### Issue: "Import errors"
**Solution:**
```powershell
pip install browser-use playwright gradio langchain-google-genai --upgrade
playwright install chromium
```

---

## 📊 Installation Checklist

- [ ] browser-use installed
- [ ] playwright installed  
- [ ] gradio installed
- [ ] langchain-google-genai installed
- [ ] Chromium browser downloaded
- [ ] Gemini API key obtained
- [ ] API key added to `.env`
- [ ] Server restarted
- [ ] Tested "Find laptop" query

---

## 🚀 Next Steps

### Step 1: Wait for installation to complete (~5 min)
Check terminal for "Installation complete!"

### Step 2: Get Gemini API key
Visit: https://aistudio.google.com/app/apikey

### Step 3: Add to .env
```bash
GOOGLE_API_KEY=AIza...your_key...
```

### Step 4: Restart server
```powershell
Get-Process python | Stop-Process -Force
python agent_bridge.py
```

### Step 5: Test!
Type in UI: "Find laptops on Amazon"

---

## ✅ Success Indicators

When working correctly, you'll see:
1. Chat shows: 🌐 **BROWSER USE (100%)**
2. Browser window opens automatically
3. Amazon page loads
4. Search executes
5. Results returned to chat
6. Browser closes

---

**Status:** Installing dependencies...  
**Next:** Get API key and add to `.env`  
**ETA to working:** ~10 minutes

---

## 📚 Documentation

- `GEMINI_API_KEY_GUIDE.md` - Detailed API key setup
- `browser_use_wrapper.py` - Implementation code
- `smart_router.py` - Routing logic

---

**Ready to proceed once installation completes!** 🎉
