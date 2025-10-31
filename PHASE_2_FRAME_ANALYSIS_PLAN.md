# Phase 2: Frame Analysis & Extraction

**Duration:** 2-3 weeks | **Status:** Not Started  
**Dependencies:** Phase 1 ✅ Complete  
**Output:** 1000s of frames per video with timestamps, change detection, interaction markers

---

## 📋 Overview

Phase 2 processes the video recordings created in Phase 1 to extract key frames and identify important moments where user interactions occur.

**Goal:** Convert continuous 15-30 FPS video into discrete, analyzed frames suitable for vision analysis in Phase 3.

---

## 🎯 Core Objectives

1. ✅ Extract frames from Phase 1 MP4 videos at strategic intervals
2. ✅ Detect frame changes (UI changes, window switches, mouse movements)
3. ✅ Identify user interaction moments (clicks, typing, scrolling)
4. ✅ Tag frames with metadata (timestamp, event type, confidence score)
5. ✅ Organize extracted frames for Phase 3 vision analysis
6. ✅ Create frame index for efficient retrieval

---

## 🏗️ Architecture

```
Phase 1 Video Recordings
        ↓
   [PHASE 2: Frame Analysis]
        ├─ Video Loader
        ├─ Frame Extractor
        ├─ Change Detector
        ├─ Interaction Detector
        └─ Frame Indexer
        ↓
Extracted Frames + Metadata
        ↓
Phase 3: Vision Analysis
```

---

## 📁 File Structure to Create

```
video_training/
├── frame_analyzer.py          (NEW - Main frame extraction engine)
├── frame_extraction.py        (NEW - Video to frames conversion)
├── change_detector.py         (NEW - Frame change detection)
├── interaction_detector.py    (NEW - User interaction detection)
├── frame_index.py             (NEW - Frame metadata & indexing)
├── tests/
│   └── test_frame_analyzer.py (NEW - Frame analysis tests)
└── config.py                  (EXISTING - Update frame settings)
```

---

## 🔧 Implementation Details

### **1. Frame Extractor (frame_extraction.py)**

**Purpose:** Convert video to individual frames

```
Input:  Phase 1 MP4 video (15-30 FPS, 10-60 minutes)
Process:
  - Use OpenCV to load video
  - Extract frames at:
    * Every Nth frame (frame sampling)
    * Key moment frames (change-based)
    * Interaction frames (detected events)
Output: PNG frames in frames/{video_id}/frames/
```

**Key Methods:**
- `extract_all_frames()` - Full extraction at sampling rate
- `extract_key_frames()` - Only important moments
- `extract_frame_range()` - Specific time range

**Configuration:**
```python
FRAME_SAMPLING_RATE = 5  # Extract every 5th frame (~3 FPS from 15 FPS video)
MAX_FRAMES_PER_VIDEO = 1000  # Limit frames to prevent explosion
FRAME_FORMAT = "png"
FRAME_QUALITY = 95
```

---

### **2. Change Detector (change_detector.py)**

**Purpose:** Identify frames with significant UI changes

**Algorithm:**
- Calculate frame-to-frame difference using:
  * Structural Similarity Index (SSIM)
  * Histogram comparison
  * Contour detection
- Flag frames with > X% change threshold
- Generate "change score" (0.0 to 1.0)

**Key Methods:**
- `detect_changes()` - Find all change moments
- `get_change_score(frame1, frame2)` - Similarity metric
- `get_key_moments()` - Return high-change frames

**Output:**
```json
{
  "frame_id": "frame_0234.png",
  "timestamp": 23.4,
  "change_score": 0.87,
  "event_type": "ui_change",
  "region": "center"
}
```

---

### **3. Interaction Detector (interaction_detector.py)**

**Purpose:** Identify user interactions (clicks, typing, scrolling)

**Techniques:**
- Mouse cursor detection (XOR method, color detection)
- Cursor movement patterns
- Window focus changes (title bar analysis)
- Typing detection (caret/text input field highlights)
- Scroll indicators
- Dialog/popup appearance

