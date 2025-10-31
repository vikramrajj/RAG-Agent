# Phase 4: Template & Guideline Generation

**Duration:** 2-3 weeks | **Status:** Not Started  
**Dependencies:** Phase 3 ✅ (Vision analysis complete)  
**Output:** Reusable action templates & Guidelines library

---

## 📋 Overview

Phase 4 is where the magic happens - converting vision analysis into **reusable action templates** and **Guidelines** (from the X post analysis).

This phase implements the Guidelines Pattern discussed in the Akshay Pachaar tweet, enabling your agent to learn from user behavior videos.

**Goal:** Extract learned patterns from Phase 3 and convert them into structured, reusable guidelines that capture "when do this, then do that" rules.

---

## 🎯 Core Objectives

1. ✅ Convert action sequences into reusable templates
2. ✅ Extract conditions from patterns (WHEN this happens)
3. ✅ Define actions for each template (THEN do this)
4. ✅ Identify required tools for each guideline (WITH these tools)
5. ✅ Generate parameter schemas
6. ✅ Build confidence scores
7. ✅ Create guideline library
8. ✅ Enable multi-topic handling via guidelines

---

## 🏗️ Architecture

```
Phase 3 Analysis Results
  (Actions, Patterns, Context)
        ↓
   [PHASE 4: Template Generation]
        ├─ Template Extractor
        ├─ Condition Analyzer
        ├─ Guideline Builder
        ├─ Parameter Schema Generator
        └─ Guideline Library Manager
        ↓
Reusable Templates + Guidelines Library
        ↓
Phase 5: Full Integration (Multi-topic Handling)
```

---

## 📁 File Structure to Create

```
video_training/
├── template_extractor.py       (NEW - Extract templates from patterns)
├── condition_analyzer.py       (NEW - Analyze pattern conditions)
├── guideline_builder.py        (NEW - Build Guidelines pattern)
├── parameter_schema.py         (NEW - Generate parameter schemas)
├── guideline_library.py        (NEW - Manage guidelines DB)
├── template_compiler.py        (NEW - Compile templates to executable)
├── tests/
│   └── test_template_generation.py (NEW - Template generation tests)
└── config.py                   (EXISTING - Update template settings)
```

---

## 🔧 Implementation Details

### **1. Template Extractor (template_extractor.py)**

**Purpose:** Convert action sequences into abstract templates

**Input:** Phase 3 action sequences  
**Output:** Abstract action templates

**Process:**
```
Action Sequence:
  1. click("Gmail Compose")
  2. type("recipient@example.com")
  3. type("Subject: Meeting Request")
  4. type("Body: Let's meet...")
  5. click("Send")
        ↓
Template (Generalized):
  1. click(<compose_button>)
  2. type(<recipient>)
  3. type(<subject>)
  4. type(<body>)
  5. click(<send_button>)
```

**Key Methods:**
- `extract_templates_from_patterns(patterns)` - Convert patterns to templates
- `generalize_sequence(action_sequence)` - Replace values with placeholders
- `identify_parameters(action_sequence)` - Find parameterizable elements
- `generate_template_variants()` - Create alternative versions
- `assign_template_id(template)` - Create unique IDs

**Template Schema:**
```json
{
    "template_id": "tpl_email_compose_001",
    "name": "Email Composition",
    "description": "Template for composing and sending emails",
    "version": "1.0",
    "created_from_patterns": ["pattern_001", "pattern_002"],
    "frequency_in_videos": 5,
    "confidence": 0.95,
    "average_duration_seconds": 45.2,
    "steps": [
        {
            "step_id": 1,
            "action": "click",
            "target": "compose_button",
            "description": "Click the compose button"
        },
        {
            "step_id": 2,
            "action": "type",
            "target": "recipient_field",
            "parameter": "recipient_email",
            "description": "Type recipient email address"
        },
        {
            "step_id": 3,
            "action": "type",
            "target": "subject_field",
            "parameter": "email_subject",
            "description": "Type email subject"
        },
        {
            "step_id": 4,
            "action": "type",
            "target": "body_field",
            "parameter": "email_body",
            "description": "Type email body"
        },
        {
            "step_id": 5,
            "action": "click",
            "target": "send_button",
            "description": "Click send button"
        }
    ],
    "parameters": {
        "recipient_email": {
            "type": "string",
            "description": "Email address of recipient",
            "required": true
        },
        "email_subject": {
            "type": "string",
            "description": "Email subject line",
            "required": true
        },
        "email_body": {
            "type": "string",
            "description": "Email body text",
            "required": true
        }
    },
    "tools_required": ["gmail_api", "browser_control"],
    "prerequisite_state": "Gmail inbox open",
    "result_state": "Email sent"
}
```

