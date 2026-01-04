# Contributing to LocalMind

Thank you for your interest in contributing to LocalMind! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic knowledge of Python, Flask, and web development

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/LocalMind.git
   cd LocalMind
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov black ruff mypy
   ```

## Development Workflow

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Type Hints

Always add type hints to function signatures:

```python
def process_message(message: str, model: str) -> Dict[str, Any]:
    """Process a message with the specified model."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def generate_response(
    self,
    prompt: str,
    model: str,
    temperature: float = 0.7
) -> ModelResponse:
    """
    Generate a response from the AI model.
    
    Args:
        prompt: The input prompt for the model
        model: The model identifier to use
        temperature: Sampling temperature (0.0 to 1.0)
    
    Returns:
        ModelResponse containing the generated text
    
    Raises:
        ValueError: If model is not available
        RuntimeError: If generation fails
    """
    ...
```

## Project Structure

```
LocalMind/
├── src/
│   ├── core/           # Core engine components
│   ├── backends/       # AI model backends
│   ├── modules/        # Extensible modules
│   ├── cli/            # Command-line interface
│   ├── web/            # Web interface
│   └── utils/          # Utility functions
├── tests/              # Test files
├── docs/               # Documentation
└── requirements.txt    # Dependencies
```

## Adding a New Backend

1. **Create backend file** in `src/backends/`:
   ```python
   from .base import BaseBackend, ModelResponse
   
   class MyBackend(BaseBackend):
       def is_available(self) -> bool:
           ...
       
       def list_models(self) -> list[str]:
           ...
       
       def generate(self, ...) -> ModelResponse:
           ...
   ```

2. **Register in `model_loader.py`**:
   ```python
   from ..backends.my_backend import MyBackend
   ```

3. **Add to configuration** in `src/utils/config.py`

4. **Update documentation** in `AI_PROVIDERS.md`

## Adding a New Module

1. **Create module directory** in `src/modules/my_module/`

2. **Implement BaseModule**:
   ```python
   from ..base import BaseModule, ModuleResponse
   
   class MyModule(BaseModule):
       def process(self, ...) -> ModuleResponse:
           ...
   ```

3. **Register in `src/modules/__init__.py`**

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_model_loader.py
```

### Writing Tests

Create test files in `tests/` directory:

```python
import pytest
from src.core.model_loader import ModelLoader

def test_model_loading():
    loader = ModelLoader(config_manager)
    assert loader is not None
```

## Code Quality

### Linting

```bash
# Check code style
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
black src/
```

### Type Checking

```bash
mypy src/
```

## Commit Guidelines

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add OpenAI backend support
fix: Resolve memory leak in model loading
docs: Update API documentation
refactor: Simplify error handling
test: Add tests for conversation manager
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** and commit them

3. **Run tests and linting:**
   ```bash
   pytest
   ruff check src/
   black src/
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/my-feature
   ```

5. **Create a Pull Request:**
   - Provide a clear description
   - Reference any related issues
   - Include screenshots for UI changes
   - Ensure all tests pass

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Type hints added
- [ ] No linting errors
- [ ] Commit messages are clear

## Documentation

### Updating Documentation

- Update relevant `.md` files in the root directory
- Add docstrings to new functions/classes
- Update `API_DOCUMENTATION.md` for API changes
- Update `CHANGELOG.md` for user-facing changes

## Reporting Issues

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Error messages/logs

### Feature Requests

Include:
- Description of the feature
- Use case/justification
- Proposed implementation (if applicable)

## Code Review

All PRs require review before merging. Reviewers will check:
- Code quality and style
- Test coverage
- Documentation
- Performance implications
- Security considerations

## Getting Help

- Check existing issues and PRs
- Read the documentation
- Ask questions in discussions
- Join the community (if available)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Thank You!

Your contributions make LocalMind better for everyone. Thank you for taking the time to contribute! 🎉

