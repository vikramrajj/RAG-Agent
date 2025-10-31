# Phase 3: Vision Analysis (GPT-4V)

**Duration:** 3-4 weeks | **Status:** Not Started  
**Dependencies:** Phase 2 ✅ (Frames extracted)  
**Output:** Frame descriptions, action identification, context understanding

---

## 📋 Overview

Phase 3 uses OpenAI's GPT-4V (Vision) model to analyze extracted frames and understand what the user is doing in each moment.

**Goal:** Convert image data into semantic understanding - describing user actions, tool usage, UI state, and context.

---

## 🎯 Core Objectives

1. ✅ Analyze frames using GPT-4V vision capabilities
2. ✅ Generate detailed descriptions of user actions
3. ✅ Identify tools and applications being used
4. ✅ Extract UI elements (buttons, menus, dialogs)
5. ✅ Recognize patterns and sequences
6. ✅ Create action context for each frame
7. ✅ Build relationships between frames

---

## 🏗️ Architecture

```
Extracted Frames (Phase 2)
        ↓
   [PHASE 3: Vision Analysis]
        ├─ Frame Loader
        ├─ GPT-4V Analyzer
        ├─ Action Extractor
        ├─ Context Builder
        └─ Pattern Recognizer
        ↓
Frame Descriptions + Actions + Context
        ↓
Phase 4: Template Generation
```

---

## 📁 File Structure to Create

```
video_training/
├── vision_analyzer.py          (NEW - Main GPT-4V integration)
├── action_extractor.py         (NEW - Extract actions from descriptions)
├── context_builder.py          (NEW - Build context from sequences)
├── pattern_recognizer.py       (NEW - Find patterns across frames)
├── vision_config.py            (NEW - Vision-specific configuration)
├── tests/
│   └── test_vision_analyzer.py (NEW - Vision analysis tests)
└── config.py                   (EXISTING - Update vision settings)
```

---

## 🔧 Implementation Details

### **1. Vision Analyzer (vision_analyzer.py)**

**Purpose:** Interface with GPT-4V API for frame analysis

```
Input:  Individual frame (PNG from Phase 2)
Process:
  - Load frame image
  - Encode as base64
  - Send to GPT-4V with system prompt
  - Parse response
  - Extract structured data
Output: Frame analysis JSON
```

**System Prompts (Multiple Specialized):**

**Prompt 1: General Action Detection**
```
You are analyzing a screenshot of a user's screen during automated task execution.
Describe:
1. What application/tool is visible?
2. What is the user doing? (action description)
3. What UI elements are visible?
4. What is the current state?
5. What happens next likely?

Format as JSON with keys: app, action, ui_elements, state, next_likely
```

**Prompt 2: Tool Identification**
```
Identify which of these tools is being used:
- Browser (Chrome, Firefox, Edge)
- Email Client (Outlook, Gmail)
- Terminal/Console
- File Explorer
- Text Editor
- System Settings
- Other (specify)

Also identify: URL/path, window title, active tab/folder
```

**Prompt 3: Element Extraction**
```
Extract all interactive UI elements visible:
- Links (URL, text)
- Buttons (label, position)
- Input fields (type, placeholder)
- Menus (options)
- Text content (headings, paragraphs)

Format as structured JSON with locations when possible.
```

**Prompt 4: Action Sequence Context**
```
This frame is part of a sequence. Given context of previous/next frames:
1. Is this part of a larger action? (e.g., multi-step form)
2. What's the goal of this action?
3. What precedes this? What follows?
4. Is there a pattern here?
```

**Key Methods:**
- `analyze_frame(frame_path)` - Single frame analysis
- `analyze_frame_batch(frame_paths)` - Batch processing
- `analyze_with_context(frame_path, previous_frame)` - Context-aware
- `extract_specific_info(frame_path, prompt_type)` - Specialized analysis

**Configuration:**
```python
GPT4V_MODEL = "gpt-4-vision-preview"
TEMPERATURE = 0.3  # Low randomness, deterministic
MAX_TOKENS = 500
RETRY_ATTEMPTS = 3
BATCH_SIZE = 10  # Batch frames for efficiency
RATE_LIMIT = 100  # Requests per minute
CACHE_RESPONSES = True
```

