// Code Execution Page JavaScript

let codeEditor = null;
let executionHistory = [];
const MAX_HISTORY = 50;

// Code templates
const codeTemplates = {
    python: [
        {
            name: "Hello World",
            code: "print('Hello, World!')"
        },
        {
            name: "Calculate Factorial",
            code: "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nresult = factorial(5)\nprint(f'Factorial of 5 is {result}')"
        },
        {
            name: "List Operations",
            code: "numbers = [1, 2, 3, 4, 5]\nsquared = [x**2 for x in numbers]\nprint(f'Original: {numbers}')\nprint(f'Squared: {squared}')"
        },
        {
            name: "Fibonacci Sequence",
            code: "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a, end=' ')\n        a, b = b, a + b\n    print()\n\nfibonacci(10)"
        },
        {
            name: "String Manipulation",
            code: "text = 'Hello, World!'\nprint(f'Uppercase: {text.upper()}')\nprint(f'Lowercase: {text.lower()}')\nprint(f'Reversed: {text[::-1]}')"
        }
    ],
    javascript: [
        {
            name: "Hello World",
            code: "console.log('Hello, World!');"
        },
    ],
    bash: [
        {
            name: "Hello World",
            code: "echo 'Hello, World!'"
        },
        {
            name: "List Files",
            code: "ls -la"
        },
        {
            name: "Current Directory",
            code: "pwd\necho 'Current directory:'\nls"
        },
        {
            name: "Environment Variables",
            code: "echo 'Environment:'\nenv | head -10"
        },
        {
            name: "Date and Time",
            code: "echo 'Current date:'\ndate\necho 'Uptime:'\nuptime"
        }
    ]
        {
            name: "Array Operations",
            code: "const numbers = [1, 2, 3, 4, 5];\nconst doubled = numbers.map(x => x * 2);\nconsole.log('Original:', numbers);\nconsole.log('Doubled:', doubled);"
        },
        {
            name: "Async Function",
            code: "async function fetchData() {\n    return new Promise(resolve => {\n        setTimeout(() => resolve('Data loaded!'), 1000);\n    });\n}\n\nfetchData().then(data => console.log(data));"
        },
        {
            name: "Object Manipulation",
            code: "const person = { name: 'John', age: 30 };\nconsole.log('Name:', person.name);\nconsole.log('Age:', person.age);\nperson.city = 'New York';\nconsole.log('Full object:', JSON.stringify(person, null, 2));"
        },
        {
            name: "Fibonacci Sequence",
            code: "function fibonacci(n) {\n    let a = 0, b = 1;\n    for (let i = 0; i < n; i++) {\n        console.log(a);\n        [a, b] = [b, a + b];\n    }\n}\n\nfibonacci(10);"
        }
    ]
};

// Initialize CodeMirror editor
function initCodeEditor() {
    codeEditor = CodeMirror(document.getElementById('codeEditor'), {
        lineNumbers: true,
        mode: 'python',
        theme: 'monokai',
        matchBrackets: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        indentUnit: 4,
        lineWrapping: true,
        value: '# Welcome to Code Execution!\n# Select a template or write your own code.\n\nprint("Hello, World!")'
    });

    // Update editor mode when language changes
    document.getElementById('languageSelect').addEventListener('change', (e) => {
        const language = e.target.value;
        let mode = 'python';
        if (language === 'javascript') {
            mode = 'javascript';
        } else if (language === 'bash') {
            mode = 'shell';
        }
        codeEditor.setOption('mode', mode);
    });
}

