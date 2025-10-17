# 🎬 Video Training Module - Phase 1: Implementation

**Status:** Phase 1 (Video Recording) - ACTIVE  
**Branch:** `video-training-dev`  
**Stable Version:** `working-stable-oct17` (GitHub backup)

---

## 📋 Quick Start

### 1. Activate Video Training (Development)

```bash
cd "c:\Users\vikra\Downloads\RAG Agent"

# Make sure you're on the video-training-dev branch
git branch
git checkout video-training-dev

# Install required dependencies
pip install mss opencv-python
```

### 2. Test Phase 1: Video Recording

```bash
# Run quick test
python video_training/video_recorder.py

# Or run full test suite
pytest video_training/tests/test_video_recorder.py -v
```

### 3. Integrate with API Server (When Ready)

Add this to your `api_server.py`:

```python
from video_training.integration import setup_video_recording, start_execution_recording, stop_execution_recording

# Initialize
setup_video_recording(enable=True)

# In your route handler
@app.post("/api/bridge")
async def handle_message(data: dict):
    learn = data.get("learn_from_execution", False)
    
    if learn:
        start_execution_recording(data.get("message", ""))
    
    # ... existing code ...
    
    if learn:
        stop_execution_recording()
    
    return response
```

---

## 📁 Folder Structure

```
video_training/
├── video_recorder.py        # Phase 1: Screen recording module
├── integration.py           # API server integration
├── config.py               # Configuration (modify this to customize)
├── recordings/             # Video files stored here
├── frames/                 # Phase 2: Extracted frames (future)
├── templates/              # Phase 4: Generated templates (future)
├── tests/
│   ├── test_video_recorder.py      # Phase 1 tests
│   ├── test_frame_analyzer.py      # Phase 2 tests (future)
│   ├── test_vision_parser.py       # Phase 3 tests (future)
│   └── test_template_generator.py  # Phase 4 tests (future)
└── reports/                # Reports and metrics
```

---

## 🚀 Phase 1: Video Recording Module

### What It Does
- Captures screen during automation tasks
- Saves as MP4 video at configurable FPS
- Runs in background (non-blocking)
- Tracks metadata (duration, frames, resolution)

### Features
✅ Multi-monitor support  
✅ Configurable FPS and quality  
✅ Asynchronous recording  
✅ Metadata tracking  
✅ Thread-safe recording  

### Usage

```python
from video_training.video_recorder import VideoRecorder

# Create recorder
recorder = VideoRecorder(fps=15)

# Start recording
video_path = recorder.start_recording(
    task_name="amazon_search",
    task_context="Searching for laptop on Amazon"
)

# ... do your automation task ...

# Stop recording
metadata = recorder.stop_recording()
print(f"Recorded: {metadata['frame_count']} frames in {metadata['duration']} seconds")
```

### Configuration

Edit `video_training/config.py`:

```python
VIDEO_RECORDING_ENABLED = True      # Enable/disable
VIDEO_RECORDING_FPS = 15            # Quality: 15 (fast) to 30 (high)
VIDEO_OUTPUT_QUALITY = 85           # File size: 50 (small) to 95 (large)
VIDEO_OUTPUT_DIR = "video_training/recordings"
```

---

## 📊 Current Status: Phase 1

| Component | Status | Notes |
|-----------|--------|-------|
| VideoRecorder class | ✅ Complete | 350+ lines, production-ready |
| Screen capture | ✅ Complete | Uses mss library |
| MP4 encoding | ✅ Complete | H.264 codec |
| Metadata tracking | ✅ Complete | Duration, frames, resolution |
| Async recording | ✅ Complete | Non-blocking background thread |
| Tests | ✅ Complete | Full test coverage |
| API integration | ✅ Complete | Ready to add to api_server.py |
| Config system | ✅ Complete | Centralized configuration |

---

## 🔄 Git Workflow

### Your Branches

```
main (original)
├── working-stable-oct17 (← SAFE BACKUP, don't touch)
└── video-training-dev (← DEVELOPMENT, work here)
```

