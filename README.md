# LocalMind

A lightweight, privacy-focused local AI that runs fully on your computer. Supports multiple model backends, customizable modules, and offline tools for automation, coding help, and text generation. No cloud, no tracking—full control over your AI.

## 📚 Documentation

All documentation is in the [`docs/`](docs/) directory:

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete REST API reference
- **[OpenAPI/Swagger Spec](docs/openapi.yaml)** - OpenAPI 3.0 specification for API documentation
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Installation Guide](docs/INSTALL_STEPS.md)** - Detailed setup instructions
- **[Quick Start](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Development Plan](docs/DEVELOPMENT_PLAN.md)** - Project roadmap and architecture
- **[Development Guide](DEVELOPMENT.md)** - Development branches, workflow, and guidelines
- **[Improvement Plan](IMPROVEMENTS.md)** - Comprehensive improvement roadmap for speed, intelligence, and quality
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to LocalMind
- **[Code Examples](docs/CODE_EXAMPLES.md)** - Practical usage examples
- **[Discord Integration](docs/DISCORD_INTEGRATION.md)** - How to integrate with Discord webhooks
- **[Plugin Guide](docs/PLUGIN_GUIDE.md)** - How to create and install plugins
- **[VS Code Integration](docs/VSCODE_INTEGRATION.md)** - VS Code extension guide

## Features

### Core Features
- 🏡 **Fully Local**: Runs entirely on your machine, no cloud dependencies
- 🔐 **Privacy-Focused**: No tracking, no data collection, complete control
- 🚀 **Unrestricted Mode**: Complete freedom - no content filtering by default
- 🧠 **Multiple Model Backends**: Support for various AI model formats (Ollama, OpenAI, Anthropic, Google, etc.)
- 💻 **Web Interface**: Professional web UI accessible from any device
- 📦 **Model Management**: Download and manage AI models from the web interface
- 💭 **Streaming Chat**: Real-time streaming responses with multiple chat tabs
- 🧩 **Customizable Modules**: Extensible architecture for different use cases
- ⚙️ **Offline Tools**: Automation, coding help, and text generation capabilities
- ⚡ **Lightweight**: Minimal resource footprint

### 🎥 Text-to-Video Generation (New!)
- 🎬 **Multiple Video AI Models**: Support for Sora 2, Runway ML, Pika Labs, and more
- 🔗 **Shared Context**: Chat prompts can be used for video generation and vice versa
- 🎨 **Customizable Settings**: Control duration, aspect ratio, and resolution
- 🎞️ **Video Gallery**: View and manage all generated videos
- 🔄 **Cross-Reference**: Link conversations to videos for better workflow

### Development Branches
- `develop-ai` - Active development for AI chat features and improvements
- `develop-video` - Active development for text-to-video features and enhancements
- `main` - Stable production branch

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
1. Run `python main.py web` or use the startup scripts in `scripts/`
2. Open your browser to `http://localhost:5000`
3. Start chatting or generating videos!

**Pages:**
- `/` - AI Chat interface with multiple models and conversation management
- `/video` - Text-to-video generation with Sora 2, Runway, Pika, and more
- `/configure` - API configuration for all backends

**Features:**
- ✨ Professional web interface accessible from any device
- 🧠 Multiple AI models with easy switching
- 📥 Download and manage models directly from the browser
- 💭 Real-time streaming chat responses
- 🎥 Text-to-video generation with multiple AI backends
- 🔗 Shared context between chat and video features
- 🌍 Network access - use from any device on your network

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
│   ├── backends/          # AI model backends (Ollama, OpenAI, etc.)
│   │   ├── video/         # Video generation backends (Sora, Runway, Pika)
│   │   └── ...
│   ├── core/              # Core functionality
│   │   ├── video_loader.py      # Video backend manager
│   │   ├── shared_context.py   # Chat-video context sharing
│   │   └── ...
│   ├── web/               # Web interface
│   │   ├── routes/        # API routes (chat, video, models, etc.)
│   │   ├── templates/     # HTML templates
│   │   │   ├── index.html # Chat interface
│   │   │   └── video.html # Video generation interface
│   │   └── static/        # CSS, JS, and assets
│   ├── modules/           # Custom modules
│   └── utils/             # Utilities and config
├── scripts/               # Startup scripts
├── config/                # Configuration files
├── videos/                # Generated videos storage
├── conversations/         # Chat conversations
└── tests/                 # Test suite
```

## Development

### Development Branches

We use separate development branches for different feature areas:

- **`develop-ai`** - AI chat features, model improvements, conversation management
  - Switch: `git checkout develop-ai`
  - Focus: Chat interface, model backends, streaming, conversation features

- **`develop-video`** - Text-to-video features, video backends, video generation
  - Switch: `git checkout develop-video`
  - Focus: Video generation, Sora/Runway/Pika integration, video management

- **`main`** - Stable production branch
  - All tested features are merged here
  - Production-ready code only

### Working with Development Branches

```bash
# Switch to AI development branch
git checkout develop-ai

# Switch to video development branch
git checkout develop-video

# Create a feature branch from development branch
git checkout -b feature/my-feature develop-ai

# Merge development branch to main (after testing)
git checkout main
git merge develop-ai
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Development Workflow:**
1. Choose the appropriate development branch (`develop-ai` or `develop-video`)
2. Create a feature branch from the development branch
3. Make your changes and test thoroughly
4. Submit a pull request to the development branch
5. After review and testing, merge to `main`

## Status

✅ **Production Ready** - All core features are complete and tested. The project is ready for use!

### Current Features Status

**AI Chat Features:**
- ✅ Multiple model backends (Ollama, OpenAI, Anthropic, Google, etc.)
- ✅ Streaming chat responses
- ✅ Conversation management
- ✅ Model switching and management
- ✅ Multiple chat tabs
- ✅ Shared context system

**Text-to-Video Features:**
- ✅ Multiple video backends (Sora 2, Runway, Pika)
- ✅ Video generation from text prompts
- ✅ Customizable video settings (duration, aspect ratio, resolution)
- ✅ Video gallery and management
- ✅ Shared context with chat features
- 🔄 Active development in `develop-video` branch

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
