# Discord Integration Guide

This guide explains how to integrate LocalMind with Discord using webhooks, allowing you to receive notifications about chat completions, conversations, model downloads, and other events directly in your Discord channels.

## Overview

LocalMind's webhook system can send events to Discord webhooks, which allows you to:
- Get notified when conversations are created/updated/deleted
- Receive chat completion notifications
- Monitor model downloads
- Track errors and budget alerts
- And more!

## Step 1: Create a Discord Webhook

1. **Open Discord** and navigate to your server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook** or **Create Webhook**
4. Configure your webhook:
   - **Name**: e.g., "LocalMind Bot"
   - **Channel**: Select the channel where notifications should appear
   - **Copy the Webhook URL** (you'll need this!)
5. Click **Save Changes**

Your webhook URL will look like:
```
https://discord.com/api/webhooks/1234567890123456789/abcdefghijklmnopqrstuvwxyz1234567890
```

## Step 2: Set Up LocalMind Webhook

### Option A: Using the API

You can create a webhook subscription using the LocalMind API:

```bash
curl -X POST http://localhost:5000/api/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN",
    "events": [
      "chat.complete",
      "conversation.created",
      "conversation.deleted",
      "model.downloaded",
      "error.occurred",
      "budget.exceeded"
    ],
    "description": "Discord notifications",
    "enabled": true
  }'
```

### Option B: Using Python Script

Create a file `setup_discord_webhook.py`:

```python
import requests
import json

# Your Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

# LocalMind API endpoint
LOCALMIND_API = "http://localhost:5000/api/webhooks"

# Events you want to subscribe to
EVENTS = [
    "chat.complete",
    "conversation.created",
    "conversation.updated",
    "conversation.deleted",
    "model.downloaded",
    "error.occurred",
    "budget.exceeded"
]

# Create webhook subscription
response = requests.post(
    LOCALMIND_API,
    json={
        "url": DISCORD_WEBHOOK_URL,
        "events": EVENTS,
        "description": "Discord notifications",
        "enabled": True
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Webhook created successfully!")
    print(f"Webhook ID: {data['data']['webhook_id']}")
else:
    print(f"❌ Error: {response.text}")
```

Run it:
```bash
python setup_discord_webhook.py
```

## Step 3: Discord Webhook Formatting

Discord webhooks expect a specific JSON format. LocalMind sends events in this format:

```json
{
  "event": "chat.complete",
  "timestamp": "2024-01-15T10:30:00",
  "data": {
    "conversation_id": "abc123",
    "model": "llama2",
    "prompt": "Hello!",
    "response_length": 150
  }
}
```

However, Discord expects a different format. You'll need a **webhook proxy** or **Discord bot** to transform the messages.

## Step 4: Create a Discord Webhook Proxy

Since Discord webhooks have a specific format, you can create a simple proxy server that transforms LocalMind events into Discord embeds.

### Simple Proxy Script

Create `discord_webhook_proxy.py`:

```python
"""
Discord Webhook Proxy
Transforms LocalMind webhook events into Discord-friendly format
"""

from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Your Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

def format_discord_embed(event_data):
    """Convert LocalMind event to Discord embed format"""
    event = event_data.get("event", "unknown")
    timestamp = event_data.get("timestamp", datetime.now().isoformat())
    data = event_data.get("data", {})
    
    # Color mapping for different event types
    color_map = {
        "chat.complete": 0x00ff00,  # Green
        "conversation.created": 0x0099ff,  # Blue
        "conversation.updated": 0xffff00,  # Yellow
        "conversation.deleted": 0xff0000,  # Red
        "model.downloaded": 0x9932cc,  # Dark Orchid
        "error.occurred": 0xff0000,  # Red
        "budget.exceeded": 0xff6600,  # Orange
    }
    
    # Title mapping
    title_map = {
        "chat.complete": "💬 Chat Completed",
        "conversation.created": "📝 Conversation Created",
        "conversation.updated": "✏️ Conversation Updated",
        "conversation.deleted": "🗑️ Conversation Deleted",
        "model.downloaded": "⬇️ Model Downloaded",
        "error.occurred": "❌ Error Occurred",
        "budget.exceeded": "💰 Budget Exceeded",
    }
    
    embed = {
        "title": title_map.get(event, "📢 LocalMind Event"),
        "color": color_map.get(event, 0x808080),
        "timestamp": timestamp,
        "fields": []
    }
    
    # Add fields based on event type
    if event == "chat.complete":
        embed["fields"].extend([
            {"name": "Model", "value": data.get("model", "Unknown"), "inline": True},
            {"name": "Response Length", "value": str(data.get("response_length", 0)), "inline": True},
            {"name": "Conversation ID", "value": data.get("conversation_id", "N/A"), "inline": False}
        ])
        if data.get("prompt"):
            prompt = data["prompt"][:200] + "..." if len(data["prompt"]) > 200 else data["prompt"]
            embed["fields"].append({"name": "Prompt", "value": prompt, "inline": False})
    
    elif event == "conversation.created":
        embed["fields"].extend([
            {"name": "Conversation ID", "value": data.get("conversation_id", "N/A"), "inline": True},
            {"name": "Model", "value": data.get("model", "Unknown"), "inline": True},
            {"name": "Title", "value": data.get("title", "New Conversation"), "inline": False}
        ])
    
    elif event == "model.downloaded":
        embed["fields"].extend([
            {"name": "Model", "value": data.get("model", "Unknown"), "inline": True},
            {"name": "Backend", "value": data.get("backend", "Unknown"), "inline": True},
            {"name": "Size", "value": data.get("size", "Unknown"), "inline": True}
        ])
    
    elif event == "error.occurred":
        embed["fields"].extend([
            {"name": "Error", "value": data.get("error", "Unknown error"), "inline": False}
        ])
    
    elif event == "budget.exceeded":
        embed["fields"].extend([
            {"name": "Budget Type", "value": data.get("budget_type", "Unknown"), "inline": True},
            {"name": "Amount", "value": str(data.get("amount", 0)), "inline": True},
            {"name": "Limit", "value": str(data.get("limit", 0)), "inline": True}
        ])
    
    return embed

@app.route("/webhook", methods=["POST"])
def webhook_proxy():
    """Receive LocalMind webhook and forward to Discord"""
    try:
        event_data = request.get_json()
        
        # Format as Discord embed
        embed = format_discord_embed(event_data)
        
        # Send to Discord
        discord_payload = {
            "embeds": [embed],
            "username": "LocalMind",
            "avatar_url": "https://github.com/Deme-Banks/LocalMind/raw/main/logo.png"  # Optional
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
        
        if response.status_code in [200, 204]:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "error", "message": response.text}), 500
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("Discord Webhook Proxy running on http://localhost:5001")
    print("Configure LocalMind to send webhooks to: http://localhost:5001/webhook")
    app.run(host="0.0.0.0", port=5001)
```

### Setup Instructions

1. **Install dependencies**:
```bash
pip install flask requests
```

2. **Update the Discord webhook URL** in the script

3. **Run the proxy**:
```bash
python discord_webhook_proxy.py
```

4. **Configure LocalMind** to send webhooks to the proxy:
```bash
curl -X POST http://localhost:5000/api/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:5001/webhook",
    "events": ["chat.complete", "conversation.created", "model.downloaded"],
    "description": "Discord via proxy",
    "enabled": true
  }'
```

## Step 5: Test the Integration

1. **Test the webhook**:
```bash
curl -X POST http://localhost:5000/api/webhooks/YOUR_WEBHOOK_ID/test
```

2. **Send a chat message** in LocalMind - you should see a notification in Discord!

3. **Create a conversation** - you should see a notification!

## Example Discord Notifications

### Chat Completion
```
💬 Chat Completed
Model: llama2
Response Length: 150
Conversation ID: abc123
Prompt: Hello, how are you?
```

### Model Downloaded
```
⬇️ Model Downloaded
Model: llama2
Backend: ollama
Size: 3.8 GB
```

### Error Occurred
```
❌ Error Occurred
Error: Model not found
```

## Advanced: Custom Discord Bot

For more advanced features, you can create a Discord bot that:
- Responds to commands
- Sends formatted messages
- Manages multiple channels
- Provides interactive features

See Discord's bot documentation: https://discord.com/developers/docs/intro

## Troubleshooting

### Webhook not receiving events
1. Check that the webhook is enabled: `GET /api/webhooks`
2. Verify the webhook URL is correct
3. Check LocalMind logs for webhook delivery errors
4. Test the webhook: `POST /api/webhooks/<id>/test`

### Discord not showing messages
1. Verify the Discord webhook URL is correct
2. Check that the proxy server is running
3. Verify the channel permissions allow webhooks
4. Check Discord's rate limits (30 requests/minute per webhook)

### Formatting issues
- Discord embeds have limits (25 fields, 6000 characters total)
- Long messages will be truncated
- Adjust the `format_discord_embed` function to customize formatting

## Security Considerations

1. **Keep webhook URLs secret** - they allow posting to Discord channels
2. **Use HTTPS** for production webhook proxies
3. **Validate webhook secret** if you set one in LocalMind
4. **Rate limiting** - Discord has rate limits, be mindful of event frequency

## Next Steps

- Customize embed colors and formatting
- Add more event types
- Create channel-specific webhooks for different event types
- Set up filters to only send important events
- Add interactive buttons or reactions (requires Discord bot)