---

### **2. Condition Analyzer (condition_analyzer.py)**

**Purpose:** Extract conditions from patterns (WHEN does this apply?)

**Condition Types:**

**Type 1: Trigger Conditions**
```
Pattern: User opens Gmail → does email composition
Trigger Condition: User opens Gmail application
Format: "app == 'Gmail' && view == 'inbox'"
```

**Type 2: State Conditions**
```
Pattern: When form validation fails → user corrects input
State Condition: "form_has_errors == true"
```

**Type 3: Contextual Conditions**
```
Pattern: During email composition, user often attaches files
Context Condition: "in_compose_mode && file_attachment_visible"
```

**Type 4: Time-based Conditions**
```
Pattern: User checks email every morning
Time Condition: "time.hour >= 8 && time.hour < 12"
```

**Type 5: Sequential Conditions**
```
Pattern: After opening email, user clicks search
Sequential Condition: "previous_action == 'open_email'"
```

**Key Methods:**
- `analyze_pattern_conditions(pattern)` - Extract trigger conditions
- `find_trigger_events(pattern)` - Find what starts the pattern
- `identify_prerequisites(pattern)` - What must be true before
- `identify_failure_conditions(pattern)` - When pattern breaks
- `extract_temporal_conditions(pattern)` - Time-based triggers
- `normalize_condition(raw_condition)` - Standardize condition syntax

**Condition Schema:**
```json
{
    "condition_id": "cond_email_composition_start",
    "pattern_id": "pattern_001",
    "condition_type": "trigger",
    "expression": {
        "logic": "AND",
        "clauses": [
            {
                "property": "current_app",
                "operator": "==",
                "value": "Gmail",
                "confidence": 0.98
            },
            {
                "property": "current_view",
                "operator": "==",
                "value": "inbox",
                "confidence": 0.95
            },
            {
                "property": "user_action",
                "operator": "==",
                "value": "clicked_compose_button",
                "confidence": 0.99
            }
        ]
    },
    "confidence": 0.97,
    "frequency": 5,
    "description": "User is in Gmail inbox and clicked compose button"
}
```

---

### **3. Guideline Builder (guideline_builder.py)**

**Purpose:** Create Guidelines per the X post pattern

**Guideline Schema (Main Data Structure):**

```python
guideline = {
    "guideline_id": "guide_email_composition_001",
    "name": "Compose and Send Email",
    "description": "Handle email composition including recipient, subject, and body",
    
    # WHEN: Condition for this guideline
    "condition": {
        "trigger": "app == 'Gmail' && view == 'inbox' && user_clicks_compose",
        "prerequisites": ["gmail_logged_in", "internet_connected"],
        "conflict_with": ["guide_email_read_001"],  # Can't read while composing
        "requires_context": ["previous_emails_loaded"]
    },
    
    # THEN: Action to take
    "actions": [
        {
            "step": 1,
            "action_type": "click",
            "target": "compose_button",
            "parameters": {}
        },
        {
            "step": 2,
            "action_type": "fill_form",
            "target": "email_form",
            "parameters": {
                "to": "${recipient}",
                "subject": "${subject}",
                "body": "${body}"
            }
        },
        {
            "step": 3,
            "action_type": "click",
            "target": "send_button",
            "parameters": {}
        }
    ],
    
    # WITH: Tools required
    "tools": {
        "required": ["browser_control", "email_api"],
        "optional": ["file_operations"],
        "settings": {
            "timeout": 30,
            "retry_on_failure": true,
            "parallel_execution": false
        }
    },
    
    # METADATA
    "metadata": {
        "learned_from_videos": 5,
        "confidence": 0.95,
        "success_rate": 0.98,
        "average_execution_time": 45.2,
        "parameters": {
            "recipient": {"type": "email", "required": true},
            "subject": {"type": "string", "required": true},
            "body": {"type": "string", "required": true},
            "attachments": {"type": "list", "required": false}
        },
        "output": {
            "type": "object",
            "properties": {
                "status": "success|failure",
                "timestamp": "sent_time",
                "email_id": "guid"
            }
        },
        "related_guidelines": ["guide_email_read_001", "guide_email_forward_001"],
        "tags": ["email", "communication", "automation"],
        "created_date": "2025-10-31",
        "version": "1.0"
    },
    
    # ERROR HANDLING
    "error_handling": [
        {
            "error_type": "recipient_not_found",
            "recovery_action": "suggest_alternatives",
            "fallback": "notify_user"
        },
        {
            "error_type": "send_failed",
            "recovery_action": "retry_with_backoff",
            "max_retries": 3
        }
    ]
}
```

