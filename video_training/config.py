"""
Video Training Configuration

Centralized configuration for video training pipeline.
Modify this file to control recording behavior, API settings, etc.
"""

import os
from pathlib import Path

# ============================================================================
# PHASE 1: VIDEO RECORDING CONFIGURATION
# ============================================================================

# Enable/disable video recording globally
VIDEO_RECORDING_ENABLED = True

# Record all executions or on-request only
RECORD_ALL_EXECUTIONS = False

# Recording quality settings
VIDEO_RECORDING_FPS = 15  # 15 FPS = good balance, use 30 for high quality
VIDEO_OUTPUT_QUALITY = 85  # 1-100, higher = larger files but better quality
VIDEO_CODEC = "mp4v"  # H.264 video codec

# Output directory for video files
VIDEO_OUTPUT_DIR = Path("video_training/recordings")
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Maximum video length (in seconds) to auto-truncate
MAX_VIDEO_DURATION = 600  # 10 minutes

# Auto-cleanup old recordings (days)
AUTO_CLEANUP_DAYS = 30


# ============================================================================
# PHASE 2-4: LEARNING PIPELINE CONFIGURATION (Future)
# ============================================================================

# Frame extraction settings
FRAME_EXTRACTION_ENABLED = False
FRAME_CHANGE_THRESHOLD = 15.0  # How much change to detect keyframes
FRAME_EXTRACTION_OUTPUT_DIR = Path("video_training/frames")

# Vision model settings (Phase 3)
VISION_MODEL_ENABLED = False
VISION_MODEL = "openai/gpt-4-vision-preview"
VISION_API_KEY = os.getenv("OPENROUTER_API_KEY")
VISION_ANALYSIS_TIMEOUT = 30  # seconds

# Template generation settings (Phase 4)
TEMPLATE_GENERATION_ENABLED = False
TEMPLATE_OUTPUT_DIR = Path("video_training/generated_templates")
AUTO_MERGE_TEMPLATES = False  # Auto-merge with existing templates
TEMPLATE_MIN_CONFIDENCE = 0.7  # Minimum confidence to save template


# ============================================================================
# API SERVER INTEGRATION
# ============================================================================

# Enable video learning via API
VIDEO_LEARNING_API_ENABLED = True

# API endpoint for recording status
RECORDING_STATUS_ENDPOINT = "/api/recording/status"
RECORDING_CONTROL_ENDPOINT = "/api/recording/control"


# ============================================================================
# MONITORING & LOGGING
# ============================================================================

# Log level for video training
VIDEO_TRAINING_LOG_LEVEL = "INFO"

# Track recording metrics
TRACK_METRICS = True
METRICS_OUTPUT_FILE = Path("video_training/metrics.json")

# Auto-generate reports
AUTO_REPORTS = True
REPORTS_DIR = Path("video_training/reports")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_video_output_path(task_name: str) -> str:
    """Get full path for video output"""
    return str(VIDEO_OUTPUT_DIR / f"{task_name}.mp4")


def is_recording_enabled() -> bool:
    """Check if recording is enabled"""
    return VIDEO_RECORDING_ENABLED


def get_config_summary() -> dict:
    """Get configuration summary"""
    return {
        "recording_enabled": VIDEO_RECORDING_ENABLED,
        "record_all": RECORD_ALL_EXECUTIONS,
        "fps": VIDEO_RECORDING_FPS,
        "output_dir": str(VIDEO_OUTPUT_DIR),
        "phase_2_enabled": FRAME_EXTRACTION_ENABLED,
        "phase_3_enabled": VISION_MODEL_ENABLED,
        "phase_4_enabled": TEMPLATE_GENERATION_ENABLED,
        "api_enabled": VIDEO_LEARNING_API_ENABLED
    }


# Ensure output directories exist
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FRAME_EXTRACTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
