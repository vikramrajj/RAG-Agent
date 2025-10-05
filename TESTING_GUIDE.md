# 🧪 SAT Lightweight Models - Testing Guide

**Purpose**: Comprehensive testing guide for the SAT + Lightweight Models integration  
**Date**: October 4, 2025

---

## 📋 Pre-Testing Checklist

### Environment Setup:
- [ ] Ollama installed and running (`ollama serve`)
- [ ] Python environment activated
- [ ] Required packages installed (`pip install -r requirements.txt`)
- [ ] At least one model downloaded (`ollama pull mistral:7b`)
- [ ] Agent bridge running (`python agent_bridge.py`)
- [ ] Browser open to `http://localhost:8000/sat`

### System Check:
```powershell
# Check Ollama
curl http://localhost:11434/api/tags

# Check downloaded models
ollama list

# Check agent bridge
# Should see: "Running on http://0.0.0.0:8000"
```

---

## 🎯 Test Suite 1: Basic Functionality

### Test 1.1: Page Load
**Objective**: Verify SAT interface loads correctly

**Steps**:
1. Open `http://localhost:8000/sat`
2. Wait for page to fully load

**Expected**:
- ✅ Page loads without errors
- ✅ Chat interface visible
- ✅ Model selector visible at top of chat panel
- ✅ Model dropdown populated
- ✅ Status shows current model or "Checking..."

**Actual**: ___________

---

### Test 1.2: Model Dropdown Display
**Objective**: Verify model dropdown shows correct information

**Steps**:
1. Click model dropdown
2. Observe available options

**Expected**:
- ✅ Downloaded models in "✅ Downloaded Models" section
- ✅ Not downloaded in "⬇️ Available to Download" section
- ✅ Model names include size (e.g., "Mistral 7B (4.1GB)")
- ✅ Current model is pre-selected

**Actual**: ___________

---

### Test 1.3: Model Info Panel
**Objective**: Verify model details display correctly

**Steps**:
1. Click "ℹ️ Info" button
2. Observe expanded panel

**Expected**:
- ✅ Panel expands smoothly
- ✅ Shows model name, size, speed, quality
- ✅ Shows context length and best use
- ✅ Speed rating displays ⚡ symbols
- ✅ Quality rating displays ⭐ symbols
- ✅ Click again to collapse

**Actual**: ___________

---

## 🎯 Test Suite 2: Model Operations

### Test 2.1: Load Downloaded Model
**Objective**: Load an already-downloaded model

**Steps**:
1. Select a downloaded model from dropdown
2. Wait for loading

**Expected**:
- ✅ Status changes to "🟡 Loading model..."
- ✅ After 1-3 seconds, status → "🟢 [Model Name]"
- ✅ Model info updates in panel
- ✅ Toast notification shows success

**Actual**: ___________

---

### Test 2.2: Select Non-Downloaded Model
**Objective**: Attempt to select model not yet downloaded

**Steps**:
1. Select model with "Not Downloaded" suffix
2. Observe prompt

**Expected**:
- ✅ Confirmation dialog appears
- ✅ Dialog explains download will happen
- ✅ Shows model size and estimated time
- ✅ Click "Cancel" → returns to previous model
- ✅ Click "Yes" → proceeds to download

**Actual**: ___________

---

### Test 2.3: Download Model
**Objective**: Download a new model

**Steps**:
1. Select non-downloaded model
2. Click "Yes" in confirmation
3. Wait for download

**Expected**:
- ✅ Status → "🟡 Downloading..."
- ✅ Toast shows "Downloading model..."
- ✅ Download completes (2-5 minutes depending on size)
- ✅ Status → "🟢 Ready"
- ✅ Model auto-loads
- ✅ Toast shows "Downloaded successfully!"
- ✅ Model appears in "Downloaded Models" section

**Actual**: ___________

---

### Test 2.4: Model Recommendations
**Objective**: Get AI model recommendations

**Steps**:
1. Click "💡 Get Recommendations" button
2. Review recommendations

**Expected**:
- ✅ Alert/dialog appears
- ✅ Shows 2-3 recommended models
- ✅ Each recommendation includes:
  - Model name and size
  - Reason for recommendation
  - Use case suitability