// Load available languages
async function loadLanguages() {
    try {
        const response = await fetch('/api/code/languages');
        const data = await response.json();
        
        if (data.status === 'ok') {
            const select = document.getElementById('languageSelect');
            select.innerHTML = '';
            
            data.languages.forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = lang.charAt(0).toUpperCase() + lang.slice(1);
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load languages:', error);
    }
}

// Auto-detect language
async function detectLanguage() {
    const code = codeEditor.getValue();
    if (!code.trim()) {
        showNotification('Please enter some code first', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/code/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const data = await response.json();
        
        if (data.status === 'ok' && data.language) {
            document.getElementById('languageSelect').value = data.language;
            let mode = 'python';
            if (data.language === 'javascript') {
                mode = 'javascript';
            } else if (data.language === 'bash') {
                mode = 'shell';
            }
            codeEditor.setOption('mode', mode);
            showNotification(`Detected language: ${data.language}`, 'success');
        } else {
            showNotification('Could not detect language. Please select manually.', 'warning');
        }
    } catch (error) {
        console.error('Language detection failed:', error);
        showNotification('Language detection failed', 'error');
    }
}

// Execute code
async function executeCode() {
    const code = codeEditor.getValue();
    const language = document.getElementById('languageSelect').value;
    const timeout = parseInt(document.getElementById('timeoutInput').value) || 30;

    if (!code.trim()) {
        showNotification('Please enter some code to execute', 'warning');
        return;
    }

    // Disable run button
    const runBtn = document.getElementById('runCodeBtn');
    const originalText = runBtn.textContent;
    runBtn.disabled = true;
    runBtn.textContent = '⏳ Running...';

    // Clear previous output
    const outputDisplay = document.getElementById('outputDisplay');
    outputDisplay.innerHTML = '<p style="color: var(--text-secondary); margin: 0;">Executing code...</p>';

    try {
        const response = await fetch('/api/code/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                language,
                timeout
            })
        });

        const data = await response.json();
        
        if (data.status === 'ok') {
            const result = data.data;
            displayOutput(result);
            addToHistory(code, language, result);
        } else {
            displayError(data.message || 'Code execution failed', data.details);
        }
    } catch (error) {
        console.error('Code execution failed:', error);
        displayError('Failed to execute code: ' + error.message);
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = originalText;
    }
}

// Display execution output
function displayOutput(result) {
    const outputDisplay = document.getElementById('outputDisplay');
    
    let html = '';
    
    if (result.status === 'success') {
        html += `<div style="color: var(--success-color, #10b981); margin-bottom: 0.5rem;">✅ Execution successful (${result.execution_time.toFixed(2)}s)</div>`;
        if (result.output) {
            html += `<pre style="margin: 0; color: var(--text-primary);"><code>${escapeHtml(result.output)}</code></pre>`;
        }
    } else {
        html += `<div style="color: var(--error-color, #ef4444); margin-bottom: 0.5rem;">❌ Execution ${result.status}</div>`;
        if (result.error) {
            html += `<pre style="margin: 0; color: var(--error-color, #ef4444);"><code>${escapeHtml(result.error)}</code></pre>`;
        }
        if (result.output) {
            html += `<pre style="margin: 0; color: var(--text-secondary); margin-top: 0.5rem;"><code>${escapeHtml(result.output)}</code></pre>`;
        }
    }
    
    outputDisplay.innerHTML = html;
    
    // Highlight code in output
    outputDisplay.querySelectorAll('code').forEach(block => {
        hljs.highlightElement(block);
    });
}

// Display error
function displayError(message, details = null) {
    const outputDisplay = document.getElementById('outputDisplay');
    let html = `<div style="color: var(--error-color, #ef4444);">❌ ${escapeHtml(message)}</div>`;
    
    if (details) {
        html += `<pre style="margin-top: 0.5rem; color: var(--text-secondary);"><code>${escapeHtml(JSON.stringify(details, null, 2))}</code></pre>`;
    }
    
    outputDisplay.innerHTML = html;
}

// Add to execution history
function addToHistory(code, language, result) {
    const historyItem = {
        id: Date.now(),
        code,
        language,
        result,
        timestamp: new Date().toLocaleString()
    };
    
    executionHistory.unshift(historyItem);
    if (executionHistory.length > MAX_HISTORY) {
        executionHistory.pop();
    }
    
    updateHistoryDisplay();
    saveHistory();
}

