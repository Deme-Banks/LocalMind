"""
Cohere backend implementation
Supports Cohere API models
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json

from .base import BaseBackend, ModelResponse
from ..core.connection_pool import ConnectionPoolManager


class CohereBackend(BaseBackend):
    """Backend for Cohere API models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("COHERE_API_KEY")
        self.base_url = config.get("base_url", "https://api.cohere.ai/v1")
        self.timeout = config.get("timeout", 120)
        # Get session with connection pooling
        self.session = ConnectionPoolManager.get_session(
            "cohere",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Cohere API is available"""
        if not self.api_key:
            return False
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            # Simple check
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Cohere models"""
        if not self.api_key:
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception:
            pass
        
        # Fallback to known models
        return [
            "command",
            "command-light",
            "command-r",
            "command-r-plus",
            "command-r7b-12-2409",
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
        """Generate text using Cohere API"""
        if not self.api_key:
            raise RuntimeError("Cohere API key not configured")
        
        url = f"{self.base_url}/generate"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
        }
        
        if system_prompt:
            payload["preamble"] = system_prompt
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        try:
            session = getattr(self, 'session', None) or requests.Session()
            response = session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                raise RuntimeError(f"Rate limit exceeded. Please wait {retry_after} seconds before trying again.")
            
            response.raise_for_status()
            data = response.json()
            
            return ModelResponse(
                text=data["generations"][0]["text"],
                model=model,
                done=True,
                metadata={
                    "meta": data.get("meta", {}),
                    "finish_reason": data["generations"][0].get("finish_reason"),
                }
            )
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                retry_after = e.response.headers.get('Retry-After', '60')
                raise RuntimeError(f"Rate limit exceeded. Please wait {retry_after} seconds.")
            raise RuntimeError(f"Cohere generation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Cohere generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Cohere API"""
        import aiohttp
        
        if not self.api_key:
            raise RuntimeError("Cohere API key not configured")
        
        url = f"{self.base_url}/generate"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True,
        }
        
        if system_prompt:
            payload["preamble"] = system_prompt
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line:
                        try:
                            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                            data = json.loads(line_str)
                            if "text" in data:
                                yield data["text"]
                            if data.get("is_finished", False):
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
    
    def load_model(self, model: str) -> bool:
        """Load model (Cohere API models are always available if API key is set)"""
        return self.is_available() and model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Configure API key for Cohere models"""
        if not self.api_key:
            return {
                "status": "error",
                "error": "Cohere API key not configured. Please set COHERE_API_KEY environment variable or configure in settings."
            }
        
        return {
            "status": "completed",
            "message": "Cohere API key is configured. Models are ready to use."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Cohere backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "models_count": len(self.list_models()) if self.is_available() else 0
        })
        return info