**Key Methods:**
- `detect_mouse_events()` - Track cursor
- `detect_typing_regions()` - Find text input
- `detect_window_changes()` - Monitor active window
- `detect_dialogs()` - Find popups/alerts

**Output:**
```json
{
  "frame_id": "frame_0150.png",
  "timestamp": 15.0,
  "interactions": [
    {"type": "mouse_click", "position": [512, 400], "confidence": 0.95},
    {"type": "window_focus_change", "old_window": "Chrome", "new_window": "Outlook"}
  ]
}
```

---

### **4. Frame Indexer (frame_index.py)**

**Purpose:** Create searchable metadata index for all frames

**Index Structure:**
```python
{
  "video_id": "20250831_122345",
  "total_frames": 847,
  "duration_seconds": 85.7,
  "frames": [
    {
      "id": "frame_0000",
      "timestamp": 0.0,
      "path": "frames/20250831_122345/frame_0000.png",
      "change_score": 0.02,
      "interactions": [],
      "window": "Desktop"
    },
    {
      "id": "frame_0235",
      "timestamp": 23.5,
      "path": "frames/20250831_122345/frame_0235.png",
      "change_score": 0.89,
      "interactions": [
        {"type": "mouse_click", "position": [512, 400]}
      ],
      "window": "Chrome - Gmail"
    }
  ]
}
```

**Key Methods:**
- `build_index()` - Create full index from video
- `get_frames_by_change()` - Get high-change frames
- `get_frames_by_time()` - Get frames in time range
- `get_frames_with_interactions()` - Get interaction frames
- `save_index()` - Persist to JSON
- `load_index()` - Load from file

---

### **5. Frame Analyzer (frame_analyzer.py)**

**Purpose:** Orchestrate entire frame analysis process

**Workflow:**
```python
analyzer = FrameAnalyzer(video_path="recordings/video_001.mp4")

# Extract all frames
frames = analyzer.extract_frames()

# Detect changes
analyzer.detect_changes(frames)

# Detect interactions
analyzer.detect_interactions(frames)

# Build index
index = analyzer.build_index()

# Save everything
analyzer.save_results()
```

**Configuration Integration:**
- Read FPS, quality settings from Phase 1 config
- Use consistent frame output directories
- Maintain metadata consistency

---

## 📊 Expected Output per Video

**Input:** 1 video (10-60 minutes at 15 FPS)

**Output:**
```
frames/
├── 20250831_122345/
│   ├── frames/
│   │   ├── frame_0000.png
│   │   ├── frame_0005.png
│   │   ├── frame_0010.png
│   │   └── ... (847 frames)
│   ├── metadata/
│   │   ├── index.json (frame metadata)
│   │   ├── changes.json (change detection results)
│   │   ├── interactions.json (interaction logs)
│   │   └── timeline.json (temporal sequence)
│   └── analysis/
│       ├── change_heatmap.json
│       └── interaction_summary.json
```

**Statistics per typical 30-minute video:**
- Frames extracted: 1000-2000 (depending on sampling)
- High-change frames: 50-200 (significant UI changes)
- Interaction frames: 100-500 (detected user actions)
- Metadata size: 2-5 MB (JSON index)
- Disk space: 500 MB - 2 GB (depending on frame quality)

---

## 🧪 Testing Strategy

**Test Categories:**

1. **Frame Extraction Tests**
   - Extract frames from real Phase 1 video
   - Verify frame count matches expected sampling
   - Check frame format and quality
   - Validate timestamp accuracy

2. **Change Detection Tests**
   - Inject known changes (color changes, window switches)
   - Verify detection sensitivity
   - Test SSIM calculation
   - Validate change scores

3. **Interaction Detection Tests**
   - Detect simulated mouse clicks
   - Find typing regions
   - Identify window changes
   - Test confidence scores

4. **Integration Tests**
   - Full pipeline on sample video
   - Verify index completeness
   - Check metadata consistency
   - Test Phase 2 → Phase 3 data flow

**Expected Test Results:**
- 15-20 unit tests
- 85%+ code coverage
- All tests passing
- Sample video processing: < 2 minutes

---

## 🔍 Key Algorithms