**Key Methods:**
- `create_guideline(template, conditions, actions)` - Create new guideline
- `merge_guidelines(guideline1, guideline2)` - Combine related guidelines
- `validate_guideline(guideline)` - Check completeness
- `assign_guideline_id(guideline)` - Generate unique ID
- `rank_guidelines_by_confidence()` - Sort by reliability

---

### **4. Parameter Schema Generator (parameter_schema.py)**

**Purpose:** Generate schemas for template parameters

**Schema Types:**

**Type 1: Simple Parameters**
```json
{
    "recipient_email": {
        "type": "string",
        "description": "Email address of recipient",
        "required": true,
        "example": "user@example.com",
        "validation": "email_format"
    }
}
```

**Type 2: Complex Parameters**
```json
{
    "email_content": {
        "type": "object",
        "required": true,
        "properties": {
            "to": {"type": "string", "required": true},
            "cc": {"type": "array", "items": {"type": "string"}, "required": false},
            "bcc": {"type": "array", "items": {"type": "string"}, "required": false},
            "subject": {"type": "string", "required": true},
            "body": {"type": "string", "required": true},
            "attachments": {"type": "array", "items": {"type": "file"}, "required": false}
        }
    }
}
```

**Type 3: Enumerated Parameters**
```json
{
    "action_type": {
        "type": "enum",
        "required": true,
        "values": ["compose", "reply", "forward", "draft"],
        "default": "compose"
    }
}
```

**Key Methods:**
- `generate_schema_from_template(template)` - Create schema from template
- `infer_parameter_type(values)` - Determine parameter type
- `create_validation_rules(parameter)` - Generate validation
- `generate_examples(parameter)` - Create example values
- `merge_schemas(schema1, schema2)` - Combine related schemas

---

### **5. Guideline Library Manager (guideline_library.py)**

**Purpose:** Manage persistent guideline database

**Library Structure:**
```
guidelines/
├── guidelines.db              (SQLite database)
├── guidelines_index.json      (Quick lookup index)
├── guidelines/
│   ├── email_guidelines.json
│   ├── browser_guidelines.json
│   ├── system_guidelines.json
│   └── ... (categorized)
└── metadata/
    ├── statistics.json
    ├── usage_stats.json
    └── performance_metrics.json
```

**Key Methods:**
- `save_guideline(guideline)` - Persist to DB
- `load_guideline(guideline_id)` - Retrieve from DB
- `search_guidelines(query)` - Find matching guidelines
- `list_guidelines_by_category(category)` - Browse by type
- `get_relevant_guidelines(user_query)` - Smart matching
- `update_guideline_confidence(guideline_id, performance)` - Learn success rates
- `get_guideline_statistics()` - Usage analytics
- `export_guidelines(format)` - Export to JSON/YAML

**Query Examples:**
```python
# Find guidelines for email tasks
email_guides = library.search_guidelines("email")

# Get all guidelines in browser category
browser_guides = library.list_guidelines_by_category("browser")

# Find guides relevant to user's query
matching_guides = library.get_relevant_guidelines("I need to send an email")

# Update success rate after execution
library.update_guideline_confidence("guide_email_001", success=True)
```

**Library Index Format:**
```json
{
    "total_guidelines": 45,
    "categories": {
        "email": 12,
        "browser": 18,
        "system": 10,
        "file_operations": 5
    },
    "guidelines": [
        {
            "id": "guide_email_001",
            "name": "Email Composition",
            "category": "email",
            "confidence": 0.95,
            "usage_count": 23,
            "success_rate": 0.98,
            "tags": ["email", "compose"]
        }
    ]
}
```

---

### **6. Template Compiler (template_compiler.py)**

**Purpose:** Convert guidelines to executable code/actions

