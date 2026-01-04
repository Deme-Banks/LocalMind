"""
Video Cache - Caching and deduplication for video generation
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class VideoCache:
    """Manages video generation cache and deduplication"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize video cache
        
        Args:
            cache_dir: Directory to store cache (default: video_cache/ in project root)
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "video_cache"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache index file
        self.index_file = self.cache_dir / "index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure index file exists"""
        if not self.index_file.exists():
            self._save_index({})
    
    def _load_index(self) -> Dict[str, Any]:
        """Load cache index"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading cache index: {e}")
            return {}
    
    def _save_index(self, index: Dict[str, Any]):
        """Save cache index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")
    
    def _generate_cache_key(
        self,
        prompt: str,
        backend: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate cache key from video generation parameters
        
        Args:
            prompt: Video prompt
            backend: Backend name
            model: Model name
            duration: Video duration
            aspect_ratio: Aspect ratio
            resolution: Resolution
            **kwargs: Additional parameters
        
        Returns:
            Cache key (SHA256 hash)
        """
        # Normalize prompt (lowercase, strip whitespace)
        normalized_prompt = prompt.lower().strip()
        
        # Create cache key from all parameters
        cache_data = {
            "prompt": normalized_prompt,
            "backend": backend,
            "model": model,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            **kwargs
        }
        
        # Convert to JSON string and hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_key = hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
        
        return cache_key
    
    def get(
        self,
        prompt: str,
        backend: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached video result
        
        Args:
            prompt: Video prompt
            backend: Backend name
            model: Model name
            duration: Video duration
            aspect_ratio: Aspect ratio
            resolution: Resolution
            **kwargs: Additional parameters
        
        Returns:
            Cached video data or None if not found
        """
        cache_key = self._generate_cache_key(
            prompt=prompt,
            backend=backend,
            model=model,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            **kwargs
        )
        
        index = self._load_index()
        
        if cache_key not in index:
            return None
        
        cache_entry = index[cache_key]
        
        # Check if cache entry is expired
        if cache_entry.get("expires_at"):
            expires_at = datetime.fromisoformat(cache_entry["expires_at"])
            if datetime.now() > expires_at:
                # Cache expired, remove it
                del index[cache_key]
                self._save_index(index)
                return None
        
        # Check if cached video file exists
        video_path = cache_entry.get("video_path")
        if video_path and not Path(video_path).exists():
            # Video file doesn't exist, remove from cache
            del index[cache_key]
            self._save_index(index)
            return None
        
        # Return cached result
        return {
            "video_id": cache_entry.get("video_id"),
            "video_url": cache_entry.get("video_url"),
            "video_path": cache_entry.get("video_path"),
            "status": "completed",
            "cached": True,
            "cache_key": cache_key,
            "created_at": cache_entry.get("created_at")
        }
    
    def set(
        self,
        prompt: str,
        backend: str,
        model: str,
        video_id: str,
        video_url: Optional[str] = None,
        video_path: Optional[str] = None,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        expires_in_days: int = 30,
        **kwargs
    ):
        """
        Cache video generation result
        
        Args:
            prompt: Video prompt
            backend: Backend name
            model: Model name
            video_id: Video ID
            video_url: Video URL
            video_path: Video file path
            duration: Video duration
            aspect_ratio: Aspect ratio
            resolution: Resolution
            expires_in_days: Cache expiration in days
            **kwargs: Additional parameters
        """
        cache_key = self._generate_cache_key(
            prompt=prompt,
            backend=backend,
            model=model,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            **kwargs
        )
        
        index = self._load_index()
        
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        index[cache_key] = {
            "cache_key": cache_key,
            "prompt": prompt,
            "backend": backend,
            "model": model,
            "video_id": video_id,
            "video_url": video_url,
            "video_path": video_path,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "metadata": kwargs
        }
        
        self._save_index(index)
        logger.info(f"Cached video generation: {cache_key[:16]}...")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        index = self._load_index()
        now = datetime.now()
        expired_keys = []
        
        for cache_key, entry in index.items():
            if entry.get("expires_at"):
                expires_at = datetime.fromisoformat(entry["expires_at"])
                if now > expires_at:
                    expired_keys.append(cache_key)
                    # Delete video file if it exists
                    video_path = entry.get("video_path")
                    if video_path:
                        try:
                            Path(video_path).unlink()
                        except Exception as e:
                            logger.warning(f"Could not delete expired cache file {video_path}: {e}")
        
        for key in expired_keys:
            del index[key]
        
        if expired_keys:
            self._save_index(index)
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def clear_all(self):
        """Clear all cache entries"""
        index = self._load_index()
        
        # Delete all cached video files
        for entry in index.values():
            video_path = entry.get("video_path")
            if video_path:
                try:
                    Path(video_path).unlink()
                except Exception as e:
                    logger.warning(f"Could not delete cache file {video_path}: {e}")
        
        self._save_index({})
        logger.info("Cleared all video cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        index = self._load_index()
        now = datetime.now()
        
        total = len(index)
        expired = 0
        valid = 0
        
        for entry in index.values():
            if entry.get("expires_at"):
                expires_at = datetime.fromisoformat(entry["expires_at"])
                if now > expires_at:
                    expired += 1
                else:
                    valid += 1
            else:
                valid += 1
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "cache_dir": str(self.cache_dir)
        }