### **Change Detection: SSIM Method**
```
For each consecutive frame pair:
  1. Convert to grayscale
  2. Calculate Structural Similarity Index (SSIM)
  3. If SSIM < threshold (0.95):
     - Flag as change frame
     - Calculate change_score = 1 - SSIM
     - Store change details
```

### **Interaction Detection: Multi-Modal**
```
For each frame:
  1. Detect mouse cursor:
     - Look for system cursor color/shape
     - Track position changes
     - Identify click moments
  
  2. Detect typing:
     - Find text input fields (borders, cursors)
     - Detect caret blinking
     - Identify keyboard activity
  
  3. Detect window changes:
     - Analyze title bar color/text
     - Monitor window dimensions
     - Track focus changes
```

---

## 📈 Performance Considerations

**Optimization Strategies:**

1. **Frame Sampling**
   - Extract every Nth frame (not all frames)
   - Reduces disk space and processing time
   - Captures sufficient temporal information

2. **Lazy Processing**
   - Extract frames first
   - Run change detection asynchronously
   - Run interaction detection on-demand

3. **Parallel Processing**
   - Process multiple videos simultaneously
   - Parallelize frame extraction
   - Batch frame processing

4. **Caching**
   - Cache extracted frames
   - Cache detection results
   - Re-use computations

**Performance Targets:**
- Extract frames: 100-200 FPS (OpenCV optimized)
- Change detection: 50-100 FPS (SSIM optimized)
- Full pipeline: 2-5 minutes per 30-minute video

---

## 🔄 Integration Points

**Input from Phase 1:**
- MP4 video files in `recordings/` directory
- Video metadata (FPS, duration, quality)
- Execution metadata (user, timestamp, action)

**Output to Phase 3:**
- Extracted frames in `frames/` directory
- Frame index JSON for quick lookup
- Metadata for vision analysis context
- Change/interaction markers for attention

---

## 📝 Implementation Checklist

- [ ] Create `frame_extraction.py` with OpenCV integration
- [ ] Create `change_detector.py` with SSIM algorithm
- [ ] Create `interaction_detector.py` with multi-modal detection
- [ ] Create `frame_index.py` with indexing system
- [ ] Create `frame_analyzer.py` as orchestrator
- [ ] Integrate with Phase 1 config system
- [ ] Create unit tests (20+ tests)
- [ ] Create integration tests
- [ ] Process sample Phase 1 video end-to-end
- [ ] Verify output format and metadata
- [ ] Document algorithms and parameters
- [ ] Optimize for performance
- [ ] Handle edge cases (short videos, high-fps videos, etc.)
- [ ] Commit to git with detailed documentation

---

## ⏱️ Timeline Estimate

- **Week 1:** Frame extraction + indexing (2-3 days)
- **Week 1:** Change detection algorithm (2-3 days)
- **Week 2:** Interaction detection (3-4 days)
- **Week 2:** Testing & optimization (2-3 days)
- **Week 3:** Integration & documentation (2-3 days)

**Total: 2-3 weeks**

---

## 🎓 Success Criteria

✅ Extract 1000+ frames per 30-minute video  
✅ Detect 80%+ of real UI changes  
✅ Identify 85%+ of user interactions  
✅ Complete index in < 2 minutes per video  
✅ All tests passing (20+ tests)  
✅ Metadata accurate to 0.1 seconds  
✅ Output ready for Phase 3 (GPT-4V analysis)  

---

## 📚 Resources & References

- OpenCV Python: https://docs.opencv.org/
- SSIM Algorithm: https://en.wikipedia.org/wiki/Structural_similarity
- Image Processing: https://scikit-image.org/
- Video Processing: https://av.readthedocs.io/

---

## 🚀 Next Steps

1. ✅ Review this Phase 2 plan
2. ⏳ Begin implementation: Frame extraction
3. ⏳ Implement change detection
4. ⏳ Implement interaction detection
5. ⏳ Create comprehensive tests
6. ⏳ Process sample videos
7. ⏳ Optimize and document
8. 🎯 Move to Phase 3: Vision Analysis

