# VS Code Integration Guide

This guide explains how to integrate LocalMind with VS Code for an enhanced development experience.

## Overview

The LocalMind VS Code extension allows you to:
- Chat with LocalMind directly in VS Code
- Explain selected code
- Refactor code with AI assistance
- Fix errors and bugs
- Generate code from descriptions
- Get context-aware coding help

## Installation

### Method 1: Install Extension (Recommended)

1. **Build the extension**:
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   ```

2. **Package the extension**:
   ```bash
   npm install -g @vscode/vsce
   vsce package
   ```

3. **Install in VS Code**:
   - Open VS Code
   - Go to Extensions view (`Ctrl+Shift+X`)
   - Click "..." menu → "Install from VSIX..."
   - Select the generated `.vsix` file

### Method 2: Development Mode

1. **Open extension folder in VS Code**:
   ```bash
   cd vscode-extension
   code .
   ```

2. **Press F5** to launch extension development host

3. **Test the extension** in the new VS Code window

## Configuration

Add to your VS Code settings (`.vscode/settings.json` or User Settings):

```json
{
  "localmind.apiUrl": "http://localhost:5000",
  "localmind.defaultModel": "llama2",
  "localmind.enabled": true,
  "localmind.temperature": 0.7
}
```

### Settings

- **localmind.apiUrl**: LocalMind server URL (default: `http://localhost:5000`)
- **localmind.defaultModel**: Default model to use (empty for auto-selection)
- **localmind.enabled**: Enable/disable LocalMind integration
- **localmind.temperature**: AI response temperature (0.0-2.0)

## Usage

### Chat Command

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "LocalMind: Chat"
3. Enter your question
4. View response in a new panel

**Keyboard Shortcut**: `Ctrl+Alt+L` (or `Cmd+Alt+L` on Mac)

### Explain Code

1. Select code in the editor
2. Press `Ctrl+Shift+P`
3. Type "LocalMind: Explain Code"
4. Get detailed explanation

**Keyboard Shortcut**: `Ctrl+Alt+E`

### Refactor Code

1. Select code to refactor
2. Press `Ctrl+Shift+P`
3. Type "LocalMind: Refactor Code"
4. Choose to replace or view refactored code

**Keyboard Shortcut**: `Ctrl+Alt+R`

### Fix Code

1. Select code with errors
2. Press `Ctrl+Shift+P`
3. Type "LocalMind: Fix Code"
4. Choose to replace or view fixed code

**Keyboard Shortcut**: `Ctrl+Alt+F`

### Generate Code

1. Press `Ctrl+Shift+P`
2. Type "LocalMind: Generate Code"
3. Describe what you want to generate
4. Choose to insert or view generated code

## Features

### Context-Aware Assistance

The extension automatically includes:
- Selected code context
- File language information
- Current file path
- Project structure (when available)

### Code Actions

Right-click on selected code to see:
- "Explain with LocalMind"
- "Refactor with LocalMind"
- "Fix with LocalMind"

### Inline Suggestions

Get AI suggestions while typing (future feature):
- Code completions
- Error fixes
- Code improvements

## Example Workflows

### Debugging

1. Select problematic code
2. Use "Fix Code" command
3. Review suggested fixes
4. Apply if appropriate

### Learning

1. Select unfamiliar code
2. Use "Explain Code" command
3. Read detailed explanation
4. Understand the code better

### Refactoring

1. Select code to improve
2. Use "Refactor Code" command
3. Review refactored version
4. Apply improvements

### Code Generation

1. Write a comment describing what you need
2. Use "Generate Code" command
3. Describe the code you want
4. Insert generated code

## Troubleshooting

### "Cannot connect to LocalMind"

**Solution**: 
1. Make sure LocalMind server is running:
   ```bash
   python main.py web
   ```
2. Check the API URL in settings
3. Verify the server is accessible

### Extension Not Working

**Solution**:
1. Check extension is enabled in VS Code
2. Verify LocalMind server is running
3. Check VS Code output panel for errors
4. Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")

### Slow Responses

**Solution**:
1. Use a faster model (e.g., smaller models)
2. Reduce temperature for faster responses
3. Check network connection if using remote server
4. Ensure LocalMind server has sufficient resources

## Advanced Usage

### Custom Prompts

You can create custom commands by modifying `extension.ts`:

```typescript
async function customCommand() {
    const prompt = "Your custom prompt here";
    const response = await callLocalMind(prompt);
    // Handle response
}
```

### Integration with Other Extensions

LocalMind can work alongside:
- GitHub Copilot (use LocalMind for local, private assistance)
- Code formatters (refactor then format)
- Linters (fix issues with LocalMind)

### API Integration

The extension uses LocalMind's REST API. You can also:
- Use the API directly from other tools
- Create custom integrations
- Build workflow automations

## Security

- All communication is local (default: `localhost:5000`)
- No data is sent to external servers
- Code stays on your machine
- Privacy-focused by design

## Future Enhancements

Planned features:
- Inline code suggestions
- Real-time error detection
- Code review assistance
- Test generation
- Documentation generation
- Multi-file context awareness

## Contributing

To contribute to the VS Code extension:
1. Fork the repository
2. Make changes in `vscode-extension/`
3. Test thoroughly
4. Submit a pull request

## Support

For issues or questions:
- Check the troubleshooting section
- Review VS Code extension logs
- Open an issue on GitHub
- Check LocalMind server logs

