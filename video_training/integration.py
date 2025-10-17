"""
Phase 1 Integration: Video Recording with API Server

This module integrates the video recorder into the existing api_server.py
to record automation tasks for learning.

Usage:
    from video_training.integration import setup_video_recording
    
    # In your api_server.py initialization:
    setup_video_recording(enable=True, record_all=False)
    
    # Then use in your route handlers:
    @app.post("/api/bridge")
    async def handle_message(data: dict):
        record_execution = data.get("learn_from_execution", False)
        
        if record_execution:
            start_execution_recording(data.get("message", ""))
        
        # ... existing code ...
        
        if record_execution:
            stop_execution_recording()
        
        return response
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Import video recorder
try:
    from video_recorder import get_recorder, start_recording_for_task, stop_recording
    VIDEO_RECORDING_AVAILABLE = True
except ImportError:
    logger.warning("video_recorder not available - video learning disabled")
    VIDEO_RECORDING_AVAILABLE = False


class VideoRecordingConfig:
    """Configuration for video recording integration"""
    
    def __init__(
        self,
        enable: bool = True,
        record_all: bool = False,
        record_on_request: bool = True,
        fps: int = 15,
        output_dir: str = "video_training/recordings",
        auto_upload: bool = False
    ):
        """
        Initialize recording config.
        
        Args:
            enable: Enable video recording globally
            record_all: Record all executions (vs on-demand)
            record_on_request: Record when client requests it
            fps: Frames per second for recording
            output_dir: Where to save recordings
            auto_upload: Auto-upload to learning pipeline
        """
        self.enable = enable
        self.record_all = record_all
        self.record_on_request = record_on_request
        self.fps = fps
        self.output_dir = output_dir
        self.auto_upload = auto_upload
        
        self.recordings: Dict[str, Dict[str, Any]] = {}


# Global config
_config: Optional[VideoRecordingConfig] = None


def setup_video_recording(
    enable: bool = True,
    record_all: bool = False,
    fps: int = 15,
    output_dir: str = "video_training/recordings"
) -> bool:
    """
    Setup video recording for the API server.
    
    Call this in your api_server.py initialization.
    
    Args:
        enable: Enable recording
        record_all: Record all executions
        fps: Recording frames per second
        output_dir: Output directory for videos
    
    Returns:
        True if setup successful
    """
    global _config
    
    if not VIDEO_RECORDING_AVAILABLE:
        logger.warning("Video recording not available - skipping setup")
        return False
    
    _config = VideoRecordingConfig(
        enable=enable,
        record_all=record_all,
        fps=fps,
        output_dir=output_dir
    )
    
    logger.info(f"✅ Video recording configured: {output_dir}")
    return True


def start_execution_recording(task_description: str) -> Optional[str]:
    """
    Start recording an execution.
    
    Call at the beginning of task execution.
    
    Args:
        task_description: What's being executed
    
    Returns:
        Video path if recording started, None otherwise
    """
    if not _config or not _config.enable:
        return None
    
    if not VIDEO_RECORDING_AVAILABLE:
        return None
    
    try:
        # Create task name from description
        task_name = task_description[:30].replace(" ", "_").lower()
        
        video_path = start_recording_for_task(
            task_name=task_name,
            context=task_description
        )
        
        logger.info(f"🎥 Started recording: {task_name}")
        
        # Track recording
        if _config:
            _config.recordings[task_name] = {
                "start_time": datetime.now(),
                "video_path": video_path,
                "description": task_description,
                "status": "recording"
            }
        
        return video_path
    
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        return None


def stop_execution_recording() -> Optional[Dict[str, Any]]:
    """
    Stop recording and get metadata.
    
    Call at the end of task execution.
    
    Returns:
        Recording metadata dict
    """
    if not _config or not _config.enable:
        return None
    
    if not VIDEO_RECORDING_AVAILABLE:
        return None
    
    try:
        metadata = stop_recording()
        
        if metadata:
            logger.info(f"✅ Recording complete: {metadata['frame_count']} frames")
            
            # Update tracking
            if _config and metadata.get("task_context"):
                task_key = metadata["task_context"][:30].replace(" ", "_").lower()
                if task_key in _config.recordings:
                    _config.recordings[task_key]["status"] = "completed"
                    _config.recordings[task_key]["metadata"] = metadata
        
        return metadata
    
    except Exception as e:
        logger.error(f"Failed to stop recording: {e}")
        return None


def is_recording_enabled() -> bool:
    """Check if recording is enabled"""
    return _config is not None and _config.enable


def get_recording_status() -> Dict[str, Any]:
    """Get current recording status for all tasks"""
    if not _config:
        return {"enabled": False}
    
    return {
        "enabled": _config.enable,
        "record_all": _config.record_all,
        "fps": _config.fps,
        "output_dir": _config.output_dir,
        "recordings": _config.recordings,
        "total_videos": len(_config.recordings)
    }


# Example integration code (add to api_server.py):
"""
# At the top of api_server.py after imports:
from video_training.integration import (
    setup_video_recording, 
    start_execution_recording,
    stop_execution_recording
)

# In FastAPI app initialization:
app = FastAPI()

# Setup video recording
setup_video_recording(enable=True, record_all=False, fps=15)

# In your route handler:
@app.post("/api/bridge")
async def handle_message(data: dict):
    message = data.get("message", "").strip()
    learn_from_execution = data.get("learn_from_execution", False)
    
    # Start recording if requested
    video_path = None
    if learn_from_execution:
        video_path = start_execution_recording(message)
    
    # ... existing execution code ...
    result = await execute_task(message)
    
    # Stop recording
    if learn_from_execution:
        metadata = stop_execution_recording()
        result["video_metadata"] = metadata
        result["learning_enabled"] = True
    
    return JSONResponse(content=result)

# Optional: Add status endpoint
@app.get("/api/recording/status")
async def get_recording_status_endpoint():
    return get_recording_status()
"""
