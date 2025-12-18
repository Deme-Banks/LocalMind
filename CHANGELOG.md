# Changelog

All notable changes to LocalMind will be documented in this file.

## [Unreleased]

### Added
- **Unrestricted Mode Toggle**: UI button to switch between unrestricted and restricted modes
  - Toggle switch in Settings sidebar
  - Real-time mode switching
  - Mode setting persists across sessions
  - Visual feedback with toast notifications
- **Unrestricted Mode**: Complete freedom - no content filtering by default (enabled by default)
  - Google backend: All safety categories set to BLOCK_NONE
  - Anthropic backend: System prompt override to disable restrictions
  - OpenAI backend: Moderation bypassed
  - Configuration options: `unrestricted_mode` and `disable_safety_filters`
  - Documentation: `UNRESTRICTED_MODE.md` guide
- **Model deletion functionality**: API endpoint and UI for deleting models (Ollama, Transformers, GGUF)
- **Conversation rename**: Click-to-rename conversations in the UI
- **Expanded test coverage**: Additional test files for ConversationManager, ContextManager, and ModelRegistry
- **Test documentation**: Comprehensive test suite documentation (tests/README.md)
- **Expanded test suite**: Unit tests for ConversationManager, ContextManager, and ModelRegistry
- **Comprehensive API documentation**: Complete REST API reference (API_DOCUMENTATION.md)
- **Troubleshooting guide**: Common issues and solutions (TROUBLESHOOTING.md)
- **Developer contribution guide**: Guidelines for contributors (CONTRIBUTING.md)
- **Code examples documentation**: Practical usage examples (CODE_EXAMPLES.md)
- **Project summary**: Complete project overview (PROJECT_SUMMARY.md)
- **Linting and formatting setup**: Ruff, Black, isort configured (pyproject.toml)
- **Pre-commit hooks**: Automated code quality checks (.pre-commit-config.yaml)
- **Basic test infrastructure**: Pytest setup with example tests
- **Type hints**: Throughout codebase for better IDE support
- **Comprehensive docstrings**: All core classes documented
- **Standardized error/success response helpers**: Consistent API responses
- **Changelog display**: Version history in About modal
- **Configure page scrolling fix**: Fixed scrolling issue on configure page
- **Fixed bare `except:` clauses**: Replaced with `except Exception:` throughout codebase
- **Improved exception handling**: Better error messages with stack traces

### Fixed
- Configure page scrolling issue
- Exception handling bugs (bare except clauses)
- Error response consistency across all endpoints
- Conversation title editing (now fully functional in UI)

## [1.0.0] - 2024

### Added
- **Multi-Backend Support**: Ollama, OpenAI, Anthropic, Google, Mistral AI, Cohere, Groq, Transformers, GGUF
- **Web Interface**: Full-featured chat interface with streaming responses
- **Conversation Management**: Save, load, search, export conversations
- **Context Management**: Automatic context window management and summarization
- **Module System**: Extensible plugin system with built-in modules (Coding Assistant, Text Generator, Automation Tools, File Processor)
- **Tool Calling**: Tool registry and executor with OpenAI function calling support
- **Performance Optimizations**: Response caching, connection pooling, batch processing
- **Model Management**: Browse, download, and manage models from web interface
- **API Configuration**: Web-based API key management
- **Theme Support**: Light/dark mode toggle
- **UI Enhancements**: 
  - Markdown rendering and code highlighting
  - Copy/delete/regenerate messages
  - Export chat as markdown
  - Print-friendly CSS
  - QR code for network access
  - File uploads with drag-and-drop
  - Favorite models
  - System information display
  - Model recommendations
  - Character/word count
  - Temperature presets
  - Toast notifications
  - Keyboard shortcuts

### Changed
- Improved error messages with troubleshooting tips
- Better handling of network timeouts and rate limits
- Enhanced connection pooling for all API backends

### Fixed
- Unicode encoding issues on Windows
- Config file migration edge cases (pathlib serialization)
- Error handling consistency

## [0.1.0] - Initial Release

### Added
- Basic CLI interface
- Ollama backend integration
- Configuration system
- Model loader abstraction

