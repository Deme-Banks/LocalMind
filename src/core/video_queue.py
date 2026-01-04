"""
Video Generation Queue - manages video generation requests
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VideoQueueStatus(Enum):
    """Video queue status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoQueueItem:
    """Represents a video generation request in the queue"""
    
    def __init__(
        self,
        prompt: str,
        backend_name: str,
        model: str,
        video_id: Optional[str] = None,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.id = video_id or str(uuid.uuid4())
        self.prompt = prompt
        self.backend_name = backend_name
        self.model = model
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.resolution = resolution
        self.metadata = metadata or {}
        
        self.status = VideoQueueStatus.PENDING
        self.progress = 0.0  # 0.0 to 1.0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        
        # Callbacks
        self.on_progress: Optional[Callable[[float], None]] = None
        self.on_complete: Optional[Callable[[Dict], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "backend_name": self.backend_name,
            "model": self.model,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata
        }


class VideoQueue:
    """Manages video generation queue"""
    
    def __init__(self, max_concurrent: int = 3):
        """
        Initialize video queue
        
        Args:
            max_concurrent: Maximum concurrent video generations
        """
        self.queue: List[VideoQueueItem] = []
        self.processing: Dict[str, VideoQueueItem] = {}
        self.completed: Dict[str, VideoQueueItem] = {}
        self.max_concurrent = max_concurrent
        self._lock = asyncio.Lock()
    
    async def add(
        self,
        prompt: str,
        backend_name: str,
        model: str,
        video_id: Optional[str] = None,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        metadata: Optional[Dict] = None,
        on_progress: Optional[Callable[[float], None]] = None,
        on_complete: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Add video generation request to queue
        
        Returns:
            Video ID
        """
        item = VideoQueueItem(
            prompt=prompt,
            backend_name=backend_name,
            model=model,
            video_id=video_id,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            metadata=metadata
        )
        
        item.on_progress = on_progress
        item.on_complete = on_complete
        item.on_error = on_error
        
        async with self._lock:
            self.queue.append(item)
        
        logger.info(f"Added video generation to queue: {item.id}")
        return item.id
    
    async def get_status(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a video generation"""
        async with self._lock:
            # Check processing
            if video_id in self.processing:
                return self.processing[video_id].to_dict()
            
            # Check completed
            if video_id in self.completed:
                return self.completed[video_id].to_dict()
            
            # Check queue
            for item in self.queue:
                if item.id == video_id:
                    return item.to_dict()
        
        return None
    
    async def cancel(self, video_id: str) -> bool:
        """Cancel a video generation"""
        async with self._lock:
            # Remove from queue
            self.queue = [item for item in self.queue if item.id != video_id]
            
            # Cancel if processing
            if video_id in self.processing:
                item = self.processing[video_id]
                item.status = VideoQueueStatus.CANCELLED
                self.completed[video_id] = item
                del self.processing[video_id]
                return True
        
        return False
    
    async def list_all(self, status: Optional[VideoQueueStatus] = None) -> List[Dict[str, Any]]:
        """List all video generations"""
        async with self._lock:
            items = []
            
            if status is None or status == VideoQueueStatus.PENDING:
                items.extend([item.to_dict() for item in self.queue])
            
            if status is None or status == VideoQueueStatus.PROCESSING:
                items.extend([item.to_dict() for item in self.processing.values()])
            
            if status is None or status in [VideoQueueStatus.COMPLETED, VideoQueueStatus.FAILED, VideoQueueStatus.CANCELLED]:
                items.extend([item.to_dict() for item in self.completed.values()])
            
            return items
    
    async def process_next(self, video_loader, video_manager):
        """Process next item in queue"""
        async with self._lock:
            # Check if we can process more
            if len(self.processing) >= self.max_concurrent:
                return False
            
            # Get next item
            if not self.queue:
                return False
            
            item = self.queue.pop(0)
            self.processing[item.id] = item
            item.status = VideoQueueStatus.PROCESSING
            item.started_at = datetime.now()
        
        # Process in background
        asyncio.create_task(self._process_item(item, video_loader, video_manager))
        return True
    
    async def _process_item(
        self,
        item: VideoQueueItem,
        video_loader,
        video_manager
    ):
        """Process a single video generation item"""
        try:
            logger.info(f"Processing video generation: {item.id}")
            
            # Update progress callback
            def update_progress(progress: float):
                item.progress = progress
                if item.on_progress:
                    try:
                        item.on_progress(progress)
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
            
            # Generate video
            result = video_loader.generate_video(
                prompt=item.prompt,
                backend_name=item.backend_name,
                model=item.model,
                duration=item.duration,
                aspect_ratio=item.aspect_ratio,
                resolution=item.resolution,
                **item.metadata
            )
            
            # Handle result
            if result.status == "failed":
                item.status = VideoQueueStatus.FAILED
                item.error = result.error or "Video generation failed"
                item.completed_at = datetime.now()
                
                if item.on_error:
                    try:
                        item.on_error(item.error)
                    except Exception as e:
                        logger.error(f"Error in error callback: {e}")
            else:
                item.status = VideoQueueStatus.COMPLETED
                item.progress = 1.0
                item.result = {
                    "video_url": result.video_url,
                    "video_path": result.video_path,
                    "video_id": result.video_id,
                    "metadata": result.metadata
                }
                item.completed_at = datetime.now()
                
                # Save to video manager
                if video_manager:
                    try:
                        video_manager.create_video(
                            prompt=item.prompt,
                            model=item.model,
                            backend=item.backend_name,
                            video_url=result.video_url,
                            video_path=result.video_path,
                            video_id=item.id,
                            duration=item.duration,
                            aspect_ratio=item.aspect_ratio,
                            resolution=item.resolution,
                            metadata=result.metadata
                        )
                    except Exception as e:
                        logger.error(f"Error saving video to manager: {e}")
                
                # Save to cache (if available)
                try:
                    from ..core.video_cache import VideoCache
                    # Check if video_cache is available in the context
                    # This will be set by the server instance
                    if hasattr(video_manager, '_video_cache'):
                        video_cache = video_manager._video_cache
                    else:
                        # Try to get from module
                        video_cache = None
                    
                    if video_cache:
                        video_cache.set(
                            prompt=item.prompt,
                            backend=item.backend_name,
                            model=item.model,
                            video_id=item.id,
                            video_url=result.video_url,
                            video_path=result.video_path,
                            duration=item.duration,
                            aspect_ratio=item.aspect_ratio,
                            resolution=item.resolution,
                            **item.metadata
                        )
                except Exception as e:
                    logger.debug(f"Could not cache video: {e}")
                
                if item.on_complete:
                    try:
                        item.on_complete(item.result)
                    except Exception as e:
                        logger.error(f"Error in complete callback: {e}")
            
            # Move to completed
            async with self._lock:
                if item.id in self.processing:
                    del self.processing[item.id]
                self.completed[item.id] = item
                
                # Keep only last 100 completed items
                if len(self.completed) > 100:
                    oldest_id = min(
                        self.completed.keys(),
                        key=lambda k: self.completed[k].completed_at or datetime.now()
                    )
                    del self.completed[oldest_id]
        
        except Exception as e:
            logger.error(f"Error processing video generation {item.id}: {e}", exc_info=True)
            item.status = VideoQueueStatus.FAILED
            item.error = str(e)
            item.completed_at = datetime.now()
            
            async with self._lock:
                if item.id in self.processing:
                    del self.processing[item.id]
                self.completed[item.id] = item
            
            if item.on_error:
                try:
                    item.on_error(str(e))
                except Exception as e2:
                    logger.error(f"Error in error callback: {e2}")
    
    async def start_processor(self, video_loader, video_manager, interval: float = 1.0):
        """Start background processor"""
        while True:
            try:
                await self.process_next(video_loader, video_manager)
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
            
            await asyncio.sleep(interval)

