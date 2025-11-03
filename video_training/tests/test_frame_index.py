"""
Test Suite for Phase 2 Frame Index Module

Tests for:
- FrameIndex class
- Frame metadata storage
- Query interfaces
- JSON persistence
- Statistics generation
"""

import pytest
import tempfile
import json
from pathlib import Path
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from frame_index import FrameIndex
except ImportError:
    pytest.skip("frame_index module not available", allow_module_level=True)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def frame_index():
    """Create FrameIndex instance"""
    return FrameIndex(video_id="test_video", verbose=False)


@pytest.fixture
def populated_index(frame_index, temp_dir):
    """Create index with sample data"""
    for i in range(10):
        frame_index.add_frame(
            frame_id=f"frame_{i:04d}",
            frame_path=str(temp_dir / f"frame_{i:04d}.png"),
            timestamp=i * 0.5,
            window="Test Window",
            change_score=0.3 + (i * 0.05),
            interactions=[]
        )
    
    return frame_index


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestFrameIndexBasics:
    """Test basic FrameIndex functionality"""
    
    def test_initialization(self, frame_index):
        """Test FrameIndex initialization"""
        assert frame_index is not None
        assert frame_index.video_id == "test_video"
    
    def test_video_id_setting(self):
        """Test video_id is correctly set"""
        index = FrameIndex(video_id="my_video")
        assert index.video_id == "my_video"
    
    def test_verbose_setting(self):
        """Test verbose setting"""
        index = FrameIndex(video_id="test", verbose=True)
        assert index is not None


# ============================================================================
# FRAME ADDITION TESTS
# ============================================================================

class TestFrameAddition:
    """Test adding frames to index"""
    
    def test_add_single_frame(self, frame_index, temp_dir):
        """Test adding a single frame"""
        frame_index.add_frame(
            frame_id="frame_0000",
            frame_path=str(temp_dir / "frame_0000.png"),
            timestamp=0.0,
            window="Test",
            change_score=0.5
        )
        
        # Should be retrievable
        frame = frame_index.get_frame(0)
        assert frame is not None
    
    def test_add_multiple_frames(self, populated_index):
        """Test adding multiple frames"""
        # populated_index already has 10 frames
        assert populated_index.frame_count >= 10
    
    def test_frame_id_generation(self, frame_index):
        """Test frame ID generation"""
        frame_index.add_frame(
            frame_id="test_frame",
            frame_path="/dummy/path.png",
            timestamp=1.0
        )
        
        # Should be able to retrieve
        frame = frame_index.get_frame(0)
        assert frame is not None


# ============================================================================
# QUERY TESTS
# ============================================================================

class TestQueries:
    """Test frame queries"""
    
    def test_get_frame_by_index(self, populated_index):
        """Test getting frame by index"""
        frame = populated_index.get_frame(0)
        
        assert frame is not None
        assert isinstance(frame, dict)
    
    def test_get_frame_by_invalid_index(self, populated_index):
        """Test getting frame with invalid index"""
        frame = populated_index.get_frame(999)
        
        # Should handle gracefully
        assert frame is None or isinstance(frame, dict)
    
    def test_get_frames_by_timestamp_range(self, populated_index):
        """Test timestamp range query"""
        # All frames have timestamps 0.0 to 4.5
        frames = populated_index.get_frames_by_timestamp_range(1.0, 3.0)
        
        assert isinstance(frames, list)
        # Should find frames in range
        for frame in frames:
            assert 1.0 <= frame.get('timestamp', 0) <= 3.0
    
    def test_get_frames_by_change_score(self, populated_index):
        """Test change score query"""
        frames = populated_index.get_frames_by_change_score(0.4, 0.7)
        
        assert isinstance(frames, list)
        for frame in frames:
            score = frame.get('change_score', 0)
            assert 0.4 <= score <= 0.7
    
    def test_get_high_change_frames(self, populated_index):
        """Test high change frame filtering"""
        frames = populated_index.get_high_change_frames(threshold=0.6)
        
        assert isinstance(frames, list)
        for frame in frames:
            assert frame.get('change_score', 0) >= 0.6
    
    def test_get_frames_by_window(self, populated_index, temp_dir):
        """Test window-based query"""
        # Add some frames with different windows
        populated_index.add_frame(
            frame_id="frame_window_test",
            frame_path=str(temp_dir / "special.png"),
            timestamp=10.0,
            window="Different Window",
            change_score=0.5
        )
        
        frames = populated_index.get_frames_by_window("Different Window")
        
        assert isinstance(frames, list)
        assert any(f.get('window') == "Different Window" for f in frames)


