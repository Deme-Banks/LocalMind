# LocalMind API Documentation

Complete REST API reference for LocalMind web interface.

## Base URL

```
http://localhost:5000
```

All API endpoints return JSON responses with a `status` field indicating success (`"ok"`) or failure (`"error"`).

## Response Format

### Success Response
```json
{
  "status": "ok",
  "data": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "error_type": "server_error",
  "details": { ... }
}
```

## Endpoints

### System Status

#### GET `/api/status`
Get system status including backends, modules, and system information.

**Response:**
```json
{
  "status": "ok",
  "backends": {
    "ollama": {
      "available": true,
      "models": ["llama2", "mistral"]
    }
  },
  "modules": [
    {
      "name": "coding_assistant",
      "description": "Coding assistance module"
    }
  ],
  "default_model": "llama2",
  "system": {
    "platform": "Windows",
    "python_version": "3.11.0",
    "architecture": "AMD64"
  }
}
```

### Configuration

#### GET `/api/config/providers`
Get list of API providers and their configuration status.

**Response:**
```json
{
  "status": "ok",
  "providers": [
    {
      "name": "openai",
      "display_name": "OpenAI (ChatGPT)",
      "enabled": true,
      "has_api_key": true,
      "setup_url": "https://platform.openai.com/api-keys"
    }
  ]
}
```

#### POST `/api/config/providers`
Configure an API provider.

**Request Body:**
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "enabled": true
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "openai configuration saved"
}
```

### Models

#### GET `/api/models`
List all available models grouped by backend.

**Response:**
```json
{
  "status": "ok",
  "models": {
    "ollama": ["llama2", "mistral"],
    "openai": ["gpt-4", "gpt-3.5-turbo"]
  }
}
```

#### GET `/api/models/available`
Get detailed information about available models across all backends.

**Response:**
```json
{
  "status": "ok",
  "backends": {
    "ollama": {
      "info": {
        "name": "ollama",
        "type": "ollama",
        "enabled": true,
        "available": true
      },
      "models": [
        {
          "name": "llama2",
          "size": "7B",
          "description": "Meta's Llama 2 model"
        }
      ],
      "installed": ["llama2"]
    }
  }
}
```

#### POST `/api/models/download`
Download or set up a model.

**Request Body:**
```json
{
  "model": "llama2",
  "backend": "ollama"
}
```

**Response:**
```json
{
  "status": "ok",
  "download_id": "abc123",
  "message": "Download started"
}
```

#### GET `/api/models/download/<download_id>`
Get download progress.

**Response:**
```json
{
  "status": "ok",
  "progress": 45,
  "message": "Downloading...",
  "status": "downloading"
}
```

### Conversations

#### GET `/api/conversations`
List all conversations.

**Query Parameters:**
- `search` (optional): Search term
- `limit` (optional): Maximum number of results

**Response:**
```json
{
  "status": "ok",
  "conversations": [
    {
      "id": "conv_123",
      "title": "Python Help",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "message_count": 5,
      "model": "llama2"
    }
  ]
}
```

#### POST `/api/conversations`
Create a new conversation.

**Request Body:**
```json
{
  "title": "New Chat",
  "model": "llama2"
}
```

**Response:**
```json
{
  "status": "ok",
  "conversation_id": "conv_123"
}
```

#### GET `/api/conversations/<conv_id>`
Get a conversation by ID.

**Response:**
```json
{
  "status": "ok",
  "conversation": {
    "id": "conv_123",
    "title": "Python Help",
    "messages": [
      {
        "role": "user",
        "content": "Hello",
        "timestamp": "2024-01-01T00:00:00"
      }
    ],
    "model": "llama2"
  }
}
```

#### PUT `/api/conversations/<conv_id>`
Update conversation metadata.

**Request Body:**
```json
{
  "title": "Updated Title"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Conversation updated"
}
```

#### DELETE `/api/conversations/<conv_id>`
Delete a conversation.

**Response:**
```json
{
  "status": "ok",
  "message": "Conversation deleted"
}
```

#### GET `/api/conversations/<conv_id>/export`
Export a conversation.

**Query Parameters:**
- `format` (optional): Export format (`json` or `markdown`, default: `json`)

**Response:**
- For JSON: Returns JSON file download
- For Markdown: Returns Markdown file download

### Chat

#### POST `/api/chat`
Send a chat message and get AI response.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "model": "llama2",
  "conversation_id": "conv_123",
  "temperature": 0.7,
  "stream": true
}
```

**Response (non-streaming):**
```json
{
  "status": "ok",
  "response": "Hello! I'm doing well, thank you for asking.",
  "conversation_id": "conv_123"
}
```

**Response (streaming):**
Returns Server-Sent Events (SSE) stream with chunks:
```
data: {"chunk": "Hello"}
data: {"chunk": "!"}
data: {"done": true}
```

### Modules

#### GET `/api/modules`
List all available modules.

**Response:**
```json
{
  "status": "ok",
  "modules": [
    {
      "name": "coding_assistant",
      "description": "Specialized assistant for programming",
      "enabled": true
    }
  ]
}
```

### Changelog

#### GET `/api/changelog`
Get changelog content.

**Response:**
```json
{
  "status": "ok",
  "changelog": "# Changelog\n\n..."
}
```

## Error Codes

- `400`: Bad Request - Invalid request parameters
- `404`: Not Found - Resource not found
- `500`: Internal Server Error - Server error

## Error Types

- `validation`: Validation error (missing required fields, invalid format)
- `not_found`: Resource not found
- `server_error`: Internal server error

## Rate Limiting

Currently no rate limiting is implemented. Future versions may add rate limiting per IP/user.

## Authentication

Currently no authentication is required. The API is accessible to anyone who can reach the server. For production use, consider adding authentication.

## Examples

### Python Example

```python
import requests

# Get status
response = requests.get("http://localhost:5000/api/status")
print(response.json())

# Send a chat message
response = requests.post(
    "http://localhost:5000/api/chat",
    json={
        "message": "Hello!",
        "model": "llama2",
        "stream": False
    }
)
print(response.json())
```

### JavaScript Example

```javascript
// Get status
const status = await fetch('http://localhost:5000/api/status')
  .then(res => res.json());

// Send a chat message
const chat = await fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello!',
    model: 'llama2',
    stream: false
  })
}).then(res => res.json());
```

### cURL Example

```bash
# Get status
curl http://localhost:5000/api/status

# Send a chat message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "model": "llama2", "stream": false}'
```

## WebSocket Support

Currently, streaming is implemented via Server-Sent Events (SSE). WebSocket support may be added in future versions.

## Version

Current API version: 1.0.0

