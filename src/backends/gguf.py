"""
GGUF backend implementation
Supports GGUF quantized models via llama.cpp
"""

import os
from typing import Dict, Any, Optional, AsyncIterator
from pathlib import Path
import logging

from .base import BaseBackend, ModelResponse

logger = logging.getLogger(__name__)


class GGUFBackend(BaseBackend):
    """Backend for GGUF quantized models (via llama.cpp)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.models_dir = Path(config.get("models_dir", "models/gguf"))
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.n_threads = config.get("n_threads", None)  # None = auto
        self.n_ctx = config.get("n_ctx", 2048)  # Context window size
        self.n_gpu_layers = config.get("n_gpu_layers", 0)  # 0 = CPU only
        self._loaded_models: Dict[str, Any] = {}  # Cache for loaded models
        
    def is_available(self) -> bool:
        """Check if GGUF backend is available (requires llama-cpp-python)"""
        try:
            import llama_cpp
            return True
        except ImportError:
            logger.warning("llama-cpp-python not installed. GGUF backend requires: pip install llama-cpp-python")
            return False
    
    def list_models(self) -> list[str]:
        """List available GGUF models in models directory"""
        if not self.is_available():
            return []
        
        models = []
        if self.models_dir.exists():
            for model_file in self.models_dir.glob("*.gguf"):
                models.append(model_file.stem)
        return sorted(models)
    
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate text using GGUF model"""
        if not self.is_available():
            raise RuntimeError("GGUF backend not available. Install llama-cpp-python: pip install llama-cpp-python")
        
        try:
            import llama_cpp
        except ImportError:
            raise RuntimeError("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        
        # Find model file
        model_path = self.models_dir / f"{model}.gguf"
        if not model_path.exists():
            # Try without extension
            model_path = self.models_dir / model
            if not model_path.exists():
                raise RuntimeError(f"GGUF model not found: {model}")
        
        # Load model if not already loaded
        if model not in self._loaded_models:
            logger.info(f"Loading GGUF model: {model_path}")
            llm = llama_cpp.Llama(
                model_path=str(model_path),
                n_threads=self.n_threads,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
            self._loaded_models[model] = llm
        else:
            llm = self._loaded_models[model]
        
        # Build full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Generate
        try:
            response = llm(
                full_prompt,
                temperature=temperature,
                max_tokens=max_tokens or 512,
                stop=kwargs.get("stop", []),
                echo=False
            )
            
            text = response["choices"][0]["text"]
            
            return ModelResponse(
                text=text,
                model=model,
                done=True,
                metadata={
                    "usage": response.get("usage", {}),
                    "model_path": str(model_path)
                }
            )
        except Exception as e:
            raise RuntimeError(f"GGUF generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using GGUF model"""
        if not self.is_available():
            raise RuntimeError("GGUF backend not available. Install llama-cpp-python: pip install llama-cpp-python")
        
        try:
            import llama_cpp
        except ImportError:
            raise RuntimeError("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        
        # Find model file
        model_path = self.models_dir / f"{model}.gguf"
        if not model_path.exists():
            model_path = self.models_dir / model
            if not model_path.exists():
                raise RuntimeError(f"GGUF model not found: {model}")
        
        # Load model if not already loaded
        if model not in self._loaded_models:
            logger.info(f"Loading GGUF model: {model_path}")
            llm = llama_cpp.Llama(
                model_path=str(model_path),
                n_threads=self.n_threads,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
            self._loaded_models[model] = llm
        else:
            llm = self._loaded_models[model]
        
        # Build full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Stream generation
        try:
            stream = llm(
                full_prompt,
                temperature=temperature,
                max_tokens=max_tokens or 512,
                stop=kwargs.get("stop", []),
                echo=False,
                stream=True
            )
            
            for chunk in stream:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("text", "")
                    if delta:
                        yield delta
        except Exception as e:
            raise RuntimeError(f"GGUF streaming failed: {e}")
    
    def load_model(self, model: str) -> bool:
        """Load a GGUF model into memory"""
        if not self.is_available():
            return False
        
        model_path = self.models_dir / f"{model}.gguf"
        if not model_path.exists():
            model_path = self.models_dir / model
            if not model_path.exists():
                return False
        
        if model not in self._loaded_models:
            try:
                import llama_cpp
                logger.info(f"Loading GGUF model: {model_path}")
                llm = llama_cpp.Llama(
                    model_path=str(model_path),
                    n_threads=self.n_threads,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    verbose=False
                )
                self._loaded_models[model] = llm
                return True
            except Exception as e:
                logger.error(f"Failed to load GGUF model {model}: {e}")
                return False
        
        return True
    
    def unload_model(self, model: str) -> bool:
        """Unload a GGUF model from memory"""
        if model in self._loaded_models:
            # llama-cpp-python doesn't have explicit unload, but we can delete the reference
            del self._loaded_models[model]
            return True
        return False
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """Download a GGUF model (placeholder - requires manual download)"""
        return {
            "status": "info",
            "message": f"GGUF models must be downloaded manually. Place {model}.gguf in {self.models_dir}. You can download GGUF models from HuggingFace or other sources."
        }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get GGUF backend information"""
        info = super().get_backend_info()
        info.update({
            "type": "gguf",
            "available": self.is_available(),
            "models_dir": str(self.models_dir),
            "loaded_models": list(self._loaded_models.keys()),
            "models_count": len(self.list_models()),
            "n_threads": self.n_threads,
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers
        })
        return info

