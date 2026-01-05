"""
Configuration management for LocalMind
Handles loading and validation of configuration files
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml
from dotenv import load_dotenv


class ModelConfig(BaseModel):
    """Configuration for a model"""
    name: str
    backend: str = Field(..., description="Backend type: ollama, transformers, etc.")
    model_id: str = Field(..., description="Model identifier")
    context_size: int = Field(default=4096, description="Context window size")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None


class BackendConfig(BaseModel):
    """Configuration for a backend"""
    type: str
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class LocalMindConfig(BaseModel):
    """Main configuration for LocalMind"""
    default_model: str = "llama2"
    backends: Dict[str, BackendConfig] = Field(default_factory=dict)
    models: Dict[str, ModelConfig] = Field(default_factory=dict)
    video_backends: Dict[str, BackendConfig] = Field(default_factory=dict, description="Video generation backends")
    modules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    storage_path: Path = Field(default_factory=lambda: Path.home() / ".localmind")
    log_level: str = Field(default="INFO")
    # Content filtering settings
    unrestricted_mode: bool = Field(default=True, description="Disable all content filtering for complete freedom")
    disable_safety_filters: bool = Field(default=True, description="Disable safety filters on API backends")
    
    class Config:
        json_encoders = {
            Path: str
        }
    
    def dict(self, **kwargs):
        """Override dict() to convert Path to string"""
        data = super().dict(**kwargs)
        # Convert Path objects to strings
        if isinstance(data.get('storage_path'), Path):
            data['storage_path'] = str(data['storage_path'])
        return data


class ConfigManager:
    """Manages LocalMind configuration"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager"""
        load_dotenv()
        
        if config_path is None:
            config_dir = Path.home() / ".localmind"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.yaml"
        
        self.config_path = config_path
        self.config: Optional[LocalMindConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Try to fix old Path serialization if present
                    import re
                    # Pattern to match: storage_path: !!python/object/apply:pathlib._local.WindowsPath\n    - "path/string"
                    # Replace with: storage_path: "path/string"
                    content = re.sub(
                        r'storage_path:\s*!!python/object/apply:pathlib\._local\.WindowsPath\s*\n\s*-\s*["\']([^"\']+)["\']',
                        r'storage_path: "\1"',
                        content,
                        flags=re.MULTILINE
                    )
                    # Also handle pathlib.Path format
                    content = re.sub(
                        r'storage_path:\s*!!python/object/apply:pathlib\.Path\s*\n\s*-\s*["\']([^"\']+)["\']',
                        r'storage_path: "\1"',
                        content,
                        flags=re.MULTILINE
                    )
                    # Handle any other Path serialization
                    content = re.sub(
                        r'!!python/object/apply:pathlib\._local\.WindowsPath\s*\n\s*-\s*["\']([^"\']+)["\']',
                        r'"\1"',
                        content,
                        flags=re.MULTILINE
                    )
                    data = yaml.safe_load(content) or {}
                
                # Clean up any remaining Path object references
                def clean_paths(obj):
                    if isinstance(obj, dict):
                        cleaned = {}
                        for k, v in obj.items():
                            if isinstance(v, dict) and any(key.startswith('__') for key in v.keys()):
                                # This might be a serialized object, try to extract value
                                if 'storage_path' in k.lower() or 'path' in k.lower():
                                    # Try to find a string value
                                    for subk, subv in v.items():
                                        if isinstance(subv, str) and not subk.startswith('__'):
                                            cleaned[k] = subv
                                            break
                                    else:
                                        cleaned[k] = clean_paths(v)
                                else:
                                    cleaned[k] = clean_paths(v)
                            else:
                                cleaned[k] = clean_paths(v)
                        return cleaned
                    elif isinstance(obj, list):
                        return [clean_paths(item) for item in obj]
                    return obj
                
                data = clean_paths(data)
                
                # Convert storage_path string back to Path if present
                if 'storage_path' in data:
                    if isinstance(data['storage_path'], str):
                        data['storage_path'] = Path(data['storage_path'])
                    elif isinstance(data['storage_path'], dict):
                        # Old serialized format, extract the path
                        path_str = None
                        for key in ['args', 'kwds', 'value']:
                            if key in data['storage_path']:
                                if isinstance(data['storage_path'][key], list) and len(data['storage_path'][key]) > 0:
                                    path_str = data['storage_path'][key][0]
                                    break
                                elif isinstance(data['storage_path'][key], str):
                                    path_str = data['storage_path'][key]
                                    break
                        if path_str:
                            data['storage_path'] = Path(path_str)
                        else:
                            data['storage_path'] = Path.home() / ".localmind"
                    elif not isinstance(data['storage_path'], Path):
                        data['storage_path'] = Path.home() / ".localmind"
                
                self.config = LocalMindConfig(**data)
            except Exception as e:
                # Use ASCII-safe error message
                error_msg = str(e)
                print(f"Warning: Error loading config: {error_msg}")
                print("Creating default configuration...")
                # Backup old config if it exists
                if self.config_path.exists():
                    backup_path = self.config_path.with_suffix('.yaml.backup')
                    try:
                        import shutil
                        shutil.copy2(self.config_path, backup_path)
                        print(f"   Backed up old config to: {backup_path}")
                    except Exception:
                        pass
                self.config = self._create_default_config()
                self.save_config()
        else:
            self.config = self._create_default_config()
            self.save_config()
    
    def _create_default_config(self) -> LocalMindConfig:
        """Create default configuration"""
        return LocalMindConfig(
            default_model="llama2",
            backends={
                "ollama": BackendConfig(
                    type="ollama",
                    enabled=True,
                    settings={
                        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                    }
                ),
                "openai": BackendConfig(
                    type="openai",
                    enabled=False,  # Disabled by default, requires API key
                    settings={
                        "api_key": os.getenv("OPENAI_API_KEY", ""),
                        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                        "organization": os.getenv("OPENAI_ORGANIZATION", "")
                    }
                ),
                "anthropic": BackendConfig(
                    type="anthropic",
                    enabled=False,  # Disabled by default, requires API key
                    settings={
                        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                        "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
                        "api_version": os.getenv("ANTHROPIC_API_VERSION", "2023-06-01")
                    }
                ),
                "google": BackendConfig(
                    type="google",
                    enabled=False,  # Disabled by default, requires API key
                    settings={
                        "api_key": os.getenv("GOOGLE_API_KEY", ""),
                        "base_url": os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com/v1")
                    }
                ),
                "mistral-ai": BackendConfig(
                    type="mistral-ai",
                    enabled=False,  # Disabled by default, requires API key
                    settings={
                        "api_key": os.getenv("MISTRAL_AI_API_KEY", ""),
                        "base_url": os.getenv("MISTRAL_AI_BASE_URL", "https://api.mistral.ai/v1")
                    }
                ),
                "cohere": BackendConfig(
                    type="cohere",
                    enabled=False,  # Disabled by default, requires API key
                    settings={
                        "api_key": os.getenv("COHERE_API_KEY", ""),
                        "base_url": os.getenv("COHERE_BASE_URL", "https://api.cohere.ai/v1")
                    }
                ),
                "groq": BackendConfig(
                    type="groq",
                    enabled=False,  # Disabled by default, requires API key
                    settings={
                        "api_key": os.getenv("GROQ_API_KEY", ""),
                        "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
                    }
                ),
                "transformers": BackendConfig(
                    type="transformers",
                    enabled=False,  # Disabled by default, requires transformers library
                    settings={
                        "cache_dir": os.getenv("TRANSFORMERS_CACHE_DIR", os.path.expanduser("~/.cache/huggingface")),
                        "device": os.getenv("TRANSFORMERS_DEVICE", "auto"),  # auto, cpu, cuda, mps
                        "load_in_8bit": os.getenv("TRANSFORMERS_8BIT", "false").lower() == "true",
                        "load_in_4bit": os.getenv("TRANSFORMERS_4BIT", "false").lower() == "true"
                    }
                ),
                "gguf": BackendConfig(
                    type="gguf",
                    enabled=False,  # Disabled by default, requires llama-cpp-python
                    settings={
                        "models_dir": os.getenv("GGUF_MODELS_DIR", os.path.join(os.getcwd(), "models", "gguf")),
                        "n_threads": None,  # None = auto
                        "n_ctx": 2048,  # Context window size
                        "n_gpu_layers": 0,  # 0 = CPU only, set > 0 for GPU
                    }
                )
            },
            models={
                "llama2": ModelConfig(
                    name="llama2",
                    backend="ollama",
                    model_id="llama2",
                    context_size=4096,
                    temperature=0.7
                )
            },
            video_backends={
                "sora": BackendConfig(
                    type="sora",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("OPENAI_API_KEY", ""),
                        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                ),
                "sora2": BackendConfig(
                    type="sora2",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("OPENAI_API_KEY", "") or os.getenv("SORA2_API_KEY", ""),
                        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300,
                        "use_third_party": os.getenv("SORA2_USE_THIRD_PARTY", "false").lower() == "true",
                        "third_party_url": os.getenv("SORA2_THIRD_PARTY_URL", "")
                    }
                ),
                "runway": BackendConfig(
                    type="runway",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("RUNWAY_API_KEY", ""),
                        "base_url": os.getenv("RUNWAY_BASE_URL", "https://api.runwayml.com/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                ),
                "pika": BackendConfig(
                    type="pika",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("PIKA_API_KEY", ""),
                        "base_url": os.getenv("PIKA_BASE_URL", "https://api.pika.art/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                ),
                "stability": BackendConfig(
                    type="stability",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("STABILITY_API_KEY", ""),
                        "base_url": os.getenv("STABILITY_BASE_URL", "https://api.stability.ai/v2beta"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                ),
                "kling": BackendConfig(
                    type="kling",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("KLING_API_KEY", ""),
                        "base_url": os.getenv("KLING_BASE_URL", "https://api.klingai.com/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                ),
                "luma": BackendConfig(
                    type="luma",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("LUMA_API_KEY", ""),
                        "base_url": os.getenv("LUMA_BASE_URL", "https://api.lumalabs.ai/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                ),
                "haiper": BackendConfig(
                    type="haiper",
                    enabled=False,
                    settings={
                        "api_key": os.getenv("HAIPER_API_KEY", ""),
                        "base_url": os.getenv("HAIPER_BASE_URL", "https://api.haiper.ai/v1"),
                        "video_storage_path": os.path.join(os.getcwd(), "videos"),
                        "timeout": 300
                    }
                )
            }
        )
    
    def save_config(self) -> None:
        """Save configuration to file"""
        if self.config:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert config to dict and handle Path objects
            config_dict = self.config.dict()
            
            # Convert Path objects to strings for YAML serialization
            def convert_paths(obj):
                if isinstance(obj, Path):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_paths(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_paths(item) for item in obj]
                return obj
            
            config_dict = convert_paths(config_dict)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def get_config(self) -> LocalMindConfig:
        """Get current configuration"""
        if self.config is None:
            self._load_config()
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """Update configuration"""
        if self.config:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            self.save_config()

