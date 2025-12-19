# LocalMind

A lightweight, privacy-focused local AI that runs fully on your computer. Supports multiple model backends, customizable modules, and offline tools for automation, coding help, and text generation. No cloud, no tracking—full control over your AI.

## 📚 Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Complete REST API reference
- **[OpenAPI/Swagger Spec](openapi.yaml)** - OpenAPI 3.0 specification for API documentation
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Installation Guide](INSTALL_STEPS.md)** - Detailed setup instructions
- **[Quick Start](QUICKSTART.md)** - Get started in 5 minutes
- **[Development Plan](DEVELOPMENT_PLAN.md)** - Project roadmap and architecture
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to LocalMind
- **[Code Examples](CODE_EXAMPLES.md)** - Practical usage examples
- **[Discord Integration](DISCORD_INTEGRATION.md)** - How to integrate with Discord webhooks
- **[Plugin Guide](PLUGIN_GUIDE.md)** - How to create and install plugins
- **[VS Code Integration](VSCODE_INTEGRATION.md)** - VS Code extension guide

## Features

- 🏠 **Fully Local**: Runs entirely on your machine, no cloud dependencies
- 🔒 **Privacy-Focused**: No tracking, no data collection, complete control
- 🆓 **Unrestricted Mode**: Complete freedom - no content filtering by default
- 🤖 **Multiple Model Backends**: Support for various AI model formats
- 🌐 **Web Interface**: Professional web UI accessible from any device
- 📥 **Model Management**: Download and manage AI models from the web interface
- 💬 **Streaming Chat**: Real-time streaming responses
- 🧩 **Customizable Modules**: Extensible architecture for different use cases
- 🛠️ **Offline Tools**: Automation, coding help, and text generation capabilities
- ⚡ **Lightweight**: Minimal resource footprint

## Getting Started

### Prerequisites

- Python 3.8+ (recommended: Python 3.10+)
- pip package manager
- (Optional) GPU support for faster inference

### Installation

```bash
# Clone the repository
git clone https://github.com/Deme-Banks/LocalMind.git
cd LocalMind

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### Command Line Interface

```bash
# Run LocalMind CLI
python main.py

# Check status
python main.py status

# List available models
python main.py models

# Start interactive chat
python main.py chat

# Start web interface
python main.py web
```

#### Web Interface (Recommended)

**Quick Start:**
1. Double-click `start-web.bat` (or `start-web.ps1` for PowerShell)
2. Open your browser to `http://localhost:5000`
3. Start chatting!

**Features:**
- 🎨 Professional web interface accessible from any device
- 🤖 Multiple AI models with easy switching
- 📥 Download and manage models directly from the browser
- 💬 Real-time streaming chat responses
- 🌐 Network access - use from any device on your network

**Control Scripts:**
- `start-web.bat` - Simple batch script (double-click to start)
- `start-web.ps1` - PowerShell script with IP detection
- `start-web-advanced.bat` - Menu-driven script with multiple options

See [CONTROL_SCRIPTS.md](CONTROL_SCRIPTS.md) for detailed information about the control scripts.

For more information, see [WEB_INTERFACE.md](WEB_INTERFACE.md).

## Project Structure

```
LocalMind/
├── README.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── models/
│   ├── modules/
│   └── utils/
├── config/
└── tests/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Status

✅ **Production Ready** - All core features are complete and tested. The project is ready for use!

### Test Coverage

Run the test suite:
```bash
pytest
```

See [tests/README.md](tests/README.md) for more information about testing.

## Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Complete REST API reference
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Installation Guide](INSTALL_STEPS.md)** - Detailed setup instructions
- **[Quick Start](QUICKSTART.md)** - Get started in 5 minutes
- **[Development Plan](DEVELOPMENT_PLAN.md)** - Project roadmap and architecture
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to LocalMind
- **[Code Examples](CODE_EXAMPLES.md)** - Practical usage examples
- **[Project Summary](PROJECT_SUMMARY.md)** - Complete project overview

## License

[Add your license here]

## Acknowledgments

Built with privacy and local-first principles in mind.
