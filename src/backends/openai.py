"""
OpenAI backend implementation
Supports OpenAI API models (GPT-3.5, GPT-4, etc.)
"""

import os
import requests
from typing import Dict, Any, Optional, AsyncIterator, List
import json

from .base import BaseBackend, ModelResponse
from ..core.connection_pool import ConnectionPoolManager


class OpenAIBackend(BaseBackend):
    """Backend for OpenAI API models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.timeout = config.get("timeout", 120)
        self.organization = config.get("organization")
        # Get session with connection pooling
        self.session = ConnectionPoolManager.get_session(
            "openai",
            self.base_url,
            config.get("pool_config")
        )
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        if not self.api_key:
            return False
        try:
            # Simple check - try to list models
            headers = {"Authorization": f"Bearer {self.api_key}"}
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
            
            # Use pooled session if available, otherwise create temporary
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
        """List available OpenAI models"""
        if not self.api_key:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
            
            # Use pooled session if available
            session = getattr(self, 'session', None) or requests.Session()
            response = session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Filter to chat models
                chat_models = [
                    model["id"] for model in data.get("data", [])
                    if "gpt" in model["id"].lower() or "chat" in model.get("id", "").lower()
                ]
                return sorted(chat_models)
            return []
        except Exception:
            return []
    
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate text using OpenAI API"""
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
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
        
        # Merge additional parameters
        payload.update(kwargs)
        
        try:
            # Use pooled session for connection reuse
            response = self.session.post(
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
            raise RuntimeError(f"OpenAI generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using OpenAI API"""
        import aiohttp
        
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
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
    
    def supports_tool_calling(self) -> bool:
        """OpenAI API supports function calling"""
        return True
    
    def generate_with_tools(
        self,
        prompt: str,
        model: str,
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate text with tool calling support"""
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "tools": tools,  # Add tools
            "tool_choice": "auto"  # Let model decide when to use tools
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        try:
            # Use pooled session for connection reuse
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            message = data["choices"][0]["message"]
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            
            return ModelResponse(
                text=content,
                model=model,
                done=True,
                metadata={
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "tool_calls": tool_calls  # Include tool calls in metadata
                }
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI generation with tools failed: {e}")
    
    def load_model(self, model: str) -> bool:
        """Load model (OpenAI API models are always available if API key is set)"""
        return self.is_available() and model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """
        Configure API key for OpenAI models (not a download, but setup)
        
        Args:
            model: Model name (not used, but kept for interface compatibility)
        
        Returns:
            Dictionary with setup information
        """
        if not self.api_key:
            return {
                "status": "error",
                "error": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable or configure in settings."
            }
        
        return {
            "status": "completed",
            "message": "OpenAI API key is configured. Models are ready to use."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get OpenAI backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available(),
            "has_api_key": bool(self.api_key),
            "models_count": len(self.list_models()) if self.is_available() else 0
        })
        return info