---

### **2. Action Extractor (action_extractor.py)**

**Purpose:** Convert GPT-4V descriptions into structured actions

**Action Schema:**
```python
{
    "action_id": "action_001",
    "frame_ids": ["frame_0100", "frame_0101", "frame_0102"],
    "type": "click|type|navigate|open_app|close_window|scroll",
    "app": "Chrome|Outlook|Explorer|Terminal",
    "target": "Gmail Compose Button|Search Box|Email",
    "description": "User clicked on Compose button to start new email",
    "coordinates": [x, y],
    "parameters": {
        "text_typed": "...",
        "url_navigated": "...",
        "menu_selected": "..."
    },
    "result": "Email compose window opened",
    "duration_seconds": 2.5,
    "confidence": 0.92
}
```

**Key Methods:**
- `extract_actions(frame_descriptions)` - Convert descriptions to actions
- `classify_action_type(description)` - Determine action type
- `identify_target(description, frame)` - Find what was acted upon
- `extract_parameters(description, action_type)` - Get action parameters
- `group_actions_into_sequences()` - Connect related actions

**Action Types Recognized:**
```
UI Interactions:
  - click(x, y, element)
  - double_click(x, y)
  - right_click(x, y)
  - hover(x, y)
  - drag(x1, y1, x2, y2)
  - scroll(direction, amount)

Text Input:
  - type(text, field)
  - clear_field(field)
  - select_all()
  - paste()

Navigation:
  - navigate_url(url)
  - click_link(link_text, url)
  - change_tab(tab_name)

Window Management:
  - open_application(app_name)
  - close_window()
  - switch_window(window_name)
  - minimize/maximize()

Data Interactions:
  - fill_form(fields)
  - submit_form()
  - download_file(filename)
  - upload_file(filepath)
```

---

### **3. Context Builder (context_builder.py)**

**Purpose:** Build multi-frame context for understanding sequences

**Context Layers:**

**Layer 1: Immediate Context (5 frames)**
```
Previous 2 frames → Current frame → Next 2 frames
  |___ What led here
  |___ What happens after
```

**Layer 2: Action Context (Action sequence)**
```
Start of action → Current frame → End of action
  |___ Action goal
  |___ Action progress
  |___ Completion status
```

**Layer 3: Session Context (Full video)**
```
Session start → Current frame → Session end
  |___ Overall goal
  |___ Progress in goal
  |___ Related actions
```

**Key Methods:**
- `build_frame_context(frame_index, window_size=5)` - Immediate context
- `build_action_context(action_sequence)` - Action-level context
- `build_session_context(frame_id, all_frames)` - Session-level context
- `identify_dependencies(action1, action2)` - Action relationships

**Context Output:**
```json
{
    "frame_id": "frame_0234",
    "immediate_context": {
        "previous_frames": [...],
        "next_frames": [...],
        "transition": "click → navigation"
    },
    "action_context": {
        "action_id": "action_015",
        "action_type": "fill_email_form",
        "progress": "Step 2 of 5",
        "steps_taken": ["opened_compose", "filled_to_field"],
        "steps_remaining": ["fill_subject", "fill_body", "send"]
    },
    "session_context": {
        "overall_goal": "Send email to team",
        "time_into_session": "45 seconds / 120 seconds",
        "related_actions": ["action_014", "action_015", "action_016"]
    }
}
```

---

### **4. Pattern Recognizer (pattern_recognizer.py)**

**Purpose:** Find recurring patterns and sequences

**Pattern Types:**

**Type 1: Repeated Sequences**
```
Pattern: User often does:
  1. Open Gmail
  2. Click Compose
  3. Type recipient
  4. Type subject
  5. Type body
  6. Send

Frequency: 5 times in video
Confidence: 95%
```

**Type 2: Conditional Sequences**
```
Pattern: When [condition], then [action]
  When user types in search box → Then clicks search button
Frequency: 8 times
Confidence: 87%
```

**Type 3: Tool Combinations**
```
Pattern: Tools used together
  Chrome + Gmail (email composition)
  Chrome + Spreadsheet (data entry)
  Terminal + Explorer (file operations)
Frequency: 12 times
Confidence: 92%
```

