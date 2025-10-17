"""
Video Training Pipeline

Phase 1-5 implementation for video-based learning in RAG Agent.

Quick Start:
    from video_training import VideoRecorder
    
    recorder = VideoRecorder()
    recorder.start_recording("task_name")
    # ... do something ...
    recorder.stop_recording()
"""

from pathlib import Path

__version__ = "0.1.0"
__phase__ = "Phase 1: Video Recording (Active)"

try:
    from .video_recorder import VideoRecorder, get_recorder
    VIDEO_RECORDING_AVAILABLE = True
except ImportError:
    VIDEO_RECORDING_AVAILABLE = False

try:
    from .integration import setup_video_recording, start_execution_recording, stop_execution_recording
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False

try:
    from .config import get_config_summary, is_recording_enabled
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


__all__ = [
    "VideoRecorder",
    "get_recorder",
    "setup_video_recording",
    "start_execution_recording",
    "stop_execution_recording",
    "get_config_summary",
    "is_recording_enabled",
]

# Ensure recordings directory exists
from pathlib import Path
Path("video_training/recordings").mkdir(parents=True, exist_ok=True)
