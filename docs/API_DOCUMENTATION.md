# LocalMind API Documentation

Complete REST API reference for LocalMind web interface.

> **📋 OpenAPI Specification**: This API is also available as an OpenAPI 3.0 specification in [`openapi.yaml`](openapi.yaml). You can view it interactively using:
> - [Swagger Editor](https://editor.swagger.io/) - Paste the contents of `openapi.yaml`
> - [Swagger UI](https://swagger.io/tools/swagger-ui/) - Host locally with `docker run -p 8080:8080 -e SWAGGER_JSON=/openapi.yaml -v $(pwd)/openapi.yaml:/openapi.yaml swaggerapi/swagger-ui`
> - Any OpenAPI-compatible tool

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
      "enabled": true
    }
  ]
}
```

### Models

#### GET `/api/models`
List all available models organized by backend.

**Response:**
```json
{
  "status": "ok",
  "models": {
    "ollama": ["llama2", "mistral", "codellama"],
    "openai": ["gpt-3.5-turbo", "gpt-4"],
    "anthropic": ["claude-3-opus", "claude-3-sonnet"]
  }
}
```

#### GET `/api/models/auto-select`
Automatically select the best default model based on availability and preferences.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "selected_model": "llama3",
    "available_models_count": 15,
    "method": "auto_select"
  }
}
```

#### POST `/api/models/suggest`
Suggest the best model based on conversation context and preferences.

**Request:**
```json
{
  "conversation_history": ["Hello", "How are you?"],
  "current_model": "llama3",
  "preferences": {
    "favorites": ["llama3", "gpt-4"],
    "most_used": ["llama3"]
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "suggested_model": "gpt-4",
    "reason": "Better for analysis tasks",
    "method": "context_aware"
  }
}
```

#### POST `/api/models/check-update`
Check if a model has updates available.

**Request:**
```json
{
  "model": "llama3",
  "backend": "ollama"
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "has_update": true,
    "current_version": "latest",
    "latest_version": "2024-01-15"
  }
}
```

#### GET `/api/models/status`
Get status of loaded models including idle time.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "loaded_models": [
      {
        "model": "llama3",
        "idle_time": 300,
        "memory_usage": 4096
      }
    ]
  }
}
```

#### POST `/api/models/unload`
Manually unload a model from memory.

**Request:**
```json
{
  "model": "llama3"
}
```

### Chat

#### POST `/api/chat`
Send a chat message to the selected model.

**Request:**
```json
{
  "prompt": "Hello, how are you?",
  "model": "llama3",
  "temperature": 0.7,
  "system_prompt": "You are a helpful assistant.",
  "conversation_id": "optional-conversation-id",
  "unrestricted_mode": true
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "response": "Hello! I'm doing well, thank you for asking.",
    "conversation_id": "conv-123",
    "metadata": {
      "prompt_tokens": 10,
      "completion_tokens": 15,
      "total_tokens": 25
    }
  }
}
```

#### POST `/api/chat/stream`
Stream chat response in real-time (Server-Sent Events).

**Request:** Same as `/api/chat`

**Response:** Server-Sent Events stream with chunks:
```
data: {"chunk": "Hello", "done": false}
data: {"chunk": "!", "done": false}
data: {"chunk": "", "done": true}
```

#### POST `/api/chat/compare`
Compare responses from multiple models side-by-side.

**Request:**
```json
{
  "prompt": "Explain quantum computing",
  "models": ["llama3", "gpt-4", "claude-3-opus"],
  "temperature": 0.7,
  "system_prompt": "You are a helpful teacher."
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "prompt": "Explain quantum computing",
    "results": [
      {
        "model": "llama3",
        "backend": "ollama",
        "response": "Quantum computing...",
        "response_time": 2.5,
        "metadata": {
          "prompt_tokens": 5,
          "completion_tokens": 100
        }
      }
    ],
    "total_models": 3,
    "successful": 3,
    "failed": 0
  }
}
```

#### POST `/api/chat/ensemble`
Generate ensemble response by combining multiple model outputs.

**Request:**
```json
{
  "prompt": "Write a Python function",
  "models": ["codellama", "gpt-4"],
  "method": "majority_vote",
  "temperature": 0.7
}
```

**Methods:**
- `majority_vote` - Select most common response pattern
- `best` - Select best response based on metrics
- `longest` - Use longest response
- `shortest` - Use shortest response
- `concatenate` - Combine all responses
- `average` - Show all responses with labels

**Response:**
```json
{
  "status": "ok",
  "data": {
    "response": "Combined response...",
    "method": "majority_vote",
    "models_used": ["codellama", "gpt-4"],
    "individual_responses": [...],
    "metadata": {
      "consensus_count": 2
    }
  }
}
```

#### POST `/api/chat/route`
Route prompt to best model based on task type detection.

**Request:**
```json
{
  "prompt": "Write a Python function to calculate factorial",
  "task_type": "code"  // Optional: explicit task type
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "recommended_model": "codellama",
    "detected_task": "code",
    "confidence": 0.85,
    "recommendations": ["codellama", "gpt-4", "claude-3-opus"]
  }
}
```

#### GET `/api/tasks/types`
Get list of supported task types for model routing.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "task_types": ["code", "writing", "analysis", "translation", "math", "question", "summarization", "creative", "fast"],
    "count": 9
  }
}
```