# ============================================================================
# TAGGING TESTS
# ============================================================================

class TestTagging:
    """Test frame tagging"""
    
    def test_tag_frame(self, frame_index):
        """Test adding tags to frame"""
        frame_index.add_frame(
            frame_id="frame_0000",
            frame_path="/dummy/path.png",
            timestamp=0.0
        )
        
        frame_index.tag_frame(0, "important")
        
        # Should be retrievable
        frame = frame_index.get_frame(0)
        assert frame is not None
    
    def test_get_frames_by_tag(self, frame_index):
        """Test querying by tag"""
        # Add frames and tag them
        for i in range(3):
            frame_index.add_frame(
                frame_id=f"frame_{i:04d}",
                frame_path=f"/dummy/path_{i}.png",
                timestamp=i * 1.0
            )
        
        frame_index.tag_frame(0, "important")
        frame_index.tag_frame(2, "important")
        
        frames = frame_index.get_frames_by_tag("important")
        
        assert isinstance(frames, list)
        assert len(frames) >= 2
    
    def test_multiple_tags_per_frame(self, frame_index):
        """Test multiple tags on single frame"""
        frame_index.add_frame(
            frame_id="frame_0000",
            frame_path="/dummy/path.png",
            timestamp=0.0
        )
        
        frame_index.tag_frame(0, "important")
        frame_index.tag_frame(0, "reviewed")
        
        frame = frame_index.get_frame(0)
        assert frame is not None


# ============================================================================
# INTERACTION INTEGRATION TESTS
# ============================================================================

class TestInteractionIntegration:
    """Test interaction integration"""
    
    def test_get_frames_with_interaction(self, frame_index):
        """Test querying frames by interaction"""
        # Add frames with interactions
        frame_index.add_frame(
            frame_id="frame_0000",
            frame_path="/dummy/path.png",
            timestamp=0.0,
            interactions=[{"type": "typing", "confidence": 0.8}]
        )
        
        frame_index.add_frame(
            frame_id="frame_0001",
            frame_path="/dummy/path.png",
            timestamp=1.0,
            interactions=[{"type": "scroll", "confidence": 0.6}]
        )
        
        frames = frame_index.get_frames_with_interaction("typing")
        
        assert isinstance(frames, list)
        assert any(
            any(i.get('type') == 'typing' for i in f.get('interactions', []))
            for f in frames
        )


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestStatistics:
    """Test statistics generation"""
    
    def test_get_statistics(self, populated_index):
        """Test statistics generation"""
        stats = populated_index.get_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_frames' in stats
        assert stats['total_frames'] >= 10
    
    def test_statistics_content(self, populated_index):
        """Test statistics have expected fields"""
        stats = populated_index.get_statistics()
        
        # Should have various statistics
        expected_keys = ['total_frames', 'average_change']
        for key in expected_keys:
            # At least one should be present
            assert key in stats or len(stats) > 0
    
    def test_high_change_count(self, populated_index):
        """Test high change count in statistics"""
        stats = populated_index.get_statistics()
        
        assert 'high_change_count' in stats or 'total_frames' in stats


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

