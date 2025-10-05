# 🌐 Browser-Use Integration Guide

## Overview

Your RAG Agent now includes powerful browser automation capabilities through integration with [browser-use/web-ui](https://github.com/browser-use/web-ui), providing advanced AI-controlled browser automation.

---

## 🎯 What's New?

### **Enhanced Browser Automation**

1. **AI-Powered Browser Control**
   - Natural language browser commands
   - Multi-step workflow automation
   - Intelligent web scraping
   - Form filling and interaction

2. **Visual WebUI Interface**
   - Gradio-based web interface
   - Real-time browser view
   - Task recording and playback
   - Configuration management

3. **Advanced Features**
   - Persistent browser sessions
   - Custom browser support (use your Chrome profile)
   - Screen recording of automation sessions
   - Deep research capabilities
   - Multiple LLM provider support

---

## 🚀 Quick Start

### **Option 1: Use Within RAG Agent API**

The browser-use functionality is now integrated into your existing API:

```python
import requests

# Execute a browser task
response = requests.post('http://localhost:8000/browser-use/execute', json={
    'task': 'Search for latest AI news and summarize top 5 articles',
    'model': 'ollama/llama3',
    'save_recording': True
})

print(response.json())
```

### **Option 2: Launch Standalone WebUI**

```bash
# Windows
start_browser_webui.bat

# Or with Python directly
python launch_browser_webui.py --ip 127.0.0.1 --port 7788 --theme Ocean
```

Access at: **http://127.0.0.1:7788**

---

## 📚 Integration Features

### **1. New API Endpoints**

#### **Check Browser-Use Status**
```http
GET /browser-use/status
```

Response:
```json
{
  "available": true,
  "features": {
    "web_search": true,
    "content_extraction": true,
    "workflow_automation": true,
    "webui_available": true
  }
}
```

#### **Execute Browser Task**
```http
POST /browser-use/execute
Content-Type: application/json

{
  "task": "Go to example.com and extract all article titles",
  "model": "ollama/llama3",
  "use_own_browser": false,
  "keep_browser_open": false,
  "save_recording": true
}
```

#### **Extract Website Content**
```http
POST /browser-use/extract
Content-Type: application/json

{
  "url": "https://example.com/article",
  "content_type": "main",
  "model": "ollama/llama3"
}
```

#### **Automate Complex Workflow**
```http
POST /browser-use/workflow
Content-Type: application/json

{
  "workflow": "1. Go to LinkedIn\n2. Search for AI jobs\n3. Get top 10 results\n4. Summarize each position",
  "model": "ollama/llama3",
  "use_persistent_browser": true
}
```

### **2. Enhanced Search Endpoint**

The `/search` endpoint now supports browser-use:

```http
POST /search
Content-Type: application/json

{
  "query": "artificial intelligence trends 2025",
  "use_browser_use": true
}
```

---

## 🛠️ Setup & Configuration

### **1. Install Browser-Use Dependencies**

```bash
cd browser-use-webui
pip install -r requirements.txt
playwright install chromium
```

### **2. Configure Environment**

Edit `browser-use-webui/.env`:

```env
# LLM Configuration
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Or use Ollama (already configured in your RAG Agent)
OLLAMA_BASE_URL=http://localhost:11434

# Browser Configuration (Optional)
BROWSER_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
BROWSER_USER_DATA=C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data

# Recording Settings
SAVE_RECORDING_PATH=./recordings
```

### **3. Test Installation**

```bash
# Test browser-use integration
python -c "from browser_integration import is_browser_integration_available; print(f'Browser-Use Available: {is_browser_integration_available()}')"
```

---

## 💡 Usage Examples

### **Example 1: Web Research**

```python
import asyncio
from browser_integration import search_web

async def research():
    result = await search_web(
        query="What is RAG in AI?",
        max_results=5,
        model="ollama/llama3"
    )
    
    if result['success']:
        print("Research Results:", result['result'])

asyncio.run(research())
```

### **Example 2: Content Extraction**

```python
import asyncio
from browser_integration import extract_website_content

async def extract():
    result = await extract_website_content(
        url="https://news.ycombinator.com",
        content_type="main",
        model="ollama/llama3"
    )
    
    if result['success']:
        print("Extracted Content:", result['result'])

asyncio.run(extract())
```

### **Example 3: Complex Workflow**

```python
import asyncio
from browser_integration import automate_workflow

async def workflow():
    result = await automate_workflow(
        workflow="""
        1. Go to GitHub trending page
        2. Find top 5 Python repositories
        3. For each repository:
           - Get the name and description
           - Count the stars
           - Check if it has good documentation
        4. Create a summary report
        """,
        model="ollama/llama3",
        use_persistent_browser=True
    )
    
    if result['success']:
        print("Workflow Result:", result['result'])

asyncio.run(workflow())
```

### **Example 4: From SAT UI**

Update your `sat_ui.html` to use browser-use:

```javascript
async function sendMessage() {
    const message = document.getElementById('userInput').value.trim();
    
    if (currentTool === 'search') {
        // Use enhanced browser-use search
        const response = await fetch('http://localhost:8000/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: message,
                use_browser_use: true  // Enable browser-use
            })
        });
        
        const data = await response.json();
        addMessage(data.content, 'agent');
    }
}
```

---

## 🎨 WebUI Features

### **Agent Settings Tab**
- Select LLM provider (OpenAI, Anthropic, Ollama, etc.)
- Configure model parameters
- Set temperature and max tokens
- Enable/disable recording

### **Browser Settings Tab**
- Use own browser (persistent sessions)
- Configure browser path
- Set user data directory
- Keep browser open between tasks
- Enable/disable headless mode

### **Run Agent Tab**
- Enter natural language tasks
- Watch real-time browser automation
- View step-by-step execution
- Download recordings

### **Agent Marketplace Tab**
- Pre-built automation agents
- Deep research agent
- Data extraction templates
- Workflow examples

### **Load & Save Config Tab**
- Save your configurations
- Load previous setups
- Export/import settings
- Quick preset switching

---

## 🔧 Advanced Configuration

### **Using Your Own Browser**

1. Close all Chrome windows
2. Set environment variables:
   ```env
   BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
   BROWSER_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"
   ```
3. Access WebUI in Firefox/Edge (not Chrome)
4. Check "Use Own Browser" in Browser Settings

### **Recording Sessions**

```python
result = await execute_browser_task(
    task="Your task here",
    save_recording=True  # Saves to ./recordings/
)
```

Recordings include:
- Screen capture of browser
- Console logs
- Network activity
- Step-by-step actions

### **Multiple LLM Support**

```python
# Use OpenAI
result = await execute_browser_task(task="...", model="openai/gpt-4")

# Use Anthropic
result = await execute_browser_task(task="...", model="anthropic/claude-3-opus")

# Use Ollama (default)
result = await execute_browser_task(task="...", model="ollama/llama3")

# Use DeepSeek
result = await execute_browser_task(task="...", model="deepseek/deepseek-chat")
```

---

## 📊 Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                RAG Agent (agent_bridge.py)              │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Browser Integration Layer                │  │
│  │      (browser_integration.py)                    │  │
│  └───────────────────┬──────────────────────────────┘  │
│                      │                                  │
│                      ▼                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Browser-Use WebUI (browser-use-webui/)      │  │
│  │                                                   │  │
│  │  ├─ Gradio Interface                             │  │
│  │  ├─ Browser Controller                           │  │
│  │  ├─ LLM Providers (OpenAI, Anthropic, Ollama)   │  │
│  │  ├─ Playwright Integration                       │  │
│  │  └─ Recording & Monitoring                       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  API Endpoints:                                         │
│  • /browser-use/status                                  │
│  • /browser-use/execute                                 │
│  • /browser-use/extract                                 │
│  • /browser-use/workflow                                │
│  • /search (enhanced)                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Use Cases for Students

### **1. Research Automation**
- "Search for academic papers on machine learning and summarize the abstracts"
- "Find top 10 universities for computer science and compare their rankings"
- "Extract citation information from research paper websites"

### **2. Study Material Collection**
- "Go to Coursera and find free AI courses"
- "Extract key concepts from educational YouTube videos"
- "Compile study resources from multiple educational websites"

### **3. Assignment Help**
- "Search for coding solutions to specific programming problems"
- "Find examples of well-written essays on a topic"
- "Extract data from government statistics websites for my report"

### **4. Career Preparation**
- "Search LinkedIn for entry-level data science jobs"
- "Extract job requirements from multiple job postings"
- "Find internship opportunities at tech companies"

---

## 🔒 Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Browser Sessions**: Be cautious with persistent sessions and saved credentials
3. **Rate Limiting**: Respect website rate limits and robots.txt
4. **Data Privacy**: Be aware of data collected during automation
5. **Recording Storage**: Recordings may contain sensitive information

---

## 🐛 Troubleshooting

### **Browser-Use Not Available**

```bash
# Check status
curl http://localhost:8000/browser-use/status

# Install dependencies
cd browser-use-webui
pip install -r requirements.txt
playwright install chromium
```

### **WebUI Won't Launch**

```bash
# Check Python environment
python --version  # Should be 3.8+

# Check Gradio installation
pip install gradio==5.27.0

# Try direct launch
cd browser-use-webui
python webui.py --ip 127.0.0.1 --port 7788
```

### **Browser Won't Start**

```bash
# Reinstall Playwright browsers
playwright install --force chromium

# Check browser path
echo $BROWSER_PATH  # Linux/Mac
echo %BROWSER_PATH%  # Windows
```

### **LLM Connection Issues**

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Test model
ollama run llama3 "Hello"
```

---

## 📈 Performance Tips

1. **Use Persistent Browser**: Faster for multiple tasks
2. **Disable Recording**: Saves resources if not needed
3. **Headless Mode**: Use for production/automated tasks
4. **Cache Results**: Store frequent search results
5. **Batch Operations**: Combine multiple tasks when possible

---

## 🎓 Learning Resources

- **Browser-Use Docs**: https://docs.browser-use.com
- **Playwright Docs**: https://playwright.dev
- **Gradio Docs**: https://gradio.app
- **RAG Agent Wiki**: Check project documentation

---

## 🤝 Contributing

If you enhance the browser-use integration:

1. Test thoroughly with different browsers
2. Update this documentation
3. Add example use cases
4. Submit improvements to the browser-use-webui project

---

## 📝 Changelog

**v1.0.0 (October 3, 2025)**
- ✅ Initial integration with browser-use-webui
- ✅ Added 4 new API endpoints
- ✅ Enhanced search endpoint
- ✅ Created browser_integration.py module
- ✅ Added launcher scripts
- ✅ Complete documentation

---

## 🎉 Summary

Your RAG Agent now has **enterprise-grade browser automation** capabilities:

✅ Natural language browser control  
✅ Visual WebUI interface  
✅ Multiple LLM provider support  
✅ Persistent browser sessions  
✅ Screen recording  
✅ Workflow automation  
✅ Easy API integration  

**Start using it today to supercharge your student assistance tool!** 🚀

---

*For questions or issues, check the browser-use-webui documentation or create an issue in the repository.*
