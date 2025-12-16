# API Configuration Guide

LocalMind supports multiple AI providers. This guide explains how to configure API keys for each provider.

## Quick Start

### Option 1: Web Interface (Recommended)
1. Start the web server: `python main.py web` or use `start-web.bat`
2. Navigate to http://localhost:5000/configure
3. Enter API keys for each provider you want to use
4. Enable the backends you want to use
5. Restart the server for changes to take effect

### Option 2: Command Line
```bash
python main.py configure
```

### Option 3: Standalone Script
```bash
python configure_apis.py
```
Or on Windows:
```bash
configure-apis.bat
```

### Option 4: Environment Variables
Set environment variables before starting the server:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "your-key-here"
$env:ANTHROPIC_API_KEY = "your-key-here"
$env:GOOGLE_API_KEY = "your-key-here"
$env:MISTRAL_AI_API_KEY = "your-key-here"
$env:COHERE_API_KEY = "your-key-here"
$env:GROQ_API_KEY = "your-key-here"

# Windows CMD
set OPENAI_API_KEY=your-key-here
set ANTHROPIC_API_KEY=your-key-here

# Linux/Mac
export OPENAI_API_KEY=your-key-here
export ANTHROPIC_API_KEY=your-key-here
```

## Supported Providers

### 1. OpenAI (ChatGPT)
- **Setup URL**: https://platform.openai.com/api-keys
- **Environment Variable**: `OPENAI_API_KEY`
- **Models**: GPT-4, GPT-3.5, and more
- **Cost**: Pay per use

### 2. Anthropic (Claude)
- **Setup URL**: https://console.anthropic.com/
- **Environment Variable**: `ANTHROPIC_API_KEY`
- **Models**: Claude 3 Opus, Sonnet, Haiku
- **Cost**: Pay per use

### 3. Google (Gemini)
- **Setup URL**: https://makersuite.google.com/app/apikey
- **Environment Variable**: `GOOGLE_API_KEY`
- **Models**: Gemini Pro, Gemini Ultra
- **Cost**: Free tier available

### 4. Mistral AI
- **Setup URL**: https://console.mistral.ai/
- **Environment Variable**: `MISTRAL_AI_API_KEY`
- **Models**: Mistral Large, Medium, Small
- **Cost**: Pay per use

### 5. Cohere
- **Setup URL**: https://dashboard.cohere.com/api-keys
- **Environment Variable**: `COHERE_API_KEY`
- **Models**: Command, Command Light, Aya
- **Cost**: Free tier available

### 6. Groq (Fast Inference)
- **Setup URL**: https://console.groq.com/keys
- **Environment Variable**: `GROQ_API_KEY`
- **Models**: Llama 3, Mixtral, Gemma
- **Cost**: Free tier available, very fast inference

## Configuration File

API keys are stored in the configuration file at:
- **Windows**: `%USERPROFILE%\.localmind\config.yaml`
- **Linux/Mac**: `~/.localmind/config.yaml`

You can also edit this file directly, but be careful with formatting:
```yaml
backends:
  openai:
    type: openai
    enabled: true
    settings:
      api_key: "sk-..."
  anthropic:
    type: anthropic
    enabled: true
    settings:
      api_key: "sk-ant-..."
```

## Enabling/Disabling Backends

After setting API keys, you need to enable the backend:

1. **Web Interface**: Check the "Enable this backend" checkbox and click Save
2. **CLI**: Use `python main.py configure` and select option 2 (Enable backend)
3. **Config File**: Set `enabled: true` in the backend configuration

## Verification

After configuring, verify your setup:

```bash
python main.py status
```

Or check in the web interface at http://localhost:5000 - the status indicator will show which backends are available.

## Troubleshooting

### "Backend not available" Error
- Check that the API key is set correctly
- Verify the backend is enabled in configuration
- Ensure you have an internet connection
- Check the provider's status page for outages

### "Invalid API key" Error
- Verify the API key is correct (no extra spaces)
- Check that the API key hasn't expired
- Ensure you have credits/quota remaining

### Changes Not Taking Effect
- **Restart the server** after making configuration changes
- Clear browser cache if using the web interface
- Check that the config file was saved correctly

### Environment Variables Not Working
- Ensure variables are set in the same terminal session
- On Windows, use `$env:VAR_NAME` in PowerShell or `set VAR_NAME` in CMD
- Restart the terminal/IDE after setting variables

## Security Notes

- **Never commit API keys to version control**
- API keys are stored in plain text in the config file
- Consider using environment variables for production
- Rotate API keys regularly
- Monitor usage to prevent unexpected charges

## Cost Management

Different providers have different pricing:
- **Groq**: Free tier with generous limits, very fast
- **Google**: Free tier available
- **Cohere**: Free tier available
- **OpenAI**: Pay per token (can be expensive)
- **Anthropic**: Pay per token
- **Mistral AI**: Pay per token

Monitor your usage in each provider's dashboard to avoid unexpected charges.

## Next Steps

After configuring APIs:
1. Restart the LocalMind server
2. Open the web interface
3. Select a model from the configured providers
4. Start chatting!

For more information, see:
- [API Models Documentation](API_MODELS.md)
- [Web Interface Guide](WEB_INTERFACE.md)
- [Quick Start Guide](QUICKSTART.md)