- ✅ Recommendations relevant to current tool mode

**Actual**: ___________

---

## 🎯 Test Suite 3: Chat Integration

### Test 3.1: Basic Chat with Model
**Objective**: Send message and receive response

**Preparation**:
- Ensure Mistral 7B is loaded

**Steps**:
1. Type message: "What is 2+2?"
2. Click Send or press Enter
3. Wait for response

**Expected**:
- ✅ Message appears in chat (user side)
- ✅ Typing indicator shows
- ✅ Response appears in 1-5 seconds
- ✅ Response is correct and coherent
- ✅ Performance metric shown (e.g., "⚡ 35.2 tokens/sec")
- ✅ Timestamp displayed

**Actual**: ___________

---

### Test 3.2: Switch Models Mid-Conversation
**Objective**: Change models between messages

**Steps**:
1. Send message with Mistral: "Hello"
2. Wait for response
3. Switch to Phi-3 Mini
4. Send another message: "Goodbye"
5. Wait for response

**Expected**:
- ✅ First response uses Mistral
- ✅ Model switches successfully
- ✅ Second response uses Phi-3 Mini
- ✅ Conversation history maintained
- ✅ Performance metrics reflect different models

**Actual**: ___________

---

### Test 3.3: Performance Metrics Display
**Objective**: Verify performance data shows correctly

**Steps**:
1. Send message with fast model (Phi-3)
2. Note tokens/sec
3. Send message with slow model (Llama 3.1)
4. Note tokens/sec
5. Compare

**Expected**:
- ✅ Phi-3 shows higher tokens/sec (60-100)
- ✅ Llama 3.1 shows lower tokens/sec (20-40)
- ✅ Metrics displayed in small gray text
- ✅ Format: "⚡ XX.X tokens/sec"

**Actual**: ___________

---

## 🎯 Test Suite 4: Quality Comparison

### Test 4.1: Speed Test
**Objective**: Compare response times across models

**Question**: "What is the capital of France?"

**Test Matrix**:
| Model | Response Time | Quality | Notes |
|-------|---------------|---------|-------|
| Phi-3 Mini | _____ | _____ | _____ |
| Mistral 7B | _____ | _____ | _____ |
| Llama 3.1 8B | _____ | _____ | _____ |

**Expected**:
- Phi-3: <1s, concise answer
- Mistral: 1-2s, detailed answer
- Llama 3.1: 2-3s, comprehensive answer

---

### Test 4.2: Essay Quality Test
**Objective**: Compare writing quality across models

**Prompt**: "Write a 100-word introduction about climate change"

**Test Matrix**:
| Model | Coherence | Depth | Academic Tone | Overall |
|-------|-----------|-------|---------------|---------|
| Phi-3 Mini | ___/5 | ___/5 | ___/5 | ___/5 |
| Mistral 7B | ___/5 | ___/5 | ___/5 | ___/5 |
| Llama 3.1 8B | ___/5 | ___/5 | ___/5 | ___/5 |

**Expected**:
- Phi-3: 3/5 overall (good, concise)
- Mistral: 4/5 overall (excellent, balanced)
- Llama 3.1: 5/5 overall (outstanding, detailed)

---

### Test 4.3: Math Accuracy Test
**Objective**: Test mathematical reasoning

**Problem**: "Solve: x² + 5x + 6 = 0"

**Test Matrix**:
| Model | Correct? | Shows Steps? | Explanation | Score |
|-------|----------|--------------|-------------|-------|
| Phi-3 Mini | _____ | _____ | _____ | ___/5 |
| Mistral 7B | _____ | _____ | _____ | ___/5 |
| Qwen 2.5 7B | _____ | _____ | _____ | ___/5 |

**Expected**:
- Phi-3: Correct, basic steps
- Mistral: Correct, good explanation
- Qwen 2.5: Correct, detailed steps (best)

---

## 🎯 Test Suite 5: Error Handling

### Test 5.1: Ollama Not Running
**Objective**: Verify graceful degradation

**Setup**:
1. Stop Ollama (`Ctrl+C` in Ollama terminal)
2. Refresh SAT page

