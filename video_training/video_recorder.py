"""
Phase 1: Video Recording Module
Records screen during automation tasks for learning

This module captures screen video at configurable FPS and provides
hooks for the learning pipeline to process recordings.
"""

import cv2
import numpy as np
import threading
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class VideoRecorder:
    """
    Records screen/monitor during automation tasks.
    
    Features:
    - Multi-monitor support
    - Configurable FPS and quality
    - Asynchronous recording (non-blocking)
    - Metadata tracking
    - Auto-compression
    """
    
    def __init__(
        self, 
        output_dir: str = "video_training/recordings",
        fps: int = 15,
        quality: int = 85,
        monitor_index: int = 1
    ):
        """
        Initialize video recorder.
        
        Args:
            output_dir: Directory to save video files
            fps: Frames per second (default 15, use 30 for high quality)
            quality: JPEG quality 1-100 (default 85)
            monitor_index: Monitor to record (1 = primary, 2 = secondary)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.fps = fps
        self.quality = quality
        self.monitor_index = monitor_index
        
        self.is_recording = False
        self.frames: List[np.ndarray] = []
        self.video_writer = None
        self.video_path: Optional[str] = None
        
        self.metadata = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "frame_count": 0,
            "fps": fps,
            "resolution": None,
            "task_context": None
        }
        
        # Threading for non-blocking recording
        self.record_thread: Optional[threading.Thread] = None
        self._stop_flag = False
        
        logger.info(f"VideoRecorder initialized: output={output_dir}, fps={fps}")
    
    def start_recording(
        self, 
        task_name: str = "default",
        task_context: str = ""
    ) -> str:
        """
        Start screen recording.
        
        Args:
            task_name: Name/identifier for the task
            task_context: Description of what's being recorded
        
        Returns:
            Path to video file being recorded to
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return self.video_path
        
        self.is_recording = True
        self._stop_flag = False
        self.frames = []
        
        # Reset metadata for new recording
        self.metadata = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "frame_count": 0,
            "fps": self.fps,
            "resolution": None,
            "task_context": None
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = str(self.output_dir / f"{task_name}_{timestamp}.mp4")
        
        self.metadata["start_time"] = datetime.now()
        self.metadata["task_context"] = task_context
        
        logger.info(f"Started recording: {self.video_path}")
        logger.info(f"Task: {task_name} | Context: {task_context}")
        
        # Start recording in background thread
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        
        return self.video_path
    
    def stop_recording(self) -> dict:
        """
        Stop recording and save video file.
        
        Returns:
            Metadata dict with recording information
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return self.metadata
        
        self.is_recording = False
        self._stop_flag = True
        
        # Wait for recording thread to finish
        if self.record_thread:
            self.record_thread.join(timeout=5)
        
        # Save video file
        if self.frames:
            self._save_video()
            logger.info(f"Saved recording: {self.video_path} ({len(self.frames)} frames)")
        else:
            logger.warning("No frames captured")
        
        self.metadata["end_time"] = datetime.now()
        if self.metadata["start_time"]:
            duration = self.metadata["end_time"] - self.metadata["start_time"]
            self.metadata["duration"] = duration.total_seconds()
        
        self.metadata["frame_count"] = len(self.frames)
        
        return self.metadata
    
    def _record_loop(self):
        """Main recording loop - runs in background thread"""
        try:
            from mss import mss
            
            with mss() as sct:
                # Get monitor info
                monitors = sct.monitors
                if self.monitor_index >= len(monitors):
                    logger.warning(f"Monitor {self.monitor_index} not found, using primary")
                    self.monitor_index = 1
                
                monitor = monitors[self.monitor_index]
                frame_interval = 1.0 / self.fps
                last_frame_time = time.time()
                
                logger.debug(f"Recording monitor: {monitor}")
                
                while not self._stop_flag:
                    current_time = time.time()
                    
                    # Capture at target FPS
                    if current_time - last_frame_time >= frame_interval:
                        try:
                            # Capture screen
                            screenshot = sct.grab(monitor)
                            frame = np.array(screenshot)
                            
                            # Convert BGRA to BGR
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                            
                            self.frames.append(frame)
                            last_frame_time = current_time
                            
                            # Store resolution on first frame
                            if not self.metadata["resolution"]:
                                self.metadata["resolution"] = (frame.shape[1], frame.shape[0])
                        
                        except Exception as e:
                            logger.error(f"Frame capture error: {e}")
                    
                    # Small sleep to prevent busy waiting
                    time.sleep(0.001)
        
        except ImportError:
            logger.error("mss library not found. Install with: pip install mss")
        except Exception as e:
            logger.error(f"Recording error: {e}", exc_info=True)
        finally:
            logger.debug("Recording loop ended")
    
    def _save_video(self):
        """Save captured frames to video file"""
        if not self.frames:
            logger.warning("No frames to save")
            return
        
        try:
            height, width = self.frames[0].shape[:2]
            
            # Use H.264 codec
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.video_path,
                fourcc,
                self.fps,
                (width, height)
            )
            
            if not self.video_writer.isOpened():
                logger.error("Failed to open VideoWriter")
                return
            
            # Write all frames
            for frame in self.frames:
                self.video_writer.write(frame)
            
            self.video_writer.release()
            logger.info(f"✅ Video saved: {self.video_path}")
            
        except Exception as e:
            logger.error(f"Error saving video: {e}")
    
    def get_recording_status(self) -> dict:
        """Get current recording status"""
        return {
            "is_recording": self.is_recording,
            "frames_captured": len(self.frames),
            "video_path": self.video_path,
            "duration_sec": (
                (datetime.now() - self.metadata["start_time"]).total_seconds()
                if self.metadata["start_time"] else 0
            ),
            "metadata": self.metadata
        }


# Singleton instance
_recorder: Optional[VideoRecorder] = None


def get_recorder(output_dir: str = "video_training/recordings") -> VideoRecorder:
    """Get or create recorder instance"""
    global _recorder
    if _recorder is None:
        _recorder = VideoRecorder(output_dir=output_dir)
    return _recorder


def start_recording_for_task(task_name: str, context: str = "") -> str:
    """Convenience function to start recording"""
    recorder = get_recorder()
    return recorder.start_recording(task_name, context)


def stop_recording() -> dict:
    """Convenience function to stop recording"""
    recorder = get_recorder()
    return recorder.stop_recording()


if __name__ == "__main__":
    # Test the recorder
    logging.basicConfig(level=logging.INFO)
    
    print("🎥 Starting 5-second test recording...")
    recorder = VideoRecorder(fps=15)
    
    video_path = recorder.start_recording("test_recording", "Testing video recorder")
    print(f"Recording to: {video_path}")
    
    time.sleep(5)
    
    metadata = recorder.stop_recording()
    print(f"\n✅ Recording complete!")
    print(f"Metadata: {metadata}")
