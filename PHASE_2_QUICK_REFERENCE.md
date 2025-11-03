# Phase 2 Quick Reference Guide

## 🎯 Phase 2 Overview

**Phase 2: Frame Analysis & Extraction**
- Input: MP4 videos from Phase 1 (15-30 FPS, 10-60 minutes)
- Output: 1000+ PNG frames + metadata with changes & interactions detected
- Timeline: Implementation complete, ready for testing
- Status: ✅ 100% code complete (4,420 lines across 10 files)

---

## 🔥 Quick Start

### Running the Full Pipeline

```python
from video_training.frame_analyzer import analyze_video

# Simple one-liner
result = analyze_video(
    video_path="path/to/video.mp4",
    output_dir="path/to/output",
    sampling_rate=5,  # Extract every 5th frame
    verbose=True
)

# Check result
print(f"Success: {result['success']}")
print(f"Frames extracted: {result['extraction']['frames_extracted']}")
print(f"Total time: {result['total_time_seconds']:.2f}s")
```

### Using FrameAnalyzer Directly

```python
from video_training.frame_analyzer import FrameAnalyzer

# Create analyzer
analyzer = FrameAnalyzer(
    video_path="path/to/video.mp4",
    output_dir="path/to/output",
    sampling_rate=5
)

# Run full pipeline
result = analyzer.run_full_pipeline()

# Or run steps individually
analyzer.extract_frames()
analyzer.detect_changes()
analyzer.detect_interactions()
analyzer.build_index()
analyzer.save_results()
```

---

## 📦 Module Quick Reference

### FrameExtractor
**Purpose:** Extract frames from video

**Key Class:** `FrameExtractor`

```python
from video_training.frame_extraction import FrameExtractor

extractor = FrameExtractor(
    video_path="video.mp4",
    output_dir="frames_output",
    sampling_rate=5,           # Extract every 5th frame
    max_frames=1000,           # Max frames to extract
    format='png',              # Output format
    quality=95                 # Quality (1-100)
)

result = extractor.extract_frames()
# result['frame_list'] contains all extracted frames
```

### ChangeDetector
**Purpose:** Detect UI changes between frames

**Key Class:** `ChangeDetector`

```python
from video_training.change_detector import ChangeDetector

detector = ChangeDetector(
    ssim_threshold=0.95,       # Threshold for change detection
    verbose=True
)

result = detector.detect_changes_from_frames(
    frame_dir="frames_output",
    frame_pattern="frame_*.png"
)
# result['change_events'] contains detected changes
# result['summary'] contains statistics
```

**Algorithms:**
- SSIM (Structural Similarity Index): 0.0-1.0 scale
- Histogram comparison: Color distribution changes
- Region analysis: 3x3 grid breakdown

### InteractionDetector
**Purpose:** Detect user interactions (clicks, typing, etc.)

**Key Class:** `InteractionDetector`

```python
from video_training.interaction_detector import InteractionDetector

detector = InteractionDetector(verbose=True)

result = detector.detect_interactions_in_frames(
    frame_dir="frames_output",
    frame_pattern="frame_*.png"
)
# result['interactions'] contains detected interactions
```

**Interaction Types Detected:**
- `typing`: Typing in text fields
- `mouse_movement`: Cursor movement
- `window_focus`: Active window change
- `scroll`: Scrolling motion
- `dialog_popup`: Dialog/popup appearance
- `mouse_position`: Cursor position

### FrameIndex
**Purpose:** Searchable index for frame metadata

**Key Class:** `FrameIndex`

```python
from video_training.frame_index import FrameIndex

index = FrameIndex(video_id="my_video")

# Add frames (usually done by build_frame_index)
index.add_frame(
    frame_id="frame_0000",
    path="path/to/frame.png",
    timestamp=0.0,
    window="App Name",
    change_score=0.5,
    interactions=[]
)

# Query methods
high_change = index.get_high_change_frames(threshold=0.6)
typing_frames = index.get_frames_with_interaction("typing")
timerange = index.get_frames_by_timestamp_range(1.0, 5.0)

# Save/load
index.save_to_json("index.json")
index.load_from_json("index.json")

# Get statistics
stats = index.get_statistics()
print(f"Total frames: {stats['total_frames']}")
print(f"High changes: {stats['high_change_count']}")
```

---

## 📊 Configuration

### Frame Extraction Settings

```python
# In config.py
VIDEO_RECORDING_FPS = 15                          # Recording FPS
FRAME_EXTRACTION_ENABLED = True                   # Enable extraction
FRAME_SAMPLING_RATE = 5                          # Extract every Nth frame
FRAME_MAX_FRAMES = 1000                          # Max frames
FRAME_EXTRACTION_OUTPUT_DIR = Path("frames")     # Output directory
```

### Change Detection Settings

```python
FRAME_CHANGE_THRESHOLD = 15.0                    # SSIM threshold
FRAME_SSIM_THRESHOLD = 0.95                      # Default SSIM threshold
HIGH_CHANGE_THRESHOLD = 0.6                      # High change threshold
```

---

## 🧪 Running Tests

### Run All Tests
```bash
cd "c:\Users\vikra\Downloads\RAG Agent"
pytest video_training/tests/ -v
```

### Run Specific Test Module
```bash
# Frame extraction tests
pytest video_training/tests/test_frame_extraction.py -v

# Change detection tests
pytest video_training/tests/test_change_detector.py -v

# Interaction detection tests
pytest video_training/tests/test_interaction_detector.py -v

# Frame index tests
pytest video_training/tests/test_frame_index.py -v

# Integration tests
pytest video_training/tests/test_frame_analyzer_integration.py -v
```

### Run with Coverage
```bash
pytest video_training/tests/ --cov=video_training --cov-report=html
```

