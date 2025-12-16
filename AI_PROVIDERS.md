# AI Providers & Backends

LocalMind supports multiple AI providers, giving you access to the best models from different companies.

## Available Providers

### 1. Ollama (Local) ✅
**Type**: Local models  
**Status**: Fully implemented  
**Models**: 50+ local models  
**Setup**: Install Ollama, pull models  
**Cost**: Free (runs on your hardware)

**Models Include:**
- Llama 2, Llama 3, Llama 3.1
- Mistral, Mixtral
- Code Llama
- DeepSeek, Phi-3, Gemma
- And 40+ more

### 2. OpenAI (ChatGPT) ✅
**Type**: API  
**Status**: Fully implemented  
**Models**: 20+ models  
**Setup**: API key required  
**Cost**: Pay per use

**Models Include:**
- GPT-3.5 Turbo (multiple versions)
- GPT-4, GPT-4 Turbo
- GPT-4o, GPT-4o Mini
- Legacy models

**Get API Key**: https://platform.openai.com/api-keys

### 3. Anthropic (Claude) ✅
**Type**: API  
**Status**: Fully implemented  
**Models**: 8 models  
**Setup**: API key required  
**Cost**: Pay per use

**Models Include:**
- Claude 3 Opus (most capable)
- Claude 3 Sonnet (balanced)
- Claude 3 Haiku (fast)
- Claude 3.5 Sonnet (latest)
- Claude 2.x, Claude Instant

**Get API Key**: https://console.anthropic.com/

### 4. Google (Gemini) ✅
**Type**: API  
**Status**: Fully implemented  
**Models**: 5 models  
**Setup**: API key required  
**Cost**: Pay per use

**Models Include:**
- Gemini Pro
- Gemini Pro Vision (multimodal)
- Gemini 1.5 Pro (latest)
- Gemini 1.5 Flash (fast)
- Gemini Ultra

**Get API Key**: https://makersuite.google.com/app/apikey

### 5. Mistral AI ✅
**Type**: API  
**Status**: Fully implemented  
**Models**: 4 models  
**Setup**: API key required  
**Cost**: Pay per use

**Models Include:**
- Mistral Tiny (smallest)
- Mistral Small (balanced)
- Mistral Medium (capable)
- Mistral Large (most capable)

**Get API Key**: https://console.mistral.ai/

### 6. Cohere ✅
**Type**: API  
**Status**: Fully implemented  
**Models**: 4 models  
**Setup**: API key required  
**Cost**: Pay per use

**Models Include:**
- Command (general purpose)
- Command Light (faster)
- Command R (advanced)
- Command R+ (most capable)

**Get API Key**: https://dashboard.cohere.com/api-keys

### 7. Groq (Fast Inference) ✅
**Type**: API  
**Status**: Fully implemented  
**Models**: 6 models  
**Setup**: API key required  
**Cost**: Pay per use (very fast, cost-effective)

**Models Include:**
- Llama 3.1 70B (very fast)
- Llama 3.1 8B Instant (ultra fast)
- Mixtral 8x7B (fast experts)
- Gemma 7B IT
- Llama 3 variants

**Get API Key**: https://console.groq.com/keys

## Quick Setup Guide

### For Each Provider:

1. **Get API Key** from the provider's website
2. **Set Environment Variable**:
   ```powershell
   # PowerShell
   $env:OPENAI_API_KEY="your-key"
   $env:ANTHROPIC_API_KEY="your-key"
   $env:GOOGLE_API_KEY="your-key"
   $env:MISTRAL_AI_API_KEY="your-key"
   $env:COHERE_API_KEY="your-key"
   $env:GROQ_API_KEY="your-key"
   ```

3. **Enable in Config** (`~/.localmind/config.yaml`):
   ```yaml
   backends:
     openai:
       type: openai
       enabled: true
       settings:
         api_key: "your-key"  # Or leave empty to use env var
   ```

4. **Restart Server**

## Model Comparison

| Provider | Best For | Speed | Quality | Cost |
|----------|----------|-------|---------|------|
| **Ollama** | Privacy, offline use | ⚡⚡ | ⭐⭐⭐⭐ | Free |
| **OpenAI** | Best overall quality | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$$ |
| **Anthropic** | Long context, analysis | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$$ |
| **Google** | Multimodal, vision | ⚡⚡ | ⭐⭐⭐⭐ | $$$ |
| **Mistral AI** | European models | ⚡⚡⚡ | ⭐⭐⭐⭐ | $$ |
| **Cohere** | Enterprise features | ⚡⚡ | ⭐⭐⭐⭐ | $$ |
| **Groq** | Ultra-fast responses | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | $ |

## Using Multiple Providers

You can use multiple providers simultaneously:

1. **Configure all desired backends** in config
2. **Set API keys** for each
3. **Enable them** in config
4. **Switch between models** from different providers in the web interface

## Provider-Specific Features

### OpenAI
- Largest model selection
- Best documentation
- GPT-4o for latest features

### Anthropic
- Long context windows
- Excellent for analysis
- Claude 3.5 Sonnet for latest

### Google
- Multimodal support (vision)
- Good for creative tasks
- Gemini 1.5 Flash for speed

### Mistral AI
- European-based
- Good balance of speed/quality
- Open-source friendly

### Cohere
- Enterprise features
- Good for RAG applications
- Command R+ for advanced tasks

### Groq
- Fastest inference
- Cost-effective
- Great for real-time applications

## Next Steps

1. Choose providers based on your needs
2. Get API keys from provider websites
3. Configure in LocalMind
4. Start using models from multiple providers!

See `API_SETUP_QUICK.md` for detailed setup instructions.

