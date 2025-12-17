// LocalMind Web Interface JavaScript

// Global state
let currentModel = null;
let conversationHistory = [];
let downloadCheckInterval = null;
let currentConversationId = null;
let conversations = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeApp();
});

// Theme management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

async function initializeApp() {
    await checkStatus();
    await loadModels();
    await loadConversations();
    setupEventListeners();
}

// Status check
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const statusDot = statusIndicator.querySelector('.status-dot');
        
        if (data.status === 'ok') {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    } catch (error) {
        console.error('Status check failed:', error);
        const statusText = document.getElementById('statusText');
        statusText.textContent = 'Error';
    }
}

// Load models
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        if (data.status === 'ok') {
            const modelSelect = document.getElementById('modelSelect');
            modelSelect.innerHTML = '<option value="">Select a model...</option>';
            
            // Flatten models from all backends
            const allModels = [];
            for (const [backend, models] of Object.entries(data.models)) {
                for (const model of models) {
                    allModels.push({ name: model, backend });
                }
            }
            
            if (allModels.length === 0) {
                modelSelect.innerHTML = '<option value="">No models available</option>';
                return;
            }
            
            allModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = `${model.name} (${model.backend})`;
                modelSelect.appendChild(option);
            });
            
            // Set default model if available
            if (allModels.length > 0 && !currentModel) {
                currentModel = allModels[0].name;
                modelSelect.value = currentModel;
                updateModelInfo();
            }
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        showNotification('Failed to load models', 'error');
    }
}

// Update model info
function updateModelInfo() {
    const modelInfo = document.getElementById('modelInfo');
    if (currentModel) {
        modelInfo.textContent = `Selected: ${currentModel}`;
    } else {
        modelInfo.textContent = 'No model selected';
    }
}

// Setup event listeners
function setupEventListeners() {
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const modelSelect = document.getElementById('modelSelect');
    const newConversationBtn = document.getElementById('newConversationBtn');
    const conversationsSearch = document.getElementById('conversationsSearch');
    
    // Model selection
    modelSelect.addEventListener('change', (e) => {
        currentModel = e.target.value;
        updateModelInfo();
    });
    
    // Send button
    sendButton.addEventListener('click', sendMessage);
    
    // Enter key to send (Shift+Enter for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
    });
    
    // New conversation button
    if (newConversationBtn) {
        newConversationBtn.addEventListener('click', createNewConversation);
    }
    
    // Conversations search
    if (conversationsSearch) {
        conversationsSearch.addEventListener('input', (e) => {
            filterConversations(e.target.value);
        });
    }
}

// Send message
async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    if (!currentModel) {
        showNotification('Please select a model first', 'error');
        return;
    }
    
    // Disable input
    chatInput.disabled = true;
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    
    // Add user message to chat
    addMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Get settings
    const temperature = parseFloat(document.getElementById('temperature').value);
    const systemPrompt = document.getElementById('systemPrompt').value || undefined;
    const streamMode = document.getElementById('streamMode').checked;
    
    try {
        if (streamMode) {
            await sendMessageStream(message, temperature, systemPrompt);
        } else {
            await sendMessageNormal(message, temperature, systemPrompt);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('assistant', `Error: ${error.message}`, true);
        showNotification('Failed to send message', 'error');
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

// Send message (normal mode)
async function sendMessageNormal(prompt, temperature, systemPrompt) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt,
            model: currentModel,
            temperature,
            system_prompt: systemPrompt,
            stream: false,
            conversation_id: currentConversationId
        })
    });
    
    const data = await response.json();
    
    if (data.status === 'ok') {
        addMessage('assistant', data.response);
        // Update conversation ID if returned
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            await loadConversations(); // Refresh list
        }
    } else {
        throw new Error(data.message || 'Unknown error');
    }
}

