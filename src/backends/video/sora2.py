"""
OpenAI Sora 2 backend for text-to-video generation
Dedicated backend with enhanced Sora 2 support
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json
import time
from pathlib import Path

from .base import BaseVideoBackend, VideoResponse
from ...core.connection_pool import ConnectionPoolManager


class Sora2VideoBackend(BaseVideoBackend):
    """Dedicated backend for OpenAI Sora 2 video generation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY") or os.getenv("SORA2_API_KEY")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        # Support for third-party Sora 2 API providers
        self.use_third_party = config.get("use_third_party", False)
        self.third_party_url = config.get("third_party_url", None)
        self.timeout = config.get("timeout", 300)
        self.session = ConnectionPoolManager.get_session(
            "sora2_video",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Sora 2 API is available"""
        if not self.api_key:
            return False
        try:
            # Check API key validity
            if self.use_third_party and self.third_party_url:
                # For third-party providers, try a simple health check
                response = self.session.get(
                    self.third_party_url.replace("/generate", "/health") if "/generate" in self.third_party_url else f"{self.third_party_url}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5
                )
                return response.status_code in [200, 404]  # 404 might mean endpoint doesn't exist but API is reachable
            else:
                # Standard OpenAI API check
                response = self.session.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Sora 2 models"""
        # Sora 2 specific models
        sora2_models = [
            "sora-2.0",
            "sora-2",
            "sora2",
            "sora-2.0-turbo",  # If available
        ]
        
        # Try to fetch from API if available
        if not self.use_third_party:
            try:
                response = self.session.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                )
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    # Filter for Sora 2 models
                    api_sora_models = [m["id"] for m in models if "sora" in m["id"].lower() and ("2" in m["id"] or "sora-2" in m["id"].lower())]
                    if api_sora_models:
                        return api_sora_models
            except Exception:
                pass
        
        return sora2_models
    
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
            # Use third-party API if configured
            if self.use_third_party and self.third_party_url:
                return self._generate_via_third_party(prompt, model, duration, aspect_ratio, resolution, **kwargs)
            
            # Standard OpenAI Sora 2 API
            # Build request payload
            payload = {
                "model": model if model.startswith("sora") else f"sora-{model}",
                "prompt": prompt,
            }
            
            # Sora 2 specific parameters
            if duration:
                payload["duration"] = min(duration, 60)  # Sora 2 typically supports up to 60 seconds
            if aspect_ratio:
                payload["aspect_ratio"] = aspect_ratio
            if resolution:
                payload["resolution"] = resolution
            
            # Sora 2 enhanced features
            if kwargs.get("synchronized_audio", False):
                payload["synchronized_audio"] = True
            if kwargs.get("cinematic_mode", False):
                payload["cinematic_mode"] = True
            
            # Add any additional parameters
            payload.update({k: v for k, v in kwargs.items() if k not in ["synchronized_audio", "cinematic_mode"]})
            
            # Try OpenAI Sora 2 endpoint
            endpoints_to_try = [
                f"{self.base_url}/video/generations",  # Standard endpoint
                f"{self.base_url}/sora/generations",    # Alternative endpoint
                f"{self.base_url}/sora2/generations",    # Sora 2 specific
            ]
            
            last_error = None
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.post(
                        endpoint,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        video_url = data.get("data", [{}])[0].get("url") if data.get("data") else data.get("video_url")
                        video_id = data.get("id") or data.get("video_id")
                        
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
                                "endpoint_used": endpoint,
                                **data
                            }
                        )
                    elif response.status_code == 404:
                        # Endpoint doesn't exist, try next one
                        continue
                    else:
                        error_data = response.json() if response.content else {}
                        last_error = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    continue
            
            # If all endpoints failed
            return VideoResponse(
                status="failed",
                model=model,
                prompt=prompt,
                error=last_error or "All Sora 2 API endpoints failed"
            )
        except Exception as e:
            return VideoResponse(
                status="failed",
                model=model,
                prompt=prompt,
                error=str(e)
            )
    
    def _generate_via_third_party(
        self,
        prompt: str,
        model: str,
        duration: Optional[int],
        aspect_ratio: Optional[str],
        resolution: Optional[str],
        **kwargs
    ) -> VideoResponse:
        """Generate video via third-party Sora 2 API provider"""
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
                self.third_party_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("video_url") or data.get("url") or (data.get("data", [{}])[0].get("url") if data.get("data") else None)
                video_id = data.get("id") or data.get("video_id")
                
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
                        "provider": "third_party",
                        **data
                    }
                )
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error") if response.content else f"HTTP {response.status_code}"
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
        # Sora 2 API doesn't support streaming, so we simulate progress
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
        
        yield VideoResponse(
            status="processing",
            progress=0.6,
            model=model,
            prompt=prompt
        )
        
        # Generate video
        result = self.generate_video(prompt, model, duration, aspect_ratio, resolution, **kwargs)
        yield result

