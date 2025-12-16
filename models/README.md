# Models Directory

This directory contains model metadata and registry information for LocalMind.

## Contents

- `registry.json` - Model registry file (auto-generated)
  - Stores metadata about downloaded and registered models
  - Includes model information, sizes, descriptions, and tags
  - Automatically updated when models are downloaded via the web interface

## Model Registry

The model registry is managed by `src/core/model_registry.py` and automatically tracks:
- Model names and identifiers
- Model sizes
- Descriptions
- Tags/categories
- Installation status
- Registration timestamps

## Supported Models

LocalMind supports downloading models from Ollama. Popular models include:

### General Purpose Models
- **llama2** - Meta's Llama 2 (3.8GB)
- **llama3** - Meta's Llama 3 (4.7GB)
- **mistral** - Mistral AI 7B (4.1GB)
- **gemma** - Google Gemma (2.0GB)
- **phi3** - Microsoft Phi-3 (2.3GB)

### Code Models
- **codellama** - Code-focused Llama (3.8GB)
- **codellama:13b** - Larger code model (7.3GB)

### Specialized Models
- **deepseek-r1** - Reasoning model (4.7GB)
- **neural-chat** - Conversational AI (4.1GB)
- **starling-lm** - Helpfulness-focused (4.1GB)

## Downloading Models

Models can be downloaded through:
1. **Web Interface** - Use the "Manage Models" button in the web UI
2. **Command Line** - Use `ollama pull <model-name>`
3. **API** - POST to `/api/models/download` with model name

## Model Storage

Ollama models are stored in Ollama's default location (typically `~/.ollama/models` on Linux/Mac or `%USERPROFILE%\.ollama\models` on Windows). The registry in this directory only stores metadata, not the actual model files.

