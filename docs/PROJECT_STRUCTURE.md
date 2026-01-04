# Project Structure

This document describes the organization of the LocalMind project.

## Directory Structure

```
LocalMind/
├── docs/                    # All documentation files
│   ├── *.md                 # Markdown documentation
│   └── openapi.yaml         # OpenAPI specification
│
├── scripts/                 # Utility scripts
│   ├── *.bat                # Windows batch scripts
│   ├── *.ps1                # PowerShell scripts
│   └── configure_apis.py    # API configuration script
│
├── src/                     # Source code
│   ├── backends/            # AI model backends
│   ├── cli/                 # Command-line interface
│   ├── core/                # Core functionality
│   ├── modules/              # Extensible modules
│   ├── utils/                # Utility functions
│   └── web/                  # Web interface
│       ├── routes/           # Route modules (future)
│       ├── static/           # Static assets (CSS, JS)
│       └── templates/        # HTML templates
│
├── tests/                    # Test files
├── conversations/            # Saved conversations
├── models/                   # Model storage
├── plugins/                  # Third-party plugins
├── venv/                     # Virtual environment (gitignored)
│
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
├── README.md                 # Main README
└── .gitignore               # Git ignore rules
```

## Key Files

### Entry Points
- `main.py` - Main CLI entry point

### Configuration
- `~/.localmind/config.yaml` - User configuration (created automatically)
- `.env` - Environment variables (optional, gitignored)

### Documentation
All documentation is in `docs/`:
- `README.md` - Main project README (in root)
- `docs/QUICKSTART.md` - Quick start guide
- `docs/API_DOCUMENTATION.md` - API reference
- `docs/DEVELOPMENT_PLAN.md` - Development roadmap
- And more...

### Scripts
All utility scripts are in `scripts/`:
- `scripts/start-web.bat` - Start web server (Windows)
- `scripts/configure_apis.py` - Configure API keys

## Code Organization

### Backends (`src/backends/`)
Each backend implements the `BaseBackend` interface:
- `ollama.py` - Ollama local models
- `openai.py` - OpenAI API
- `anthropic.py` - Anthropic API
- `google.py` - Google Gemini API
- And more...

### Core (`src/core/`)
Core functionality modules:
- `model_loader.py` - Model loading and management
- `conversation_manager.py` - Conversation storage
- `context_manager.py` - Context window management
- `module_loader.py` - Module system
- And more...

### Web Interface (`src/web/`)
- `server.py` - Flask web server (main file)
- `static/` - CSS and JavaScript
- `templates/` - HTML templates

## Adding New Features

### Adding a New Backend
1. Create `src/backends/your_backend.py`
2. Implement `BaseBackend` interface
3. Register in `src/core/model_loader.py`

### Adding a New Module
1. Create module in `src/modules/your_module/`
2. Extend `BaseModule` class
3. Register in `src/core/module_loader.py`

### Adding a New Route
Currently routes are in `src/web/server.py`. Future: split into `src/web/routes/`.

## Best Practices

1. **Keep files focused** - Each file should have a single responsibility
2. **Use type hints** - Help with code clarity and IDE support
3. **Add docstrings** - Document all public functions and classes
4. **Handle errors** - Use try/except with proper error messages
5. **Follow PEP 8** - Python style guide

## Future Improvements

- [ ] Split `server.py` into route modules
- [ ] Add more comprehensive error handling
- [ ] Improve type hints coverage
- [ ] Add more unit tests
- [ ] Create API client library

