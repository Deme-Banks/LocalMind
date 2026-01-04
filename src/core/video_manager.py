"""
Video Manager - handles saving, loading, and managing generated videos
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VideoManager:
    """Manages video storage and retrieval"""
    
    def __init__(self, videos_dir: Optional[Path] = None):
        """
        Initialize video manager
        
        Args:
            videos_dir: Directory to store videos (default: videos/ in project root)
        """
        if videos_dir is None:
            videos_dir = Path(__file__).parent.parent.parent / "videos"
        
        self.videos_dir = videos_dir
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file to track all videos
        self.index_file = self.videos_dir / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure index file exists"""
        if not self.index_file.exists():
            self._save_index({})
    
    def _load_index(self) -> Dict[str, Any]:
        """Load video index"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading video index: {e}")
            return {}
    
    def _save_index(self, index: Dict[str, Any]):
        """Save video index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving video index: {e}")
    
    def create_video(
        self,
        prompt: str,
        model: str,
        backend: str,
        video_url: Optional[str] = None,
        video_path: Optional[str] = None,
        video_id: Optional[str] = None,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new video entry
        
        Args:
            prompt: Video prompt
            model: Model used
            backend: Backend used
            video_url: URL to video
            video_path: Local path to video
            video_id: Backend-specific video ID
            duration: Video duration
            aspect_ratio: Aspect ratio
            resolution: Resolution
            metadata: Additional metadata
        
        Returns:
            Video ID
        """
        if not video_id:
            video_id = str(uuid.uuid4())
        
        timestamp = datetime.now().isoformat()
        
        video_entry = {
            "id": video_id,
            "prompt": prompt,
            "model": model,
            "backend": backend,
            "video_url": video_url,
            "video_path": video_path,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "created_at": timestamp,
            "updated_at": timestamp,
            "status": "completed" if video_url or video_path else "pending",
            "metadata": metadata or {}
        }
        
        # Save video entry file
        video_file = self.videos_dir / f"{video_id}.json"
        try:
            with open(video_file, 'w', encoding='utf-8') as f:
                json.dump(video_entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error creating video entry: {e}")
            raise
        
        # Update index
        index = self._load_index()
        index[video_id] = {
            "id": video_id,
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "model": model,
            "backend": backend,
            "created_at": timestamp,
            "updated_at": timestamp,
            "status": video_entry["status"],
            "has_video": bool(video_url or video_path)
        }
        self._save_index(index)
        
        return video_id
    
    def update_video(
        self,
        video_id: str,
        video_url: Optional[str] = None,
        video_path: Optional[str] = None,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update a video entry
        
        Args:
            video_id: Video ID
            video_url: Updated video URL
            video_path: Updated video path
            status: Updated status
            progress: Progress (0.0 to 1.0)
            metadata: Updated metadata
        
        Returns:
            True if updated, False if not found
        """
        video_file = self.videos_dir / f"{video_id}.json"
        
        if not video_file.exists():
            return False
        
        try:
            with open(video_file, 'r', encoding='utf-8') as f:
                video_entry = json.load(f)
        except Exception as e:
            logger.error(f"Error loading video entry: {e}")
            return False
        
        # Update fields
        if video_url is not None:
            video_entry["video_url"] = video_url
        if video_path is not None:
            video_entry["video_path"] = video_path
        if status is not None:
            video_entry["status"] = status
        if progress is not None:
            video_entry["progress"] = progress
        if metadata is not None:
            video_entry["metadata"].update(metadata)
        
        video_entry["updated_at"] = datetime.now().isoformat()
        
        # Save updated entry
        try:
            with open(video_file, 'w', encoding='utf-8') as f:
                json.dump(video_entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving video entry: {e}")
            return False
        
        # Update index
        index = self._load_index()
        if video_id in index:
            if status is not None:
                index[video_id]["status"] = status
            if video_url or video_path:
                index[video_id]["has_video"] = True
            index[video_id]["updated_at"] = video_entry["updated_at"]
            self._save_index(index)
        
        return True
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a video by ID
        
        Args:
            video_id: Video ID
        
        Returns:
            Video data or None if not found
        """
        video_file = self.videos_dir / f"{video_id}.json"
        
        if not video_file.exists():
            return None
        
        try:
            with open(video_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading video {video_id}: {e}")
            return None
    
    def list_videos(
        self,
        limit: Optional[int] = None,
        search: Optional[str] = None,
        backend: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all videos
        
        Args:
            limit: Maximum number of videos to return
            search: Search term to filter videos
            backend: Filter by backend
            status: Filter by status
        
        Returns:
            List of video summaries
        """
        index = self._load_index()
        videos = []
        
        for vid_id, vid_info in index.items():
            # Apply filters
            if backend and vid_info.get("backend") != backend:
                continue
            if status and vid_info.get("status") != status:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in vid_info.get("prompt", "").lower() and
                    search_lower not in vid_id.lower()):
                    continue
            
            videos.append(vid_info)
        
        # Sort by updated_at (most recent first)
        videos.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Apply limit
        if limit:
            videos = videos[:limit]
        
        return videos
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video
        
        Args:
            video_id: Video ID
        
        Returns:
            True if deleted, False otherwise
        """
        video_file = self.videos_dir / f"{video_id}.json"
        
        # Delete video file if it exists locally
        if video_file.exists():
            try:
                # Get video entry to find local video file
                video_entry = self.get_video(video_id)
                if video_entry and video_entry.get("video_path"):
                    video_path = Path(video_entry["video_path"])
                    if video_path.exists():
                        video_path.unlink()
                
                video_file.unlink()
            except Exception as e:
                logger.error(f"Error deleting video file {video_id}: {e}")
                return False
        
        # Remove from index
        index = self._load_index()
        if video_id in index:
            del index[video_id]
            self._save_index(index)
        
        return True

