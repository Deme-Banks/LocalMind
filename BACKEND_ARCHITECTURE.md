# Backend Architecture

## Overview

LocalMind is designed to be **backend-agnostic**, meaning it supports multiple AI backends, not just Ollama. Ollama is one of many backends the system can use.

## Backend System

### Base Backend Interface

All backends must implement the `BaseBackend` interface (`src/backends/base.py`):

- `is_available()` - Check if backend is ready
- `list_models()` - List available models
- `generate()` - Generate text from a prompt
- `generate_stream()` - Stream text generation
- `load_model()` - Load a model into memory
- `download_model()` - Download a model (optional)
- `get_backend_info()` - Get backend information

### Supported Backends

#### 1. Ollama Backend (`src/backends/ollama.py`)
- **Type**: `ollama`
- **Description**: Local Ollama models
- **Supports Downloads**: Yes
- **Models**: 50+ models available

#### 2. Transformers Backend (Planned)
- **Type**: `transformers`
- **Description**: HuggingFace Transformers models
- **Supports Downloads**: Yes (via HuggingFace Hub)
- **Status**: Framework ready, implementation pending

#### 3. OpenAI Backend (Planned)
- **Type**: `openai`
- **Description**: OpenAI API compatibility
- **Supports Downloads**: No (API-based)
- **Status**: Framework ready, implementation pending

### Adding New Backends

To add a new backend:

1. **Create Backend Class** (`src/backends/your_backend.py`):
```python
from .base import BaseBackend, ModelResponse

class YourBackend(BaseBackend):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your backend
    
    def is_available(self) -> bool:
        # Check if backend is available
        pass
    
    def list_models(self) -> list[str]:
        # Return list of available models
        pass
    
    def generate(self, prompt, model, **kwargs) -> ModelResponse:
        # Generate text
        pass
    
    # ... implement other required methods
```

2. **Register in Model Loader** (`src/core/model_loader.py`):
```python
elif backend_config.type == "your_backend":
    backend = YourBackend(backend_config.settings)
    if backend.is_available():
        self.backends[backend_name] = backend
```

3. **Add Models to Registry** (`src/core/model_registry.py`):
```python
def _get_your_backend_models(self) -> List[Dict[str, Any]]:
    return [
        {"name": "model1", "size": "1GB", "description": "...", "tags": [...]},
        # ...
    ]
```

4. **Update Config** - Add backend to default config

## Model Registry

The model registry (`src/core/model_registry.py`) manages models for all backends:

- **Backend-specific model lists**: Each backend has its own model catalog
- **Unified interface**: Same API for all backends
- **Metadata tracking**: Size, description, tags for each model
- **Installation status**: Tracks which models are installed

## Web Interface

The web interface now shows:

- **Backend sections**: Models grouped by backend
- **Backend status**: Shows if backend is available
- **Backend-specific downloads**: Each backend handles its own downloads
- **Unified model selection**: Choose from any backend

## Configuration

Backends are configured in `~/.localmind/config.yaml`:

```yaml
backends:
  ollama:
    type: ollama
    enabled: true
    settings:
      base_url: http://localhost:11434
  
  transformers:
    type: transformers
    enabled: false
    settings:
      cache_dir: ~/.cache/huggingface
```

## API Endpoints

### List Available Models (All Backends)
```
GET /api/models/available
```

Returns:
```json
{
  "status": "ok",
  "backends": {
    "ollama": {
      "info": {...},
      "models": [...],
      "installed": [...]
    },
    "transformers": {
      "info": {...},
      "models": [...],
      "installed": [...]
    }
  }
}
```

### Download Model
```
POST /api/models/download
{
  "model": "llama2",
  "backend": "ollama"
}
```

## Benefits

1. **Flexibility**: Use any backend that fits your needs
2. **Extensibility**: Easy to add new backends
3. **Unified Interface**: Same API for all backends
4. **Future-Proof**: Not locked into one solution
5. **Best Tool for the Job**: Choose the right backend for each use case

## Future Backends

Potential backends to add:

- **Transformers**: HuggingFace models
- **OpenAI**: API compatibility
- **Anthropic**: Claude API
- **GGUF**: Direct GGUF file support
- **vLLM**: High-performance inference
- **TensorRT**: NVIDIA optimized inference

## Migration Notes

If you're upgrading from the Ollama-only version:

- All existing Ollama functionality still works
- Models are now organized by backend
- Web interface shows backends separately
- API now requires `backend` parameter for downloads (defaults to "ollama" for compatibility)

