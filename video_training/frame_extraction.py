"""
Frame Extraction Module - Phase 2

Extracts frames from MP4 videos created by Phase 1 video recording.
Handles video loading, frame sampling, and frame saving.

Key Responsibilities:
- Load MP4 videos using OpenCV
- Extract frames at configurable sampling rate
- Handle different video formats and resolutions
- Save frames as PNG images with proper naming
- Track extraction metadata (timestamps, frame count, etc.)
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import cv2
import numpy as np

# Handle both relative and absolute imports
try:
    from .config import FRAME_EXTRACTION_OUTPUT_DIR, VIDEO_RECORDING_FPS
except (ImportError, ValueError):
    # Fallback for direct imports
    from config import FRAME_EXTRACTION_OUTPUT_DIR, VIDEO_RECORDING_FPS

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
# FRAME EXTRACTOR CLASS
# ============================================================================

class FrameExtractor:
    """
    Extracts frames from MP4 videos with configurable sampling.
    
    Attributes:
        video_path (str): Path to video file
        output_dir (Path): Directory to save frames
        sampling_rate (int): Extract every Nth frame
        max_frames (int): Maximum frames to extract
        frame_format (str): Output format (png, jpg)
        frame_quality (int): Output quality (1-100)
        verbose (bool): Enable verbose logging
    """
    
    def __init__(
        self,
        video_path: str,
        output_dir: Optional[Path] = None,
        sampling_rate: int = 5,
        max_frames: int = 1000,
        frame_format: str = "png",
        frame_quality: int = 95,
        verbose: bool = True
    ):
        """
        Initialize frame extractor.
        
        Args:
            video_path: Path to video file
            output_dir: Output directory for frames (default: FRAME_EXTRACTION_OUTPUT_DIR)
            sampling_rate: Extract every Nth frame (default: 5)
            max_frames: Maximum frames to extract (default: 1000)
            frame_format: Output format - 'png' or 'jpg' (default: png)
            frame_quality: Output quality 1-100 (default: 95)
            verbose: Enable verbose logging (default: True)
        """
        self.video_path = video_path
        self.output_dir = output_dir or FRAME_EXTRACTION_OUTPUT_DIR
        self.sampling_rate = sampling_rate
        self.max_frames = max_frames
        self.frame_format = frame_format
        self.frame_quality = frame_quality
        self.verbose = verbose
        
        # State tracking
        self.video = None
        self.frame_count = 0
        self.extracted_frames = []
        self.metadata = {}
        
        self._log(f"Initialized FrameExtractor for: {video_path}")
    
    def _log(self, message: str, level: str = "info"):
        """Log message if verbose is enabled"""
        if self.verbose:
            getattr(logger, level)(message)
    
    def _validate_video(self) -> bool:
        """Validate that video file exists and is readable"""
        if not os.path.exists(self.video_path):
            self._log(f"Video file not found: {self.video_path}", "error")
            return False
        
        if not os.path.isfile(self.video_path):
            self._log(f"Not a file: {self.video_path}", "error")
            return False
        
        self._log(f"Video file validated: {self.video_path}")
        return True
    
    def _open_video(self) -> bool:
        """Open video file and validate"""
        try:
            self.video = cv2.VideoCapture(self.video_path)
            
            if not self.video.isOpened():
                self._log("Failed to open video file", "error")
                return False
            
            self._log("Video file opened successfully")
            return True
        
        except Exception as e:
            self._log(f"Error opening video: {str(e)}", "error")
            return False
    
    def _close_video(self):
        """Close video file"""
        if self.video:
            self.video.release()
            self._log("Video file closed")
    
    def _get_video_info(self) -> Dict:
        """Get video metadata"""
        if not self.video or not self.video.isOpened():
            return {}
        
        try:
            frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = self.video.get(cv2.CAP_PROP_FPS)
            width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            return {
                "total_frames": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration_seconds": duration,
                "codec": int(self.video.get(cv2.CAP_PROP_FOURCC))
            }
        except Exception as e:
            self._log(f"Error getting video info: {str(e)}", "error")
            return {}
    
    def _create_output_directory(self, video_id: str) -> Path:
        """Create output directory for frames"""
        frame_dir = self.output_dir / video_id / "frames"
        
        try:
            frame_dir.mkdir(parents=True, exist_ok=True)
            self._log(f"Created frame directory: {frame_dir}")
            return frame_dir
        except Exception as e:
            self._log(f"Error creating directory: {str(e)}", "error")
            raise
    
    def _save_frame(
        self,
        frame: np.ndarray,
        frame_id: int,
        frame_dir: Path
    ) -> Tuple[bool, Optional[str]]:
        """
        Save frame to disk.
        
        Args:
            frame: OpenCV frame (numpy array)
            frame_id: Frame ID (0-based index)
            frame_dir: Output directory
        
        Returns:
            Tuple of (success, filepath)
        """
        try:
            # Create filename
            filename = f"frame_{frame_id:05d}.{self.frame_format}"
            filepath = frame_dir / filename
            
            # Set quality parameters
            if self.frame_format == "png":
                cv2.imwrite(
                    str(filepath),
                    frame,
                    [cv2.IMWRITE_PNG_COMPRESSION, 9 - (self.frame_quality // 10)]
                )
            else:  # jpg
                cv2.imwrite(
                    str(filepath),
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, self.frame_quality]
                )
            
            return True, str(filepath)
        
        except Exception as e:
            self._log(f"Error saving frame {frame_id}: {str(e)}", "error")
            return False, None
    
    def extract_frames(self) -> Dict:
        """
        Extract frames from video.
        
        Returns:
            Dictionary with extraction results:
            {
                'success': bool,
                'video_id': str,
                'frames_extracted': int,
                'frame_dir': str,
                'metadata': dict,
                'frame_list': list of frame metadata
            }
        """
        self._log("Starting frame extraction...")
        
        # Validate video
        if not self._validate_video():
            return {'success': False, 'error': 'Video validation failed'}
        
        # Generate video ID from filename and timestamp
        video_name = Path(self.video_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = f"{video_name}_{timestamp}"
        
        # Open video
        if not self._open_video():
            return {'success': False, 'error': 'Failed to open video'}
        
        # Get video info
        video_info = self._get_video_info()
        if not video_info:
            self._close_video()
            return {'success': False, 'error': 'Failed to get video info'}
        
        self._log(f"Video info: {video_info}")
        
        # Create output directory
        try:
            frame_dir = self._create_output_directory(video_id)
        except Exception as e:
            self._close_video()
            return {'success': False, 'error': f'Failed to create directory: {str(e)}'}
        
        # Extract frames
        frame_list = []
        current_frame_index = 0
        extracted_count = 0
        fps = video_info.get('fps', VIDEO_RECORDING_FPS)
        
        self._log(f"Extracting frames: sampling_rate={self.sampling_rate}, max_frames={self.max_frames}")
        
        while extracted_count < self.max_frames:
            ret, frame = self.video.read()
            
            if not ret:
                self._log("Reached end of video")
                break
            
            # Check sampling rate
            if current_frame_index % self.sampling_rate == 0:
                # Calculate timestamp
                timestamp_sec = current_frame_index / fps if fps > 0 else 0
                
                # Save frame
                success, filepath = self._save_frame(frame, extracted_count, frame_dir)
                
                if success:
                    frame_metadata = {
                        'frame_id': f"frame_{extracted_count:05d}",
                        'frame_index': current_frame_index,
                        'timestamp': timestamp_sec,
                        'path': filepath
                    }
                    frame_list.append(frame_metadata)
                    extracted_count += 1
                else:
                    self._log(f"Failed to save frame {extracted_count}", "warning")
            
            current_frame_index += 1
        
        # Close video
        self._close_video()
        
        # Store results
        self.frame_count = extracted_count
        self.extracted_frames = frame_list
        self.metadata = {
            'video_id': video_id,
            'video_path': self.video_path,
            'video_info': video_info,
            'extraction_config': {
                'sampling_rate': self.sampling_rate,
                'max_frames': self.max_frames,
                'frame_format': self.frame_format,
                'frame_quality': self.frame_quality
            },
            'extraction_result': {
                'frames_extracted': extracted_count,
                'frame_dir': str(frame_dir),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        self._log(f"Extracted {extracted_count} frames successfully")
        
        return {
            'success': True,
            'video_id': video_id,
            'frames_extracted': extracted_count,
            'frame_dir': str(frame_dir),
            'metadata': self.metadata,
            'frame_list': frame_list
        }
    
    def extract_frame_range(
        self,
        start_frame: int = 0,
        end_frame: Optional[int] = None
    ) -> Dict:
        """
        Extract specific range of frames.
        
        Args:
            start_frame: Starting frame index
            end_frame: Ending frame index (None = to end)
        
        Returns:
            Extraction results dictionary
        """
        self._log(f"Extracting frame range: {start_frame} to {end_frame}")
        
        if not self._validate_video() or not self._open_video():
            return {'success': False, 'error': 'Failed to open video'}
        
        video_info = self._get_video_info()
        video_name = Path(self.video_path).stem
        video_id = f"{video_name}_range_{start_frame}_{end_frame or 'end'}"
        
        try:
            frame_dir = self._create_output_directory(video_id)
        except Exception as e:
            self._close_video()
            return {'success': False, 'error': f'Failed to create directory: {str(e)}'}
        
        frame_list = []
        current_frame_index = 0
        extracted_count = 0
        fps = video_info.get('fps', VIDEO_RECORDING_FPS)
        
        while True:
            ret, frame = self.video.read()
            
            if not ret:
                break
            
            # Check if in range
            if current_frame_index < start_frame:
                current_frame_index += 1
                continue
            
            if end_frame and current_frame_index >= end_frame:
                break
            
            # Extract frame
            timestamp_sec = current_frame_index / fps if fps > 0 else 0
            success, filepath = self._save_frame(frame, extracted_count, frame_dir)
            
            if success:
                frame_list.append({
                    'frame_id': f"frame_{extracted_count:05d}",
                    'frame_index': current_frame_index,
                    'timestamp': timestamp_sec,
                    'path': filepath
                })
                extracted_count += 1
            
            current_frame_index += 1
        
        self._close_video()
        
        self._log(f"Extracted {extracted_count} frames from range")
        
        return {
            'success': True,
            'video_id': video_id,
            'frames_extracted': extracted_count,
            'frame_dir': str(frame_dir),
            'metadata': self.metadata,
            'frame_list': frame_list
        }
    
    def save_frame_index(self, index_path: Optional[Path] = None) -> bool:
        """
        Save frame extraction index to JSON.
        
        Args:
            index_path: Path to save index (default: frame_dir/index.json)
        
        Returns:
            Success status
        """
        try:
            if not index_path and self.extracted_frames:
                # Use frame directory
                frame_path = Path(self.extracted_frames[0]['path'])
                index_path = frame_path.parent.parent / "index.json"
            
            if not index_path:
                self._log("No index path specified", "warning")
                return False
            
            index_data = {
                'metadata': self.metadata,
                'frames': self.extracted_frames
            }
            
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            self._log(f"Frame index saved: {index_path}")
            return True
        
        except Exception as e:
            self._log(f"Error saving index: {str(e)}", "error")
            return False
    
    def get_extraction_summary(self) -> Dict:
        """Get summary of extraction results"""
        return {
            'total_frames': self.frame_count,
            'frames': self.extracted_frames,
            'metadata': self.metadata
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_video_frames(
    video_path: str,
    output_dir: Optional[Path] = None,
    sampling_rate: int = 5,
    max_frames: int = 1000,
    verbose: bool = True
) -> Dict:
    """
    Convenience function to extract frames from a video.
    
    Args:
        video_path: Path to video file
        output_dir: Output directory (default: FRAME_EXTRACTION_OUTPUT_DIR)
        sampling_rate: Extract every Nth frame
        max_frames: Maximum frames to extract
        verbose: Enable verbose logging
    
    Returns:
        Extraction results dictionary
    """
    extractor = FrameExtractor(
        video_path=video_path,
        output_dir=output_dir,
        sampling_rate=sampling_rate,
        max_frames=max_frames,
        verbose=verbose
    )
    
    return extractor.extract_frames()


if __name__ == "__main__":
    # Example usage
    print("Frame Extraction Module")
    print("This module is meant to be imported, not run directly.")