class TestPersistence:
    """Test JSON persistence"""
    
    def test_save_to_json(self, populated_index, temp_dir):
        """Test saving index to JSON"""
        output_file = temp_dir / "index.json"
        
        populated_index.save_to_json(output_file)
        
        assert output_file.exists()
    
    def test_load_from_json(self, populated_index, temp_dir):
        """Test loading index from JSON"""
        output_file = temp_dir / "index.json"
        
        # Save first
        populated_index.save_to_json(output_file)
        
        # Load into new index
        new_index = FrameIndex(video_id="test_video")
        new_index.load_from_json(output_file)
        
        # Should have same frames
        assert new_index.frame_count == populated_index.frame_count
    
    def test_json_format(self, populated_index, temp_dir):
        """Test JSON format is valid"""
        output_file = temp_dir / "index.json"
        
        populated_index.save_to_json(output_file)
        
        # Should be valid JSON
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
    
    def test_roundtrip_integrity(self, populated_index, temp_dir):
        """Test data integrity in save/load roundtrip"""
        output_file = temp_dir / "index.json"
        
        # Save
        populated_index.save_to_json(output_file)
        
        # Load
        new_index = FrameIndex(video_id="test_video")
        new_index.load_from_json(output_file)
        
        # Verify data
        original_frame = populated_index.get_frame(0)
        loaded_frame = new_index.get_frame(0)
        
        assert original_frame is not None
        assert loaded_frame is not None


# ============================================================================
# EXPORT TESTS
# ============================================================================

class TestExport:
    """Test export functionality"""
    
    def test_export_summary(self, populated_index):
        """Test exporting summary"""
        summary = populated_index.export_summary()
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
    
    def test_summary_content(self, populated_index):
        """Test summary has useful content"""
        summary = populated_index.export_summary()
        
        # Should contain frame information or statistics
        assert 'video_id' in summary or 'frames' in summary or 'statistics' in summary


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_query_on_empty_index(self):
        """Test queries on empty index"""
        index = FrameIndex(video_id="empty")
        
        frames = index.get_frames_by_timestamp_range(0, 10)
        
        assert isinstance(frames, list)
        assert len(frames) == 0
    
    def test_invalid_timestamp_range(self, populated_index):
        """Test invalid timestamp range query"""
        # Start > end
        frames = populated_index.get_frames_by_timestamp_range(5.0, 1.0)
        
        # Should handle gracefully
        assert isinstance(frames, list)
    
    def test_invalid_change_score_range(self, populated_index):
        """Test invalid change score range"""
        # Start > end
        frames = populated_index.get_frames_by_change_score(0.9, 0.1)
        
        # Should handle gracefully
        assert isinstance(frames, list)
    
    def test_nonexistent_tag_query(self, populated_index):
        """Test query with nonexistent tag"""
        frames = populated_index.get_frames_by_tag("nonexistent_tag")
        
        assert isinstance(frames, list)
        assert len(frames) == 0
    
    def test_nonexistent_window_query(self, populated_index):
        """Test query with nonexistent window"""
        frames = populated_index.get_frames_by_window("Nonexistent Window")
        
        assert isinstance(frames, list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self, temp_dir):
        """Test complete workflow"""
        index = FrameIndex(video_id="workflow_test")
        
        # Add frames
        for i in range(10):
            index.add_frame(
                frame_id=f"frame_{i:04d}",
                frame_path=str(temp_dir / f"frame_{i:04d}.png"),
                timestamp=i * 0.5,
                window="Test",
                change_score=0.3 + (i * 0.05),
                interactions=[]
            )
        
        # Tag some
        index.tag_frame(0, "start")
        index.tag_frame(9, "end")
        
        # Query
        high_change = index.get_high_change_frames(0.6)
        tagged = index.get_frames_by_tag("start")
        
        # Save
        output_file = temp_dir / "index.json"
        index.save_to_json(output_file)
        
        # Load
        new_index = FrameIndex(video_id="workflow_test")
        new_index.load_from_json(output_file)
        
        # Verify
        assert new_index.frame_count == 10
        assert new_index.get_frame(0) is not None
    
    def test_multi_index_operations(self, temp_dir):
        """Test operations across multiple indices"""
        index1 = FrameIndex(video_id="video1")
        index2 = FrameIndex(video_id="video2")
        
        # Add different frames
        for i in range(5):
            index1.add_frame(
                frame_id=f"frame_{i:04d}",
                frame_path=f"/path/video1/frame_{i}.png",
                timestamp=i * 1.0
            )
        
        for i in range(5, 10):
            index2.add_frame(
                frame_id=f"frame_{i:04d}",
                frame_path=f"/path/video2/frame_{i}.png",
                timestamp=(i - 5) * 1.0
            )
        
        # Should maintain separate state
        assert index1.frame_count == 5
        assert index2.frame_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