**Compilation Process:**
```
Guideline (JSON)
       ↓
Template Compiler
  ├─ Parse condition
  ├─ Generate execution code
  ├─ Setup parameter binding
  ├─ Add error handling
  └─ Create execution plan
       ↓
Executable Action Plan
```

**Key Methods:**
- `compile_guideline(guideline)` - Convert to executable
- `generate_execution_plan(guideline)` - Step-by-step plan
- `bind_parameters(template, params)` - Substitute values
- `generate_code(guideline, language='python')` - Generate Python code
- `validate_compiled_template()` - Check compilation success

**Example Compilation Output:**
```python
# Input: Guideline for email composition
# Output: Compiled execution plan

async def execute_email_composition(recipient, subject, body):
    """
    Compiled from: guide_email_composition_001
    Confidence: 95%
    """
    try:
        # Step 1: Verify preconditions
        assert app_is_open("Gmail"), "Gmail not open"
        
        # Step 2: Click compose
        await browser.click("compose_button")
        await sleep(2)
        
        # Step 3: Fill email form
        await browser.type("to_field", recipient)
        await browser.type("subject_field", subject)
        await browser.type("body_field", body)
        
        # Step 4: Send
        await browser.click("send_button")
        await sleep(1)
        
        # Step 5: Verify success
        assert email_sent(), "Email send failed"
        
        return {
            "status": "success",
            "timestamp": datetime.now(),
            "guideline_used": "guide_email_composition_001"
        }
    
    except AssertionError as e:
        logger.error(f"Precondition failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Email composition failed: {e}")
        await recovery_action("notify_user", {"error": str(e)})
        raise
```

---

## 📊 Expected Output per Video

**Input:** Phase 3 analysis (1000+ frames, 50-200 actions, 5-20 patterns)

**Output:**
```
templates_and_guidelines/
├── 20250831_122345/
│   ├── templates/
│   │   ├── email_composition_template.json
│   │   ├── browser_navigation_template.json
│   │   └── ... (extracted templates)
│   ├── guidelines/
│   │   ├── email_guidelines.json
│   │   ├── browser_guidelines.json
│   │   └── ... (extracted guidelines)
│   ├── conditions/
│   │   ├── trigger_conditions.json
│   │   ├── state_conditions.json
│   │   └── prerequisites.json
│   ├── parameter_schemas/
│   │   ├── email_params.json
│   │   ├── browser_params.json
│   │   └── common_params.json
│   └── compiled/
│       ├── guide_email_001.py
│       ├── guide_browser_001.py
│       └── ... (executable guidelines)
└── library/
    ├── guidelines.db             (SQLite)
    ├── guidelines_index.json     (Quick lookup)
    └── statistics.json           (Usage stats)
```

**Statistics per typical 30-minute video:**
- Templates extracted: 8-15
- Guidelines generated: 10-25
- Parameters identified: 30-80
- Conditions extracted: 15-40
- Compiled guides: 10-25
- Library size: 50-100 KB
- Compilation time: 5-15 minutes

---

## 🧪 Testing Strategy

**Test Categories:**

1. **Template Extraction Tests**
   - Extract templates from known patterns
   - Verify parameter identification
   - Test template generalization
   - Check template uniqueness

2. **Condition Analysis Tests**
   - Extract trigger conditions
   - Identify prerequisites
   - Find conflict conditions
   - Test condition normalization

3. **Guideline Building Tests**
   - Create guidelines from templates
   - Verify guideline structure
   - Test condition-action pairing
   - Validate tool requirements

4. **Parameter Schema Tests**
   - Generate schemas from templates
   - Test schema validation
   - Verify parameter types
   - Check validation rules

5. **Library Management Tests**
   - Save/load guidelines
   - Search functionality
   - Category filtering
   - Statistics tracking

6. **Compilation Tests**
   - Compile guidelines to code
   - Verify execution plans
   - Test parameter binding
   - Check error handling

7. **Integration Tests**
   - End-to-end template generation
   - Multi-phase guideline creation
   - Library population
   - Guideline execution

**Expected Test Results:**
- 35-50 unit tests
- 85%+ code coverage
- All tests passing
- Template extraction: > 90% accuracy
- Guideline compilation: > 95% success

---

## 🔄 Integration with Guidelines Pattern (X Post)

This phase directly implements the Guidelines Pattern from the Akshay Pachaar tweet:

