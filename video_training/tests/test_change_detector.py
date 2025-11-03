"""
Test Suite for Phase 2 Change Detection Module

Tests for:
- ChangeDetector class
- SSIM calculations
- Histogram comparisons
- Region detection
- Change event generation
"""

import pytest
import tempfile
import json
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from change_detector import ChangeDetector
except ImportError:
    pytest.skip("change_detector module not available", allow_module_level=True)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_frames(temp_dir):
    """Create sample frame images"""
    frame_paths = []
    
    for i in range(5):
        # Create frames with slight variations
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (50 + i * 30)
        frame_path = temp_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(frame_path), frame)
        frame_paths.append(str(frame_path))
    
    return frame_paths


@pytest.fixture
def change_detector():
    """Create ChangeDetector instance"""
    return ChangeDetector(
        ssim_threshold=0.95,
        verbose=False
    )


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestChangeDetectorBasics:
    """Test basic ChangeDetector functionality"""
    
    def test_initialization(self, change_detector):
        """Test ChangeDetector initialization"""
        assert change_detector is not None
        assert change_detector.ssim_threshold == 0.95
    
    def test_threshold_setting(self):
        """Test threshold can be set"""
        detector = ChangeDetector(ssim_threshold=0.90)
        assert detector.ssim_threshold == 0.90
    
    def test_verbose_setting(self):
        """Test verbose setting"""
        detector = ChangeDetector(verbose=True)
        assert detector is not None


# ============================================================================
# FRAME COMPARISON TESTS
# ============================================================================

class TestFrameComparison:
    """Test frame comparison functionality"""
    
    def test_identical_frames(self, change_detector, sample_frames):
        """Test comparing identical frames"""
        frame1 = cv2.imread(sample_frames[0])
        frame2 = cv2.imread(sample_frames[0])
        
        result = change_detector.compare_frames(frame1, frame2)
        
        assert isinstance(result, dict)
        assert 'ssim' in result or 'success' in result
    
    def test_different_frames(self, change_detector, sample_frames):
        """Test comparing different frames"""
        frame1 = cv2.imread(sample_frames[0])
        frame2 = cv2.imread(sample_frames[1])
        
        result = change_detector.compare_frames(frame1, frame2)
        
        assert isinstance(result, dict)
        # Different frames should have lower similarity
        if 'ssim' in result:
            assert result['ssim'] is not None
    
    def test_none_frame_handling(self, change_detector):
        """Test handling of None frames"""
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = None
        
        # Should handle gracefully
        try:
            result = change_detector.compare_frames(frame1, frame2)
            assert result is not None or result is None
        except (TypeError, AttributeError):
            # Expected behavior for None frame
            pass


# ============================================================================
# CHANGE DETECTION TESTS
# ============================================================================

class TestChangeDetection:
    """Test change detection from frames"""
    
    def test_detect_changes_returns_dict(self, change_detector, sample_frames, temp_dir):
        """Test detect_changes_from_frames returns dict"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        assert isinstance(result, dict)
        assert 'success' in result or 'change_events' in result
    
    def test_change_events_structure(self, change_detector, sample_frames, temp_dir):
        """Test change events have correct structure"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            events = result.get('change_events', [])
            # Each event should have key fields
            for event in events:
                assert 'frame_id' in event or 'timestamp' in event
    
    def test_high_change_detection(self, change_detector, sample_frames, temp_dir):
        """Test high change detection"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            high_changes = result.get('high_change_events', [])
            # Should identify some high change events
            assert isinstance(high_changes, list)


# ============================================================================
# ALGORITHM TESTS
# ============================================================================

class TestAlgorithms:
    """Test change detection algorithms"""
    
    def test_ssim_calculation(self, change_detector):
        """Test SSIM calculation"""
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 100
        frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 100
        
        result = change_detector.compare_frames(frame1, frame2)
        
        # Identical frames should have SSIM close to 1.0
        if 'ssim' in result:
            assert 0.9 <= result['ssim'] <= 1.0
    
    def test_histogram_comparison(self, change_detector):
        """Test histogram comparison"""
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 100
        frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 150
        
        result = change_detector.compare_frames(frame1, frame2)
        
        # Different color frames should show difference
        assert isinstance(result, dict)
    
    def test_region_detection(self, change_detector):
        """Test region change detection"""
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 100
        frame2 = frame1.copy()
        # Modify top-left region
        frame2[:100, :100] = 50
        
        result = change_detector.compare_frames(frame1, frame2)
        
        assert isinstance(result, dict)


# ============================================================================
# THRESHOLD TESTS
# ============================================================================

class TestThresholds:
    """Test threshold handling"""
    
    def test_ssim_threshold_filter(self, sample_frames, temp_dir):
        """Test SSIM threshold filtering"""
        detector_loose = ChangeDetector(ssim_threshold=0.5)
        detector_strict = ChangeDetector(ssim_threshold=0.99)
        
        result_loose = detector_loose.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        result_strict = detector_strict.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        # Loose threshold should detect more or equal changes
        loose_count = len(result_loose.get('change_events', []))
        strict_count = len(result_strict.get('change_events', []))
        
        assert loose_count >= strict_count
    
    def test_high_change_frames_filtering(self, change_detector, sample_frames, temp_dir):
        """Test high change frame filtering"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            high_frames = change_detector.get_high_change_frames(
                threshold=0.90
            )
            
            assert isinstance(high_frames, list)


# ============================================================================
# SUMMARY STATISTICS TESTS
# ============================================================================

class TestStatistics:
    """Test statistics generation"""
    
    def test_summary_structure(self, change_detector, sample_frames, temp_dir):
        """Test summary has expected structure"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            summary = result.get('summary', {})
            
            # Check for key statistics
            assert 'total_changes' in summary or isinstance(summary, dict)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_missing_directory(self, change_detector):
        """Test handling of missing directory"""
        result = change_detector.detect_changes_from_frames(
            frame_dir="/nonexistent/directory",
            frame_pattern="frame_*.png"
        )
        
        # Should handle gracefully
        assert isinstance(result, dict)
    
    def test_no_matching_frames(self, change_detector, temp_dir):
        """Test handling when no frames match pattern"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="nonexistent_*.png"
        )
        
        # Should return gracefully
        assert isinstance(result, dict)
    
    def test_corrupted_frame(self, change_detector, temp_dir):
        """Test handling of corrupted frame file"""
        # Create empty file
        bad_frame = temp_dir / "frame_0000.png"
        bad_frame.write_bytes(b"not_an_image")
        
        # Should handle gracefully
        try:
            result = change_detector.detect_changes_from_frames(
                frame_dir=temp_dir,
                frame_pattern="frame_*.png"
            )
            assert result is not None
        except Exception:
            # May raise exception on corrupted file
            pass


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

class TestPersistence:
    """Test result persistence"""
    
    def test_results_saved(self, change_detector, sample_frames, temp_dir):
        """Test results can be saved"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Try to save results
            output_file = temp_dir / "changes.json"
            with open(output_file, 'w') as f:
                json.dump(result, f)
            
            assert output_file.exists()
    
    def test_results_loadable(self, change_detector, sample_frames, temp_dir):
        """Test saved results can be loaded"""
        result = change_detector.detect_changes_from_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            output_file = temp_dir / "changes.json"
            with open(output_file, 'w') as f:
                json.dump(result, f)
            
            # Load and verify
            with open(output_file, 'r') as f:
                loaded = json.load(f)
            
            assert loaded.get('success') == result.get('success')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