// Update history display
function updateHistoryDisplay() {
    const historyList = document.getElementById('historyList');
    
    if (executionHistory.length === 0) {
        historyList.innerHTML = '<p style="color: var(--text-secondary); margin: 0; text-align: center;">No execution history yet</p>';
        return;
    }
    
    let html = '';
    executionHistory.forEach((item, index) => {
        const statusColor = item.result.status === 'success' ? 'var(--success-color, #10b981)' : 'var(--error-color, #ef4444)';
        const statusIcon = item.result.status === 'success' ? '✅' : '❌';
        
        html += `
            <div class="history-item" style="border-bottom: 1px solid var(--border-color); padding: 0.75rem 0; cursor: pointer;" onclick="loadHistoryItem(${index})">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                    <span style="color: ${statusColor}; font-weight: 500;">${statusIcon} ${item.language.toUpperCase()}</span>
                    <span style="color: var(--text-secondary); font-size: 0.75rem;">${item.timestamp}</span>
                </div>
                <pre style="margin: 0; color: var(--text-secondary); font-size: 0.75rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(item.code.substring(0, 100))}${item.code.length > 100 ? '...' : ''}</pre>
            </div>
        `;
    });
    
    historyList.innerHTML = html;
}

// Load history item
function loadHistoryItem(index) {
    const item = executionHistory[index];
    if (!item) return;
    
    codeEditor.setValue(item.code);
    document.getElementById('languageSelect').value = item.language;
    let mode = 'python';
    if (item.language === 'javascript') {
        mode = 'javascript';
    } else if (item.language === 'bash') {
        mode = 'shell';
    }
    codeEditor.setOption('mode', mode);
    displayOutput(item.result);
}

// Load templates
function loadTemplates() {
    const templatesPanel = document.getElementById('templatesPanel');
    const isVisible = templatesPanel.style.display !== 'none';
    
    if (isVisible) {
        templatesPanel.style.display = 'none';
        return;
    }
    
    templatesPanel.style.display = 'block';
    const language = document.getElementById('languageSelect').value;
    const templates = codeTemplates[language] || [];
    
    const templatesList = document.getElementById('templatesList');
    templatesList.innerHTML = '';
    
    templates.forEach(template => {
        const button = document.createElement('button');
        button.className = 'btn btn-secondary';
        button.style.cssText = 'width: 100%; text-align: left; padding: 0.75rem;';
        button.textContent = template.name;
        button.onclick = () => {
            codeEditor.setValue(template.code);
            templatesPanel.style.display = 'none';
        };
        templatesList.appendChild(button);
    });
}

// Clear code
function clearCode() {
    if (confirm('Clear the code editor?')) {
        codeEditor.setValue('');
        document.getElementById('outputDisplay').innerHTML = '<p style="color: var(--text-secondary); margin: 0;">Output will appear here...</p>';
    }
}

// Clear output
function clearOutput() {
    document.getElementById('outputDisplay').innerHTML = '<p style="color: var(--text-secondary); margin: 0;">Output will appear here...</p>';
}

// Clear history
function clearHistory() {
    if (confirm('Clear execution history?')) {
        executionHistory = [];
        updateHistoryDisplay();
        saveHistory();
    }
}

// Save history to localStorage
function saveHistory() {
    try {
        localStorage.setItem('codeExecutionHistory', JSON.stringify(executionHistory));
    } catch (error) {
        console.error('Failed to save history:', error);
    }
}

// Load history from localStorage
function loadHistory() {
    try {
        const saved = localStorage.getItem('codeExecutionHistory');
        if (saved) {
            executionHistory = JSON.parse(saved);
            updateHistoryDisplay();
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show notification (reuse from app.js if available)
function showNotification(message, type = 'info') {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        alert(message);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initCodeEditor();
    loadLanguages();
    loadHistory();
    
    // Event listeners
    document.getElementById('runCodeBtn').addEventListener('click', executeCode);
    document.getElementById('clearCodeBtn').addEventListener('click', clearCode);
    document.getElementById('clearOutputBtn').addEventListener('click', clearOutput);
    document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);
    document.getElementById('loadTemplateBtn').addEventListener('click', loadTemplates);
    document.getElementById('detectLanguageBtn').addEventListener('click', detectLanguage);
    
    // Keyboard shortcut: Ctrl+Enter to run code
    codeEditor.on('keydown', (editor, event) => {
        if (event.ctrlKey && event.key === 'Enter') {
            event.preventDefault();
            executeCode();
        }
    });
});

