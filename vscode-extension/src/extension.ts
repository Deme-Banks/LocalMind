/**
 * LocalMind VS Code Extension
 * Integrates LocalMind AI assistant into VS Code
 */

import * as vscode from 'vscode';
import axios from 'axios';

const API_URL = vscode.workspace.getConfiguration('localmind').get<string>('apiUrl', 'http://localhost:5000');
const DEFAULT_MODEL = vscode.workspace.getConfiguration('localmind').get<string>('defaultModel', '');

/**
 * Call LocalMind API
 */
async function callLocalMind(prompt: string, context?: string): Promise<string> {
    try {
        const response = await axios.post(`${API_URL}/api/chat`, {
            prompt: prompt,
            model: DEFAULT_MODEL || undefined,
            system_prompt: context ? `You are a helpful coding assistant. Context:\n${context}` : "You are a helpful coding assistant.",
            temperature: 0.7
        }, {
            timeout: 30000
        });

        if (response.data.status === 'ok') {
            return response.data.response || '';
        } else {
            throw new Error(response.data.message || 'Unknown error');
        }
    } catch (error: any) {
        if (error.code === 'ECONNREFUSED') {
            throw new Error('Cannot connect to LocalMind. Make sure the server is running at ' + API_URL);
        }
        throw error;
    }
}

/**
 * Get selected text from editor
 */
function getSelectedText(): string | null {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return null;
    }
    const selection = editor.selection;
    if (selection.isEmpty) {
        return editor.document.getText();
    }
    return editor.document.getText(selection);
}

/**
 * Replace selected text in editor
 */
function replaceSelectedText(text: string) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }
    const selection = editor.selection;
    editor.edit(editBuilder => {
        if (selection.isEmpty) {
            editBuilder.insert(selection.start, text);
        } else {
            editBuilder.replace(selection, text);
        }
    });
}

/**
 * Show response in output panel
 */
function showResponse(response: string, title: string = 'LocalMind Response') {
    const panel = vscode.window.createWebviewPanel(
        'localmindResponse',
        title,
        vscode.ViewColumn.Beside,
        {}
    );
    panel.webview.html = `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: var(--vscode-font-family); padding: 20px; }
                pre { background: var(--vscode-textCodeBlock-background); padding: 10px; border-radius: 4px; }
                code { font-family: var(--vscode-editor-font-family); }
            </style>
        </head>
        <body>
            <pre><code>${escapeHtml(response)}</code></pre>
        </body>
        </html>
    `;
}

function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Chat command
 */
async function chatCommand() {
    const prompt = await vscode.window.showInputBox({
        prompt: 'Enter your question for LocalMind',
        placeHolder: 'e.g., How do I sort a list in Python?'
    });

    if (!prompt) {
        return;
    }

    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "LocalMind",
        cancellable: false
    }, async (progress) => {
        progress.report({ message: "Thinking..." });
        
        try {
            const response = await callLocalMind(prompt);
            showResponse(response, 'LocalMind Chat');
        } catch (error: any) {
            vscode.window.showErrorMessage(`LocalMind Error: ${error.message}`);
        }
    });
}

/**
 * Explain code command
 */
async function explainCodeCommand() {
    const selectedText = getSelectedText();
    if (!selectedText) {
        vscode.window.showWarningMessage('Please select code to explain');
        return;
    }

    const prompt = `Explain this code:\n\n\`\`\`\n${selectedText}\n\`\`\``;

    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "LocalMind",
        cancellable: false
    }, async (progress) => {
        progress.report({ message: "Explaining code..." });
        
        try {
            const response = await callLocalMind(prompt);
            showResponse(response, 'Code Explanation');
        } catch (error: any) {
            vscode.window.showErrorMessage(`LocalMind Error: ${error.message}`);
        }
    });
}

/**
 * Refactor code command
 */
