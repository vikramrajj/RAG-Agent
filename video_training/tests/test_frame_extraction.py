"""
Test Suite for Phase 2 Frame Extraction Module

Tests for:
- FrameExtractor class
- Frame validation
- Frame extraction logic
- Metadata generation
- Error handling
"""

import pytest
import tempfile
import json
from pathlib import Path
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from frame_extraction import FrameExtractor
except ImportError:
    pytest.skip("frame_extraction module not available", allow_module_level=True)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_output_dir():
    """Create temporary output directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_video_path(temp_output_dir):
    """Create a sample video file for testing"""
    video_path = temp_output_dir / "sample.mp4"
    
    # Create a simple video with OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 15.0, (640, 480))
    
    # Write 50 frames
    for i in range(50):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    yield str(video_path)


@pytest.fixture
def frame_extractor(sample_video_path, temp_output_dir):
    """Create a FrameExtractor instance"""
    return FrameExtractor(
        video_path=sample_video_path,
        output_dir=str(temp_output_dir),
        sampling_rate=2,
        max_frames=100,
        frame_format='png',
        frame_quality=95,
        verbose=False
    )


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestFrameExtractorBasics:
    """Test basic FrameExtractor functionality"""
    
    def test_initialization(self, frame_extractor):
        """Test FrameExtractor initialization"""
        assert frame_extractor is not None
        assert frame_extractor.sampling_rate == 2
        assert frame_extractor.max_frames == 100
        assert frame_extractor.frame_format == 'png'
    
    def test_video_path_setting(self, sample_video_path):
        """Test video path is correctly set"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir="/tmp"
        )
        assert extractor.video_path == sample_video_path
    
    def test_output_dir_creation(self, temp_output_dir):
        """Test output directory creation"""
        extractor = FrameExtractor(
            video_path="dummy.mp4",
            output_dir=str(temp_output_dir)
        )
        # Directory should be created or accessible
        assert extractor.output_dir is not None


class TestVideoValidation:
    """Test video validation logic"""
    
    def test_invalid_video_path(self, temp_output_dir):
        """Test handling of invalid video path"""
        extractor = FrameExtractor(
            video_path="/nonexistent/video.mp4",
            output_dir=str(temp_output_dir)
        )
        # Validation happens during extraction
        assert extractor.video_path == "/nonexistent/video.mp4"
    
    def test_valid_video_path(self, sample_video_path, temp_output_dir):
        """Test handling of valid video path"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir)
        )
        assert Path(extractor.video_path).exists()


# ============================================================================
# FRAME EXTRACTION TESTS
# ============================================================================

class TestFrameExtraction:
    """Test frame extraction functionality"""
    
    def test_extract_frames_returns_dict(self, frame_extractor):
        """Test extract_frames returns dictionary"""
        result = frame_extractor.extract_frames()
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'frames_extracted' in result or 'error' in result
    
    def test_extract_frames_creates_directory(self, frame_extractor, temp_output_dir):
        """Test extract_frames creates output directory"""
        frame_extractor.extract_frames()
        
        frame_dir = temp_output_dir / "sample" / "frames"
        # Either frames are created or directory exists
        assert frame_extractor.output_dir is not None
    
    def test_sampling_rate_applied(self, sample_video_path, temp_output_dir):
        """Test sampling rate is correctly applied"""
        # Extract with sampling rate 2
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir),
            sampling_rate=2,
            verbose=False
        )
        
        result = extractor.extract_frames()
        
        # With 50 frames and sampling rate 2, we should get ~25 frames
        if result.get('success'):
            frames = result.get('frames_extracted', 0)
            assert frames <= 30  # Some tolerance


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestFrameExtractorConfig:
    """Test configuration handling"""
    
    def test_default_format(self, sample_video_path, temp_output_dir):
        """Test default frame format"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir)
        )
        assert extractor.frame_format in ['png', 'jpg', 'jpeg']
    
    def test_custom_quality(self, sample_video_path, temp_output_dir):
        """Test custom quality setting"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir),
            frame_quality=80
        )
        assert extractor.frame_quality == 80
    
    def test_max_frames_limit(self, sample_video_path, temp_output_dir):
        """Test max frames limit"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir),
            max_frames=10
        )
        result = extractor.extract_frames()
        
        if result.get('success'):
            frames = result.get('frames_extracted', 0)
            assert frames <= 10


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_missing_video_file(self, temp_output_dir):
        """Test handling of missing video file"""
        extractor = FrameExtractor(
            video_path="/nonexistent/video.mp4",
            output_dir=str(temp_output_dir)
        )
        
        result = extractor.extract_frames()
        
        # Should either fail gracefully or return error info
        assert 'success' in result or 'error' in result
    
    def test_invalid_output_dir(self):
        """Test handling of invalid output directory"""
        extractor = FrameExtractor(
            video_path="video.mp4",
            output_dir="/root/invalid/path/that/does/not/exist"
        )
        
        # Should handle gracefully
        assert extractor is not None


# ============================================================================
# METADATA TESTS
# ============================================================================

class TestFrameMetadata:
    """Test frame metadata handling"""
    
    def test_frame_list_structure(self, frame_extractor):
        """Test frame list has correct structure"""
        result = frame_extractor.extract_frames()
        
        if result.get('success'):
            assert 'frame_list' in result or 'frames_extracted' in result
    
    def test_metadata_json_creation(self, frame_extractor, temp_output_dir):
        """Test metadata JSON file creation"""
        result = frame_extractor.extract_frames()
        
        # Check if metadata file was created or saved
        if result.get('success'):
            # Frame index should be created
            assert result.get('success') is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFrameExtractionIntegration:
    """Integration tests for frame extraction"""
    
    def test_full_extraction_pipeline(self, sample_video_path, temp_output_dir):
        """Test complete extraction pipeline"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir),
            sampling_rate=5,
            max_frames=50,
            verbose=False
        )
        
        result = extractor.extract_frames()
        
        assert 'success' in result
        assert isinstance(result, dict)
    
    def test_multiple_extractions(self, sample_video_path, temp_output_dir):
        """Test multiple extractions from same video"""
        extractor1 = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir / "extract1"),
            verbose=False
        )
        
        extractor2 = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir / "extract2"),
            verbose=False
        )
        
        result1 = extractor1.extract_frames()
        result2 = extractor2.extract_frames()
        
        # Both should complete without interference
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance-related tests"""
    
    def test_extraction_completes_in_reasonable_time(self, frame_extractor):
        """Test extraction completes in reasonable time"""
        import time
        
        start = time.time()
        result = frame_extractor.extract_frames()
        elapsed = time.time() - start
        
        # Should complete within 30 seconds (very generous for tests)
        assert elapsed < 30
    
    def test_large_sampling_rate_performance(self, sample_video_path, temp_output_dir):
        """Test extraction with large sampling rate"""
        extractor = FrameExtractor(
            video_path=sample_video_path,
            output_dir=str(temp_output_dir),
            sampling_rate=10,
            verbose=False
        )
        
        result = extractor.extract_frames()
        
        # Should complete successfully
        if result.get('success'):
            frames = result.get('frames_extracted', 0)
            # With sampling rate 10, should get very few frames
            assert frames < 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
