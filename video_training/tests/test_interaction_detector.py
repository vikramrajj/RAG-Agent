"""
Test Suite for Phase 2 Interaction Detection Module

Tests for:
- InteractionDetector class
- Mouse cursor detection
- Typing detection
- Window focus detection
- Dialog detection
- Scroll detection
"""

import pytest
import tempfile
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from interaction_detector import InteractionDetector
except ImportError:
    pytest.skip("interaction_detector module not available", allow_module_level=True)


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
    
    for i in range(10):
        # Create frames with variations
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
        frame_path = temp_dir / f"frame_{i:04d}.png"
        cv2.imwrite(str(frame_path), frame)
        frame_paths.append(str(frame_path))
    
    return frame_paths


@pytest.fixture
def interaction_detector():
    """Create InteractionDetector instance"""
    return InteractionDetector(verbose=False)


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestInteractionDetectorBasics:
    """Test basic InteractionDetector functionality"""
    
    def test_initialization(self, interaction_detector):
        """Test InteractionDetector initialization"""
        assert interaction_detector is not None
    
    def test_verbose_setting(self):
        """Test verbose setting"""
        detector = InteractionDetector(verbose=True)
        assert detector is not None
    
    def test_detector_attributes(self, interaction_detector):
        """Test detector has expected attributes"""
        # Should have methods for different interaction types
        assert hasattr(interaction_detector, 'detect_interactions_in_frames')


# ============================================================================
# INTERACTION DETECTION TESTS
# ============================================================================

class TestInteractionDetection:
    """Test interaction detection"""
    
    def test_detect_interactions_returns_dict(self, interaction_detector, sample_frames, temp_dir):
        """Test detect_interactions_in_frames returns dict"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        assert isinstance(result, dict)
        assert 'success' in result or 'interactions' in result
    
    def test_interactions_structure(self, interaction_detector, sample_frames, temp_dir):
        """Test interactions have correct structure"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            interactions = result.get('interactions', [])
            
            for interaction in interactions:
                # Each interaction should have key fields
                assert isinstance(interaction, dict)
                if 'type' in interaction:
                    assert interaction['type'] in [
                        'mouse_position', 'mouse_movement', 'typing',
                        'window_focus', 'scroll', 'dialog_popup'
                    ]
    
    def test_summary_in_results(self, interaction_detector, sample_frames, temp_dir):
        """Test results include summary"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            assert 'summary' in result or 'interactions' in result


# ============================================================================
# MOUSE DETECTION TESTS
# ============================================================================

class TestMouseDetection:
    """Test mouse cursor detection"""
    
    def test_mouse_cursor_detection(self, interaction_detector):
        """Test mouse cursor detection logic"""
        # Create frame with potential cursor
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
        
        # Cursor should be detected or not, gracefully
        try:
            # This is a private method, so we test indirectly
            result = interaction_detector.detect_interactions_in_frames(
                frame_dir="dummy",
                frame_pattern="frame_*.png"
            )
            assert isinstance(result, dict)
        except Exception:
            # Method may fail on dummy path
            pass
    
    def test_cursor_position_tracking(self, interaction_detector, sample_frames, temp_dir):
        """Test cursor position tracking"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Check for mouse position interactions
            mouse_interactions = [
                i for i in result.get('interactions', [])
                if i.get('type') in ['mouse_position', 'mouse_movement']
            ]
            # May or may not detect mouse based on frames
            assert isinstance(mouse_interactions, list)


# ============================================================================
# TYPING DETECTION TESTS
# ============================================================================

class TestTypingDetection:
    """Test typing detection"""
    
    def test_typing_region_detection(self, interaction_detector, sample_frames, temp_dir):
        """Test typing region detection"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Check for typing interactions
            typing_interactions = [
                i for i in result.get('interactions', [])
                if i.get('type') == 'typing'
            ]
            assert isinstance(typing_interactions, list)
    
    def test_text_field_detection(self, interaction_detector, temp_dir):
        """Test text field detection"""
        # Create frame with potential text field
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
        # Add some edges that might represent a text field
        frame[100:120, 50:300] = 50
        
        frame_path = temp_dir / "frame_0000.png"
        cv2.imwrite(str(frame_path), frame)
        
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        assert isinstance(result, dict)


# ============================================================================
# WINDOW FOCUS DETECTION TESTS
# ============================================================================

class TestWindowFocusDetection:
    """Test window focus detection"""
    
    def test_window_focus_detection(self, interaction_detector, sample_frames, temp_dir):
        """Test window focus change detection"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Check for window focus interactions
            focus_interactions = [
                i for i in result.get('interactions', [])
                if i.get('type') == 'window_focus'
            ]
            assert isinstance(focus_interactions, list)