async function refactorCodeCommand() {
    const selectedText = getSelectedText();
    if (!selectedText) {
        vscode.window.showWarningMessage('Please select code to refactor');
        return;
    }

    const prompt = `Refactor this code to make it better, cleaner, and more efficient. Only return the refactored code:\n\n\`\`\`\n${selectedText}\n\`\`\``;

    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "LocalMind",
        cancellable: false
    }, async (progress) => {
        progress.report({ message: "Refactoring code..." });
        
        try {
            const response = await callLocalMind(prompt);
            
            // Ask user if they want to replace
            const action = await vscode.window.showInformationMessage(
                'Refactored code ready. Replace selected code?',
                'Replace',
                'View Only'
            );
            
            if (action === 'Replace') {
                replaceSelectedText(response);
            } else {
                showResponse(response, 'Refactored Code');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`LocalMind Error: ${error.message}`);
        }
    });
}

/**
 * Fix code command
 */
async function fixCodeCommand() {
    const selectedText = getSelectedText();
    if (!selectedText) {
        vscode.window.showWarningMessage('Please select code to fix');
        return;
    }

    const prompt = `Fix any errors or bugs in this code. Only return the fixed code:\n\n\`\`\`\n${selectedText}\n\`\`\``;

    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "LocalMind",
        cancellable: false
    }, async (progress) => {
        progress.report({ message: "Fixing code..." });
        
        try {
            const response = await callLocalMind(prompt);
            
            // Ask user if they want to replace
            const action = await vscode.window.showInformationMessage(
                'Fixed code ready. Replace selected code?',
                'Replace',
                'View Only'
            );
            
            if (action === 'Replace') {
                replaceSelectedText(response);
            } else {
                showResponse(response, 'Fixed Code');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`LocalMind Error: ${error.message}`);
        }
    });
}

/**
 * Generate code command
 */
async function generateCodeCommand() {
    const prompt = await vscode.window.showInputBox({
        prompt: 'Describe the code you want to generate',
        placeHolder: 'e.g., A function to calculate fibonacci numbers'
    });

    if (!prompt) {
        return;
    }

    const codePrompt = `Generate code for: ${prompt}. Only return the code, no explanations.`;

    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "LocalMind",
        cancellable: false
    }, async (progress) => {
        progress.report({ message: "Generating code..." });
        
        try {
            const response = await callLocalMind(codePrompt);
            
            // Ask user if they want to insert
            const action = await vscode.window.showInformationMessage(
                'Code generated. Insert at cursor?',
                'Insert',
                'View Only'
            );
            
            if (action === 'Insert') {
                replaceSelectedText(response);
            } else {
                showResponse(response, 'Generated Code');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`LocalMind Error: ${error.message}`);
        }
    });
}

/**
 * Extension activation
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('LocalMind extension is now active!');

    // Register commands
    const chatCmd = vscode.commands.registerCommand('localmind.chat', chatCommand);
    const explainCmd = vscode.commands.registerCommand('localmind.explain', explainCodeCommand);
    const refactorCmd = vscode.commands.registerCommand('localmind.refactor', refactorCodeCommand);
    const fixCmd = vscode.commands.registerCommand('localmind.fix', fixCodeCommand);
    const generateCmd = vscode.commands.registerCommand('localmind.generate', generateCodeCommand);

    context.subscriptions.push(chatCmd, explainCmd, refactorCmd, fixCmd, generateCmd);

    // Check if LocalMind is running
    checkLocalMindConnection();
}

/**
 * Check LocalMind connection
 */
async function checkLocalMindConnection() {
    try {
        const response = await axios.get(`${API_URL}/api/status`, { timeout: 5000 });
        if (response.data.status === 'ok') {
            vscode.window.showInformationMessage('LocalMind connected successfully!');
        }
    } catch (error) {
        vscode.window.showWarningMessage(
            'LocalMind server not found. Make sure it\'s running at ' + API_URL,
            'Open Settings'
        ).then(selection => {
            if (selection === 'Open Settings') {
                vscode.commands.executeCommand('workbench.action.openSettings', 'localmind');
            }
        });
    }
}

/**
 * Extension deactivation
 */
export function deactivate() {}

