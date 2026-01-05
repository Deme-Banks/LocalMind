"""
Luma AI Video Backend
"""

import os
from typing import Dict, Any, Optional, AsyncIterator
import logging
import requests

from .base import BaseVideoBackend, VideoResponse

logger = logging.getLogger(__name__)


class LumaVideoBackend(BaseVideoBackend):
    """Backend for Luma AI Dream Machine"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("LUMA_API_KEY")
        self.base_url = config.get("base_url", "https://api.lumalabs.ai/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def list_models(self) -> list[str]:
        """List available Luma AI models"""
        return [
            "dream-machine",
            "dream-machine-v1",
            "dream-machine-v2"
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
        """Generate video using Luma AI"""
        if not self.is_available():
            raise ConnectionError("Luma AI API key not configured.")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/generations",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            video_id = data.get("id")
            status = data.get("status", "pending")
            url = data.get("url")
            
            return VideoResponse(
                video_id=video_id,
                status=status,
                video_url=url,
                model=model,
                prompt=prompt,
                metadata=data
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Luma AI video generation failed: {e}")
            raise
    
    def get_video_status(self, video_id: str) -> Optional[VideoResponse]:
        """Get status of a video generation"""
        if not self.is_available():
            raise ConnectionError("Luma AI API key not configured.")
        
        try:
            response = requests.get(
                f"{self.base_url}/generations/{video_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status")
            video_url = data.get("url")
            model = data.get("model", "dream-machine")
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
            logger.error(f"Luma AI video status check failed for {video_id}: {e}")
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

