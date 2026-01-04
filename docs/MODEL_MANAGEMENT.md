# Model Management Guide

## Overview

LocalMind now includes comprehensive model management features that allow you to:
- View all available Ollama models
- Download models directly from the web interface
- Track model information in the `models/` directory
- Search and filter models
- See which models are installed vs available

## Model Registry

The model registry (`models/registry.json`) automatically tracks:
- Model names and metadata
- Model sizes
- Descriptions and tags
- Installation status
- Registration timestamps

This registry is automatically updated when you download models through the web interface.

## Using the Web Interface

### Accessing Model Manager

1. Start the web server: `python main.py web` or use `start-web.bat`
2. Open `http://localhost:5000` in your browser
3. Click the **"Manage Models"** button in the header

### Downloading Models

1. Open the Model Manager
2. Go to the **"Available Models"** tab
3. Browse the list of available models
4. Click **"Download"** on any model you want
5. Watch the progress in real-time
6. The model will be available once download completes

### Features

- **Search**: Use the search box to filter models by name or description
- **Installed Indicator**: Installed models show a checkmark and green border
- **Model Information**: Each model card shows:
  - Model name
  - Description
  - Size
  - Tags/categories
  - Installation status

### Available Models

The system includes a comprehensive list of popular Ollama models:

#### General Purpose
- llama2, llama3 - Meta's latest models
- mistral - Efficient and capable
- gemma - Google's open model
- phi3 - Microsoft's small but powerful model

#### Code Models
- codellama - Specialized for code generation
- codellama:13b - Larger code model

#### Specialized
- deepseek-r1 - Reasoning-focused
- neural-chat - Conversational AI
- starling-lm - Helpfulness-focused

## API Endpoints

### List Available Models
```bash
GET /api/models/available
```

Returns:
```json
{
  "status": "ok",
  "available": [
    {
      "name": "llama2",
      "size": "3.8GB",
      "description": "Meta's Llama 2 model",
      "tags": ["general", "chat"],
      "installed": false
    }
  ],
  "installed": ["deepseek-r1:latest"]
}
```

### Download Model
```bash
POST /api/models/download
Content-Type: application/json

{
  "model": "llama2"
}
```

Returns:
```json
{
  "status": "ok",
  "download_id": "download_llama2_12345",
  "message": "Download started for llama2"
}
```

### Check Download Progress
```bash
GET /api/models/download/{download_id}
```

Returns:
```json
{
  "status": "ok",
  "progress": {
    "model": "llama2",
    "status": "downloading",
    "progress": 45,
    "message": "Downloading llama2... 45%"
  }
}
```

## Model Storage

### Ollama Models
Ollama models are stored in Ollama's default location:
- **Windows**: `%USERPROFILE%\.ollama\models`
- **Linux/Mac**: `~/.ollama/models`

### Registry
The LocalMind registry is stored in:
- `models/registry.json` - Model metadata and information

## Command Line

You can also download models using Ollama directly:

```bash
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

Models downloaded this way will be detected by LocalMind and shown in the web interface.

## Troubleshooting

### Download Fails
- Ensure Ollama is running: `ollama list`
- Check internet connection
- Verify sufficient disk space
- Check Ollama logs for errors

### Model Not Showing
- Refresh the web page
- Check that Ollama is accessible
- Verify model was downloaded: `ollama list`

### Registry Issues
- The registry file is auto-generated
- If corrupted, delete `models/registry.json` and it will be recreated
- Registry is optional - models work without it

## Best Practices

1. **Start Small**: Download smaller models first (phi3, gemma) to test
2. **Check Space**: Large models (70B) require significant disk space
3. **One at a Time**: Download models one at a time for better progress tracking
4. **Use Search**: Use the search feature to find specific models quickly
5. **Monitor Progress**: Keep the download modal open to see progress

## Next Steps

- Download your first model through the web interface
- Try different models to find what works best for your use case
- Use the search feature to explore available models
- Check the model tags to find specialized models (code, reasoning, etc.)

