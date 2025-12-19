# LocalMind VS Code Extension

VS Code extension for integrating LocalMind AI assistant into your development workflow.

## Features

- 💬 **Inline Chat**: Chat with LocalMind directly in VS Code
- 📝 **Code Explanation**: Explain selected code
- 🔧 **Code Refactoring**: Refactor code with AI assistance
- 🐛 **Code Fixing**: Fix errors and bugs
- ✨ **Code Generation**: Generate code from comments
- 🎯 **Context-Aware**: Understands your codebase

## Installation

### Method 1: From Source

1. Clone the repository
2. Navigate to `vscode-extension/` directory
3. Install dependencies:
   ```bash
   npm install
   ```
4. Compile:
   ```bash
   npm run compile
   ```
5. Press `F5` in VS Code to launch extension development host
6. Or package: `vsce package` and install the `.vsix` file

### Method 2: Manual Installation

1. Copy the extension files to your VS Code extensions folder
2. Reload VS Code

## Configuration

Add to your VS Code settings (`.vscode/settings.json`):

```json
{
  "localmind.apiUrl": "http://localhost:5000",
  "localmind.defaultModel": "llama2",
  "localmind.enabled": true
}
```

## Usage

### Chat Command

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "LocalMind: Chat"
3. Enter your question
4. Get AI response in the output panel

### Explain Code

1. Select code in the editor
2. Press `Ctrl+Shift+P`
3. Type "LocalMind: Explain Code"
4. Get explanation in a new panel

### Refactor Code

1. Select code to refactor
2. Press `Ctrl+Shift+P`
3. Type "LocalMind: Refactor Code"
4. Get refactored code suggestions

### Fix Code

1. Select code with errors
2. Press `Ctrl+Shift+P`
3. Type "LocalMind: Fix Code"
4. Get fixed code

## Requirements

- LocalMind server running (default: `http://localhost:5000`)
- VS Code 1.60.0 or higher

## Commands

- `localmind.chat` - Open chat panel
- `localmind.explain` - Explain selected code
- `localmind.refactor` - Refactor selected code
- `localmind.fix` - Fix selected code
- `localmind.generate` - Generate code from prompt

## Keyboard Shortcuts

- `Ctrl+Alt+L` - Open LocalMind chat
- `Ctrl+Alt+E` - Explain selected code
- `Ctrl+Alt+R` - Refactor selected code
- `Ctrl+Alt+F` - Fix selected code

