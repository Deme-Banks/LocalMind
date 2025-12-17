"""
Google backend implementation
Supports Gemini API models
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json

from .base import BaseBackend, ModelResponse
from ..core.connection_pool import ConnectionPoolManager


class GoogleBackend(BaseBackend):
    """Backend for Google Gemini API models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        self.base_url = config.get("base_url", "https://generativelanguage.googleapis.com/v1")
        self.timeout = config.get("timeout", 120)
        # Get session with connection pooling
        self.session = ConnectionPoolManager.get_session(
            "google",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Google API is available"""
        if not self.api_key:
            return False
        try:
            # Simple check - try to list models
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url}/models?key={self.api_key}",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Google models"""
        if not self.api_key:
            return []
        
        try:
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url}/models?key={self.api_key}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [model["name"].split("/")[-1] for model in data.get("models", [])]
        except:
            pass
        
        # Fallback to known models
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-ultra",
        ]
    
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate text using Google API"""
        if not self.api_key:
            raise RuntimeError("Google API key not configured")
        
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        contents = [{"parts": [{"text": prompt}]}]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        payload.update(kwargs)
        
        try:
            session = getattr(self, 'session', None) or requests.Session()
            response = session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            return ModelResponse(
                text=text,
                model=model,
                done=True,
                metadata={
                    "usageMetadata": data.get("usageMetadata", {}),
                    "finishReason": data["candidates"][0].get("finishReason"),
                }
            )
        except Exception as e:
            raise RuntimeError(f"Google generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Google API"""
        import aiohttp
        
        if not self.api_key:
            raise RuntimeError("Google API key not configured")
        
        url = f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}"
        
        contents = [{"parts": [{"text": prompt}]}]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        payload.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line:
                        try:
                            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                            data = json.loads(line_str)
                            if "candidates" in data and len(data["candidates"]) > 0:
                                if "content" in data["candidates"][0]:
                                    parts = data["candidates"][0]["content"].get("parts", [])
                                    for part in parts:
                                        if "text" in part:
                                            yield part["text"]
                        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                            continue
    
    def load_model(self, model: str) -> bool:
        """Load model (Google API models are always available if API key is set)"""
        return self.is_available() and model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Configure API key for Google models"""
        if not self.api_key:
            return {
                "status": "error",
                "error": "Google API key not configured. Please set GOOGLE_API_KEY environment variable or configure in settings."
            }
        
        return {
            "status": "completed",
            "message": "Google API key is configured. Models are ready to use."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Google backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "models_count": len(self.list_models()) if self.is_available() else 0
        })
        return info

