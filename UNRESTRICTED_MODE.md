# Unrestricted Mode - Complete Freedom

LocalMind is designed to give you **complete freedom** in what you can ask and what the AI can answer. By default, LocalMind runs in **unrestricted mode** with all content filtering disabled.

## What is Unrestricted Mode?

Unrestricted mode means:
- ✅ **No content filtering** - Ask anything you want
- ✅ **No topic restrictions** - Discuss any subject matter
- ✅ **No safety filters** - AI responds without censorship
- ✅ **Complete privacy** - All conversations stay local (for local backends)
- ✅ **Full control** - You decide what's appropriate

## Configuration

Unrestricted mode is **enabled by default**. You can toggle it in two ways:

### Via Web Interface (Recommended)

1. Open the LocalMind web interface
2. Look for the **"🆓 Unrestricted Mode"** toggle in the Settings sidebar
3. Toggle it on/off as needed
4. The setting is saved automatically

### Via Config File

### Via Config File

Edit `~/.localmind/config.yaml`:

```yaml
unrestricted_mode: true  # Enable unrestricted mode (default: true)
disable_safety_filters: true  # Disable API safety filters (default: true)
```

### Via Web Interface

1. Go to Settings (if available in future versions)
2. Toggle "Unrestricted Mode"
3. Toggle "Disable Safety Filters"

## Backend-Specific Settings

### Local Backends (Ollama, Transformers, GGUF)

Local backends have **no restrictions by default**. They run entirely on your machine with no content filtering.

### API Backends

For API-based backends, we disable safety filters:

#### OpenAI
- Moderation API is bypassed
- No content filtering applied

#### Google (Gemini)
- All safety categories set to `BLOCK_NONE`:
  - Harassment: Not blocked
  - Hate speech: Not blocked
  - Sexually explicit: Not blocked
  - Dangerous content: Not blocked

#### Anthropic (Claude)
- System prompt override to disable safety restrictions
- No content filtering applied

#### Other API Backends
- Mistral AI, Cohere, Groq: Safety filters disabled where supported

## Privacy & Local Control

### Local Backends
- **100% Private** - Everything runs on your machine
- **No data sent** - No conversations leave your computer
- **No tracking** - Complete anonymity

### API Backends
- **API providers may log requests** - Check their privacy policies
- **Conversations sent to API** - Be aware of data transmission
- **No LocalMind filtering** - We don't add any restrictions

## Important Notes

⚠️ **Responsibility**: With unrestricted mode, you have complete control. Use responsibly.

⚠️ **API Providers**: Some API providers may still apply their own restrictions regardless of our settings. Check provider documentation.

⚠️ **Legal Compliance**: Ensure your usage complies with local laws and regulations.

⚠️ **Content Warning**: Unrestricted AI can generate any content. Be prepared for unfiltered responses.

## Troubleshooting

### AI Still Refusing to Answer

1. **Check API Provider Settings**: Some providers have account-level restrictions
2. **Verify Config**: Ensure `unrestricted_mode: true` in config
3. **Try Different Backend**: Some backends may have stricter defaults
4. **Use Local Backends**: For maximum freedom, use Ollama, Transformers, or GGUF

### Safety Filters Still Active

1. **Check Backend Config**: Verify `disable_safety_filters: true`
2. **Restart Server**: Changes require server restart
3. **Check API Account**: Some API accounts have mandatory safety settings

## Default Behavior

**LocalMind defaults to unrestricted mode** - you have complete freedom by default. No configuration needed to enable it.

## Support

If you encounter restrictions that shouldn't be there:
1. Check this documentation
2. Verify your configuration
3. Try a local backend for maximum freedom
4. Check API provider documentation for account-level settings

---

**Remember**: With great freedom comes great responsibility. Use LocalMind responsibly and in accordance with applicable laws.

