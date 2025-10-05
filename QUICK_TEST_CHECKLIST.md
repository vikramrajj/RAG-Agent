# 🧪 Quick Test Checklist

## ✅ All Fixes Applied - Ready to Test!

---

## 🎯 Test 1: Sidebar Collapse/Expand

**Steps:**
1. Look at the right side "🛠️ Tools" panel
2. Click the **◀** button in the panel header
3. **Expected:** Panel collapses, **blue ▶ button appears on right edge**
4. Click the blue **▶** button
5. **Expected:** Panel expands smoothly

**Status:** ⬜ Not tested yet

---

## 🎯 Test 2: Shopping/Laptop Routing

**Query 1:** "Find laptop"
- **Expected Badge:** 🌐 **BROWSER USE**
- **Confidence:** 100% or 1.0
- **Status:** ⬜ Not tested yet

**Query 2:** "Find laptops on Amazon"
- **Expected Badge:** 🌐 **BROWSER USE**
- **Confidence:** 90-100%
- **Status:** ⬜ Not tested yet

**Query 3:** "Search for cheaper laptops"
- **Expected Badge:** 🌐 **BROWSER USE**
- **Confidence:** 60-90%
- **Status:** ⬜ Not tested yet

**Query 4:** "Open amazon"
- **Expected Badge:** 🌐 **BROWSER USE**
- **Confidence:** 60%
- **Status:** ⬜ Not tested yet

---

## 🎯 Test 3: Other Routing (Sanity Check)

**Query:** "Hello"
- **Expected Badge:** 🤖 **MISTRAL** or 🧠 **LLAMA3**
- **Status:** ⬜ Not tested yet

**Query:** "Outlook not working"
- **Expected Badge:** 📧 **RAG OUTLOOK**
- **Confidence:** 60%
- **Status:** ⬜ Not tested yet

---

## 🎯 Test 4: Diagnostics Button

**Steps:**
1. Expand Tools panel if collapsed
2. Look for "🔧 Troubleshooting" section
3. Click "Run Diagnostics"
4. **Expected:** No emoji encoding errors in response
5. **Expected:** Shows `[OK]`, `[WARNING]`, `[INFO]` instead of emoji

**Status:** ⬜ Not tested yet

---

## 📝 Notes

### Why Responses Might Be Slow:
- Ollama (local LLM) takes 20-45 seconds per response
- This is normal for Mistral/Llama3 models
- Browser-use (when configured) would be faster

### If Something Doesn't Work:
1. Check server console window for errors
2. Refresh the browser page (Ctrl+F5)
3. Check `server_console.log` for detailed logs

---

## ✅ Expected Results Summary

| Test | Expected Result |
|------|-----------------|
| Sidebar collapse | Blue ▶ button appears |
| Sidebar expand | Panel opens smoothly |
| "Find laptop" | 🌐 BROWSER USE badge |
| "Find laptops on Amazon" | 🌐 BROWSER USE badge |
| "Open amazon" | 🌐 BROWSER USE badge |
| "Hello" | 🤖 MISTRAL badge |
| "Outlook not working" | 📧 RAG OUTLOOK badge |
| Run Diagnostics | No emoji errors |

---

## 🚀 Ready to Test!

**Browser opened at:** http://localhost:8000/sat

**Start testing and let me know the results!**

---

**Quick Start:** Type "Find laptop" and press Enter