---

## 📁 Output Structure

After running Phase 2 analysis:

```
output_dir/
├── frames/
│   ├── frame_0000.png
│   ├── frame_0001.png
│   ├── frame_0002.png
│   └── ... (all extracted frames)
├── metadata/
│   ├── extraction.json        # Frame extraction metadata
│   ├── frame_index.json       # Searchable frame index
│   └── ...
└── analysis/
    ├── changes.json           # Change detection results
    ├── interactions.json      # Interaction detection results
    └── ...
```

### Frame Index JSON Structure
```json
{
  "video_id": "test_video",
  "total_frames": 120,
  "frames": [
    {
      "id": "frame_0000",
      "path": "path/to/frame.png",
      "timestamp": 0.0,
      "window": "App Name",
      "change_score": 0.5,
      "interactions": ["typing"],
      "tags": []
    },
    ...
  ],
  "statistics": {
    "total_frames": 120,
    "average_change": 0.35,
    "high_change_count": 12
  }
}
```

---

## 🔍 Common Queries

### Get All High-Change Frames
```python
high_changes = index.get_high_change_frames(threshold=0.6)
for frame in high_changes:
    print(f"Frame {frame['id']}: change={frame['change_score']:.2f}")
```

### Get Frames with Typing
```python
typing_frames = index.get_frames_with_interaction("typing")
for frame in typing_frames:
    print(f"Typing at {frame['timestamp']:.1f}s")
```

### Get Frames by Window
```python
chrome_frames = index.get_frames_by_window("Google Chrome")
print(f"Found {len(chrome_frames)} Chrome frames")
```

### Get Frames in Time Range
```python
section = index.get_frames_by_timestamp_range(10.0, 20.0)
print(f"10-20 second section: {len(section)} frames")
```

### Tag Important Frames
```python
index.tag_frame(0, "important")
index.tag_frame(5, "important")
important = index.get_frames_by_tag("important")
```

---

## 🐛 Troubleshooting

### Import Errors
```
ImportError: No module named 'skimage'
```
**Solution:** Install scikit-image
```bash
pip install scikit-image
```

### Video Not Found
```
FileNotFoundError: video.mp4 not found
```
**Solution:** Verify video path exists
```python
from pathlib import Path
assert Path("video.mp4").exists()
```

### Out of Memory
```
MemoryError during frame extraction
```
**Solution:** Reduce max_frames or increase sampling_rate
```python
analyzer = FrameAnalyzer(
    video_path="video.mp4",
    sampling_rate=10,  # Extract every 10th frame
    max_frames=500     # Reduce max frames
)
```

### Slow Processing
**Solution:** Optimize parameters
- Increase `sampling_rate` (extract fewer frames)
- Reduce video resolution before processing
- Use GPU acceleration if available

---

## 📈 Performance Tips

1. **Increase Sampling Rate**
   - `sampling_rate=5` → extract every 5th frame
   - `sampling_rate=10` → extract every 10th frame (faster, less detailed)

2. **Reduce Max Frames**
   - `max_frames=1000` → default
   - `max_frames=500` → faster, covers less video

3. **Pre-process Video**
   - Reduce resolution before extraction
   - Use keyframes only for faster processing

4. **Parallel Processing**
   - Process multiple videos simultaneously
   - Use separate FrameAnalyzer instances

---

## 🔗 API Reference

### FrameAnalyzer

| Method | Purpose | Returns |
|--------|---------|---------|
| `extract_frames()` | Extract frames from video | bool |
| `detect_changes()` | Detect UI changes | bool |
| `detect_interactions()` | Detect user interactions | bool |
| `build_index()` | Build searchable index | bool |
| `save_results()` | Save all results to disk | bool |
| `run_full_pipeline()` | Execute complete workflow | dict |
| `get_summary()` | Get brief summary | dict |

### FrameIndex Query Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_frame(index)` | Get frame by index | dict |
| `get_frames_by_timestamp_range(start, end)` | Query by time | list |
| `get_frames_by_change_score(min, max)` | Query by change | list |
| `get_high_change_frames(threshold)` | Get high-change frames | list |
| `get_frames_with_interaction(type)` | Query by interaction | list |
| `get_frames_by_window(name)` | Query by app/window | list |
| `get_frames_by_tag(tag)` | Query by tag | list |
| `get_statistics()` | Get statistics | dict |
| `save_to_json(path)` | Save to JSON | None |
| `load_from_json(path)` | Load from JSON | None |

---

## 📋 Checklist for Phase 2 Usage

- [ ] Install dependencies: `pip install opencv-python scikit-image numpy pillow`
- [ ] Prepare video file from Phase 1
- [ ] Create output directory
- [ ] Run frame extraction: `analyzer.extract_frames()`
- [ ] Verify frames created in output directory
- [ ] Run change detection: `analyzer.detect_changes()`
- [ ] Check changes.json for detected events
- [ ] Run interaction detection: `analyzer.detect_interactions()`
- [ ] Check interactions.json for user actions
- [ ] Build index: `analyzer.build_index()`
- [ ] Query index to verify data
- [ ] Save results: `analyzer.save_results()`
- [ ] Proceed to Phase 3 (Vision Analysis)

---

## 🚀 Next Steps

1. **Test Phase 2**
   - Run pytest suite
   - Process sample video
   - Verify outputs

2. **Optimize Performance**
   - Profile execution
   - Tune parameters
   - Target: <5 minutes per 30-min video

3. **Prepare for Phase 3**
   - Phase 3 uses high-change frames from Phase 2
   - High-change frames fed to GPT-4V
   - Set up OpenAI API access

---

**Phase 2 Status:** ✅ Implementation Complete - Ready for Testing
**Last Updated:** October 31, 2025
**Version:** 1.0.0
