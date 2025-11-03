"""
Frame Analyzer Module - Phase 2 Orchestrator

Coordinates all frame analysis tasks:
- Frame extraction from videos
- Change detection
- Interaction detection
- Index creation

This module orchestrates the Phase 2 pipeline.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import time

# Handle both relative and absolute imports
try:
    from .frame_extraction import FrameExtractor
    from .change_detector import ChangeDetector
    from .interaction_detector import InteractionDetector
    from .frame_index import FrameIndex, build_frame_index
except (ImportError, ValueError):
    # Fallback for direct imports
    from frame_extraction import FrameExtractor
    from change_detector import ChangeDetector
    from interaction_detector import InteractionDetector
    from frame_index import FrameIndex, build_frame_index

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ============================================================================
# FRAME ANALYZER CLASS
# ============================================================================

class FrameAnalyzer:
    """
    Orchestrates complete Phase 2 frame analysis pipeline.
    
    Handles:
    1. Frame extraction from video
    2. Change detection between frames
    3. Interaction detection
    4. Index creation
    5. Results persistence
    
    Attributes:
        video_path (str): Path to source video
        output_dir (Path): Output directory for results
        sampling_rate (int): Frame extraction sampling rate
        ssim_threshold (float): SSIM threshold for change detection
        verbose (bool): Enable verbose logging
    """
    
    def __init__(
        self,
        video_path: str,
        output_dir: Optional[Path] = None,
        sampling_rate: int = 5,
        max_frames: int = 1000,
        ssim_threshold: float = 0.95,
        verbose: bool = True
    ):
        """
        Initialize frame analyzer.
        
        Args:
            video_path: Path to video file
            output_dir: Output directory (default: auto-generated)
            sampling_rate: Frame sampling rate
            max_frames: Maximum frames to extract
            ssim_threshold: SSIM threshold for change detection
            verbose: Enable verbose logging
        """
        self.video_path = video_path
        self.sampling_rate = sampling_rate
        self.max_frames = max_frames
        self.ssim_threshold = ssim_threshold
        self.verbose = verbose
        
        # Generate video ID and output directory
        video_name = Path(video_path).stem
        self.video_id = video_name
        
        if output_dir is None:
            try:
                from .config import FRAME_EXTRACTION_OUTPUT_DIR
            except (ImportError, ValueError):
                from config import FRAME_EXTRACTION_OUTPUT_DIR
            self.output_dir = FRAME_EXTRACTION_OUTPUT_DIR / self.video_id
        else:
            self.output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
        
        self.frame_dir = self.output_dir / "frames"
        self.metadata_dir = self.output_dir / "metadata"
        self.analysis_dir = self.output_dir / "analysis"
        
        # Create directories
        for d in [self.frame_dir, self.metadata_dir, self.analysis_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Results storage
        self.extraction_results = None
        self.change_results = None
        self.interaction_results = None
        self.frame_index = None
        
        self._log(f"Initialized FrameAnalyzer for: {video_path}")
        self._log(f"Output directory: {self.output_dir}")
    
    def _log(self, message: str, level: str = "info"):
        """Log message if verbose is enabled"""
        if self.verbose:
            getattr(logger, level)(message)
    
    def extract_frames(self) -> bool:
        """
        Extract frames from video.
        
        Returns:
            Success status
        """
        try:
            self._log("=== STEP 1: Frame Extraction ===")
            start_time = time.time()
            
            extractor = FrameExtractor(
                video_path=self.video_path,
                output_dir=self.output_dir.parent,
                sampling_rate=self.sampling_rate,
                max_frames=self.max_frames,
                verbose=self.verbose
            )
            
            self.extraction_results = extractor.extract_frames()
            
            if not self.extraction_results['success']:
                self._log("Frame extraction failed", "error")
                return False
            
            elapsed = time.time() - start_time
            self._log(f"Extracted {self.extraction_results['frames_extracted']} frames in {elapsed:.2f}s")
            
            return True
        
        except Exception as e:
            self._log(f"Error during frame extraction: {str(e)}", "error")
            return False
    
    def detect_changes(self) -> bool:
        """
        Detect changes between consecutive frames.
        
        Returns:
            Success status
        """
        if not self.extraction_results:
            self._log("No frames extracted. Run extract_frames() first.", "error")
            return False
        
        try:
            self._log("=== STEP 2: Change Detection ===")
            start_time = time.time()
            
            frame_dir = Path(self.extraction_results['frame_dir'])
            
            detector = ChangeDetector(
                ssim_threshold=self.ssim_threshold,
                verbose=self.verbose
            )
            
            self.change_results = detector.detect_changes_from_frames(
                frame_dir=frame_dir,
                frame_pattern="frame_*.png"
            )
            
            if not self.change_results['success']:
                self._log("Change detection failed", "error")
                return False
            
            elapsed = time.time() - start_time
            summary = self.change_results.get('summary', {})
            self._log(
                f"Detected {summary.get('total_changes', 0)} changes in {elapsed:.2f}s "
                f"(avg={summary.get('average_change', 0):.3f})"
            )
            
            return True
        
        except Exception as e:
            self._log(f"Error during change detection: {str(e)}", "error")
            return False
    
    def detect_interactions(self) -> bool:
        """
        Detect user interactions in frames.
        
        Returns:
            Success status
        """
        if not self.extraction_results:
            self._log("No frames extracted. Run extract_frames() first.", "error")
            return False
        
        try:
            self._log("=== STEP 3: Interaction Detection ===")
            start_time = time.time()
            
            frame_dir = Path(self.extraction_results['frame_dir'])
            
            detector = InteractionDetector(verbose=self.verbose)
            
            self.interaction_results = detector.detect_interactions_in_frames(
                frame_dir=frame_dir,
                frame_pattern="frame_*.png"
            )
            
            if not self.interaction_results['success']:
                self._log("Interaction detection failed", "error")
                return False
            
            elapsed = time.time() - start_time
            summary = self.interaction_results.get('summary', {})
            self._log(
                f"Detected {summary.get('total_interactions', 0)} interactions in {elapsed:.2f}s"
            )
            
            return True
        
        except Exception as e:
            self._log(f"Error during interaction detection: {str(e)}", "error")
            return False
    
    def build_index(self) -> bool:
        """
        Build searchable frame index.
        
        Returns:
            Success status
        """
        if not self.extraction_results:
            self._log("No frames extracted. Run extract_frames() first.", "error")
            return False
        
        try:
            self._log("=== STEP 4: Building Frame Index ===")
            start_time = time.time()
            
            self.frame_index = build_frame_index(
                video_id=self.video_id,
                extraction_results=self.extraction_results,
                change_results=self.change_results or {},
                interaction_results=self.interaction_results or {},
                verbose=self.verbose
            )
            
            elapsed = time.time() - start_time
            stats = self.frame_index.get_statistics()
            self._log(
                f"Index created in {elapsed:.2f}s "
                f"({stats.get('total_frames', 0)} frames, "
                f"{stats.get('high_change_count', 0)} high-change)"
            )
            
            return True
        
        except Exception as e:
            self._log(f"Error building index: {str(e)}", "error")
            return False
    
    def save_results(self) -> bool:
        """
        Save all results to disk.
        
        Returns:
            Success status
        """
        try:
            self._log("=== STEP 5: Saving Results ===")
            
            # Save extraction metadata
            if self.extraction_results:
                with open(self.metadata_dir / "extraction.json", 'w') as f:
                    import json
                    json.dump(self.extraction_results, f, indent=2)
            
            # Save change detection
            if self.change_results:
                with open(self.analysis_dir / "changes.json", 'w') as f:
                    import json
                    json.dump(self.change_results, f, indent=2)
            
            # Save interactions
            if self.interaction_results:
                with open(self.analysis_dir / "interactions.json", 'w') as f:
                    import json
                    json.dump(self.interaction_results, f, indent=2)
            
            # Save frame index
            if self.frame_index:
                self.frame_index.save_to_json(self.metadata_dir / "frame_index.json")
            
            self._log(f"Results saved to: {self.output_dir}")
            return True
        
        except Exception as e:
            self._log(f"Error saving results: {str(e)}", "error")
            return False
    
    def run_full_pipeline(self) -> Dict:
        """
        Run complete Phase 2 analysis pipeline.
        
        Steps:
        1. Extract frames
        2. Detect changes
        3. Detect interactions
        4. Build index
        5. Save results
        
        Returns:
            Analysis results dictionary
        """
        self._log("=" * 60)
        self._log("PHASE 2: FRAME ANALYSIS - FULL PIPELINE")
        self._log("=" * 60)
        
        pipeline_start = time.time()
        
        # Step 1: Extract frames
        if not self.extract_frames():
            return {'success': False, 'error': 'Frame extraction failed'}
        
        # Step 2: Detect changes
        if not self.detect_changes():
            self._log("Continuing without change detection...", "warning")
        
        # Step 3: Detect interactions
        if not self.detect_interactions():
            self._log("Continuing without interaction detection...", "warning")
        
        # Step 4: Build index
        if not self.build_index():
            return {'success': False, 'error': 'Index building failed'}
        
        # Step 5: Save results
        if not self.save_results():
            self._log("Warning: Some results may not have been saved", "warning")
        
        pipeline_elapsed = time.time() - pipeline_start
        
        self._log("=" * 60)
        self._log(f"PIPELINE COMPLETE in {pipeline_elapsed:.2f}s")
        self._log("=" * 60)
        
        return {
            'success': True,
            'video_id': self.video_id,
            'output_dir': str(self.output_dir),
            'frame_dir': str(self.frame_dir),
            'metadata_dir': str(self.metadata_dir),
            'analysis_dir': str(self.analysis_dir),
            'extraction': self.extraction_results,
            'changes': self.change_results,
            'interactions': self.interaction_results,
            'index': self.frame_index.export_summary() if self.frame_index else None,
            'total_time_seconds': pipeline_elapsed
        }
    
    def get_summary(self) -> Dict:
        """Get analysis summary"""
        if not self.frame_index:
            return {'status': 'No analysis results'}
        
        return {
            'video_id': self.video_id,
            'status': 'complete',
            'frames': self.frame_index.export_summary()
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def analyze_video(
    video_path: str,
    output_dir: Optional[Path] = None,
    sampling_rate: int = 5,
    max_frames: int = 1000,
    ssim_threshold: float = 0.95,
    verbose: bool = True
) -> Dict:
    """
    Convenience function to analyze a complete video.
    
    Args:
        video_path: Path to video file
        output_dir: Output directory
        sampling_rate: Frame sampling rate
        max_frames: Maximum frames
        ssim_threshold: SSIM threshold
        verbose: Enable verbose logging
    
    Returns:
        Analysis results dictionary
    """
    analyzer = FrameAnalyzer(
        video_path=video_path,
        output_dir=output_dir,
        sampling_rate=sampling_rate,
        max_frames=max_frames,
        ssim_threshold=ssim_threshold,
        verbose=verbose
    )
    
    return analyzer.run_full_pipeline()


if __name__ == "__main__":
    print("Frame Analyzer Module")
    print("This module is meant to be imported, not run directly.")
