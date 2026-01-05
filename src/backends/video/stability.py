"""
Stability AI Video Backend - Stable Video Diffusion
"""

import os
from typing import Dict, Any, Optional, AsyncIterator
import logging
import requests

from .base import BaseVideoBackend, VideoResponse

logger = logging.getLogger(__name__)


class StabilityVideoBackend(BaseVideoBackend):
    """Backend for Stability AI's Stable Video Diffusion"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("STABILITY_API_KEY")
        self.base_url = config.get("base_url", "https://api.stability.ai/v2beta")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def list_models(self) -> list[str]:
        """List available Stability AI video models"""
        return [
            "stable-video-diffusion",
            "svd-1.1",
            "svd-xt"
        ]
    
    def generate_video(
        self,
        prompt: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> VideoResponse:
        """Generate video using Stability AI"""
        if not self.is_available():
            raise ConnectionError("Stability AI API key not configured.")
        
        # Map resolution to Stability AI format
        width, height = self._parse_resolution(resolution, aspect_ratio)
        
        payload = {
            "prompt": prompt,
            **kwargs
        }
        
        if duration:
            payload["duration"] = duration
        if width and height:
            payload["width"] = width
            payload["height"] = height
        
        try:
            response = requests.post(
                f"{self.base_url}/image-to-video",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            video_id = data.get("id")
            status = "pending"
            video_url = data.get("url")
            
            return VideoResponse(
                video_id=video_id,
                status=status,
                video_url=video_url,
                model=model,
                prompt=prompt,
                metadata=data
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Stability AI video generation failed: {e}")
            raise
    
    def get_video_status(self, video_id: str) -> Optional[VideoResponse]:
        """Get status of a video generation"""
        if not self.is_available():
            raise ConnectionError("Stability AI API key not configured.")
        
        try:
            response = requests.get(
                f"{self.base_url}/image-to-video/{video_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status", "pending")
            video_url = data.get("url")
            model = data.get("model", "stable-video-diffusion")
            prompt = data.get("prompt", "")
            
            return VideoResponse(
                video_id=video_id,
                status=status,
                video_url=video_url,
                model=model,
                prompt=prompt,
                metadata=data
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Stability AI video status check failed for {video_id}: {e}")
            return None
    
    async def generate_video_async(
        self,
        prompt: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[VideoResponse]:
        """Generate video asynchronously"""
        yield VideoResponse(status="pending", progress=0.0, model=model, prompt=prompt)
        yield VideoResponse(status="processing", progress=0.5, model=model, prompt=prompt)
        result = self.generate_video(prompt, model, duration, aspect_ratio, resolution, **kwargs)
        yield result
    
    def _parse_resolution(self, resolution: str, aspect_ratio: str) -> tuple[int, int]:
        """Parse resolution and aspect ratio to width/height"""
        # Default resolutions
        resolutions = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160)
        }
        
        # Aspect ratio overrides
        aspect_ratios = {
            "16:9": (1920, 1080),
            "9:16": (1080, 1920),
            "1:1": (1080, 1080),
            "4:3": (1440, 1080)
        }
        
        if aspect_ratio in aspect_ratios:
            return aspect_ratios[aspect_ratio]
        
        return resolutions.get(resolution, (1920, 1080))
    
    async def generate_video_async(
        self,
        prompt: str,
        model: str,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[VideoResponse]:
        """Generate video asynchronously"""
        yield VideoResponse(status="pending", progress=0.0, model=model, prompt=prompt)
        yield VideoResponse(status="processing", progress=0.5, model=model, prompt=prompt)
        result = self.generate_video(prompt, model, duration, aspect_ratio, resolution, **kwargs)
        yield result

