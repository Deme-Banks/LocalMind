"""
Ollama backend implementation
Supports local Ollama models
"""

import requests
from typing import Dict, Any, Optional, AsyncIterator
import asyncio
import json

from .base import BaseBackend, ModelResponse


class OllamaBackend(BaseBackend):
    """Backend for Ollama models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.timeout = config.get("timeout", 120)
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """List available Ollama models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
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
        """Generate text using Ollama"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Merge additional options
        if "options" in kwargs:
            payload["options"].update(kwargs["options"])
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return ModelResponse(
                text=data.get("response", ""),
                model=model,
                done=data.get("done", True),
                metadata={
                    "context": data.get("context", []),
                    "total_duration": data.get("total_duration", 0),
                    "load_duration": data.get("load_duration", 0),
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0),
                }
            )
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Ollama"""
        import aiohttp
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if "options" in kwargs:
            payload["options"].update(kwargs["options"])
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line:
                        try:
                            # Decode bytes to string
                            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                            data = json.loads(line_str)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
    
    def load_model(self, model: str) -> bool:
        """Load model (Ollama handles this automatically)"""
        # Ollama loads models on-demand, so we just check if it's available
        return model in self.list_models()
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """
        Download a model via Ollama
        
        Args:
            model: Model name to download
        
        Returns:
            Dictionary with download information
        """
        import subprocess
        import sys
        import re
        
        try:
            # Set up environment for UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Run ollama pull command
            process = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                env=env,
                universal_newlines=False
            )
            
            return {
                "status": "started",
                "process": process,
                "model": model
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_model(self, model: str) -> Dict[str, Any]:
        """
        Delete a model from Ollama.
        
        Args:
            model: Model name to delete
        
        Returns:
            Dictionary with deletion status and information
        """
        import subprocess
        
        try:
            # Run ollama rm command
            process = subprocess.Popen(
                ["ollama", "rm", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return {
                    "status": "ok",
                    "message": f"Model '{model}' deleted successfully",
                    "model": model
                }
            else:
                return {
                    "status": "error",
                    "error": stderr or f"Failed to delete model '{model}'",
                    "model": model
                }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error deleting model: {str(e)}",
                "model": model
            }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Ollama backend information"""
        info = super().get_backend_info()
        info.update({
            "base_url": self.base_url,
            "available": self.is_available()
        })
        return info

