"""
Frame Index Module - Phase 2

Creates and manages searchable frame index with metadata.
Provides fast lookup of frames by various criteria.

Key Responsibilities:
- Build frame index from extraction results
- Store frame metadata
- Provide query interfaces
- Support filtering by timestamp, change score, interactions
- Persist index to JSON
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

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
# FRAME INDEX CLASS
# ============================================================================

class FrameIndex:
    """
    Searchable index of video frames with metadata.
    
    Stores and retrieves:
    - Frame file paths
    - Timestamps
    - Change detection scores
    - Interaction metadata
    - Window/application info
    
    Attributes:
        video_id (str): Unique video identifier
        frames (List[Dict]): List of frame metadata
        changes (Dict): Change detection results
        interactions (Dict): Interaction detection results
    """
    
    def __init__(
        self,
        video_id: str,
        verbose: bool = True
    ):
        """
        Initialize frame index.
        
        Args:
            video_id: Unique video identifier
            verbose: Enable verbose logging
        """
        self.video_id = video_id
        self.verbose = verbose
        
        # Data storage
        self.frames = []  # List of frame metadata
        self.changes = {}  # Change detection results
        self.interactions = {}  # Interaction detection results
        self.metadata = {}  # General metadata
        
        self._log(f"Initialized FrameIndex for video: {video_id}")
    
    @property
    def frame_count(self) -> int:
        """Get total number of frames in index"""
        return len(self.frames)
    
    def _log(self, message: str, level: str = "info"):
        """Log message if verbose is enabled"""
        if self.verbose:
            getattr(logger, level)(message)
    
    def add_frame(
        self,
        frame_id: str,
        frame_path: str,
        timestamp: float,
        change_score: float = 0.0,
        window: Optional[str] = None,
        interactions: Optional[List[str]] = None
    ) -> bool:
        """
        Add frame metadata to index.
        
        Args:
            frame_id: Frame identifier (e.g., 'frame_0000')
            frame_path: Full path to frame file
            timestamp: Timestamp in seconds
            change_score: Change detection score (0.0-1.0)
            window: Active window/application name
            interactions: List of interaction types in this frame
        
        Returns:
            Success status
        """
        try:
            frame_entry = {
                'id': frame_id,
                'path': frame_path,
                'timestamp': timestamp,
                'change_score': change_score,
                'window': window or 'Unknown',
                'interactions': interactions or [],
                'tags': []
            }
            
            self.frames.append(frame_entry)
            return True
        
        except Exception as e:
            self._log(f"Error adding frame: {str(e)}", "error")
            return False
    
    def add_change_detection(self, changes: Dict) -> bool:
        """
        Add change detection results to index.
        
        Args:
            changes: Change detection results dictionary
        
        Returns:
            Success status
        """
        try:
            self.changes = changes
            
            # Update frame change scores
            if 'change_events' in changes:
                for event in changes['change_events']:
                    frame_id = event.get('frame_id')
                    if frame_id < len(self.frames):
                        self.frames[frame_id]['change_score'] = event.get('change_score', 0.0)
                        self.frames[frame_id]['tags'].append(event.get('event_type', 'unknown'))
            
            self._log(f"Added change detection results: {changes.get('summary', {})}")
            return True
        
        except Exception as e:
            self._log(f"Error adding change detection: {str(e)}", "error")
            return False
    
    def add_interactions(self, interactions: Dict) -> bool:
        """
        Add interaction detection results to index.
        
        Args:
            interactions: Interaction detection results dictionary
        
        Returns:
            Success status
        """
        try:
            self.interactions = interactions
            
            # Update frame interactions
            if 'interactions' in interactions:
                interaction_map = {}
                for interaction in interactions['interactions']:
                    frame_id = interaction.get('frame_id')
                    if frame_id not in interaction_map:
                        interaction_map[frame_id] = []
                    interaction_map[frame_id].append(interaction.get('interaction_type'))
                
                for frame_id, types in interaction_map.items():
                    if frame_id < len(self.frames):
                        self.frames[frame_id]['interactions'] = types
            
            self._log(f"Added interaction detection results")
            return True
        
        except Exception as e:
            self._log(f"Error adding interactions: {str(e)}", "error")
            return False
    
    def get_frame(self, frame_id: int) -> Optional[Dict]:
        """
        Get frame metadata by index.
        
        Args:
            frame_id: Frame index (0-based)
        
        Returns:
            Frame metadata dictionary or None
        """
        try:
            if 0 <= frame_id < len(self.frames):
                return self.frames[frame_id]
            return None
        except Exception as e:
            self._log(f"Error getting frame: {str(e)}", "error")
            return None
    
    def get_frames_by_timestamp_range(
        self,
        start_time: float,
        end_time: float
    ) -> List[Dict]:
        """
        Get frames within time range.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
        
        Returns:
            List of frame metadata
        """
        try:
            return [
                f for f in self.frames
                if start_time <= f['timestamp'] <= end_time
            ]
        except Exception as e:
            self._log(f"Error querying by timestamp: {str(e)}", "error")
            return []
    
    def get_frames_by_change_score(
        self,
        min_score: float = 0.0,
        max_score: float = 1.0
    ) -> List[Dict]:
        """
        Get frames with change scores in range.
        
        Args:
            min_score: Minimum change score
            max_score: Maximum change score
        
        Returns:
            List of frame metadata
        """
        try:
            return [
                f for f in self.frames
                if min_score <= f['change_score'] <= max_score
            ]
        except Exception as e:
            self._log(f"Error querying by change score: {str(e)}", "error")
            return []
    
    def get_high_change_frames(self, threshold: float = 0.5) -> List[Dict]:
        """
        Get frames with significant changes.
        
        Args:
            threshold: Change score threshold
        
        Returns:
            List of high-change frame metadata
        """
        return self.get_frames_by_change_score(threshold, 1.0)
    
    def get_frames_with_interaction(
        self,
        interaction_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get frames with specific interaction type.
        
        Args:
            interaction_type: Type of interaction (None = any interaction)
        
        Returns:
            List of frame metadata
        """
        try:
            if interaction_type:
                return [
                    f for f in self.frames
                    if any(
                        i.get('type') == interaction_type or i == interaction_type
                        for i in f.get('interactions', [])
                    )
                ]
            else:
                return [
                    f for f in self.frames
                    if len(f.get('interactions', [])) > 0
                ]
        except Exception as e:
            self._log(f"Error querying by interaction: {str(e)}", "error")
            return []
    
    def get_frames_by_window(self, window_name: str) -> List[Dict]:
        """
        Get frames from specific window/application.
        
        Args:
            window_name: Window/application name
        
        Returns:
            List of frame metadata
        """
        try:
            return [
                f for f in self.frames
                if f['window'].lower() == window_name.lower()
            ]
        except Exception as e:
            self._log(f"Error querying by window: {str(e)}", "error")
            return []
    
    def get_frames_by_tag(self, tag: str) -> List[Dict]:
        """
        Get frames with specific tag.
        
        Args:
            tag: Tag name
        
        Returns:
            List of frame metadata
        """
        try:
            return [
                f for f in self.frames
                if tag in f['tags']
            ]
        except Exception as e:
            self._log(f"Error querying by tag: {str(e)}", "error")
            return []
    
    def tag_frame(self, frame_id: int, tag: str) -> bool:
        """
        Add tag to frame.
        
        Args:
            frame_id: Frame index
            tag: Tag to add
        
        Returns:
            Success status
        """
        try:
            if 0 <= frame_id < len(self.frames):
                if tag not in self.frames[frame_id]['tags']:
                    self.frames[frame_id]['tags'].append(tag)
                return True
            return False
        except Exception as e:
            self._log(f"Error tagging frame: {str(e)}", "error")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get index statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            if not self.frames:
                return {
                    'total_frames': 0,
                    'average_change': 0.0,
                    'high_change_count': 0,
                    'interaction_count': 0
                }
            
            change_scores = [f['change_score'] for f in self.frames]
            high_change_count = sum(1 for s in change_scores if s > 0.5)
            interaction_count = sum(1 for f in self.frames if len(f['interactions']) > 0)
            
            return {
                'total_frames': len(self.frames),
                'average_change': sum(change_scores) / len(change_scores) if change_scores else 0.0,
                'max_change': max(change_scores) if change_scores else 0.0,
                'min_change': min(change_scores) if change_scores else 0.0,
                'high_change_count': high_change_count,
                'interaction_count': interaction_count,
                'avg_timestamp': sum(f['timestamp'] for f in self.frames) / len(self.frames) if self.frames else 0.0
            }
        
        except Exception as e:
            self._log(f"Error generating statistics: {str(e)}", "error")
            return {}
    
    def save_to_json(self, output_path: Path) -> bool:
        """
        Save index to JSON file.
        
        Args:
            output_path: Path to save JSON file
        
        Returns:
            Success status
        """
        try:
            index_data = {
                'video_id': self.video_id,
                'created_at': datetime.now().isoformat(),
                'total_frames': len(self.frames),
                'statistics': self.get_statistics(),
                'frames': self.frames,
                'changes': self.changes,
                'interactions': self.interactions
            }
            
            with open(output_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            self._log(f"Index saved to: {output_path}")
            return True
        
        except Exception as e:
            self._log(f"Error saving index: {str(e)}", "error")
            return False
    
    def load_from_json(self, input_path: Path) -> bool:
        """
        Load index from JSON file.
        
        Args:
            input_path: Path to JSON file
        
        Returns:
            Success status
        """
        try:
            with open(input_path, 'r') as f:
                index_data = json.load(f)
            
            self.video_id = index_data.get('video_id', self.video_id)
            self.frames = index_data.get('frames', [])
            self.changes = index_data.get('changes', {})
            self.interactions = index_data.get('interactions', {})
            
            self._log(f"Index loaded from: {input_path}")
            return True
        
        except Exception as e:
            self._log(f"Error loading index: {str(e)}", "error")
            return False
    
    def export_summary(self) -> Dict:
        """
        Export index summary (for quick reference).
        
        Returns:
            Summary dictionary
        """
        return {
            'video_id': self.video_id,
            'total_frames': len(self.frames),
            'statistics': self.get_statistics(),
            'change_summary': self.changes.get('summary', {}),
            'interaction_summary': self.interactions.get('summary', {})
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def build_frame_index(
    video_id: str,
    extraction_results: Dict,
    change_results: Dict,
    interaction_results: Dict,
    verbose: bool = True
) -> FrameIndex:
    """
    Build complete frame index from all Phase 2 results.
    
    Args:
        video_id: Video identifier
        extraction_results: Frame extraction results
        change_results: Change detection results
        interaction_results: Interaction detection results
        verbose: Enable verbose logging
    
    Returns:
        Populated FrameIndex object
    """
    index = FrameIndex(video_id, verbose)
    
    # Add frames from extraction results
    if 'frame_list' in extraction_results:
        for i, frame_meta in enumerate(extraction_results['frame_list']):
            index.add_frame(
                frame_id=frame_meta['frame_id'],
                frame_path=frame_meta['path'],
                timestamp=frame_meta['timestamp']
            )
    
    # Add change detection
    if change_results and change_results.get('success'):
        index.add_change_detection(change_results)
    
    # Add interactions
    if interaction_results and interaction_results.get('success'):
        index.add_interactions(interaction_results)
    
    return index


if __name__ == "__main__":
    print("Frame Index Module")
    print("This module is meant to be imported, not run directly.")
