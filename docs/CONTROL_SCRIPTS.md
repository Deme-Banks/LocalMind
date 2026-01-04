# LocalMind Control Scripts

This directory contains control scripts to easily start and manage the LocalMind web interface.

## Available Scripts

### 1. `start-web.bat` (Simple)
**Windows Batch Script** - Quick start for the web server

**Usage:**
```batch
start-web.bat
```

**Features:**
- Automatically activates virtual environment
- Starts web server on port 5000
- Accessible from network (0.0.0.0)
- Shows connection information
- Quick status check
- Information about API models setup

### 2. `start-web.ps1` (PowerShell)
**PowerShell Script** - Enhanced version with IP detection

**Usage:**
```powershell
.\start-web.ps1
```

**Features:**
- Automatically detects your local IP address
- Shows both local and network URLs
- Better error handling
- Colored output
- API key detection and status
- System status check

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. `start-web-advanced.bat` (Menu-driven)
**Advanced Control Script** - Interactive menu with multiple options

**Usage:**
```batch
start-web-advanced.bat
```

**Features:**
- Interactive menu
- Multiple startup options:
  - Default (port 5000, network access)
  - Custom port
  - Local only (127.0.0.1)
  - Debug mode
- Status checker
- List available models
- Check API key configuration
- Easy to use

## Quick Start

1. **Double-click** `start-web.bat` (or `start-web.ps1` for PowerShell)
2. Wait for the server to start
3. Open your browser to `http://localhost:5000`
4. Access the Model Manager to download models or configure API keys

## Manual Start

If you prefer to start manually:

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Start web server
python main.py web

# Or with custom options
python main.py web --host 0.0.0.0 --port 8080
python main.py web --host 127.0.0.1 --port 5000  # Local only
python main.py web --debug  # Debug mode
```

## Accessing the Web Interface

Once the server is running:

- **Local access**: `http://localhost:5000`
- **Network access**: `http://YOUR_IP:5000`
  - Find your IP: Run `ipconfig` in Command Prompt
  - Look for "IPv4 Address" under your network adapter

## Stopping the Server

Press `Ctrl+C` in the terminal/command window where the server is running.

## Troubleshooting

### "Virtual environment not found"
- Make sure you've created the virtual environment: `python -m venv venv`
- Install dependencies: `pip install -r requirements.txt`

### "Execution policy" error (PowerShell)
Run this command in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port already in use
- Use a different port: `python main.py web --port 8080`
- Or stop the process using port 5000

### Can't access from network
- Make sure you're using `--host 0.0.0.0` (default in scripts)
- Check Windows Firewall settings
- Ensure both devices are on the same network

## Tips

- **For development**: Use `start-web-advanced.bat` and select "Debug mode"
- **For local use only**: Use `start-web-advanced.bat` and select "Local only"
- **For production**: Consider adding authentication to the web interface
- **Custom port**: Use the advanced script or modify the port in the simple scripts
- **API Models**: Set environment variables for API keys (OPENAI_API_KEY, etc.)
- **Check API Keys**: Use advanced script option 7 to verify API key configuration
- **Multiple Backends**: The system supports Ollama (local) and API backends (ChatGPT, Claude, etc.)

## API Key Setup

To use API models (ChatGPT, Claude, Gemini, etc.):

**Windows (Command Prompt):**
```batch
set OPENAI_API_KEY=sk-your-key-here
set ANTHROPIC_API_KEY=your-key-here
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
$env:ANTHROPIC_API_KEY="your-key-here"
```

**Permanent Setup:**
Add to System Environment Variables or use `start-web-advanced.bat` option 7 to check configuration.

See `API_MODELS.md` for detailed setup instructions.

