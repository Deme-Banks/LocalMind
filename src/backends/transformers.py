"""
Transformers backend implementation
Supports local HuggingFace models via transformers library
"""

import os
from typing import Dict, Any, Optional, AsyncIterator
import asyncio
import logging
from pathlib import Path

from .base import BaseBackend, ModelResponse

logger = logging.getLogger(__name__)

# Try to import transformers - make it optional
try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        pipeline, TextGenerationPipeline
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None
    logger.warning("Transformers library not available. Install with: pip install transformers torch")


class TransformersBackend(BaseBackend):
    """Backend for HuggingFace Transformers models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cache_dir = config.get("cache_dir", os.path.expanduser("~/.cache/huggingface"))
        self.device = config.get("device", "auto")  # "auto", "cpu", "cuda", "mps"
        self.load_in_8bit = config.get("load_in_8bit", False)
        self.load_in_4bit = config.get("load_in_4bit", False)
        self.max_memory = config.get("max_memory", None)
        
        # Store loaded models in memory
        self.loaded_models: Dict[str, Any] = {}
        self.loaded_tokenizers: Dict[str, Any] = {}
        self.loaded_pipelines: Dict[str, TextGenerationPipeline] = {}
        
        # Auto-detect device
        if self.device == "auto" and TRANSFORMERS_AVAILABLE:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        elif self.device == "auto":
            self.device = "cpu"
    
    def is_available(self) -> bool:
        """Check if transformers backend is available"""
        if not TRANSFORMERS_AVAILABLE or torch is None:
            return False
        
        try:
            # Check basic functionality
            return True
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """
        List available models (models that are downloaded/cached)
        
        Returns:
            List of model identifiers
        """
        if not TRANSFORMERS_AVAILABLE:
            return []
        
        models = []
        cache_path = Path(self.cache_dir) / "hub"
        
        if cache_path.exists():
            # Look for downloaded models in cache
            for model_dir in cache_path.iterdir():
                if model_dir.is_dir():
                    # Check if it has required files
                    if (model_dir / "config.json").exists():
                        models.append(model_dir.name)
        
        # Also check loaded models
        models.extend(self.loaded_models.keys())
        
        # Remove duplicates and return
        return sorted(list(set(models)))
    
    def _get_model_path(self, model: str) -> Optional[Path]:
        """Get local path for a model"""
        cache_path = Path(self.cache_dir) / "hub"
        model_path = cache_path / model
        
        if model_path.exists() and (model_path / "config.json").exists():
            return model_path
        
        # Try to find in subdirectories
        for subdir in cache_path.iterdir():
            if subdir.is_dir():
                model_path = subdir / model
                if model_path.exists() and (model_path / "config.json").exists():
                    return model_path
        
        return None
    
    def load_model(self, model: str) -> bool:
        """
        Load a model into memory
        
        Args:
            model: Model identifier (HuggingFace model ID or path)
        
        Returns:
            True if model loaded successfully
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.error("Transformers library not available")
            return False
        
        if model in self.loaded_models:
            logger.info(f"Model {model} already loaded")
            return True
        
        try:
            logger.info(f"Loading model {model} on device {self.device}...")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # Set pad token if not set
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Prepare model loading kwargs
            model_kwargs = {
                "cache_dir": self.cache_dir,
                "trust_remote_code": True,
            }
            
            # Add quantization if requested
            if self.load_in_8bit or self.load_in_4bit:
                try:
                    from transformers import BitsAndBytesConfig
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=self.load_in_8bit,
                        load_in_4bit=self.load_in_4bit,
                    )
                    model_kwargs["quantization_config"] = quantization_config
                except ImportError:
                    logger.warning("bitsandbytes not available, skipping quantization")
            
            # Load model
            model_obj = AutoModelForCausalLM.from_pretrained(
                model,
                device_map="auto" if self.device == "cuda" else None,
                max_memory=self.max_memory,
                **model_kwargs
            )
            
            # Move to device if not using device_map
            if self.device != "cuda" or "device_map" not in model_kwargs:
                model_obj = model_obj.to(self.device)
            
            # Create pipeline
            pipeline_obj = pipeline(
                "text-generation",
                model=model_obj,
                tokenizer=tokenizer,
                device=0 if self.device == "cuda" else -1,
            )
            
            # Store loaded components
            self.loaded_models[model] = model_obj
            self.loaded_tokenizers[model] = tokenizer
            self.loaded_pipelines[model] = pipeline_obj
            
            logger.info(f"✅ Model {model} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model}: {e}")
            return False
    
    def unload_model(self, model: str) -> bool:
        """
        Unload a model from memory
        
        Args:
            model: Model identifier
        
        Returns:
            True if model unloaded successfully
        """
        if model in self.loaded_models:
            try:
                # Clear references
                del self.loaded_models[model]
                del self.loaded_tokenizers[model]
                del self.loaded_pipelines[model]
                
                # Force garbage collection
                import gc
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                
                logger.info(f"Model {model} unloaded")
                return True
            except Exception as e:
                logger.error(f"Failed to unload model {model}: {e}")
                return False
        return True
    
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate text using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available")
        
        # Load model if not loaded
        if model not in self.loaded_pipelines:
            if not self.load_model(model):
                raise RuntimeError(f"Failed to load model {model}")
        
        pipeline_obj = self.loaded_pipelines[model]
        
        # Build full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Generation parameters
        generation_kwargs = {
            "temperature": temperature,
            "do_sample": temperature > 0,
            "max_new_tokens": max_tokens or 512,
            "pad_token_id": self.loaded_tokenizers[model].eos_token_id,
            **kwargs
        }
        
        try:
            # Generate
            outputs = pipeline_obj(
                full_prompt,
                return_full_text=False,
                **generation_kwargs
            )
            
            # Extract generated text
            if isinstance(outputs, list) and len(outputs) > 0:
                generated_text = outputs[0].get("generated_text", "")
            else:
                generated_text = str(outputs)
            
            return ModelResponse(
                text=generated_text,
                model=model,
                done=True,
                metadata={
                    "device": self.device,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            )
        except Exception as e:
            raise RuntimeError(f"Transformers generation failed: {e}")
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Generate streaming text using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available")
        
        # Load model if not loaded
        if model not in self.loaded_pipelines:
            if not self.load_model(model):
                raise RuntimeError(f"Failed to load model {model}")
        
        pipeline_obj = self.loaded_pipelines[model]
        tokenizer = self.loaded_tokenizers[model]
        
        # Build full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Tokenize
        inputs = tokenizer(full_prompt, return_tensors="pt").to(self.device)
        
        # Generation parameters
        generation_kwargs = {
            "temperature": temperature,
            "do_sample": temperature > 0,
            "max_new_tokens": max_tokens or 512,
            "pad_token_id": tokenizer.eos_token_id,
            **kwargs
        }
        
        # For streaming, we need to generate token by token
        # This is a simplified version - full streaming requires more complex setup
        model_obj = self.loaded_models[model]
        
        try:
            with torch.no_grad():
                generated_ids = model_obj.generate(
                    **inputs,
                    **generation_kwargs,
                    streamer=None  # We'll implement custom streaming
                )
            
            # Decode and yield chunks
            generated_text = tokenizer.decode(
                generated_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )
            
            # Yield in chunks (simulate streaming)
            chunk_size = 10
            for i in range(0, len(generated_text), chunk_size):
                chunk = generated_text[i:i + chunk_size]
                if chunk:
                    yield chunk
                    await asyncio.sleep(0.01)  # Small delay to simulate streaming
                    
        except Exception as e:
            raise RuntimeError(f"Transformers streaming failed: {e}")
    
    def download_model(self, model: str) -> Dict[str, Any]:
        """
        Download a model from HuggingFace
        
        Args:
            model: HuggingFace model identifier (e.g., "gpt2", "microsoft/DialoGPT-medium")
        
        Returns:
            Dictionary with download status
        """
        if not TRANSFORMERS_AVAILABLE:
            return {
                "status": "error",
                "error": "Transformers library not available"
            }
        
        try:
            logger.info(f"Downloading model {model} from HuggingFace...")
            
            # Download tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # Download model (just config and tokenizer for now)
            # Full model download happens on first load
            _ = AutoModelForCausalLM.from_pretrained(
                model,
                cache_dir=self.cache_dir,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            return {
                "status": "completed",
                "message": f"Model {model} downloaded successfully",
                "model": model,
                "cache_dir": self.cache_dir
            }
        except Exception as e:
            logger.error(f"Failed to download model {model}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get Transformers backend information"""
        info = super().get_backend_info()
        info.update({
            "available": self.is_available(),
            "device": self.device,
            "cache_dir": self.cache_dir,
            "loaded_models": list(self.loaded_models.keys()),
            "cuda_available": torch.cuda.is_available() if (TRANSFORMERS_AVAILABLE and torch is not None) else False,
            "mps_available": (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()) if (TRANSFORMERS_AVAILABLE and torch is not None) else False,
        })
        return info