**Type 4: Error Recovery**
```
Pattern: When error occurs → User does X
  When page doesn't load → User refreshes
  When form validation fails → User corrects input
Frequency: 3 times
Confidence: 80%
```

**Key Methods:**
- `find_repeated_sequences(frame_actions, min_frequency=2)` - Find repeated patterns
- `find_conditional_patterns(actions)` - Find if-then patterns
- `find_tool_combinations(actions)` - Find co-occurring tools
- `find_error_recovery_patterns(actions)` - Find error handling
- `calculate_pattern_confidence(pattern)` - Confidence scoring
- `generate_pattern_rules(patterns)` - Create reusable rules

**Pattern Output:**
```json
{
    "patterns": [
        {
            "id": "pattern_001",
            "type": "repeated_sequence",
            "name": "Email Composition",
            "sequence": [
                "open_gmail",
                "click_compose",
                "type_recipient",
                "type_subject",
                "type_body",
                "click_send"
            ],
            "frequency": 5,
            "confidence": 0.95,
            "average_duration": 45.2
        }
    ]
}
```

---

### **5. Vision Analyzer Orchestrator**

**Workflow:**
```python
analyzer = VisionAnalyzer(frame_index_path="frames/index.json")

# Analyze all frames
descriptions = analyzer.analyze_all_frames()

# Extract actions
actions = analyzer.extract_actions(descriptions)

# Build context
contexts = analyzer.build_context(actions)

# Find patterns
patterns = analyzer.recognize_patterns(actions)

# Save results
analyzer.save_analysis()
```

**Configuration Integration:**
- Read frame paths from Phase 2 index
- Use GPU for image processing (if available)
- Manage API rate limits
- Cache GPT-4V responses

---

## 📊 Expected Output per Video

**Input:** 1000+ frames from Phase 2

**Output:**
```
analysis/
├── 20250831_122345/
│   ├── frame_descriptions/
│   │   ├── frame_0000_description.json
│   │   ├── frame_0005_description.json
│   │   └── ... (all frames)
│   ├── actions/
│   │   ├── actions_list.json
│   │   └── action_sequence.json
│   ├── context/
│   │   ├── frame_contexts.json
│   │   ├── action_contexts.json
│   │   └── session_context.json
│   ├── patterns/
│   │   ├── repeated_sequences.json
│   │   ├── conditional_patterns.json
│   │   ├── tool_combinations.json
│   │   └── error_recovery_patterns.json
│   └── summary/
│       ├── analysis_summary.json
│       ├── key_insights.json
│       └── recommended_templates.json
```

**Statistics per typical 30-minute video:**
- Frames analyzed: 1000-2000
- Actions identified: 50-200
- Patterns found: 5-20
- API calls: ~1000-2000 (batched)
- Processing time: 2-4 hours
- API cost: ~$20-50 (GPT-4V pricing)

---

## 🧪 Testing Strategy

**Test Categories:**

1. **Frame Analysis Tests**
   - Analyze known screenshots
   - Verify description accuracy
   - Test different prompt types
   - Validate JSON output format

2. **Action Extraction Tests**
   - Extract actions from known descriptions
   - Verify action types classification
   - Test parameter extraction
   - Check confidence scoring

3. **Context Building Tests**
   - Build immediate context
   - Build action sequences
   - Test context completeness
   - Verify time references

4. **Pattern Recognition Tests**
   - Find repeated sequences
   - Identify conditional patterns
   - Recognize tool combinations
   - Test error recovery patterns

5. **Integration Tests**
   - End-to-end analysis on sample video
   - Verify output structure
   - Test API error handling
   - Check rate limiting

**Expected Test Results:**
- 20-30 unit tests
- 80%+ code coverage
- All tests passing
- Sample video analysis: 2-4 hours
- Cost per test: minimal (use mock responses)

---

## 🔄 Integration with GPT-4V API

