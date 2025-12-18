# LocalMind Test Suite

This directory contains the test suite for LocalMind.

## Test Structure

- `test_model_loader.py` - Tests for the ModelLoader class
- `test_config.py` - Tests for the ConfigManager class
- `test_web_server.py` - Tests for the WebServer and API endpoints
- `test_e2e.py` - End-to-end tests for complete user flows
- `test_backends.py` - Backend integration tests
- `test_conversation_manager.py` - Conversation management tests
- `test_context_manager.py` - Context management tests
- `test_model_registry.py` - Model registry tests
- `test_module_loader.py` - Module system tests

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_model_loader.py
```

### Run end-to-end tests only
```bash
pytest tests/test_e2e.py
```

### Run specific test
```bash
pytest tests/test_model_loader.py::test_model_loader_initialization
```

### Run with verbose output
```bash
pytest -v
```

## Test Coverage

Current test coverage includes:
- ✅ ModelLoader initialization and basic operations
- ✅ ConfigManager configuration loading and saving
- ✅ WebServer initialization and route setup
- ✅ API endpoint basic functionality
- ✅ End-to-end user flow tests
- ✅ Conversation management flow
- ✅ Resource management flow
- ✅ Error handling flow
- ✅ Model comparison and ensemble flows
- ✅ Model routing and auto-selection

## Adding New Tests

When adding new tests:

1. **Follow naming conventions**: Test files should start with `test_` and test functions should start with `test_`
2. **Use fixtures**: Create reusable fixtures for common test setup
3. **Mock external dependencies**: Use `unittest.mock` to mock API calls, file operations, etc.
4. **Test edge cases**: Include tests for error conditions and edge cases
5. **Keep tests isolated**: Each test should be independent and not rely on other tests

## Example Test

```python
import pytest
from src.core.model_loader import ModelLoader
from src.utils.config import ConfigManager

@pytest.fixture
def config_manager():
    """Create a test config manager."""
    return ConfigManager()

def test_example(config_manager):
    """Example test function."""
    loader = ModelLoader(config_manager)
    assert loader is not None
```

## Continuous Integration

Tests should pass before committing. Pre-commit hooks will run basic checks, but full test suite should be run before pushing.

## Test Types

### Unit Tests
- `test_config.py` - Configuration management
- `test_model_loader.py` - Model loading and backend management
- `test_model_registry.py` - Model registry operations
- `test_conversation_manager.py` - Conversation management
- `test_context_manager.py` - Context window management
- `test_module_loader.py` - Module system

### Integration Tests
- `test_backends.py` - Backend integration tests
- `test_web_server.py` - Web server API endpoints

### End-to-End Tests
- `test_e2e.py` - Complete user flow tests
  - Web interface flow
  - Conversation management flow
  - Resource management flow
  - Error handling flow
  - Full user journey integration

## Future Test Additions

- Performance tests
- Load tests for API endpoints
- Security tests
- Browser-based UI tests (Selenium/Playwright)

