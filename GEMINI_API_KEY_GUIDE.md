# 🔑 Getting Your Google Gemini API Key

## Step-by-Step Guide

### 1. Go to Google AI Studio
**URL:** https://aistudio.google.com/app/apikey

### 2. Sign in with Google Account
- Use any Google account (Gmail)
- Free tier available

### 3. Create API Key
1. Click **"Get API Key"** or **"Create API Key"**
2. Select a Google Cloud project (or create new one)
3. Click **"Create API Key in new project"** if you don't have one
4. **Copy the API key** (starts with `AIza...`)

### 4. Add to .env File

Open `.env` file and add this line:
```bash
# Google Gemini API for browser-use
GOOGLE_API_KEY=AIza...your_key_here...
```

**Example:**
```bash
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## ⚠️ Important Notes

1. **Keep it secret!** Never share your API key or commit it to Git
2. **Free tier limits:** 60 requests per minute
3. **Model used:** Gemini 2.0 Flash (fast and free)

---

## 🧪 After Adding API Key

1. Save the `.env` file
2. Restart the server
3. Test with: "Find laptop on Amazon"
4. Browser should open automatically!

---

## 💰 Pricing (as of Oct 2024)

**Gemini 2.0 Flash:**
- First 1M tokens/month: **FREE**
- After that: $0.075 per 1M input tokens
- Very affordable for testing and personal use

---

## ❓ Troubleshooting

### Can't access Google AI Studio?
- Try using a personal Gmail (not work/school)
- Some organizations block access
- Alternative: Use OpenAI or Anthropic APIs

### API key not working?
- Check for typos
- Make sure no extra spaces
- Verify the key starts with `AIza`

---

## 🚀 Next Steps

1. Get your API key from: https://aistudio.google.com/app/apikey
2. Add it to `.env` file
3. Restart server
4. Test browser automation!

---

**Time to get key:** ~2 minutes ⏱️