### Conversations

#### GET `/api/conversations`
List all saved conversations.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "conversations": [
      {
        "id": "conv-123",
        "title": "Python Help",
        "model": "codellama",
        "created_at": "2024-01-15T10:00:00Z",
        "message_count": 10
      }
    ]
  }
}
```

#### POST `/api/conversations`
Create a new conversation.

**Request:**
```json
{
  "model": "llama3",
  "title": "New Conversation"
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "conversation_id": "conv-123",
    "conversation": {
      "id": "conv-123",
      "title": "New Conversation",
      "model": "llama3",
      "messages": []
    }
  }
}
```

#### GET `/api/conversations/{conversation_id}`
Get a specific conversation by ID.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "conversation": {
      "id": "conv-123",
      "title": "Python Help",
      "model": "codellama",
      "messages": [
        {
          "role": "user",
          "content": "Hello",
          "timestamp": "2024-01-15T10:00:00Z"
        }
      ]
    }
  }
}
```

#### DELETE `/api/conversations/{conversation_id}`
Delete a conversation.

**Response:**
```json
{
  "status": "ok",
  "message": "Conversation deleted"
}
```

### Usage Statistics

#### GET `/api/usage/statistics`
Get usage statistics including API calls, tokens, costs, and response times.

**Query Parameters:**
- `days` (optional): Number of days to include (default: 7)

**Response:**
```json
{
  "status": "ok",
  "data": {
    "total_calls": 150,
    "total_tokens": 50000,
    "total_cost": 12.50,
    "average_response_time": 2.3,
    "by_backend": {
      "openai": {
        "calls": 100,
        "tokens": 30000,
        "cost": 10.00
      }
    }
  }
}
```

#### GET `/api/usage/budget`
Get current budget settings and status.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "daily_budget": 10.00,
    "monthly_budget": 300.00,
    "alert_threshold": 0.8,
    "alerts_enabled": true,
    "current_daily_spend": 5.50,
    "current_monthly_spend": 120.00
  }
}
```

#### POST `/api/usage/budget`
Update budget settings.

**Request:**
```json
{
  "daily_budget": 10.00,
  "monthly_budget": 300.00,
  "alert_threshold": 0.8,
  "alerts_enabled": true
}
```

### Resources

#### GET `/api/resources`
Get current system resource usage (CPU, memory, GPU, disk).

**Response:**
```json
{
  "status": "ok",
  "data": {
    "cpu": {
      "percent": 45.5,
      "count": 8
    },
    "memory": {
      "total": 16384,
      "available": 8192,
      "percent": 50.0,
      "used": 8192
    },
    "gpu": {
      "available": true,
      "memory_used": 4096,
      "memory_total": 8192
    },
    "disk": {
      "total": 500000,
      "used": 250000,
      "free": 250000,
      "percent": 50.0
    }
  }
}
```

#### GET `/api/cleanup/stats`
Get statistics about cleanable resources.

**Response:**
```json
{
  "status": "ok",
  "data": {
    "cache": {
      "size_mb": 500,
      "file_count": 1000,
      "oldest_file": "2024-01-01T00:00:00Z"
    },
    "conversations": {
      "count": 50,
      "size_mb": 10,
      "oldest": "2024-01-01T00:00:00Z"
    },
    "temp_files": {
      "size_mb": 5,
      "file_count": 20
    },
    "logs": {
      "size_mb": 100,
      "file_count": 30
    }
  }
}
```

#### POST `/api/cleanup/run`
Run resource cleanup operations.

**Request:**
```json
{
  "type": "all",  // or "cache", "conversations", "temp", "logs"
  "max_age_days": 7,
  "max_size_mb": 1000,
  "keep_recent": 50
}
```

**Response:**
```json
{
  "status": "ok",
  "data": {
    "message": "Cleanup completed. Freed 250.50 MB",
    "total_bytes_freed": 262656000,
    "total_mb_freed": 250.50
  }
}
```

## Error Codes

- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `503` - Service Unavailable (backend not available)

## Rate Limiting

Currently no rate limiting is enforced, but it's recommended to:
- Avoid sending too many requests in quick succession
- Use streaming for long responses
- Cache responses when possible

## Authentication

Currently no authentication is required. All endpoints are accessible locally.

For production deployments, consider adding:
- API key authentication
- User authentication
- Rate limiting per user/IP
