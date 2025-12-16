"""
Mistral AI backend implementation
Supports Mistral AI API models
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator
import json

from .base import BaseBackend, ModelResponse


class MistralAIBackend(BaseBackend):
    """Backend for Mistral AI API models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("MISTRAL_AI_API_KEY")
        self.base_url = config.get("base_url", "https://api.mistral.ai/v1")
        self.timeout = config.get("timeout", 120)
    
    def is_available(self) -> bool:
        """Check if Mistral AI API is available"""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Mistral AI models"""
        if not self.api_key:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
        except:
            pass
        
        # Fallback to known models
        return [
            "mistral-tiny",
            "mistral-small",
            "mistral-medium",
            "mistral-large",
            "mistral-large-latest",
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
        """Generate text using Mistral AI API"""
        if not self.api_key:
            raise RuntimeError("Mistral AI API key not configured")
        
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
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
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
        except Exception as e:
            raise RuntimeError(f"Mistral AI generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Mistral AI API"""
        import aiohttp
        
        if not self.api_key:
            raise RuntimeError("Mistral AI API key not configured")
        
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
        """Load model (Mistral AI API models are always available if API key is set)"""
        return self.is_available() and model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Configure API key for Mistral AI models"""
        if not self.api_key:
            return {
                "status": "error",
                "error": "Mistral AI API key not configured. Please set MISTRAL_AI_API_KEY environment variable or configure in settings."
            }
        
        return {
            "status": "completed",
            "message": "Mistral AI API key is configured. Models are ready to use."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Mistral AI backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "models_count": len(self.list_models()) if self.is_available() else 0
        })
        return info

