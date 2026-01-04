# Quick API Setup Guide

## OpenAI (ChatGPT) Setup

### Step 1: Get API Key
1. Go to: https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Step 2: Set Environment Variable

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Windows Command Prompt:**
```batch
set OPENAI_API_KEY=sk-your-key-here
```

**Permanent (Windows):**
1. Open System Properties → Environment Variables
2. Add new variable: `OPENAI_API_KEY`
3. Value: `sk-your-key-here`

### Step 3: Enable Backend

Edit `~/.localmind/config.yaml`:
```yaml
backends:
  openai:
    type: openai
    enabled: true
    settings:
      api_key: "sk-your-key-here"  # Or leave empty to use env var
```

### Step 4: Restart Server
Restart LocalMind web server for changes to take effect.

## Testing

After setup, you should see:
- OpenAI backend shows as "Available" in status
- ChatGPT models appear in Model Manager
- You can use models like `gpt-3.5-turbo`, `gpt-4`, etc.

## Troubleshooting

**"Backend not available"**
- Check API key is set correctly
- Verify key starts with `sk-` for OpenAI
- Restart the server after setting the key

**"API key not configured"**
- Make sure environment variable is set
- Or configure in `config.yaml`
- Check for typos in the key

**"Backend is disabled"**
- Set `enabled: true` in config file
- Restart server

## Other API Backends

Similar process for other backends:

- **Anthropic (Claude)**: `ANTHROPIC_API_KEY`
- **Google (Gemini)**: `GOOGLE_API_KEY`
- **Mistral AI**: `MISTRAL_AI_API_KEY`
- **Cohere**: `COHERE_API_KEY`

See `API_MODELS.md` for detailed information about each provider.

