"""
Runway ML backend for text-to-video generation
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json
import time
from pathlib import Path

from .base import BaseVideoBackend, VideoResponse
from ...core.connection_pool import ConnectionPoolManager


class RunwayVideoBackend(BaseVideoBackend):
    """Backend for Runway ML video generation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("RUNWAY_API_KEY")
        self.base_url = config.get("base_url", "https://api.runwayml.com/v1")
        self.timeout = config.get("timeout", 300)
        self.session = ConnectionPoolManager.get_session(
            "runway",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Runway API is available"""
        return bool(self.api_key)
    
    def list_models(self) -> list[str]:
        """List available Runway models"""
        return ["gen3-alpha-turbo", "gen3-alpha", "gen2"]
    
    def generate_video(
        self,
        prompt: str,
        model: str = "gen3-alpha-turbo",
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> VideoResponse:
        """Generate video using Runway"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
            }
            
            if duration:
                payload["duration"] = duration
            if aspect_ratio:
                payload["aspect_ratio"] = aspect_ratio
            if resolution:
                payload["resolution"] = resolution
            
            payload.update(kwargs)
            
            response = self.session.post(
                f"{self.base_url}/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("output", [None])[0] if data.get("output") else None
                video_id = data.get("id")
                
                return VideoResponse(
                    video_url=video_url,
                    video_id=video_id,
                    status="completed",
                    progress=1.0,
                    model=model,
                    prompt=prompt,
                    metadata=data
                )
            else:
                error_msg = response.json().get("error", "Unknown error")
                return VideoResponse(
                    status="failed",
                    model=model,
                    prompt=prompt,
                    error=error_msg
                )
        except Exception as e:
            return VideoResponse(
                status="failed",
                model=model,
                prompt=prompt,
                error=str(e)
            )
    
    async def generate_video_async(
        self,
        prompt: str,
        model: str = "gen3-alpha-turbo",
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

