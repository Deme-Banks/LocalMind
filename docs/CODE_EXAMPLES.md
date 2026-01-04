# Code Examples

Practical examples for using LocalMind in your projects.

## Table of Contents

- [Basic Usage](#basic-usage)
- [CLI Examples](#cli-examples)
- [Web API Examples](#web-api-examples)
- [Backend Integration](#backend-integration)
- [Module Development](#module-development)
- [Advanced Usage](#advanced-usage)

## Basic Usage

### Simple Chat

```python
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

# Initialize
config_manager = ConfigManager()
model_loader = ModelLoader(config_manager)

# Generate response
response = model_loader.generate(
    prompt="What is Python?",
    model="llama2"
)

print(response.text)
```

### With System Prompt

```python
response = model_loader.generate(
    prompt="Explain quantum computing",
    model="llama2",
    system_prompt="You are a helpful physics teacher.",
    temperature=0.7
)

print(response.text)
```

### Streaming Response

```python
import asyncio

async def stream_response():
    async for chunk in model_loader.generate_stream(
        prompt="Write a short story",
        model="llama2"
    ):
        print(chunk, end="", flush=True)

asyncio.run(stream_response())
```

## CLI Examples

### Basic Commands

```bash
# Check system status
python main.py status

# List available models
python main.py models

# Start interactive chat
python main.py chat

# Start web interface
python main.py web

# Configure API keys
python main.py configure
```

### Chat with Options

```bash
# Use specific model
python main.py chat "Hello!" --model llama2

# Adjust temperature
python main.py chat "Write a story" --temperature 0.9

# With system prompt
python main.py chat "Explain AI" --system "You are a teacher"
```

## Web API Examples

### Python Requests

```python
import requests

BASE_URL = "http://localhost:5000"

# Get status
response = requests.get(f"{BASE_URL}/api/status")
print(response.json())

# Send chat message
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "Hello!",
        "model": "llama2",
        "stream": False
    }
)
print(response.json())

# List conversations
response = requests.get(f"{BASE_URL}/api/conversations")
conversations = response.json()["conversations"]
print(f"Found {len(conversations)} conversations")
```

### JavaScript/Fetch

```javascript
const BASE_URL = 'http://localhost:5000';

// Get status
async function getStatus() {
    const response = await fetch(`${BASE_URL}/api/status`);
    const data = await response.json();
    console.log(data);
}

// Send chat message
async function sendMessage(message, model = 'llama2') {
    const response = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            model: model,
            stream: false
        })
    });
    const data = await response.json();
    return data.response;
}

// Stream response
async function streamMessage(message, model = 'llama2') {
    const response = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            model: model,
            stream: true
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.chunk) {
                    process.stdout.write(data.chunk);
                }
                if (data.done) {
                    return;
                }
            }
        }
    }
}
```

### cURL Examples

```bash
# Get status
curl http://localhost:5000/api/status

# Send chat message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "model": "llama2",
    "stream": false
  }'

# List conversations
curl http://localhost:5000/api/conversations

# Create conversation
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Chat",
    "model": "llama2"
  }'
```

## Backend Integration

### Using Specific Backend

```python
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

config_manager = ConfigManager()
model_loader = ModelLoader(config_manager)

# Get specific backend
backend = model_loader.get_backend("openai")

if backend and backend.is_available():
    response = backend.generate(
        prompt="Hello!",
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    print(response.text)
```

### List Models by Backend

```python
models = model_loader.list_available_models()

for backend_name, model_list in models.items():
    print(f"{backend_name}: {len(model_list)} models")
    for model in model_list:
        print(f"  - {model}")
```

## Module Development

### Creating a Custom Module

```python
from src.modules.base import BaseModule, ModuleResponse
from typing import Dict, Any, Optional

class MyCustomModule(BaseModule):
    """A custom module example."""
    
    def __init__(self):
        super().__init__()
        self.name = "my_custom_module"
        self.description = "My custom module description"
    
    def can_handle(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if this module can handle the prompt."""
        return "custom" in prompt.lower()
    
    def process(
        self,
        prompt: str,
        model_loader=None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ModuleResponse:
        """Process the prompt."""
        # Your custom logic here
        result = f"Processed: {prompt}"
        
        return ModuleResponse(
            content=result,
            metadata={"module": self.name},
            success=True
        )
    
    def get_info(self) -> Dict[str, Any]:
        """Get module information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0"
        }
```

### Registering a Module

```python
from src.core.module_loader import ModuleLoader

module_loader = ModuleLoader()
module_loader.register_module(MyCustomModule())
```

## Advanced Usage

### Conversation Management

```python
from src.core.conversation_manager import ConversationManager

manager = ConversationManager()

# Create conversation
conv_id = manager.create_conversation(
    title="Python Help",
    model="llama2"
)

# Save messages
manager.save_message(conv_id, "user", "What is a list?")
manager.save_message(conv_id, "assistant", "A list is...")

# Get conversation
conversation = manager.get_conversation(conv_id)
print(conversation["messages"])

# Export conversation
markdown = manager.export_conversation(conv_id, format="markdown")
print(markdown)
```

### Context Management

```python
from src.core.context_manager import ContextManager

context_manager = ContextManager()

# Build context for a conversation
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What is Python?"}
]

context = context_manager.build_context(
    messages=messages,
    model="llama2",
    max_tokens=1000
)

print(f"Context length: {len(context)} messages")
```

### Using Cache

```python
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

config_manager = ConfigManager()
model_loader = ModelLoader(config_manager)

# First call - not cached
response1 = model_loader.generate(
    prompt="What is Python?",
    model="llama2",
    use_cache=True
)

# Second call - uses cache
response2 = model_loader.generate(
    prompt="What is Python?",
    model="llama2",
    use_cache=True
)

# response2 will be faster (from cache)
```

### Error Handling

```python
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

config_manager = ConfigManager()
model_loader = ModelLoader(config_manager)

try:
    response = model_loader.generate(
        prompt="Hello!",
        model="nonexistent-model"
    )
except RuntimeError as e:
    print(f"Error: {e}")
    # Try fallback model
    response = model_loader.generate(
        prompt="Hello!",
        model=config_manager.get_config().default_model
    )
```

## Integration Examples

### Flask Integration

```python
from flask import Flask, request, jsonify
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

app = Flask(__name__)
config_manager = ConfigManager()
model_loader = ModelLoader(config_manager)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("message")
    model = data.get("model", "llama2")
    
    try:
        response = model_loader.generate(
            prompt=prompt,
            model=model
        )
        return jsonify({
            "status": "ok",
            "response": response.text
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(port=5001)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

app = FastAPI()
config_manager = ConfigManager()
model_loader = ModelLoader(config_manager)

class ChatRequest(BaseModel):
    message: str
    model: str = "llama2"
    temperature: float = 0.7

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = model_loader.generate(
            prompt=request.message,
            model=request.model,
            temperature=request.temperature
        )
        return {
            "status": "ok",
            "response": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## More Examples

For more examples, check:
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Quick Start Guide](QUICKSTART.md) - Getting started examples
- [Contributing Guide](CONTRIBUTING.md) - Development examples

