"""
Anthropic backend implementation
Supports Claude API models
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json

from .base import BaseBackend, ModelResponse
from ..core.connection_pool import ConnectionPoolManager


class AnthropicBackend(BaseBackend):
    """Backend for Anthropic Claude API models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")
        self.timeout = config.get("timeout", 120)
        self.api_version = config.get("api_version", "2023-06-01")
        # Get session with connection pooling
        self.session = ConnectionPoolManager.get_session(
            "anthropic",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Anthropic API is available"""
        if not self.api_key:
            return False
        try:
            # Simple check - try to list messages (we'll use a lightweight endpoint)
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.api_version,
                "content-type": "application/json"
            }
            # Just check if we can reach the API
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url.replace('/v1', '')}/v1/models",
                headers={"x-api-key": self.api_key},
                timeout=5
            )
            return response.status_code in [200, 404]  # 404 is OK, means API is reachable
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Anthropic models"""
        if not self.api_key:
            return []
        
        # Anthropic's available models (as of 2024)
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
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
        """Generate text using Anthropic API"""
        if not self.api_key:
            raise RuntimeError("Anthropic API key not configured")
        
        url = f"{self.base_url}/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        payload.update(kwargs)
        
        try:
            session = getattr(self, 'session', None) or requests.Session()
            response = session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return ModelResponse(
                text=data["content"][0]["text"],
                model=model,
                done=True,
                metadata={
                    "usage": data.get("usage", {}),
                    "stop_reason": data.get("stop_reason"),
                }
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Anthropic API"""
        import aiohttp
        
        if not self.api_key:
            raise RuntimeError("Anthropic API key not configured")
        
        url = f"{self.base_url}/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        payload.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line:
                        try:
                            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                            if line_str.startswith('data: '):
                                data_str = line_str[6:].strip()
                                if data_str == '[DONE]':
                                    break
                                data = json.loads(data_str)
                                if "delta" in data and "text" in data["delta"]:
                                    yield data["delta"]["text"]
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
    
    def load_model(self, model: str) -> bool:
        """Load model (Anthropic API models are always available if API key is set)"""
        return self.is_available() and model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Configure API key for Anthropic models"""
        if not self.api_key:
            return {
                "status": "error",
                "error": "Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable or configure in settings."
            }
        
        return {
            "status": "completed",
            "message": "Anthropic API key is configured. Models are ready to use."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Anthropic backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "models_count": len(self.list_models()) if self.is_available() else 0
        })
        return info