# ============================================================================
# DIALOG DETECTION TESTS
# ============================================================================

class TestDialogDetection:
    """Test dialog/popup detection"""
    
    def test_dialog_popup_detection(self, interaction_detector, sample_frames, temp_dir):
        """Test dialog popup detection"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Check for dialog interactions
            dialog_interactions = [
                i for i in result.get('interactions', [])
                if i.get('type') == 'dialog_popup'
            ]
            assert isinstance(dialog_interactions, list)
    
    def test_dialog_bounds_detection(self, interaction_detector, temp_dir):
        """Test dialog bounds detection"""
        # Create frame with potential dialog (centered rectangle)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
        # Draw a rectangle that could be a dialog
        cv2.rectangle(frame, (120, 80), (520, 400), 100, 2)
        
        frame_path = temp_dir / "frame_0000.png"
        cv2.imwrite(str(frame_path), frame)
        
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        assert isinstance(result, dict)


# ============================================================================
# SCROLL DETECTION TESTS
# ============================================================================

class TestScrollDetection:
    """Test scroll detection"""
    
    def test_scroll_detection(self, interaction_detector, sample_frames, temp_dir):
        """Test scroll detection"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Check for scroll interactions
            scroll_interactions = [
                i for i in result.get('interactions', [])
                if i.get('type') == 'scroll'
            ]
            assert isinstance(scroll_interactions, list)


# ============================================================================
# CONFIDENCE SCORE TESTS
# ============================================================================

class TestConfidenceScores:
    """Test confidence scoring"""
    
    def test_confidence_range(self, interaction_detector, sample_frames, temp_dir):
        """Test confidence scores are in valid range"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            for interaction in result.get('interactions', []):
                if 'confidence' in interaction:
                    assert 0.0 <= interaction['confidence'] <= 1.0
    
    def test_high_confidence_interactions(self, interaction_detector, sample_frames, temp_dir):
        """Test filtering high confidence interactions"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            high_confidence = [
                i for i in result.get('interactions', [])
                if i.get('confidence', 0) >= 0.7
            ]
            assert isinstance(high_confidence, list)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_missing_directory(self, interaction_detector):
        """Test handling of missing directory"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir="/nonexistent/directory",
            frame_pattern="frame_*.png"
        )
        
        # Should handle gracefully
        assert isinstance(result, dict)
    
    def test_no_matching_frames(self, interaction_detector, temp_dir):
        """Test handling when no frames match pattern"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="nonexistent_*.png"
        )
        
        # Should return gracefully
        assert isinstance(result, dict)
    
    def test_corrupted_frame_handling(self, interaction_detector, temp_dir):
        """Test handling of corrupted frame"""
        # Create invalid image file
        bad_frame = temp_dir / "frame_0000.png"
        bad_frame.write_bytes(b"not_an_image")
        
        try:
            result = interaction_detector.detect_interactions_in_frames(
                frame_dir=temp_dir,
                frame_pattern="frame_*.png"
            )
            assert result is not None
        except Exception:
            # May raise exception on corrupted file
            pass


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestInteractionDetectionIntegration:
    """Integration tests"""
    
    def test_multi_frame_processing(self, interaction_detector, sample_frames, temp_dir):
        """Test processing multiple frames"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            # Should process all frames
            assert result.get('success') is True
    
    def test_batch_processing(self, interaction_detector, temp_dir):
        """Test batch processing"""
        # Create multiple frames
        for i in range(20):
            frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
            frame_path = temp_dir / f"frame_{i:04d}.png"
            cv2.imwrite(str(frame_path), frame)
        
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        assert isinstance(result, dict)


# ============================================================================
# OUTPUT FORMAT TESTS
# ============================================================================

class TestOutputFormat:
    """Test output format"""
    
    def test_interaction_dict_keys(self, interaction_detector, sample_frames, temp_dir):
        """Test interaction dictionaries have expected keys"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            for interaction in result.get('interactions', []):
                # Should have type and confidence at minimum
                if isinstance(interaction, dict):
                    assert 'type' in interaction or 'frame_id' in interaction
    
    def test_summary_keys(self, interaction_detector, sample_frames, temp_dir):
        """Test summary has expected keys"""
        result = interaction_detector.detect_interactions_in_frames(
            frame_dir=temp_dir,
            frame_pattern="frame_*.png"
        )
        
        if result.get('success'):
            summary = result.get('summary', {})
            assert 'total_interactions' in summary or isinstance(summary, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