### How to Use

```bash
# Always work on video-training-dev
git checkout video-training-dev

# Make changes and commit
git add video_training/
git commit -m "Phase 1: Add video recording feature"

# Push to GitHub
git push

# When ready to merge to main (ask for review first):
git checkout main
git pull
git merge video-training-dev
```

### If Something Breaks

```bash
# Revert to last working version (ALWAYS SAFE)
git checkout working-stable-oct17

# Or reset current branch
git reset --hard HEAD~1  # Undo last commit
```

---

## 🧪 Testing

### Quick Test

```bash
# Test video recording (5 seconds)
python video_training/video_recorder.py

# Check if video was created
ls video_training/recordings/
```

### Full Test Suite

```bash
# Run all Phase 1 tests
pytest video_training/tests/test_video_recorder.py -v

# Run with coverage
pytest video_training/tests/ --cov=video_training --cov-report=html
```

### Integration Test (With API)

```bash
# 1. Start api_server.py
python api_server.py

# 2. Send request with learning enabled
curl -X POST http://localhost:8000/api/bridge \
  -H "Content-Type: application/json" \
  -d '{
    "message": "google search for python tutorial",
    "learn_from_execution": true
  }'

# 3. Check recordings folder
ls video_training/recordings/
```

---

## 📈 What's Next?

### Phase 2 (Frames): 2-3 weeks
- Extract key frames from video
- Detect when UI changes occur
- Prepare for vision analysis

### Phase 3 (Vision): 3-4 weeks
- Analyze frames with GPT-4V
- Extract what action occurred
- Convert to structured data

### Phase 4 (Templates): 2-3 weeks
- Auto-generate action templates
- Merge with existing templates
- Save for future use

### Phase 5 (Integration): 1 week
- Connect all phases
- Automatic learning pipeline
- Metrics and monitoring

---

## 🐛 Troubleshooting

### Issue: "mss module not found"
```bash
pip install mss
```

### Issue: "opencv module not found"
```bash
pip install opencv-python
```

### Issue: Video file not created
- Check `video_training/recordings/` folder exists
- Check disk space available
- Ensure write permissions to folder

### Issue: Poor video quality
- Increase `VIDEO_RECORDING_FPS` (15 → 30)
- Increase `VIDEO_OUTPUT_QUALITY` (85 → 95)
- Check monitor resolution

### Issue: Recording blocks execution
- This should NOT happen (uses background thread)
- If it does, check logs for thread errors

---

## 📝 Development Notes

### Architecture Decisions

1. **Background Threading** - Recording doesn't block main thread
2. **mss Library** - Fastest cross-platform screen capture
3. **H.264 Codec** - Good compression and compatibility
4. **JSON Metadata** - Easy to parse for learning phases

### Performance Targets

- FPS: 15 (balanced) to 30 (high quality)
- Latency: <1ms per frame
- Memory: ~2-3MB per second of video
- CPU: ~10-20% usage during recording

### Future Optimizations

- Hardware acceleration (GPU encoding)
- Adaptive bitrate (compress based on activity)
- Selective frame capture (skip unchanged regions)

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- [x] VideoRecorder class implemented
- [x] Screen capture working
- [x] MP4 encoding working
- [x] Metadata tracking working
- [x] Tests passing
- [x] Integration code ready
- [ ] Successfully integrated into api_server.py

### Ready for Phase 2 When:
- [ ] Stable recordings for 5+ different tasks
- [ ] No performance issues with api_server.py
- [ ] Metadata being captured correctly
- [ ] Videos play back successfully

---

## 📞 Questions?

Refer to main analysis document:
- **RAG_AGENT_VS_VIDEO_TRAINING_ANALYSIS.md** → Phase 1 section
- **ONE_PAGE_VISUAL_SUMMARY.md** → Quick overview

---

**Branch:** video-training-dev  
**Status:** Phase 1 Implementation Active  
**Last Updated:** October 17, 2025
