# API Models Guide

## Overview

LocalMind now supports multiple API-based AI models including ChatGPT, Claude, Gemini, and more. These models don't require downloading - they just need API key configuration.

## Available API Backends

### OpenAI (ChatGPT)
**Models Available:**
- **GPT-3.5 Turbo** - Fast and efficient
  - `gpt-3.5-turbo`
  - `gpt-3.5-turbo-16k` (larger context)
  - `gpt-3.5-turbo-1106`, `gpt-3.5-turbo-0125` (latest versions)

- **GPT-4** - Most capable
  - `gpt-4`
  - `gpt-4-turbo` (faster)
  - `gpt-4-turbo-preview` (latest features)
  - `gpt-4-32k` (very large context)

- **GPT-4o** - Optimized (Latest)
  - `gpt-4o`
  - `gpt-4o-mini` (smaller, faster)

**Setup:**
1. Get API key from: https://platform.openai.com/api-keys
2. Set environment variable: `OPENAI_API_KEY=your_key_here`
3. Or configure in `~/.localmind/config.yaml`
4. Restart LocalMind server

### Anthropic (Claude)
**Models Available:**
- `claude-3-opus` - Most capable
- `claude-3-sonnet` - Balanced
- `claude-3-haiku` - Fast and efficient
- `claude-3-5-sonnet` - Latest generation
- `claude-2`, `claude-2.1` - Previous generation

**Setup:**
1. Get API key from: https://console.anthropic.com/
2. Set: `ANTHROPIC_API_KEY=your_key_here`
3. Restart server

### Google (Gemini)
**Models Available:**
- `gemini-pro` - Advanced model
- `gemini-pro-vision` - With image support
- `gemini-1.5-pro` - Latest generation
- `gemini-1.5-flash` - Fast and efficient
- `gemini-ultra` - Most capable

**Setup:**
1. Get API key from: https://makersuite.google.com/app/apikey
2. Set: `GOOGLE_API_KEY=your_key_here`
3. Restart server

### Mistral AI
**Models Available:**
- `mistral-tiny` - Smallest
- `mistral-small` - Balanced
- `mistral-medium` - Capable
- `mistral-large` - Most capable

**Setup:**
1. Get API key from: https://console.mistral.ai/
2. Set: `MISTRAL_AI_API_KEY=your_key_here`
3. Restart server

### Cohere
**Models Available:**
- `command` - General purpose
- `command-light` - Faster
- `command-r` - Advanced
- `command-r-plus` - Most capable

**Setup:**
1. Get API key from: https://dashboard.cohere.com/api-keys
2. Set: `COHERE_API_KEY=your_key_here`
3. Restart server

## Using API Models

### Via Web Interface

1. **Start the server**: `python main.py web`
2. **Open Model Manager**: Click "Manage Models"
3. **Go to Available Models tab**
4. **Find the API backend section** (e.g., "Openai Backend")
5. **Click "Setup"** on any model
6. **Configure API key** if prompted
7. **Start using the model!**

### Via Configuration

Edit `~/.localmind/config.yaml`:

```yaml
backends:
  openai:
    type: openai
    enabled: true
    settings:
      api_key: "sk-your-key-here"
      base_url: "https://api.openai.com/v1"
  
  anthropic:
    type: anthropic
    enabled: true
    settings:
      api_key: "your-key-here"
```

### Via Environment Variables

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"
$env:ANTHROPIC_API_KEY="your-key-here"

# Linux/Mac
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

## Model Comparison

| Model | Speed | Capability | Cost | Best For |
|-------|-------|------------|------|----------|
| GPT-3.5 Turbo | ⚡⚡⚡ | ⭐⭐⭐ | $ | Fast responses, general tasks |
| GPT-4 | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$$ | Complex reasoning, best quality |
| GPT-4o | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ | Balanced speed and quality |
| Claude 3 Opus | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$$ | Complex analysis, long context |
| Claude 3 Haiku | ⚡⚡⚡ | ⭐⭐⭐⭐ | $ | Fast, efficient responses |
| Gemini Pro | ⚡⚡ | ⭐⭐⭐⭐ | $$ | Multimodal, good balance |

## Pricing Notes

- **API models charge per token** - usage-based pricing
- **Local models (Ollama) are free** - but require hardware
- **Choose based on your needs**:
  - High volume → Local models
  - Best quality → GPT-4, Claude Opus
  - Fast responses → GPT-3.5, Claude Haiku
  - Budget-friendly → Local models or smaller APIs

## Troubleshooting

### "API key not configured"
- Set the environment variable
- Or configure in `config.yaml`
- Restart the server after setting

### "Backend not available"
- Check API key is correct
- Verify internet connection
- Check API service status
- Review error logs

### Models not showing
- Ensure backend is enabled in config
- Check API key is set
- Refresh the web page
- Restart the server

## Security

⚠️ **Important**: Never commit API keys to version control!

- Use environment variables
- Store keys securely
- Rotate keys regularly
- Use separate keys for development/production

## Next Steps

1. Choose your API provider
2. Get an API key
3. Configure it (env var or config file)
4. Restart LocalMind
5. Start using API models!

For local models, continue using Ollama. For cloud models, use the API backends.

