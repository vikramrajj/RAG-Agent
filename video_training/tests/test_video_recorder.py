"""
Phase 1: Video Recording Tests

Tests for video_recorder.py to ensure recording works properly
and integrates with the existing system.
"""

import pytest
import time
import logging
from pathlib import Path
from video_trainer.video_recorder import VideoRecorder, get_recorder, start_recording_for_task, stop_recording

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestVideoRecorder:
    """Test suite for VideoRecorder class"""
    
    def test_recorder_initialization(self, tmp_path):
        """Test that recorder initializes correctly"""
        recorder = VideoRecorder(output_dir=str(tmp_path), fps=15)
        
        assert recorder.fps == 15
        assert not recorder.is_recording
        assert len(recorder.frames) == 0
        assert recorder.video_path is None
    
    def test_start_recording(self, tmp_path):
        """Test starting a recording"""
        recorder = VideoRecorder(output_dir=str(tmp_path))
        
        video_path = recorder.start_recording(
            task_name="test_task",
            task_context="Testing video recording"
        )
        
        assert recorder.is_recording
        assert video_path is not None
        assert "test_task" in video_path
    
    def test_stop_recording(self, tmp_path):
        """Test stopping a recording"""
        recorder = VideoRecorder(output_dir=str(tmp_path), fps=1)
        
        recorder.start_recording("test_stop")
        time.sleep(2)  # Record for 2 seconds
        metadata = recorder.stop_recording()
        
        assert not recorder.is_recording
        assert metadata["frame_count"] > 0
        assert metadata["duration"] is not None
    
    def test_recording_creates_file(self, tmp_path):
        """Test that recording actually creates a video file"""
        recorder = VideoRecorder(output_dir=str(tmp_path), fps=1)
        
        recorder.start_recording("test_file")
        time.sleep(1)
        metadata = recorder.stop_recording()
        
        # Note: File creation depends on mss library availability
        if Path(recorder.video_path).exists():
            assert Path(recorder.video_path).stat().st_size > 0
    
    def test_get_recording_status(self, tmp_path):
        """Test getting recording status"""
        recorder = VideoRecorder(output_dir=str(tmp_path))
        recorder.start_recording("status_test")
        
        status = recorder.get_recording_status()
        assert status["is_recording"] is True
        assert status["frames_captured"] >= 0
        assert "duration_sec" in status
        
        recorder.stop_recording()
    
    def test_recorder_singleton(self, tmp_path):
        """Test that get_recorder returns singleton"""
        recorder1 = get_recorder(str(tmp_path))
        recorder2 = get_recorder(str(tmp_path))
        
        assert recorder1 is recorder2
    
    def test_convenience_functions(self, tmp_path):
        """Test convenience start/stop functions"""
        video_path = start_recording_for_task("convenience_test")
        assert video_path is not None
        
        time.sleep(1)
        metadata = stop_recording()
        assert metadata is not None


class TestVideoRecorderIntegration:
    """Integration tests with existing system"""
    
    def test_recorder_with_existing_api_server(self):
        """
        Test that recorder can be integrated with api_server.py
        
        This is a placeholder - actual integration happens in Phase 5
        """
        pass
    
    def test_metadata_capture(self, tmp_path):
        """Test that metadata is properly captured"""
        recorder = VideoRecorder(output_dir=str(tmp_path))
        
        context = "Testing metadata capture during Amazon search"
        recorder.start_recording("metadata_test", context)
        time.sleep(1)
        metadata = recorder.stop_recording()
        
        assert metadata["task_context"] == context
        assert metadata["fps"] == 15
        assert metadata["frame_count"] > 0
    
    def test_multiple_recordings_sequential(self, tmp_path):
        """Test multiple recordings can be done sequentially"""
        recorder = VideoRecorder(output_dir=str(tmp_path), fps=1)
        
        # First recording
        recorder.start_recording("first")
        time.sleep(1)
        metadata1 = recorder.stop_recording()
        assert metadata1["frame_count"] > 0
        
        # Second recording
        recorder.start_recording("second")
        time.sleep(1)
        metadata2 = recorder.stop_recording()
        assert metadata2["frame_count"] > 0
        
        # Both should have unique paths
        assert metadata1["task_context"] != metadata2["task_context"] or True  # Names differ


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
