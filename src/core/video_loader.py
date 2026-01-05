"""
Video loader - manages different video generation backends
"""

from typing import Dict, Optional, List
from pathlib import Path
import logging

from ..backends.video.base import BaseVideoBackend, VideoResponse
from ..backends.video.sora import SoraVideoBackend
from ..backends.video.sora2 import Sora2VideoBackend
from ..backends.video.runway import RunwayVideoBackend
from ..backends.video.pika import PikaVideoBackend
from ..backends.video.stability import StabilityVideoBackend
from ..backends.video.kling import KlingVideoBackend
from ..backends.video.luma import LumaVideoBackend
from ..backends.video.haiper import HaiperVideoBackend
from ..utils.config import ConfigManager, LocalMindConfig

logger = logging.getLogger(__name__)


class VideoLoader:
    """Manages video generation backends"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize video loader
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.backends: Dict[str, BaseVideoBackend] = {}
        self._initialize_backends()
    
    def _initialize_backends(self) -> None:
        """Initialize available video backends"""
        # Get video backend configs (we'll add this to config later)
        video_backends_config = getattr(self.config, 'video_backends', {})
        
        # Initialize Sora (original)
        if video_backends_config.get('sora', {}).get('enabled', False):
            try:
                backend = SoraVideoBackend(video_backends_config.get('sora', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['sora'] = backend
                    logger.info("✅ Sora video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Sora backend: {e}")
        
        # Initialize Sora 2 (dedicated backend)
        if video_backends_config.get('sora2', {}).get('enabled', False):
            try:
                backend = Sora2VideoBackend(video_backends_config.get('sora2', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['sora2'] = backend
                    logger.info("✅ Sora 2 video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Sora 2 backend: {e}")
        
        # Initialize Runway
        if video_backends_config.get('runway', {}).get('enabled', False):
            try:
                backend = RunwayVideoBackend(video_backends_config.get('runway', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['runway'] = backend
                    logger.info("✅ Runway video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Runway backend: {e}")
        
        # Initialize Pika
        if video_backends_config.get('pika', {}).get('enabled', False):
            try:
                backend = PikaVideoBackend(video_backends_config.get('pika', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['pika'] = backend
                    logger.info("✅ Pika video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Pika backend: {e}")
        
        # Initialize Stability AI
        if video_backends_config.get('stability', {}).get('enabled', False):
            try:
                backend = StabilityVideoBackend(video_backends_config.get('stability', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['stability'] = backend
                    logger.info("✅ Stability AI video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Stability AI backend: {e}")
        
        # Initialize Kling AI
        if video_backends_config.get('kling', {}).get('enabled', False):
            try:
                backend = KlingVideoBackend(video_backends_config.get('kling', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['kling'] = backend
                    logger.info("✅ Kling AI video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Kling AI backend: {e}")
        
        # Initialize Luma AI
        if video_backends_config.get('luma', {}).get('enabled', False):
            try:
                backend = LumaVideoBackend(video_backends_config.get('luma', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['luma'] = backend
                    logger.info("✅ Luma AI video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Luma AI backend: {e}")
        
        # Initialize Haiper
        if video_backends_config.get('haiper', {}).get('enabled', False):
            try:
                backend = HaiperVideoBackend(video_backends_config.get('haiper', {}).get('settings', {}))
                if backend.is_available():
                    self.backends['haiper'] = backend
                    logger.info("✅ Haiper video backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Haiper backend: {e}")
    
    def get_backend(self, backend_name: str) -> Optional[BaseVideoBackend]:
        """Get a video backend by name"""
        return self.backends.get(backend_name)
    
    def list_backends(self) -> List[str]:
        """List available video backends"""
        return list(self.backends.keys())
    
    def list_all_models(self) -> Dict[str, List[str]]:
        """List all models from all backends"""
        models = {}
        for backend_name, backend in self.backends.items():
            try:
                models[backend_name] = backend.list_models()
            except Exception as e:
                logger.error(f"Error listing models for {backend_name}: {e}")
                models[backend_name] = []
        return models
    
    def generate_video(
        self,
        prompt: str,
        backend_name: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> VideoResponse:
        """
        Generate video using specified backend
        
        Args:
            prompt: Text prompt
            backend_name: Backend name (sora, runway, pika)
            model: Model identifier
            duration: Video duration in seconds
            aspect_ratio: Aspect ratio
            resolution: Resolution
            **kwargs: Additional parameters
        
        Returns:
            VideoResponse
        """
        backend = self.get_backend(backend_name)
        if not backend:
            return VideoResponse(
                status="failed",
                model=model,
                prompt=prompt,
                error=f"Backend '{backend_name}' not available"
            )
        
        try:
            return backend.generate_video(
                prompt=prompt,
                model=model,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            return VideoResponse(
                status="failed",
                model=model,
                prompt=prompt,
                error=str(e)
            )

