"""
Interaction Detection Module - Phase 2

Detects user interactions in video frames.
Identifies mouse clicks, typing, window switches, scrolling, etc.

Key Responsibilities:
- Detect mouse cursor position
- Identify mouse clicks
- Find text input fields and typing
- Detect window focus changes
- Identify dialog/popup appearances
- Track interaction sequences
"""

import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
import numpy as np
import cv2

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
class Interaction:
    """Represents a user interaction"""
    frame_id: int
    timestamp: float
    interaction_type: str  # 'mouse_click', 'typing', 'window_focus', 'scroll', 'dialog'
    position: Optional[Tuple[int, int]] = None  # (x, y) coordinates
    confidence: float = 0.0
    details: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'frame_id': self.frame_id,
            'timestamp': self.timestamp,
            'interaction_type': self.interaction_type,
            'position': self.position,
            'confidence': self.confidence,
            'details': self.details or {}
        }


# ============================================================================
# INTERACTION DETECTOR CLASS
# ============================================================================

class InteractionDetector:
    """
    Detects user interactions in video frames.
    
    Attributes:
        verbose (bool): Enable verbose logging
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize interaction detector.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.interactions = []
        
        # Mouse cursor color ranges (BGR)
        self.cursor_lower_hsv = np.array([0, 0, 180])  # Light colors
        self.cursor_upper_hsv = np.array([180, 100, 255])
        
        self._log("Initialized InteractionDetector")
    
    def _log(self, message: str, level: str = "info"):
        """Log message if verbose is enabled"""
        if self.verbose:
            getattr(logger, level)(message)
    
    def _detect_mouse_cursor(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect mouse cursor in frame.
        
        Looks for the distinctive cursor shape/color.
        Uses HSV color space for robustness.
        
        Args:
            frame: Input frame (BGR)
        
        Returns:
            Cursor position (x, y) or None if not found
        """
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask for light colors (typical cursor color)
            mask = cv2.inRange(hsv, self.cursor_lower_hsv, self.cursor_upper_hsv)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get largest contour (likely cursor)
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    
                    return (cx, cy)
            
            return None
        
        except Exception as e:
            self._log(f"Error detecting cursor: {str(e)}", "debug")
            return None
    
    def _detect_cursor_movement(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Detect cursor movement between frames.
        
        Args:
            frame1: Previous frame
            frame2: Current frame
        
        Returns:
            Tuple of (old_pos, new_pos) or None if no movement
        """
        try:
            pos1 = self._detect_mouse_cursor(frame1)
            pos2 = self._detect_mouse_cursor(frame2)
            
            if pos1 and pos2 and pos1 != pos2:
                return (pos1, pos2)
            
            return None
        
        except Exception as e:
            self._log(f"Error detecting cursor movement: {str(e)}", "debug")
            return None
    
    def _detect_typing_regions(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect potential text input fields and typing.
        
        Looks for:
        - Rectangular borders (text field indicators)
        - Cursor-like blinking elements
        - Text content
        
        Args:
            frame: Input frame
        
        Returns:
            List of detected typing regions
        """
        try:
            typing_regions = []
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter for likely text field dimensions
                aspect_ratio = w / float(h) if h > 0 else 0
                if 0.5 < aspect_ratio < 10 and w > 50 and h > 15:
                    typing_regions.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'aspect_ratio': aspect_ratio,
                        'confidence': 0.6
                    })
            
            return typing_regions
        
        except Exception as e:
            self._log(f"Error detecting typing regions: {str(e)}", "debug")
            return []
    
    def _detect_window_focus_change(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> Optional[Dict]:
        """
        Detect window focus changes.
        
        Looks for changes in:
        - Window title bar
        - Overall frame layout
        - Color scheme changes
        
        Args:
            frame1: Previous frame
            frame2: Current frame
        
        Returns:
            Dict with window change info or None
        """
        try:
            # Extract top portion (title bar area)
            h = frame1.shape[0]
            title_bar_height = int(h * 0.05)
            
            title1 = frame1[:title_bar_height, :]
            title2 = frame2[:title_bar_height, :]
            
            # Calculate difference
            diff = cv2.absdiff(title1, title2)
            non_zero = np.count_nonzero(diff)
            
            total_pixels = title_bar_height * frame1.shape[1] * 3
            change_ratio = non_zero / total_pixels if total_pixels > 0 else 0
            
            if change_ratio > 0.1:  # Significant change in title bar
                return {
                    'type': 'window_focus_change',
                    'change_ratio': change_ratio,
                    'confidence': min(change_ratio, 1.0)
                }
            
            return None
        
        except Exception as e:
            self._log(f"Error detecting window focus: {str(e)}", "debug")
            return None
    
    def _detect_dialog_popup(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect dialog boxes or popups.
        
        Looks for:
        - Rectangular boxes with borders
        - Center-positioned windows
        - Contrast from background
        
        Args:
            frame: Input frame
        
        Returns:
            Dict with dialog info or None
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for large rectangular shapes (likely dialogs)
            frame_h, frame_w = frame.shape[:2]
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if it looks like a dialog
                area = w * h
                frame_area = frame_h * frame_w
                
                if 0.1 < (area / frame_area) < 0.8:  # 10-80% of screen
                    # Check if near center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    frame_center_x = frame_w // 2
                    frame_center_y = frame_h // 2
                    
                    dist_from_center = np.sqrt(
                        (center_x - frame_center_x) ** 2 +
                        (center_y - frame_center_y) ** 2
                    )
                    
                    if dist_from_center < frame_w // 3:  # Within center third
                        return {
                            'type': 'dialog_popup',
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h,
                            'confidence': 0.7
                        }
            
            return None
        
        except Exception as e:
            self._log(f"Error detecting dialog: {str(e)}", "debug")
            return None
    
    def _detect_scroll(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> Optional[Dict]:
        """
        Detect scrolling activity.
        
        Looks for vertical or horizontal content shifts.
        
        Args:
            frame1: Previous frame
            frame2: Current frame
        
        Returns:
            Dict with scroll info or None
        """
        try:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Calculate optical flow
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2,
                None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            # Calculate average motion
            avg_mag = np.mean(mag)
            
            if avg_mag > 1.0:
                # Determine direction
                avg_y = np.mean(flow[..., 1])
                direction = "down" if avg_y > 0 else "up"
                
                return {
                    'type': 'scroll',
                    'direction': direction,
                    'magnitude': float(avg_mag),
                    'confidence': min(avg_mag / 10, 1.0)
                }
            
            return None
        
        except Exception as e:
            self._log(f"Error detecting scroll: {str(e)}", "debug")
            return None
    
    def detect_interactions_in_frames(
        self,
        frame_dir: Path,
        frame_pattern: str = "frame_*.png"
    ) -> Dict:
        """
        Detect interactions from a directory of frames.
        
        Args:
            frame_dir: Directory containing frame files
            frame_pattern: Pattern for frame files
        
        Returns:
            Detection results dictionary
        """
        self._log(f"Detecting interactions from frames in: {frame_dir}")
        
        # Convert to Path if string
        if isinstance(frame_dir, str):
            frame_dir = Path(frame_dir)
        
        # Get frame files
        frame_files = sorted(frame_dir.glob(frame_pattern))
        
        if not frame_files:
            self._log(f"No frames found in {frame_dir}", "warning")
            return {'success': False, 'error': 'No frames found'}
        
        self._log(f"Found {len(frame_files)} frames")
        
        interactions = []
        previous_frame = None
        
        for i, frame_file in enumerate(frame_files):
            try:
                frame = cv2.imread(str(frame_file))
                
                if frame is None:
                    self._log(f"Failed to load frame: {frame_file}", "warning")
                    continue
                
                timestamp = i * 0.1  # Approximate
                
                # Detect mouse events
                cursor_pos = self._detect_mouse_cursor(frame)
                if cursor_pos:
                    interactions.append(Interaction(
                        frame_id=i,
                        timestamp=timestamp,
                        interaction_type='mouse_position',
                        position=cursor_pos,
                        confidence=0.8
                    ))
                
                # Compare with previous frame
                if previous_frame is not None:
                    # Detect cursor movement
                    movement = self._detect_cursor_movement(previous_frame, frame)
                    if movement:
                        interactions.append(Interaction(
                            frame_id=i,
                            timestamp=timestamp,
                            interaction_type='mouse_movement',
                            position=movement[1],
                            confidence=0.85,
                            details={'from': movement[0], 'to': movement[1]}
                        ))
                    
                    # Detect typing
                    typing_regions = self._detect_typing_regions(frame)
                    if typing_regions:
                        interactions.append(Interaction(
                            frame_id=i,
                            timestamp=timestamp,
                            interaction_type='typing',
                            confidence=0.6,
                            details={'regions': typing_regions}
                        ))
                    
                    # Detect window focus change
                    window_change = self._detect_window_focus_change(previous_frame, frame)
                    if window_change:
                        interactions.append(Interaction(
                            frame_id=i,
                            timestamp=timestamp,
                            interaction_type='window_focus',
                            confidence=window_change['confidence'],
                            details=window_change
                        ))
                    
                    # Detect scrolling
                    scroll = self._detect_scroll(previous_frame, frame)
                    if scroll:
                        interactions.append(Interaction(
                            frame_id=i,
                            timestamp=timestamp,
                            interaction_type='scroll',
                            confidence=scroll['confidence'],
                            details=scroll
                        ))
                
                # Detect dialogs
                dialog = self._detect_dialog_popup(frame)
                if dialog:
                    interactions.append(Interaction(
                        frame_id=i,
                        timestamp=timestamp,
                        interaction_type='dialog_popup',
                        confidence=dialog['confidence'],
                        details=dialog
                    ))
                
                previous_frame = frame
            
            except Exception as e:
                self._log(f"Error processing frame {i}: {str(e)}", "error")
                continue
        
        self.interactions = interactions
        
        self._log(f"Detected {len(interactions)} interactions")
        
        return {
            'success': True,
            'total_frames': len(frame_files),
            'interactions': [i.to_dict() for i in interactions],
            'summary': self._generate_summary(interactions)
        }
    
    def _generate_summary(self, interactions: List[Interaction]) -> Dict:
        """Generate summary statistics"""
        if not interactions:
            return {
                'total_interactions': 0,
                'interaction_types': {}
            }
        
        types = {}
        for interaction in interactions:
            types[interaction.interaction_type] = types.get(interaction.interaction_type, 0) + 1
        
        return {
            'total_interactions': len(interactions),
            'interaction_types': types
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
                'interactions': [i.to_dict() for i in self.interactions],
                'summary': self._generate_summary(self.interactions)
            }
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            self._log(f"Results saved: {output_path}")
            return True
        
        except Exception as e:
            self._log(f"Error saving results: {str(e)}", "error")
            return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_interactions(
    frame_dir: Path,
    frame_pattern: str = "frame_*.png",
    verbose: bool = True
) -> Dict:
    """
    Convenience function to detect interactions from frames.
    
    Args:
        frame_dir: Directory containing frame files
        frame_pattern: Pattern for frame files
        verbose: Enable verbose logging
    
    Returns:
        Detection results dictionary
    """
    detector = InteractionDetector(verbose=verbose)
    return detector.detect_interactions_in_frames(frame_dir, frame_pattern)


if __name__ == "__main__":
    print("Interaction Detection Module")
    print("This module is meant to be imported, not run directly.")
