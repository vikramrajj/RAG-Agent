"""
Change Detection Module - Phase 2

Detects significant changes between consecutive frames in video.
Uses Structural Similarity Index (SSIM) to identify key moments.

Key Responsibilities:
- Compare consecutive frames
- Calculate change scores (0.0 to 1.0)
- Identify UI changes and interactions
- Tag important frames
- Generate change reports
"""

import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim

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
# DATA STRUCTURES
# ============================================================================

@dataclass
class ChangeEvent:
    """Represents a change event between frames"""
    frame_id: int
    timestamp: float
    change_score: float
    event_type: str  # 'ui_change', 'color_change', 'motion', etc.
    region: Optional[str] = None  # 'center', 'left', 'right', etc.
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'frame_id': self.frame_id,
            'timestamp': self.timestamp,
            'change_score': self.change_score,
            'event_type': self.event_type,
            'region': self.region,
            'confidence': self.confidence
        }


# ============================================================================
# CHANGE DETECTOR CLASS
# ============================================================================

class ChangeDetector:
    """
    Detects changes between consecutive frames.
    
    Uses SSIM (Structural Similarity Index) to measure frame similarity.
    Lower SSIM = more change.
    
    Attributes:
        ssim_threshold (float): SSIM threshold for detecting changes (default: 0.95)
        verbose (bool): Enable verbose logging
    """
    
    def __init__(
        self,
        ssim_threshold: float = 0.95,
        histogram_threshold: float = 0.1,
        verbose: bool = True
    ):
        """
        Initialize change detector.
        
        Args:
            ssim_threshold: SSIM threshold for detecting changes (0.0-1.0)
            histogram_threshold: Histogram comparison threshold
            verbose: Enable verbose logging
        """
        self.ssim_threshold = ssim_threshold
        self.histogram_threshold = histogram_threshold
        self.verbose = verbose
        self.change_events = []
        
        self._log(f"Initialized ChangeDetector: ssim_threshold={ssim_threshold}")
    
    def _log(self, message: str, level: str = "info"):
        """Log message if verbose is enabled"""
        if self.verbose:
            getattr(logger, level)(message)
    
    def _convert_to_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """Convert frame to grayscale for comparison"""
        if len(frame.shape) == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame
    
    def _calculate_ssim(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        """
        Calculate Structural Similarity Index (SSIM) between two frames.
        
        SSIM ranges from -1 to 1:
        - 1 = identical
        - 0 = no similarity
        - -1 = inverse
        
        Args:
            frame1: First frame (grayscale)
            frame2: Second frame (grayscale)
        
        Returns:
            Tuple of (ssim_score, ssim_map)
        """
        try:
            # Ensure frames are same size
            if frame1.shape != frame2.shape:
                frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
            
            # Calculate SSIM
            similarity, ssim_map = ssim(
                frame1,
                frame2,
                full=True,
                data_range=255
            )
            
            return similarity, ssim_map
        
        except Exception as e:
            self._log(f"Error calculating SSIM: {str(e)}", "error")
            return 0.0, np.zeros_like(frame1)
    
    def _calculate_histogram_difference(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> float:
        """
        Calculate histogram difference between frames.
        
        Returns:
            Difference score (0.0 = identical, 1.0 = completely different)
        """
        try:
            hist1 = cv2.calcHist([frame1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([frame2], [0], None, [256], [0, 256])
            
            cv2.normalize(hist1, hist1, alpha=1, beta=0, norm_type=cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, alpha=1, beta=0, norm_type=cv2.NORM_MINMAX)
            
            # Bhattacharyya distance
            distance = cv2.compareHist(
                hist1,
                hist2,
                cv2.HISTCMP_BHATTACHARYYA
            )
            
            return min(distance, 1.0)
        
        except Exception as e:
            self._log(f"Error calculating histogram: {str(e)}", "error")
            return 0.0
    
    def _detect_region(
        self,
        ssim_map: np.ndarray,
        threshold: float = 0.3
    ) -> Optional[str]:
        """
        Detect which region of frame has the most change.
        
        Divides frame into regions and identifies the most changed one.
        
        Args:
            ssim_map: SSIM similarity map
            threshold: Threshold for considering a change
        
        Returns:
            Region name ('center', 'left', 'right', 'top', 'bottom', etc.)
        """
        try:
            if ssim_map is None or ssim_map.size == 0:
                return None
            
            h, w = ssim_map.shape
            
            # Divide into 9 regions (3x3 grid)
            regions = {
                'top_left': ssim_map[:h//3, :w//3],
                'top_center': ssim_map[:h//3, w//3:2*w//3],
                'top_right': ssim_map[:h//3, 2*w//3:],
                'center_left': ssim_map[h//3:2*h//3, :w//3],
                'center': ssim_map[h//3:2*h//3, w//3:2*w//3],
                'center_right': ssim_map[h//3:2*h//3, 2*w//3:],
                'bottom_left': ssim_map[2*h//3:, :w//3],
                'bottom_center': ssim_map[2*h//3:, w//3:2*w//3],
                'bottom_right': ssim_map[2*h//3:, 2*w//3:],
            }
            
            # Find region with most change (lowest average similarity)
            min_region = min(
                regions.items(),
                key=lambda x: np.mean(x[1])
            )
            
            return min_region[0]
        
        except Exception as e:
            self._log(f"Error detecting region: {str(e)}", "error")
            return None
    
    def compare_frames(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
        frame_id: int = 0,
        timestamp: float = 0.0
    ) -> ChangeEvent:
        """
        Compare two frames and detect changes.
        
        Args:
            frame1: First frame (original color)
            frame2: Second frame (original color)
            frame_id: Frame ID for tracking
            timestamp: Frame timestamp in seconds
        
        Returns:
            ChangeEvent with detection results
        """
        # Convert to grayscale
        gray1 = self._convert_to_grayscale(frame1)
        gray2 = self._convert_to_grayscale(frame2)
        
        # Calculate SSIM
        ssim_score, ssim_map = self._calculate_ssim(gray1, gray2)
        
        # Calculate change score (inverse of SSIM)
        change_score = max(0.0, 1.0 - ssim_score)
        
        # Calculate histogram difference
        hist_diff = self._calculate_histogram_difference(gray1, gray2)
        
        # Determine event type
        if change_score > 0.3:
            event_type = "ui_change"
        elif hist_diff > 0.15:
            event_type = "color_change"
        else:
            event_type = "minor_change"
        
        # Detect region
        region = self._detect_region(ssim_map) if ssim_score < 0.98 else None
        
        # Create event
        event = ChangeEvent(
            frame_id=frame_id,
            timestamp=timestamp,
            change_score=change_score,
            event_type=event_type,
            region=region,
            confidence=min(change_score, 1.0)
        )
        
        return event
    
    def detect_changes_from_frames(
        self,
        frame_dir: Path,
        frame_pattern: str = "frame_*.png"
    ) -> Dict:
        """
        Detect changes from a directory of frame files.
        
        Args:
            frame_dir: Directory containing frame files
            frame_pattern: Pattern for frame files (glob)
        
        Returns:
            Detection results dictionary
        """
        self._log(f"Detecting changes from frames in: {frame_dir}")
        
        # Get all frame files
        frame_files = sorted(frame_dir.glob(frame_pattern))
        
        if not frame_files:
            self._log(f"No frames found in {frame_dir}", "warning")
            return {'success': False, 'error': 'No frames found'}
        
        self._log(f"Found {len(frame_files)} frames")
        
        change_events = []
        previous_frame = None
        
        for i, frame_file in enumerate(frame_files):
            try:
                # Load frame
                frame = cv2.imread(str(frame_file))
                
                if frame is None:
                    self._log(f"Failed to load frame: {frame_file}", "warning")
                    continue
                
                # Compare with previous frame
                if previous_frame is not None:
                    event = self.compare_frames(
                        previous_frame,
                        frame,
                        frame_id=i,
                        timestamp=i * 0.1  # Approximate timestamp
                    )
                    change_events.append(event)
                    
                    # Log significant changes
                    if event.change_score > self.ssim_threshold:
                        self._log(
                            f"Frame {i}: Change detected (score={event.change_score:.3f}, "
                            f"type={event.event_type}, region={event.region})"
                        )
                
                previous_frame = frame
            
            except Exception as e:
                self._log(f"Error processing frame {i}: {str(e)}", "error")
                continue
        
        self.change_events = change_events
        
        self._log(f"Detected {len(change_events)} change events")
        
        return {
            'success': True,
            'total_frames': len(frame_files),
            'change_events': [e.to_dict() for e in change_events],
            'summary': self._generate_summary(change_events)
        }
    
    def get_high_change_frames(
        self,
        threshold: Optional[float] = None
    ) -> List[ChangeEvent]:
        """
        Get frames with changes above threshold.
        
        Args:
            threshold: Change score threshold (default: self.ssim_threshold)
        
        Returns:
            List of high-change events
        """
        threshold = threshold or self.ssim_threshold
        return [e for e in self.change_events if e.change_score > threshold]
    
    def _generate_summary(self, events: List[ChangeEvent]) -> Dict:
        """Generate summary statistics"""
        if not events:
            return {
                'total_changes': 0,
                'average_change': 0.0,
                'max_change': 0.0,
                'min_change': 0.0,
                'event_types': {}
            }
        
        scores = [e.change_score for e in events]
        event_types = {}
        for e in events:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1
        
        return {
            'total_changes': len(events),
            'average_change': float(np.mean(scores)),
            'max_change': float(np.max(scores)),
            'min_change': float(np.min(scores)),
            'event_types': event_types
        }
    
    def save_results(self, output_path: Path) -> bool:
        """
        Save detection results to JSON.
        
        Args:
            output_path: Path to save results
        
        Returns:
            Success status
        """
        try:
            results = {
                'config': {
                    'ssim_threshold': self.ssim_threshold,
                    'histogram_threshold': self.histogram_threshold
                },
                'events': [e.to_dict() for e in self.change_events],
                'summary': self._generate_summary(self.change_events)
            }
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            self._log(f"Results saved: {output_path}")
            return True
        
        except Exception as e:
            self._log(f"Error saving results: {str(e)}", "error")
            return False
    
    def get_results_summary(self) -> Dict:
        """Get summary of detection results"""
        return self._generate_summary(self.change_events)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_changes(
    frame_dir: Path,
    ssim_threshold: float = 0.95,
    frame_pattern: str = "frame_*.png",
    verbose: bool = True
) -> Dict:
    """
    Convenience function to detect changes from frames.
    
    Args:
        frame_dir: Directory containing frame files
        ssim_threshold: SSIM threshold for detecting changes
        frame_pattern: Pattern for frame files
        verbose: Enable verbose logging
    
    Returns:
        Detection results dictionary
    """
    detector = ChangeDetector(ssim_threshold=ssim_threshold, verbose=verbose)
    return detector.detect_changes_from_frames(frame_dir, frame_pattern)


if __name__ == "__main__":
    print("Change Detection Module")
    print("This module is meant to be imported, not run directly.")
