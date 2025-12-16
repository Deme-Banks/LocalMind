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
    modules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    storage_path: Path = Field(default=Path.home() / ".localmind")
    log_level: str = Field(default="INFO")
    
    class Config:
        json_encoders = {
            Path: str
        }


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
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                self.config = LocalMindConfig(**data)
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
                print("📝 Creating default configuration...")
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
            }
        )
    
    def save_config(self) -> None:
        """Save configuration to file"""
        if self.config:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config.dict(), f, default_flow_style=False, sort_keys=False)
    
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

