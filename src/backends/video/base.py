"""
Base video backend interface for text-to-video generation
All video backends must implement this interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
from pydantic import BaseModel, Field
from pathlib import Path


class VideoResponse(BaseModel):
    """Response from a video generation backend"""
    video_url: Optional[str] = None  # URL to generated video
    video_path: Optional[str] = None  # Local file path to video
    video_id: Optional[str] = None  # Backend-specific video ID
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = 0.0  # 0.0 to 1.0
    model: str
    prompt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class BaseVideoBackend(ABC):
    """Base class for all video generation backends"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize video backend
        
        Args:
            config: Backend-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__
        self.video_storage_path = Path(config.get("video_storage_path", "videos"))
        self.video_storage_path.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if backend is available and ready
        
        Returns:
            True if backend is available
        """
        pass
    
    @abstractmethod
    def list_models(self) -> list[str]:
        """
        List available video models for this backend
        
        Returns:
            List of model identifiers
        """
        pass
    
    @abstractmethod
    def generate_video(
        self,
        prompt: str,
        model: str,
        duration: Optional[int] = None,  # Duration in seconds
        aspect_ratio: Optional[str] = None,  # e.g., "16:9", "9:16", "1:1"
        resolution: Optional[str] = None,  # e.g., "720p", "1080p", "4k"
        **kwargs
    ) -> VideoResponse:
        """
        Generate video from text prompt
        
        Args:
            prompt: Text prompt describing the video
            model: Model identifier
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            resolution: Video resolution
            **kwargs: Additional backend-specific parameters
        
        Returns:
            VideoResponse with video information
        """
        pass
    
    @abstractmethod
    async def generate_video_async(
        self,
        prompt: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[VideoResponse]:
        """
        Generate video asynchronously with progress updates
        
        Args:
            prompt: Text prompt describing the video
            model: Model identifier
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            resolution: Video resolution
            **kwargs: Additional backend-specific parameters
        
        Yields:
            VideoResponse objects with progress updates
        """
        pass
    
    def get_video_status(self, video_id: str) -> VideoResponse:
        """
        Get status of a video generation job
        
        Args:
            video_id: Backend-specific video ID
        
        Returns:
            VideoResponse with current status
        """
        raise NotImplementedError("This backend does not support status checking")
    
    def download_video(self, video_id: str, save_path: Optional[Path] = None) -> Path:
        """
        Download a generated video
        
        Args:
            video_id: Backend-specific video ID
            save_path: Optional path to save video
        
        Returns:
            Path to downloaded video file
        """
        raise NotImplementedError("This backend does not support video download")
    
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about this backend
        
        Returns:
            Dictionary with backend information
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__.replace("VideoBackend", "").lower(),
            "supports_async": hasattr(self, "generate_video_async"),
            "supports_status_check": hasattr(self, "get_video_status") and 
                                    self.get_video_status.__func__ != BaseVideoBackend.get_video_status
        }