**API Configuration:**
```python
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_frame_with_gpt4v(frame_path, prompt_type="general"):
    # Load and encode frame
    with open(frame_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Select system prompt
    system_prompt = get_system_prompt(prompt_type)
    
    # Call GPT-4V
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze this screenshot"
                    }
                ]
            }
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## 💰 Cost Considerations

**GPT-4V Pricing (as of Oct 2025):**
- Vision analysis: ~$0.01-0.02 per frame
- Typical 30-min video: ~$10-40
- Optimization: Batch processing, caching, selective analysis

**Optimization Strategies:**
1. Cache responses for identical frames
2. Batch analyze frames (10 frames per API call)
3. Selective analysis (key frames only initially)
4. Local model fallback for simple tasks
5. Reuse patterns to avoid re-analysis

---

## 📈 Performance Considerations

**Optimization Strategies:**

1. **Batching**
   - Group 10 frames per API call
   - Reduces API overhead
   - Speeds up processing

2. **Parallel Processing**
   - Process multiple videos
   - Parallel API calls (with rate limiting)
   - Concurrent frame loading

3. **Caching**
   - Cache GPT-4V responses
   - Cache frame descriptions
   - Avoid duplicate analysis

4. **Smart Filtering**
   - Skip near-identical frames
   - Focus on key moments
   - Skip low-confidence results

**Performance Targets:**
- Analyze frames: 5-10 FPS with batching
- Full pipeline: 2-4 hours per 30-minute video
- Cost per video: $10-40 for full analysis

---

## 🔄 Integration Points

**Input from Phase 2:**
- Extracted frames in `frames/` directory
- Frame index with metadata
- Change scores and interactions
- Frame timestamps

**Output to Phase 4:**
- Frame descriptions (semantic understanding)
- Action list with parameters
- Pattern library for templates
- Context relationships
- Tool usage statistics

---

## 📝 Implementation Checklist

- [ ] Create `vision_analyzer.py` with GPT-4V integration
- [ ] Create specialized system prompts (4+ types)
- [ ] Create `action_extractor.py` with action parsing
- [ ] Create `context_builder.py` with multi-layer context
- [ ] Create `pattern_recognizer.py` with pattern detection
- [ ] Integrate API error handling and rate limiting
- [ ] Implement response caching system
- [ ] Create unit tests (25+ tests)
- [ ] Create mock responses for cost-free testing
- [ ] Process sample Phase 2 frames end-to-end
- [ ] Verify action extraction accuracy
- [ ] Test pattern recognition on sample video
- [ ] Optimize batch processing
- [ ] Handle API errors gracefully
- [ ] Document prompts and outputs
- [ ] Commit to git with detailed documentation

---

## ⏱️ Timeline Estimate

- **Week 1:** GPT-4V integration + prompts (3-4 days)
- **Week 1-2:** Action extraction (2-3 days)
- **Week 2:** Context building (2-3 days)
- **Week 2:** Pattern recognition (3-4 days)
- **Week 3:** Testing & optimization (2-3 days)
- **Week 3:** Integration & documentation (2-3 days)

**Total: 3-4 weeks**

---

## 🎓 Success Criteria

✅ Analyze 1000+ frames with GPT-4V  
✅ Extract 80%+ accurate actions from descriptions  
✅ Build context for 95%+ of frames  
✅ Identify 5+ recurring patterns per video  
✅ All tests passing (25+ tests)  
✅ Response caching reduces API calls by 40%+  
✅ Cost per video: $10-40  
✅ Output ready for Phase 4 (template generation)  

---

## 📚 Resources & References

- OpenAI GPT-4V: https://openai.com/blog/gpt-4v/
- Vision API Docs: https://platform.openai.com/docs/guides/vision
- Image Processing: https://pillow.readthedocs.io/
- JSON Processing: https://docs.python.org/3/library/json.html

---

## 🚀 Next Steps

1. ✅ Review this Phase 3 plan
2. ⏳ Set up OpenAI API credentials
3. ⏳ Begin implementation: GPT-4V analyzer
4. ⏳ Create specialized prompts
5. ⏳ Implement action extraction
6. ⏳ Build context system
7. ⏳ Implement pattern recognition
8. ⏳ Create comprehensive tests
9. ⏳ Optimize and document
10. 🎯 Move to Phase 4: Template Generation

