# SAT UI Integration Issues & Fixes

## Current Status

✅ **FIXED:**
1. Server now serves `sat_ui_improved.html` instead of legacy `sat_ui.html`
2. Emoji encoding issues in agent orchestrator fixed
3. Smart routing backend is working (tested via API)

❌ **NEEDS FIXING:**
1. **UI doesn't call backend API** - Uses mock `generateResponse()` function
2. **No smart routing indicators** - UI doesn't show route badges
3. **Voice input doesn't auto-submit** - Just fills the text field

---

## Issue 1: UI Not Calling Backend API

**Current Code (Lines ~1594):**
```javascript
addMessage('agent', generateResponse(message));  // Mock response!
```

**Should Be:**
```javascript
// Call actual backend
const response = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: message,
        model: 'mistral',
        smart_routing: true
    })
});
const data = await response.json();
addMessage('agent', data.content, data.route, data.confidence);
```

---

## Issue 2: No Route Badges in UI

**Need to Add:**

### CSS for Route Badges:
```css
.route-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
    margin-left: 8px;
}

.route-rag { 
    background: #dbeafe; 
    color: #1e40af; 
}

.route-browser { 
    background: #fef3c7; 
    color: #92400e; 
}

.route-mistral { 
    background: #e0e7ff; 
    color: #3730a3; 
}

.confidence {
    font-size: 0.7em;
    color: var(--text-muted);
    margin-left: 8px;
}
```

### Update addMessage() function:
```javascript
function addMessage(sender, content, route, confidence) {
    // ... existing code ...
    
    let routeBadge = '';
    if (sender === 'agent' && route) {
        const routeIcons = {
            'rag_outlook': '📧',
            'browser_use': '🌐',
            'mistral': '🤖'
        };
        const routeClass = route.replace('_', '-');
        routeBadge = `<span class="route-badge route-${routeClass}">${routeIcons[route] || ''} ${route.toUpperCase()}</span>`;
        
        if (confidence) {
            routeBadge += `<span class="confidence">${Math.round(confidence * 100)}%</span>`;
        }
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${senderName}</span>
                ${routeBadge}
                <span class="message-time">${time}</span>
                ...
            </div>
            ...
        </div>
    `;
}
```

---

## Issue 3: Voice Input Auto-Submit

**Current Code (Lines ~1714):**
```javascript
state.recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
    
    document.getElementById('inputField').value = transcript;
    updateCharCount();
};
```

**Should Add:**
```javascript
state.recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
    
    document.getElementById('inputField').value = transcript;
    updateCharCount();
    
    // Auto-submit when speech ends (final result)
    if (event.results[event.results.length - 1].isFinal) {
        setTimeout(() => {
            sendMessage();  // Auto-submit after speech ends
        }, 500);  // Small delay to ensure transcript is complete
    }
};
```

---

## Quick Fix: Replace generateResponse() with Real API Call

### Find and Replace in sat_ui_improved.html:

**FIND (around line 1575-1595):**
```javascript
async function sendMessage(quickPrompt = null) {
    const input = document.getElementById('inputField');
    const message = quickPrompt || input.value.trim();

    if (!message) return;

    addMessage('user', message);
    input.value = '';
    updateCharCount();

    showTypingIndicator();

    setTimeout(() => {
        removeTypingIndicator();
        addMessage('agent', generateResponse(message));
    }, 1000);
}
```

**REPLACE WITH:**
```javascript
async function sendMessage(quickPrompt = null) {
    const input = document.getElementById('inputField');
    const message = quickPrompt || input.value.trim();

    if (!message) return;

    addMessage('user', message);
    input.value = '';
    updateCharCount();

    showTypingIndicator();

    try {
        // Call actual backend API with smart routing
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                model: 'mistral',
                smart_routing: true
            })
        });

        const data = await response.json();
        
        removeTypingIndicator();
        
        // Pass route and confidence to addMessage
        addMessage('agent', data.content || data.response, data.route, data.confidence);
        
    } catch (error) {
        removeTypingIndicator();
        addMessage('agent', '❌ Error: Unable to get response from server. Please try again.');
        console.error('Chat error:', error);
    }
}
```

---

## Implementation Priority

### High Priority (Breaks functionality):
1. ✅ Fix emoji encoding in agent_orchestrator ← DONE
2. 🔴 **Replace generateResponse() with real API call** ← CRITICAL
3. 🔴 **Add route badges to UI** ← Important for visibility

### Medium Priority (UX improvements):
4. 🟡 Voice input auto-submit
5. 🟡 Model selector dropdown (documented in SAT_UI_MODEL_SELECTOR_PATCH.md)

### Low Priority (Nice to have):
6. ⚪ Confidence score display
7. ⚪ Route statistics

---

## Testing Steps After Fixes

1. **Test General Query:**
   ```
   Message: "What is 2+2?"
   Expected: Routes to MISTRAL, shows 🤖 badge
   ```

2. **Test Outlook Query:**
   ```
   Message: "My Outlook is not syncing"
   Expected: Routes to RAG_OUTLOOK, shows 📧 badge
   ```

3. **Test Shopping Query:**
   ```
   Message: "Find cheap laptops"
   Expected: Routes to BROWSER_USE, shows 🌐 badge
   ```

4. **Test Voice Input:**
   - Click voice button
   - Say "Hello"
   - Should auto-submit when done speaking

---

## Files to Modify

1. `agent_bridge.py` - ✅ Already fixed emoji encoding
2. `sat_ui_improved.html` - Needs updates to:
   - `sendMessage()` function (line ~1575)
   - `addMessage()` function (line ~1602)
   - CSS for route badges
   - Voice recognition auto-submit

---

## Current Server Status

✅ Server running on http://localhost:8000
✅ Smart routing working in backend
✅ API endpoint /chat accepting requests
✅ Improved UI being served at /sat
✅ Legacy UI available at /sat_legacy

**Next Step:** Apply the fixes to sat_ui_improved.html
