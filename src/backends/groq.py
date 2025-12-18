"""
Groq backend implementation
Supports Groq API models (fast inference)
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json

from .base import BaseBackend, ModelResponse
from ..core.connection_pool import ConnectionPoolManager


class GroqBackend(BaseBackend):
    """Backend for Groq API models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("GROQ_API_KEY")
        self.base_url = config.get("base_url", "https://api.groq.com/openai/v1")
        self.timeout = config.get("timeout", 120)
        # Get session with connection pooling
        self.session = ConnectionPoolManager.get_session(
            "groq",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if Groq API is available"""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
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
        """List available Groq models"""
        if not self.api_key:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
        except Exception:
            pass
        
        # Fallback to known models
        return [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
            "llama-3-70b-8192",
            "llama-3-8b-8192",
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
        """Generate text using Groq API (OpenAI-compatible)"""
        if not self.api_key:
            raise RuntimeError("Groq API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
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
                text=data["choices"][0]["message"]["content"],
                model=model,
                done=True,
                metadata={
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                }
            )
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                retry_after = e.response.headers.get('Retry-After', '60')
                raise RuntimeError(f"Rate limit exceeded. Please wait {retry_after} seconds.")
            raise RuntimeError(f"Groq generation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Groq generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Groq API"""
        import aiohttp
        
        if not self.api_key:
            raise RuntimeError("Groq API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
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
                            if line_str.startswith('data: '):
                                data_str = line_str[6:].strip()
                                if data_str == '[DONE]':
                                    break
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
    
    def load_model(self, model: str) -> bool:
        """Load model (Groq API models are always available if API key is set)"""
        return self.is_available() and model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Configure API key for Groq models"""
        if not self.api_key:
            return {
                "status": "error",
                "error": "Groq API key not configured. Please set GROQ_API_KEY environment variable or configure in settings."
            }
        
        return {
            "status": "completed",
            "message": "Groq API key is configured. Models are ready to use."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Groq backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "models_count": len(self.list_models()) if self.is_available() else 0
        })
        return info

