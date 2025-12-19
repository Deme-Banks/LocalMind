# Plugin Development Guide

This guide explains how to create plugins for LocalMind to extend its functionality.

## What are Plugins?

Plugins are third-party extensions that can add new features to LocalMind, such as:
- Custom modules for specific tasks
- Integration with external services
- New UI components
- Custom backends
- Automation tools
- And more!

## Plugin Structure

A LocalMind plugin must have the following structure:

```
my_plugin/
├── plugin.json          # Plugin manifest (required)
├── plugin.py           # Main plugin entry point (required)
└── ...                 # Other files as needed
```

## Plugin Manifest (plugin.json)

The `plugin.json` file contains metadata about your plugin:

```json
{
  "id": "my_plugin",
  "name": "My Awesome Plugin",
  "version": "1.0.0",
  "description": "A plugin that does something awesome",
  "author": "Your Name",
  "entry_point": "plugin.py",
  "dependencies": [],
  "requirements": [
    "requests>=2.28.0"
  ],
  "permissions": [
    "file_read",
    "network_access"
  ]
}
```

### Manifest Fields

- **id**: Unique plugin identifier (required)
- **name**: Display name for the plugin (required)
- **version**: Plugin version (required)
- **description**: Brief description (optional)
- **author**: Plugin author (optional)
- **entry_point**: Main Python file (default: "plugin.py")
- **dependencies**: Other plugin IDs this plugin depends on (optional)
- **requirements**: Python package requirements (optional)
- **permissions**: Required permissions (optional)

## Plugin Entry Point

Your `plugin.py` file should export a plugin class or functions. Here's a basic example:

```python
"""
My Awesome Plugin
"""

class MyPlugin:
    """Plugin class"""
    
    def __init__(self):
        """Initialize plugin"""
        self.name = "My Awesome Plugin"
        self.version = "1.0.0"
    
    def process(self, prompt: str, context: dict) -> str:
        """
        Process a prompt
        
        Args:
            prompt: User prompt
            context: Context dictionary with model, conversation_id, etc.
            
        Returns:
            Processed response
        """
        # Your plugin logic here
        return f"Plugin processed: {prompt}"

# Export plugin instance
plugin = MyPlugin()
```

## Example: Simple Text Processor Plugin

```python
"""
Text Processor Plugin
Processes text with custom transformations
"""

import re

class TextProcessorPlugin:
    """Text processing plugin"""
    
    def __init__(self):
        self.name = "Text Processor"
        self.version = "1.0.0"
    
    def process(self, prompt: str, context: dict) -> str:
        """Process text with transformations"""
        # Example: Convert to uppercase
        if prompt.startswith("UPPERCASE:"):
            text = prompt.replace("UPPERCASE:", "").strip()
            return text.upper()
        
        # Example: Remove extra spaces
        if prompt.startswith("CLEAN:"):
            text = prompt.replace("CLEAN:", "").strip()
            return re.sub(r'\s+', ' ', text)
        
        return None  # Don't handle this prompt

plugin = TextProcessorPlugin()
```

## Example: API Integration Plugin

```python
"""
Weather Plugin
Fetches weather information
"""

import requests

class WeatherPlugin:
    """Weather information plugin"""
    
    def __init__(self):
        self.name = "Weather Plugin"
        self.version = "1.0.0"
        self.api_key = None  # Set via configuration
    
    def process(self, prompt: str, context: dict) -> str:
        """Handle weather queries"""
        if not prompt.lower().startswith("weather:"):
            return None
        
        location = prompt.replace("weather:", "").strip()
        if not location:
            return "Please specify a location"
        
        # Fetch weather (example - replace with actual API)
        try:
            # This is a placeholder - use a real weather API
            response = f"Weather in {location}: Sunny, 72°F"
            return response
        except Exception as e:
            return f"Error fetching weather: {e}"

plugin = WeatherPlugin()
```

## Installing Plugins

### Method 1: Via Web Interface

1. Navigate to the Plugins page
2. Click "Install Plugin"
3. Upload a ZIP file or select a directory
4. Plugin will be installed and enabled automatically

### Method 2: Via API

```bash
# Install from ZIP file
curl -X POST http://localhost:5000/api/plugins \
  -F "file=@my_plugin.zip" \
  -F "plugin_id=my_plugin"

# Install from directory
curl -X POST http://localhost:5000/api/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/my_plugin",
    "plugin_id": "my_plugin"
  }'
```

### Method 3: Manual Installation

1. Create a directory in the `plugins/` folder
2. Copy your plugin files there
3. Ensure `plugin.json` exists
4. Restart LocalMind or reload plugins

## Plugin Lifecycle

1. **Installation**: Plugin files are copied to `plugins/` directory
2. **Registration**: Plugin is registered in `plugins.json`
3. **Loading**: Plugin module is loaded when needed
4. **Execution**: Plugin processes prompts or handles events
5. **Unloading**: Plugin can be disabled/unloaded

## Plugin Integration with Modules

Plugins can integrate with LocalMind's module system:

```python
from src.modules.base import BaseModule, ModuleResponse

class MyPluginModule(BaseModule):
    """Plugin as a module"""
    
    def __init__(self):
        super().__init__()
        self.name = "My Plugin Module"
        self.description = "Plugin module description"
    
    def process(self, prompt: str, context: dict) -> ModuleResponse:
        """Process prompt"""
        # Your logic here
        result = self._do_something(prompt)
        
        return ModuleResponse(
            success=True,
            content=result,
            metadata={"plugin": "my_plugin"}
        )
```

## Best Practices

1. **Error Handling**: Always handle errors gracefully
2. **Logging**: Use Python's logging module for debugging
3. **Configuration**: Store settings in plugin directory
4. **Dependencies**: List all requirements in manifest
5. **Documentation**: Document your plugin's functionality
6. **Testing**: Test your plugin before distribution
7. **Security**: Validate inputs and sanitize outputs
8. **Performance**: Keep processing fast and efficient

## Plugin Permissions

Plugins can request permissions for:
- `file_read`: Read files from disk
- `file_write`: Write files to disk
- `network_access`: Make network requests
- `system_access`: Access system resources
- `model_access`: Access AI models

## Distribution

### Creating a Plugin Package

1. Create your plugin directory with all files
2. Create a ZIP file:
   ```bash
   zip -r my_plugin.zip my_plugin/
   ```
3. Share the ZIP file

### Plugin Repository (Future)

In the future, LocalMind may support a plugin repository where you can:
- Publish plugins
- Discover plugins
- Install plugins with one click
- Rate and review plugins

## Troubleshooting

### Plugin Not Loading

- Check that `plugin.json` exists and is valid JSON
- Verify `entry_point` file exists
- Check plugin logs for errors
- Ensure all dependencies are installed

### Plugin Not Executing

- Verify plugin is enabled
- Check that plugin handles the prompt format
- Review plugin logs
- Test plugin independently

### Permission Errors

- Ensure plugin has required permissions
- Check file/directory permissions
- Verify network access if needed

## Example Plugins

See the `plugins/` directory for example plugins:
- `example_text_processor/` - Simple text processing
- `example_api_integration/` - API integration example
- `example_module/` - Module integration example

## Support

For plugin development support:
- Check the documentation
- Review example plugins
- Open an issue on GitHub
- Join the community discussions

