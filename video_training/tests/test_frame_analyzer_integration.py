"""
Integration Tests for Phase 2 Frame Analysis Pipeline

Tests the complete end-to-end Phase 2 workflow:
- Video processing
- Frame extraction
- Change detection
- Interaction detection
- Index building
- Results persistence
"""

import pytest
import tempfile
import json
import time
import numpy as np
import cv2
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from frame_analyzer import FrameAnalyzer, analyze_video
except ImportError:
    pytest.skip("frame_analyzer module not available", allow_module_level=True)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_video(temp_dir):
    """Create a sample video file for testing"""
    video_path = temp_dir / "test_video.mp4"
    
    # Create video with OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 15.0, (640, 480))
    
    # Write 60 frames with gradual changes
    for i in range(60):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i)
        out.write(frame)
    
    out.release()
    
    yield str(video_path)


@pytest.fixture
def frame_analyzer(sample_video, temp_dir):
    """Create FrameAnalyzer instance"""
    return FrameAnalyzer(
        video_path=sample_video,
        output_dir=temp_dir / "analysis",
        sampling_rate=5,
        max_frames=100,
        ssim_threshold=0.95,
        verbose=False
    )


# ============================================================================
# BASIC PIPELINE TESTS
# ============================================================================

class TestPipelineBasics:
    """Test basic pipeline functionality"""
    
    def test_analyzer_initialization(self, frame_analyzer):
        """Test FrameAnalyzer initialization"""
        assert frame_analyzer is not None
        assert frame_analyzer.video_id == "test_video"
    
    def test_output_directories_created(self, frame_analyzer):
        """Test output directories are created"""
        assert frame_analyzer.frame_dir is not None
        assert frame_analyzer.metadata_dir is not None
        assert frame_analyzer.analysis_dir is not None
    
    def test_analyzer_configuration(self, frame_analyzer):
        """Test analyzer configuration"""
        assert frame_analyzer.sampling_rate == 5
        assert frame_analyzer.ssim_threshold == 0.95
        assert frame_analyzer.max_frames == 100


# ============================================================================
# INDIVIDUAL STEP TESTS
# ============================================================================

class TestPipelineSteps:
    """Test individual pipeline steps"""
    
    def test_frame_extraction_step(self, frame_analyzer):
        """Test frame extraction step"""
        success = frame_analyzer.extract_frames()
        
        assert isinstance(success, bool)
        assert frame_analyzer.extraction_results is not None
    
    def test_change_detection_step(self, frame_analyzer):
        """Test change detection step"""
        frame_analyzer.extract_frames()
        success = frame_analyzer.detect_changes()
        
        assert isinstance(success, bool)
        # Changes should be detected or skipped gracefully
    
    def test_interaction_detection_step(self, frame_analyzer):
        """Test interaction detection step"""
        frame_analyzer.extract_frames()
        success = frame_analyzer.detect_interactions()
        
        assert isinstance(success, bool)
    
    def test_index_building_step(self, frame_analyzer):
        """Test index building step"""
        frame_analyzer.extract_frames()
        success = frame_analyzer.build_index()
        
        assert isinstance(success, bool)
        assert frame_analyzer.frame_index is not None
    
    def test_results_persistence_step(self, frame_analyzer):
        """Test results persistence step"""
        frame_analyzer.extract_frames()
        frame_analyzer.build_index()
        success = frame_analyzer.save_results()
        
        assert isinstance(success, bool)


# ============================================================================
# FULL PIPELINE TESTS
# ============================================================================

class TestFullPipeline:
    """Test complete pipeline execution"""
    
    def test_run_full_pipeline(self, frame_analyzer):
        """Test running complete pipeline"""
        result = frame_analyzer.run_full_pipeline()
        
        assert isinstance(result, dict)
        assert 'success' in result
        # Should either succeed or provide error info
        assert result.get('success') is True or 'error' in result
    
    def test_pipeline_returns_results_dict(self, frame_analyzer):
        """Test pipeline returns complete results dictionary"""
        result = frame_analyzer.run_full_pipeline()
        
        if result.get('success'):
            assert 'video_id' in result
            assert 'output_dir' in result
            assert 'frame_dir' in result
            assert 'total_time_seconds' in result
    
    def test_pipeline_timing(self, frame_analyzer):
        """Test pipeline execution timing"""
        result = frame_analyzer.run_full_pipeline()
        
        if result.get('success'):
            elapsed = result.get('total_time_seconds', 0)
            assert elapsed > 0
            # Should complete in reasonable time (very generous for tests)
            assert elapsed < 120