```python
# Phase 4 Implementation of Guidelines Pattern

agent.create_guideline(
    guideline_id="guide_email_and_browser_001",
    condition="Customer asks about 'Return laptop + warranty'",
    actions=[
        {"action": "search_return_policy"},
        {"action": "search_warranty_policy"}
    ],
    tools=["browser", "email", "knowledge_base"]
)

# Instead of routing to single agent:
# OLD: Route to Returns Agent OR Warranty Agent
# NEW: Load both guidelines simultaneously
# RESULT: Coherent response covering both topics
```

---

## 📈 Performance Considerations

**Optimization Strategies:**

1. **Parallel Processing**
   - Process multiple patterns simultaneously
   - Parallel template extraction
   - Concurrent guideline generation

2. **Caching**
   - Cache extracted templates
   - Cache condition analysis
   - Cache compiled guidelines

3. **Incremental Updates**
   - Process new videos incrementally
   - Merge new guidelines with existing
   - Update library without full rebuild

4. **Library Optimization**
   - Index guidelines by category
   - Search indexing for fast lookup
   - Compression for storage

**Performance Targets:**
- Template extraction: < 1 minute
- Condition analysis: < 1 minute
- Guideline generation: < 2 minutes
- Library operations: < 100 ms

---

## 🔄 Integration Points

**Input from Phase 3:**
- Action descriptions
- Pattern library
- Context relationships
- Tool usage statistics
- Confidence scores

**Output to Phase 5:**
- Template library
- Guidelines library (SQLite DB)
- Parameter schemas
- Compiled execution plans
- Guideline index
- Usage statistics

**Enables Phase 5:**
- Multi-topic query handling via multiple guidelines
- Dynamic tool loading based on guidelines
- Context-aware routing using conditions
- Learned behavior patterns

---

## 📝 Implementation Checklist

- [ ] Create `template_extractor.py` with pattern-to-template conversion
- [ ] Create `condition_analyzer.py` with condition extraction
- [ ] Create `guideline_builder.py` with guideline schema implementation
- [ ] Create `parameter_schema.py` with schema generation
- [ ] Create `guideline_library.py` with database management
- [ ] Create `template_compiler.py` with execution plan generation
- [ ] Implement SQLite database for guideline persistence
- [ ] Create unit tests (40+ tests)
- [ ] Test on Phase 3 analysis output
- [ ] Generate templates from sample video
- [ ] Build complete guideline library
- [ ] Test guideline compilation
- [ ] Optimize database queries
- [ ] Create library statistics/analytics
- [ ] Document template format
- [ ] Document guideline schema
- [ ] Commit to git with detailed documentation

---

## ⏱️ Timeline Estimate

- **Week 1:** Template extraction + conditions (3-4 days)
- **Week 1-2:** Guideline building (2-3 days)
- **Week 2:** Parameter schemas + compilation (2-3 days)
- **Week 2:** Library management (2-3 days)
- **Week 3:** Testing & optimization (2-3 days)
- **Week 3:** Integration & documentation (2-3 days)

**Total: 2-3 weeks**

---

## 🎓 Success Criteria

✅ Extract 8-15 templates per 30-min video  
✅ Generate 10-25 guidelines per video  
✅ Identify 80%+ of action parameters  
✅ Extract 90%+ of trigger conditions  
✅ All tests passing (40+ tests)  
✅ Template accuracy: > 90%  
✅ Guideline compilation success: > 95%  
✅ Library operations: < 100 ms query time  
✅ Output ready for Phase 5 (multi-topic handling)  

---

## 📚 Resources & References

- JSON Schema: https://json-schema.org/
- SQLite: https://www.sqlite.org/docs.html
- Pattern Mining: https://en.wikipedia.org/wiki/Data_mining
- Workflow Automation: https://github.com/langchain-ai/langgraph
- Guidelines Pattern: https://github.com/emcie-co/parlant

---

## 🚀 Next Steps

1. ✅ Review this Phase 4 plan
2. ⏳ Study template extraction techniques
3. ⏳ Begin implementation: Template extractor
4. ⏳ Implement condition analyzer
5. ⏳ Build guideline builder
6. ⏳ Create parameter schema generator
7. ⏳ Implement library management
8. ⏳ Build template compiler
9. ⏳ Create comprehensive tests
10. ⏳ Generate templates from Phase 3 data
11. ⏳ Optimize and document
12. 🎯 Move to Phase 5: Full Integration