// Send message (streaming mode)
async function sendMessageStream(prompt, temperature, systemPrompt) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt,
            model: currentModel,
            temperature,
            system_prompt: systemPrompt,
            stream: true,
            conversation_id: currentConversationId
        })
    });
    
    if (!response.ok) {
        throw new Error('Stream request failed');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let assistantMessageId = null;
    
    while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.chunk) {
                        if (!assistantMessageId) {
                            assistantMessageId = addMessage('assistant', '', true);
                        }
                        appendToMessage(assistantMessageId, data.chunk);
                    }
                    
                    if (data.done) {
                        // Update conversation ID if returned
                        if (data.conversation_id) {
                            currentConversationId = data.conversation_id;
                            loadConversations(); // Refresh list
                        }
                        return;
                    }
                } catch (e) {
                    console.error('Error parsing stream data:', e);
                }
            }
        }
    }
}

// Add message to chat
function addMessage(role, text, isStreaming = false) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Remove welcome message if present
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = isStreaming ? `msg-${Date.now()}` : undefined;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;
    
    content.appendChild(textDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv.id;
}

// Append to streaming message
function appendToMessage(messageId, chunk) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;
    
    const textDiv = messageDiv.querySelector('.message-text');
    if (textDiv) {
        textDiv.textContent += chunk;
        
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Model Manager
function showModelManager() {
    const modal = document.getElementById('modelManagerModal');
    modal.classList.add('active');
    loadInstalledModels();
    loadAvailableModels();
}

function closeModelManager() {
    const modal = document.getElementById('modelManagerModal');
    modal.classList.remove('active');
}

function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}Tab`).classList.add('active');
    event.target.classList.add('active');
}

// Load installed models
async function loadInstalledModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        const listDiv = document.getElementById('installedModelsList');
        
        if (data.status === 'ok' && Object.keys(data.models).length > 0) {
            listDiv.innerHTML = '';
            
            for (const [backend, models] of Object.entries(data.models)) {
                if (models.length === 0) continue;
                
                models.forEach(model => {
                    const card = createModelCard(model, backend, true);
                    listDiv.appendChild(card);
                });
            }
        } else {
            listDiv.innerHTML = '<p style="color: var(--text-secondary);">No models installed</p>';
        }
    } catch (error) {
        console.error('Failed to load installed models:', error);
        document.getElementById('installedModelsList').innerHTML = 
            '<p style="color: var(--error);">Failed to load models</p>';
    }
}

// Load available models
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models/available');
        const data = await response.json();
        
        const listDiv = document.getElementById('availableModelsList');
        
        if (data.status === 'ok' && data.backends) {
            listDiv.innerHTML = '';
            
            // Show models grouped by backend
            for (const [backendName, backendData] of Object.entries(data.backends)) {
                if (!backendData.models || backendData.models.length === 0) continue;
                
                // Create backend section
                const backendSection = document.createElement('div');
                backendSection.className = 'backend-section';
                
                const backendHeader = document.createElement('div');
                backendHeader.className = 'backend-header';
                const displayName = getBackendDisplayName(backendName);
                backendHeader.innerHTML = `
                    <h3>${displayName}</h3>
                    <span class="backend-status ${backendData.info?.available ? 'available' : 'unavailable'}">
                        ${backendData.info?.available ? 'Available' : 'Unavailable'}
                    </span>
                `;
                backendSection.appendChild(backendHeader);
                
                const modelsContainer = document.createElement('div');
                modelsContainer.className = 'models-container';
                
                backendData.models.forEach(model => {
                    // For API backends, models are "available" if backend is available
                    const isInstalled = backendData.installed && backendData.installed.includes(model.name);
                    // API models show as available if backend is available, local models need download
                    const canDownload = backendName === 'ollama' ? !isInstalled : backendData.info?.available;
                    const card = createModelCard(model, backendName, isInstalled, canDownload);
                    modelsContainer.appendChild(card);
                });
                
                backendSection.appendChild(modelsContainer);
                listDiv.appendChild(backendSection);
            }
            
            if (listDiv.children.length === 0) {
                listDiv.innerHTML = '<p style="color: var(--text-secondary);">No models available</p>';
            }
        } else {
            listDiv.innerHTML = '<p style="color: var(--text-secondary);">No models available</p>';
        }
    } catch (error) {
        console.error('Failed to load available models:', error);
        document.getElementById('availableModelsList').innerHTML = 
            '<p style="color: var(--error);">Failed to load available models</p>';
    }
}

// Create model card
function createModelCard(model, backend, isInstalled, canDownload = false) {
    const card = document.createElement('div');
    card.className = 'model-card';
    if (isInstalled) {
        card.classList.add('installed');
    }
    
    const info = document.createElement('div');
    info.className = 'model-card-info';
    
    const name = document.createElement('h4');
    const modelName = typeof model === 'string' ? model : model.name;
    name.textContent = modelName;
    
    const desc = document.createElement('p');
    if (typeof model === 'object') {
        let descText = model.description || 'No description available';
        if (model.size) {
            descText += ` • ${model.size}`;
        }
        if (model.tags && model.tags.length > 0) {
            descText += ` • Tags: ${model.tags.join(', ')}`;
        }
        desc.textContent = descText;
    } else {
        desc.textContent = `Backend: ${backend}`;
    }
    
    info.appendChild(name);
    info.appendChild(desc);
    
    const actions = document.createElement('div');
    actions.className = 'model-card-actions';
    
    if (isInstalled) {
        const useBtn = document.createElement('button');
        useBtn.className = 'btn btn-primary btn-small';
        useBtn.textContent = 'Use';
        useBtn.onclick = () => {
            currentModel = modelName;
            document.getElementById('modelSelect').value = currentModel;
            updateModelInfo();
            closeModelManager();
            showNotification(`Switched to ${currentModel}`, 'success');
        };
        actions.appendChild(useBtn);
    } else if (canDownload || (typeof model === 'object' && !model.installed)) {
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-success btn-small';
        // API backends say "Setup" instead of "Download"
        downloadBtn.textContent = backend === 'ollama' ? 'Download' : 'Setup';
        downloadBtn.onclick = () => downloadModel(modelName, backend);
        actions.appendChild(downloadBtn);
    }
    
    card.appendChild(info);
    card.appendChild(actions);
    
    return card;
}

// Download model
async function downloadModel(modelName, backendName = 'ollama') {
    try {
        const response = await fetch('/api/models/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model: modelName, backend: backendName })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showDownloadModal(data.download_id, modelName);
        } else if (data.requires_api_key) {
            // Show API key configuration dialog
            showApiKeyDialog(backendName, data.env_var, modelName, data.setup_url);
        } else if (data.requires_enable) {
            showNotification('Backend is disabled. Please enable it in the config file.', 'error');
        } else if (data.requires_config) {
            showNotification('Backend is not configured. Please add it to your config file.', 'error');
        } else {
            showNotification(data.message || 'Setup failed', 'error');
        }
    } catch (error) {
        console.error('Download error:', error);
        showNotification('Failed to start download', 'error');
    }
}

// Show API key configuration dialog
function showApiKeyDialog(backendName, envVar, modelName, setupUrl = null) {
    const url = setupUrl || getApiKeyUrl(backendName);
    const message = `This model requires an API key to use.\n\n` +
                   `Setup Instructions:\n` +
                   `1. Get an API key from: ${url}\n` +
                   `2. Set environment variable:\n` +
                   `   ${envVar}=your_api_key\n\n` +
                   `   Windows (PowerShell):\n` +
                   `   $env:${envVar}="your_api_key"\n\n` +
                   `   Windows (CMD):\n` +
                   `   set ${envVar}=your_api_key\n\n` +
                   `3. Restart LocalMind server\n` +
                   `4. Try again\n\n` +
                   `Would you like to open the API key page?`;
    
    if (confirm(message)) {
        if (url) {
            window.open(url, '_blank');
        }
    }
}

function getApiKeyUrl(backendName) {
    const urls = {
        'openai': 'https://platform.openai.com/api-keys',
        'anthropic': 'https://console.anthropic.com/',
        'google': 'https://makersuite.google.com/app/apikey',
        'mistral-ai': 'https://console.mistral.ai/',
        'cohere': 'https://dashboard.cohere.com/api-keys',
        'groq': 'https://console.groq.com/keys'
    };
    return urls[backendName] || 'the provider\'s website';
}

function getBackendDisplayName(backendName) {
    const names = {
        'openai': 'OpenAI (ChatGPT)',
        'anthropic': 'Anthropic (Claude)',
        'google': 'Google (Gemini)',
        'mistral-ai': 'Mistral AI',
        'cohere': 'Cohere',
        'groq': 'Groq (Fast Inference)',
        'ollama': 'Ollama (Local)'
    };
    return names[backendName] || backendName.charAt(0).toUpperCase() + backendName.slice(1);
}

// Show download modal
function showDownloadModal(downloadId, modelName) {
    const modal = document.getElementById('downloadModal');
    const progressFill = document.getElementById('progressFill');
    const downloadMessage = document.getElementById('downloadMessage');
    
    modal.classList.add('active');
    progressFill.style.width = '0%';
    downloadMessage.textContent = `Starting download of ${modelName}...`;
    
    let checkCount = 0;
    const maxChecks = 600; // 10 minutes max (600 * 1 second)
    
    // Check progress
    downloadCheckInterval = setInterval(async () => {
        checkCount++;
        
        // Timeout after max checks
        if (checkCount > maxChecks) {
            clearInterval(downloadCheckInterval);
            downloadMessage.textContent = 'Download timeout - please check manually';
            setTimeout(() => {
                modal.classList.remove('active');
            }, 3000);
            return;
        }
        
        try {
            const response = await fetch(`/api/models/download/${downloadId}`);
            const data = await response.json();
            
            if (data.status === 'ok' && data.progress) {
                const progress = data.progress;
                const progressPercent = Math.min(progress.progress || 0, 100);
                progressFill.style.width = `${progressPercent}%`;
                downloadMessage.textContent = progress.message || `Downloading ${modelName}...`;
                
                if (progress.status === 'completed') {
                    clearInterval(downloadCheckInterval);
                    progressFill.style.width = '100%';
                    downloadMessage.textContent = `Successfully downloaded ${modelName}!`;
                    setTimeout(() => {
                        modal.classList.remove('active');
                        showNotification(`Successfully downloaded ${modelName}`, 'success');
                        // Refresh model lists
                        loadModels();
                        loadInstalledModels();
                        loadAvailableModels();
                    }, 2000);
                } else if (progress.status === 'error') {
                    clearInterval(downloadCheckInterval);
                    downloadMessage.textContent = progress.message || `Failed to download ${modelName}`;
                    progressFill.style.background = 'var(--error)';
                    setTimeout(() => {
                        modal.classList.remove('active');
                        progressFill.style.background = 'var(--primary-color)';
                    }, 3000);
                }
            } else if (data.status === 'error') {
                clearInterval(downloadCheckInterval);
                downloadMessage.textContent = data.message || 'Download failed';
                progressFill.style.background = 'var(--error)';
                setTimeout(() => {
                    modal.classList.remove('active');
                    progressFill.style.background = 'var(--primary-color)';
                }, 3000);
            }
        } catch (error) {
            console.error('Error checking download progress:', error);
            if (checkCount > 10) {
                // Only show error after a few failed attempts
                downloadMessage.textContent = 'Error checking download status...';
            }
        }
    }, 1000);
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this with a proper toast system
    console.log(`[${type.toUpperCase()}] ${message}`);
    // For now, just alert - can be replaced with a toast notification component
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

// Filter models
function filterModels(tab, searchTerm) {
    const listId = tab === 'installed' ? 'installedModelsList' : 'availableModelsList';
    const listDiv = document.getElementById(listId);
    const cards = listDiv.querySelectorAll('.model-card');
    
    const term = searchTerm.toLowerCase().trim();
    
    cards.forEach(card => {
        const name = card.querySelector('h4')?.textContent.toLowerCase() || '';
        const desc = card.querySelector('p')?.textContent.toLowerCase() || '';
        
        if (term === '' || name.includes(term) || desc.includes(term)) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
}

// Close modal on outside click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        if (downloadCheckInterval) {
            clearInterval(downloadCheckInterval);
            downloadCheckInterval = null;
        }
    }
});

// Conversation Management
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        const data = await response.json();
        
        if (data.status === 'ok') {
            conversations = data.conversations;
            renderConversations();
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
    }
}

function renderConversations() {
    const listDiv = document.getElementById('conversationsList');
    if (!listDiv) return;
    
    if (conversations.length === 0) {
        listDiv.innerHTML = '<p style="color: var(--text-secondary); padding: 1rem; text-align: center;">No conversations yet</p>';
        return;
    }
    
    listDiv.innerHTML = '';
    
    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        if (conv.id === currentConversationId) {
            item.classList.add('active');
        }
        
        const titleDiv = document.createElement('div');
        titleDiv.style.flex = '1';
        titleDiv.style.minWidth = '0';
        
        const title = document.createElement('div');
        title.className = 'conversation-item-title';
        title.textContent = conv.title || 'Untitled Conversation';
        titleDiv.appendChild(title);
        
        const meta = document.createElement('div');
        meta.className = 'conversation-item-meta';
        const date = new Date(conv.updated_at);
        meta.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        titleDiv.appendChild(meta);
        
        const actions = document.createElement('div');
        actions.className = 'conversation-item-actions';
        
        const exportBtn = document.createElement('button');
        exportBtn.textContent = '📥';
        exportBtn.title = 'Export';
        exportBtn.onclick = (e) => {
            e.stopPropagation();
            exportConversation(conv.id);
        };
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '🗑️';
        deleteBtn.title = 'Delete';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        };
        
        actions.appendChild(exportBtn);
        actions.appendChild(deleteBtn);
        
        item.appendChild(titleDiv);
        item.appendChild(actions);
        
        item.onclick = () => loadConversation(conv.id);
        
        listDiv.appendChild(item);
    });
}

function filterConversations(searchTerm) {
    const listDiv = document.getElementById('conversationsList');
    if (!listDiv) return;
    
    const items = listDiv.querySelectorAll('.conversation-item');
    const term = searchTerm.toLowerCase().trim();
    
    items.forEach(item => {
        const title = item.querySelector('.conversation-item-title')?.textContent.toLowerCase() || '';
        if (term === '' || title.includes(term)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

async function createNewConversation() {
    try {
        const response = await fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: null,
                model: currentModel
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            currentConversationId = data.conversation_id;
            // Clear chat
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '<div class="welcome-message"><h2>Welcome to LocalMind</h2><p>Select a model and start chatting! Your conversations stay local and private.</p></div>';
            await loadConversations();
        }
    } catch (error) {
        console.error('Failed to create conversation:', error);
        showNotification('Failed to create conversation', 'error');
    }
}

async function loadConversation(convId) {
    try {
        const response = await fetch(`/api/conversations/${convId}`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            const conversation = data.conversation;
            currentConversationId = convId;
            
            // Clear chat
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';
            
            // Load messages
            conversation.messages.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
            
            // Update model if specified
            if (conversation.model) {
                currentModel = conversation.model;
                const modelSelect = document.getElementById('modelSelect');
                if (modelSelect) {
                    modelSelect.value = currentModel;
                    updateModelInfo();
                }
            }
            
            await loadConversations(); // Refresh list to highlight active
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
        showNotification('Failed to load conversation', 'error');
    }
}

async function deleteConversation(convId) {
    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/conversations/${convId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            if (currentConversationId === convId) {
                currentConversationId = null;
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.innerHTML = '<div class="welcome-message"><h2>Welcome to LocalMind</h2><p>Select a model and start chatting! Your conversations stay local and private.</p></div>';
            }
            await loadConversations();
            showNotification('Conversation deleted', 'success');
        }
    } catch (error) {
        console.error('Failed to delete conversation:', error);
        showNotification('Failed to delete conversation', 'error');
    }
}

async function exportConversation(convId) {
    try {
        const response = await fetch(`/api/conversations/${convId}/export?format=markdown`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation_${convId}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Conversation exported', 'success');
    } catch (error) {
        console.error('Failed to export conversation:', error);
        showNotification('Failed to export conversation', 'error');
    }
}

