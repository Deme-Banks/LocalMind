# LocalMind Web Interface

## Overview

LocalMind now includes a professional web interface that allows you to:
- Chat with AI models through a beautiful web UI
- Manage and download models directly from the browser
- Access the interface from any device on your network
- Use multiple AI models with easy switching

## Starting the Web Server

To start the web interface, run:

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Start web server (default: http://0.0.0.0:5000)
python main.py web

# Or specify custom host and port
python main.py web --host 0.0.0.0 --port 8080

# Enable debug mode (for development)
python main.py web --debug
```

## Accessing the Web Interface

Once the server is running:

1. **Local access**: Open your browser and go to `http://localhost:5000`
2. **Network access**: From any device on your network, use `http://YOUR_IP_ADDRESS:5000`
   - To find your IP address on Windows: Run `ipconfig` and look for "IPv4 Address"
   - Example: `http://192.168.1.100:5000`

## Features

### Chat Interface
- **Streaming responses**: See AI responses appear in real-time
- **Model selection**: Choose from available models in the sidebar
- **Temperature control**: Adjust creativity with a slider
- **System prompts**: Customize AI behavior with system prompts
- **Message history**: View your conversation history

### Model Management
- **View installed models**: See all models currently available
- **Download models**: Browse and download new models directly from the web interface
- **Model switching**: Switch between models with one click
- **Download progress**: Real-time progress tracking for model downloads

### API Endpoints

The web server also provides REST API endpoints:

- `GET /api/status` - Get system status
- `GET /api/models` - List all available models
- `GET /api/models/available` - Get list of models available to download
- `POST /api/models/download` - Download a model
- `GET /api/models/download/<download_id>` - Check download progress
- `POST /api/chat` - Send a chat message (supports streaming)

## Example API Usage

### Chat API

```bash
# Non-streaming
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello!",
    "model": "deepseek-r1:latest",
    "temperature": 0.7
  }'

# Streaming
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello!",
    "model": "deepseek-r1:latest",
    "stream": true
  }'
```

### List Models

```bash
curl http://localhost:5000/api/models
```

### Download Model

```bash
curl -X POST http://localhost:5000/api/models/download \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2"}'
```

## Security Notes

⚠️ **Important**: The web server binds to `0.0.0.0` by default, making it accessible from any device on your network. 

- For local-only access, use `--host 127.0.0.1`
- For network access, ensure your firewall allows connections on the specified port
- The interface has no authentication by default - consider adding authentication for production use

## Troubleshooting

### Server won't start
- Make sure Flask is installed: `pip install flask flask-cors`
- Check if the port is already in use
- Verify Ollama is running: `ollama list`

### Can't access from other devices
- Check Windows Firewall settings
- Ensure you're using `0.0.0.0` as the host (not `localhost` or `127.0.0.1`)
- Verify both devices are on the same network

### Models not showing
- Make sure Ollama is running: `ollama serve`
- Check that models are installed: `ollama list`
- Refresh the web page

### Download fails
- Ensure Ollama is running and accessible
- Check available disk space
- Verify internet connection for downloading models

## Next Steps

1. Start the web server: `python main.py web`
2. Open `http://localhost:5000` in your browser
3. Select a model from the sidebar
4. Start chatting!

For more information, see the main [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md).