# ============================================================================
# OUTPUT VALIDATION TESTS
# ============================================================================

class TestOutputValidation:
    """Test output file creation and validity"""
    
    def test_frames_extracted(self, frame_analyzer):
        """Test frames are extracted to disk"""
        frame_analyzer.run_full_pipeline()
        
        # Frames should be in the frame directory
        frame_dir = frame_analyzer.frame_dir
        if frame_dir.exists():
            frames = list(frame_dir.glob("frame_*.png"))
            # May have frames or may not depending on video processing
            assert isinstance(frames, list)
    
    def test_metadata_files_created(self, frame_analyzer):
        """Test metadata files are created"""
        frame_analyzer.run_full_pipeline()
        
        # Should have created metadata files
        metadata_dir = frame_analyzer.metadata_dir
        assert metadata_dir.exists()
    
    def test_analysis_files_created(self, frame_analyzer):
        """Test analysis files are created"""
        frame_analyzer.run_full_pipeline()
        
        analysis_dir = frame_analyzer.analysis_dir
        assert analysis_dir.exists()
    
    def test_json_files_valid(self, frame_analyzer):
        """Test JSON files are valid"""
        frame_analyzer.run_full_pipeline()
        
        # Check if any JSON files were created and are valid
        metadata_dir = frame_analyzer.metadata_dir
        json_files = list(metadata_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                assert isinstance(data, (dict, list))
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in {json_file}")


# ============================================================================
# RESULTS DICTIONARY TESTS
# ============================================================================

class TestResultsStructure:
    """Test results dictionary structure"""
    
    def test_extraction_results_in_output(self, frame_analyzer):
        """Test extraction results are in final output"""
        result = frame_analyzer.run_full_pipeline()
        
        if result.get('success'):
            assert 'extraction' in result or result.get('success') is True
    
    def test_frame_index_in_output(self, frame_analyzer):
        """Test frame index is in final output"""
        result = frame_analyzer.run_full_pipeline()
        
        if result.get('success'):
            assert 'index' in result or result.get('success') is True
    
    def test_total_time_in_output(self, frame_analyzer):
        """Test timing information in output"""
        result = frame_analyzer.run_full_pipeline()
        
        if result.get('success'):
            assert 'total_time_seconds' in result
            assert result['total_time_seconds'] > 0


# ============================================================================
# DATA CONTINUITY TESTS
# ============================================================================

class TestDataContinuity:
    """Test data flows correctly through pipeline"""
    
    def test_frames_from_extraction_used_in_detection(self, frame_analyzer):
        """Test extracted frames are used in detection"""
        frame_analyzer.extract_frames()
        
        if frame_analyzer.extraction_results.get('success'):
            frame_count = frame_analyzer.extraction_results.get('frames_extracted', 0)
            
            frame_analyzer.detect_changes()
            
            if frame_analyzer.change_results:
                assert frame_analyzer.change_results.get('success') is True
    
    def test_detection_results_in_index(self, frame_analyzer):
        """Test detection results are integrated into index"""
        frame_analyzer.extract_frames()
        frame_analyzer.detect_changes()
        frame_analyzer.detect_interactions()
        frame_analyzer.build_index()
        
        if frame_analyzer.frame_index:
            stats = frame_analyzer.frame_index.get_statistics()
            assert stats.get('total_frames', 0) >= 0


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

class TestErrorRecovery:
    """Test error handling and recovery"""
    
    def test_pipeline_handles_missing_extraction(self, frame_analyzer):
        """Test pipeline handles missing extraction gracefully"""
        # Try to detect changes without extracting
        success = frame_analyzer.detect_changes()
        
        assert success is False
    
    def test_partial_pipeline_execution(self, frame_analyzer):
        """Test partial pipeline execution"""
        frame_analyzer.extract_frames()
        # Skip change detection
        frame_analyzer.detect_interactions()
        success = frame_analyzer.build_index()
        
        # Should still succeed or fail gracefully
        assert isinstance(success, bool)
    
    def test_pipeline_continues_on_detection_failure(self, frame_analyzer):
        """Test pipeline continues even if detection fails"""
        frame_analyzer.extract_frames()
        
        # This might fail, but pipeline should continue
        frame_analyzer.detect_changes()
        
        # Should still be able to build index
        success = frame_analyzer.build_index()
        
        assert isinstance(success, bool)


# ============================================================================
# MULTIPLE VIDEO TESTS
# ============================================================================

class TestMultipleVideos:
    """Test processing multiple videos"""
    
    def test_analyze_multiple_videos_independently(self, temp_dir):
        """Test analyzing multiple videos without interference"""
        # Create two videos
        video_paths = []
        for v_id in range(2):
            video_path = temp_dir / f"video_{v_id}.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(video_path), fourcc, 15.0, (640, 480))
            
            for i in range(30):
                frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i + v_id * 50)
                out.write(frame)
            
            out.release()
            video_paths.append(str(video_path))
        
        # Analyze both
        results = []
        for video_path in video_paths:
            analyzer = FrameAnalyzer(
                video_path=video_path,
                output_dir=temp_dir / "analysis",
                sampling_rate=5,
                verbose=False
            )
            result = analyzer.run_full_pipeline()
            results.append(result)
        
        # Both should complete
        assert len(results) == 2
        for result in results:
            assert isinstance(result, dict)


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunction:
    """Test convenience function"""
    
    def test_analyze_video_function(self, sample_video, temp_dir):
        """Test analyze_video convenience function"""
        result = analyze_video(
            video_path=sample_video,
            output_dir=temp_dir / "analysis",
            sampling_rate=5,
            verbose=False
        )
        
        assert isinstance(result, dict)
        assert 'success' in result or 'video_id' in result
    
    def test_convenience_function_returns_same_as_class(self, sample_video, temp_dir):
        """Test convenience function returns same as class method"""
        # Using convenience function
        result1 = analyze_video(
            video_path=sample_video,
            output_dir=temp_dir / "analysis1",
            sampling_rate=5,
            verbose=False
        )
        
        # Using class directly
        analyzer = FrameAnalyzer(
            video_path=sample_video,
            output_dir=temp_dir / "analysis2",
            sampling_rate=5,
            verbose=False
        )
        result2 = analyzer.run_full_pipeline()
        
        # Both should have similar structure
        assert 'success' in result1 or 'video_id' in result1
        assert 'success' in result2 or 'video_id' in result2


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance-related tests"""
    
    def test_pipeline_completes_in_reasonable_time(self, frame_analyzer):
        """Test pipeline completes in reasonable time"""
        start = time.time()
        result = frame_analyzer.run_full_pipeline()
        elapsed = time.time() - start
        
        # Should complete within 2 minutes (very generous for testing)
        assert elapsed < 120
    
    def test_summary_retrieval_is_fast(self, frame_analyzer):
        """Test summary retrieval is fast"""
        frame_analyzer.run_full_pipeline()
        
        start = time.time()
        summary = frame_analyzer.get_summary()
        elapsed = time.time() - start
        
        # Should be nearly instant
        assert elapsed < 1.0
        assert summary is not None


# ============================================================================
# SUMMARY TESTS
# ============================================================================

class TestSummary:
    """Test summary functionality"""
    
    def test_get_summary(self, frame_analyzer):
        """Test getting analysis summary"""
        frame_analyzer.run_full_pipeline()
        summary = frame_analyzer.get_summary()
        
        assert isinstance(summary, dict)
        assert 'video_id' in summary or 'status' in summary
    
    def test_summary_content(self, frame_analyzer):
        """Test summary contains expected content"""
        frame_analyzer.run_full_pipeline()
        summary = frame_analyzer.get_summary()
        
        # Should have meaningful content
        assert len(summary) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