**Expected**:
- ✅ Page loads without crashing
- ✅ Status shows error: "❌ Error loading models"
- ✅ Toast shows helpful message
- ✅ Suggests starting Ollama
- ✅ Chat falls back to default reasoner (if available)

**Actual**: ___________

---

### Test 5.2: Model Load Failure
**Objective**: Handle failed model loading

**Setup**:
1. Select a very large model (Mixtral 8x7B)
2. If insufficient RAM, should fail

**Expected**:
- ✅ Status shows "🔴 Failed to load"
- ✅ Toast explains error
- ✅ Previous model remains active
- ✅ Can select different model
- ✅ Chat continues working

**Actual**: ___________

---

### Test 5.3: Download Failure
**Objective**: Handle interrupted download

**Setup**:
1. Start downloading large model
2. Disconnect internet mid-download
3. Wait for timeout

**Expected**:
- ✅ Status shows "🔴 Download failed"
- ✅ Toast explains error
- ✅ Suggests checking connection
- ✅ Can retry download
- ✅ Model not added to downloaded list

**Actual**: ___________

---

### Test 5.4: API Timeout
**Objective**: Handle slow responses

**Setup**:
1. Send very long/complex prompt
2. Wait for response

**Expected**:
- ✅ Shows typing indicator
- ✅ Waits patiently (no premature timeout)
- ✅ Eventually returns response or error
- ✅ If timeout, shows clear error message
- ✅ Can send new message

**Actual**: ___________

---

## 🎯 Test Suite 6: UI/UX Testing

### Test 6.1: Responsive Design
**Objective**: Verify layout on different sizes

**Steps**:
1. Resize browser window
2. Test at: 1920px, 1366px, 1024px, 768px

**Expected**:
- ✅ Model selector adjusts to width
- ✅ Dropdown doesn't overflow
- ✅ Info panel remains readable
- ✅ Chat interface responsive
- ✅ No horizontal scrolling

**Actual**: ___________

---

### Test 6.2: Animations & Transitions
**Objective**: Verify smooth animations

**Elements to Test**:
- [ ] Model dropdown expand/collapse
- [ ] Info panel expand/collapse
- [ ] Status indicator color changes
- [ ] Typing indicator animation
- [ ] Message appearance
- [ ] Button hover effects

**Expected**:
- All animations smooth (no lag)
- Transitions appropriate speed (0.2-0.3s)
- No janky movements

---

### Test 6.3: Color Contrast & Accessibility
**Objective**: Verify readability

**Check**:
- [ ] Model selector text readable
- [ ] Status indicator colors distinct
- [ ] Dropdown options readable
- [ ] Info panel text clear
- [ ] Chat messages high contrast
- [ ] Performance metrics visible

**Expected**:
- All text passes WCAG AA standard
- Colors distinguishable for colorblind users

---

## 🎯 Test Suite 7: Performance Testing

### Test 7.1: Multiple Rapid Requests
**Objective**: Test system under load

**Steps**:
1. Send 10 messages rapidly (one after another)
2. Observe behavior

**Expected**:
- ✅ All messages queued properly
- ✅ Responses appear in order
- ✅ No crashes or freezes
- ✅ Performance metrics accurate
- ✅ UI remains responsive

**Actual**: ___________

---

### Test 7.2: Large Context Test
**Objective**: Test long conversation handling

**Steps**:
1. Have 20+ message conversation
2. Observe memory usage
3. Send another message

**Expected**:
- ✅ Chat history maintained
- ✅ Scrolling smooth
- ✅ No memory leaks
- ✅ Response still contextual
- ✅ Performance doesn't degrade

**Actual**: ___________

---

### Test 7.3: Model Switch Performance
**Objective**: Measure model loading times

**Test Matrix**:
| Model | Load Time | Memory Usage | Notes |
|-------|-----------|--------------|-------|
| Phi-3 Mini | _____ | _____ | _____ |
| Mistral 7B | _____ | _____ | _____ |
| Llama 3.1 8B | _____ | _____ | _____ |
| Qwen 2.5 7B | _____ | _____ | _____ |

