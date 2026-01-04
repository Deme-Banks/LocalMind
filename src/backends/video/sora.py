"""
OpenAI Sora 2 backend for text-to-video generation
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json
import time
from pathlib import Path

from .base import BaseVideoBackend, VideoResponse
from ...core.connection_pool import ConnectionPoolManager


class SoraVideoBackend(BaseVideoBackend):
    """Backend for OpenAI Sora 2 video generation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.timeout = config.get("timeout", 300)
        self.session = ConnectionPoolManager.get_session(
            "openai_video",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Sora API is available"""
        if not self.api_key:
            return False
        try:
            # Check API key validity
            response = self.session.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Sora models"""
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                models = response.json().get("data", [])
                # Filter for Sora models
                sora_models = [m["id"] for m in models if "sora" in m["id"].lower()]
                return sora_models if sora_models else ["sora-2.0"]  # Default fallback
            return ["sora-2.0"]
        except Exception:
            return ["sora-2.0"]
    
    def generate_video(
        self,
        prompt: str,
        model: str = "sora-2.0",
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> VideoResponse:
        """Generate video using Sora 2"""
        try:
            # Build request payload
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
            
            # Add any additional parameters
            payload.update(kwargs)
            
            response = self.session.post(
                f"{self.base_url}/video/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("data", [{}])[0].get("url") if data.get("data") else None
                video_id = data.get("id")
                
                return VideoResponse(
                    video_url=video_url,
                    video_id=video_id,
                    status="completed",
                    progress=1.0,
                    model=model,
                    prompt=prompt,
                    metadata={
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution,
                        **data
                    }
                )
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
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
        model: str = "sora-2.0",
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[VideoResponse]:
        """Generate video asynchronously with progress updates"""
        # Sora API doesn't support streaming, so we simulate progress
        yield VideoResponse(
            status="pending",
            progress=0.0,
            model=model,
            prompt=prompt
        )
        
        yield VideoResponse(
            status="processing",
            progress=0.3,
            model=model,
            prompt=prompt
        )
        
        # Generate video
        result = self.generate_video(prompt, model, duration, aspect_ratio, resolution, **kwargs)
        yield result