**Expected**:
- Phi-3: <1s load, ~2GB RAM
- Mistral: 1-2s load, ~8GB RAM
- Llama 3.1: 2-3s load, ~10GB RAM
- Qwen 2.5: 2-3s load, ~10GB RAM

---

## 🎯 Test Suite 8: Edge Cases

### Test 8.1: Empty Message
**Objective**: Handle empty input

**Steps**:
1. Click send without typing
2. Type only spaces and send

**Expected**:
- ✅ Nothing happens (button disabled or no action)
- ✅ No error messages
- ✅ Input clears after spaces

**Actual**: ___________

---

### Test 8.2: Very Long Message
**Objective**: Handle large inputs

**Steps**:
1. Paste 5000+ character text
2. Try to send

**Expected**:
- ✅ Input accepts text
- ✅ Textarea expands appropriately
- ✅ Either sends or shows length warning
- ✅ If sends, response handles context well

**Actual**: ___________

---

### Test 8.3: Special Characters
**Objective**: Handle special input

**Messages to Test**:
- "Test with émojis: 😀🎓📚"
- "Math symbols: ∑ ∫ √ π"
- "Code: `console.log('test')`"
- "URLs: https://example.com"

**Expected**:
- ✅ All characters display correctly
- ✅ Response handles special chars
- ✅ No encoding errors
- ✅ Formatting preserved

**Actual**: ___________

---

### Test 8.4: Simultaneous Model Change + Message
**Objective**: Handle race conditions

**Steps**:
1. Start sending message
2. Immediately change model
3. Observe behavior

**Expected**:
- ✅ Message uses original model OR
- ✅ Message queued for new model OR
- ✅ Clear indication of which model used
- ✅ No crashes or errors

**Actual**: ___________

---

## 🎯 Test Suite 9: Integration Testing

### Test 9.1: With Other SAT Features
**Objective**: Verify compatibility with existing features

**Test**:
- [ ] File upload button works
- [ ] Voice input button works  
- [ ] Tool selector (Chat/Search/Analyze/Write) works
- [ ] Feature cards clickable
- [ ] Status indicator updates

**Expected**:
- Model selector doesn't interfere with other features
- All buttons functional
- Layout intact

---

### Test 9.2: Browser Compatibility
**Objective**: Test across browsers

**Browsers to Test**:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on Mac)

**Expected**:
- ✅ Model selector appears correctly
- ✅ Dropdown functions properly
- ✅ Animations smooth
- ✅ API calls successful
- ✅ No console errors

**Actual**: ___________

---

## 📊 Test Results Summary

### Overall Results:
- **Total Tests**: 30+
- **Passed**: _____
- **Failed**: _____
- **Skipped**: _____

### Critical Issues Found:
1. _________________________________
2. _________________________________
3. _________________________________

### Minor Issues Found:
1. _________________________________
2. _________________________________
3. _________________________________

### Performance Notes:
- _________________________________
- _________________________________
- _________________________________

### Recommendations:
1. _________________________________
2. _________________________________
3. _________________________________

---

## 🚀 Quick Test Script

For rapid testing, run this sequence:

```powershell
# 1. Start services
ollama serve
python agent_bridge.py

# 2. Download test models (in separate terminal)
ollama pull phi3:3.8b
ollama pull mistral:7b

# 3. Open browser
start http://localhost:8000/sat

# 4. Quick test sequence:
# - Verify page loads
# - Select Mistral from dropdown
# - Send message: "Hello"
# - Check response appears
# - Switch to Phi-3 Mini
# - Send message: "What is 2+2?"
# - Check response appears faster
# - Click Info button
# - Verify details show
# - Success! ✅
```

---

## 📝 Test Report Template

```markdown
## Test Session Report

**Date**: ___________
**Tester**: ___________
**Environment**: ___________

### Setup:
- Ollama Version: ___________
- Python Version: ___________
- Browser: ___________
- Models Downloaded: ___________

### Results:
- Tests Passed: _____ / _____
- Critical Issues: _____
- Time Taken: _____

### Notes:
_________________________________
_________________________________

### Sign-off:
Tested by: ___________
Approved by: ___________
```

---

**Happy Testing! 🧪✨**

Make sure to document any issues found and celebrate all the passes! 🎉
