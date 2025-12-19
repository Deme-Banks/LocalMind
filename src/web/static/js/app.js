// LocalMind Web Interface JavaScript

// Global state
let currentModel = null;
let conversationHistory = [];
let downloadCheckInterval = null;
let currentConversationId = null;
let conversations = [];
let favoriteModels = JSON.parse(localStorage.getItem('favoriteModels') || '[]');
let unrestrictedMode = true; // Default to unrestricted
let comparisonMode = false;
let comparisonModels = [];
let autoRouting = false;

// Multiple chat sessions/tabs
let chatTabs = [];
let activeTabId = null;

// Chat templates
const chatTemplates = {
    presets: [
        {
            id: 'general',
            name: 'General Assistant',
            icon: '💬',
            description: 'Helpful and friendly AI assistant',
            systemPrompt: 'You are a helpful, friendly, and knowledgeable AI assistant. Provide clear, accurate, and helpful responses.',
            suggestedModel: null,
            temperature: 0.7
        },
        {
            id: 'coding',
            name: 'Coding Assistant',
            icon: '💻',
            description: 'Expert programming help',
            systemPrompt: 'You are an expert software developer and programming assistant. Write clean, efficient, and well-documented code. Explain your solutions clearly.',
            suggestedModel: 'codellama',
            temperature: 0.3
        },
        {
            id: 'writing',
            name: 'Writing Assistant',
            icon: '✍️',
            description: 'Creative and professional writing',
            systemPrompt: 'You are a professional writer and editor. Help create engaging, well-structured, and polished written content. Provide suggestions for improvement.',
            suggestedModel: null,
            temperature: 0.8
        },
        {
            id: 'analysis',
            name: 'Analyst',
            icon: '📊',
            description: 'Data analysis and insights',
            systemPrompt: 'You are a data analyst and researcher. Analyze information thoroughly, provide insights, and support conclusions with evidence.',
            suggestedModel: null,
            temperature: 0.5
        },
        {
            id: 'creative',
            name: 'Creative Writer',
            icon: '🎨',
            description: 'Creative storytelling and ideas',
            systemPrompt: 'You are a creative writer and storyteller. Generate imaginative, engaging, and original content. Think outside the box.',
            suggestedModel: null,
            temperature: 1.0
        },
        {
            id: 'teacher',
            name: 'Teacher',
            icon: '👨‍🏫',
            description: 'Educational explanations',
            systemPrompt: 'You are a patient and knowledgeable teacher. Explain concepts clearly, use examples, and adapt to different learning styles.',
            suggestedModel: null,
            temperature: 0.7
        },
        {
            id: 'translator',
            name: 'Translator',
            icon: '🌐',
            description: 'Language translation',
            systemPrompt: 'You are a professional translator. Provide accurate translations while preserving meaning, tone, and cultural context.',
            suggestedModel: null,
            temperature: 0.3
        },
        {
            id: 'debugger',
            name: 'Debug Helper',
            icon: '🐛',
            description: 'Find and fix bugs',
            systemPrompt: 'You are a debugging expert. Analyze code, identify issues, and provide clear explanations of problems and solutions.',
            suggestedModel: 'codellama',
            temperature: 0.2
        }
    ],
    custom: []
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeMarkdown();
    initializeApp();
    loadUnrestrictedMode();
});

// Configure markdown rendering
function initializeMarkdown() {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });
    }
}

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
    await autoSelectModel();  // Auto-select after models are loaded
    await loadConversations();
    loadComparisonModels();
    loadAutoRouting();
    loadChatTemplates();
    initializeChatTabs();
    loadSharedConversation(); // Check for shared conversation in URL
    setupEventListeners();
    setupFileUpload();
}

// Chat Tabs Management
function initializeChatTabs() {
    // Create initial tab
    if (chatTabs.length === 0) {
        createNewChatTab();
    } else {
        // Restore tabs from localStorage
        const savedTabs = localStorage.getItem('chatTabs');
        if (savedTabs) {
            try {
                chatTabs = JSON.parse(savedTabs);
                activeTabId = localStorage.getItem('activeTabId') || chatTabs[0]?.id || null;
                renderChatTabs();
                if (activeTabId) {
                    switchToTab(activeTabId);
                }
            } catch (e) {
                console.error('Error loading chat tabs:', e);
                createNewChatTab();
            }
        } else {
            createNewChatTab();
        }
    }
}

function createNewChatTab(title = null) {
    const tabId = `tab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const tab = {
        id: tabId,
        title: title || `Chat ${chatTabs.length + 1}`,
        conversationId: null,
        model: currentModel,
        messages: [],
        unread: false,
        createdAt: new Date().toISOString()
    };
    
    chatTabs.push(tab);
    activeTabId = tabId;
    renderChatTabs();
    switchToTab(tabId);
    saveChatTabs();
    
    return tabId;
}

function renderChatTabs() {
    const tabsList = document.getElementById('chatTabsList');
    if (!tabsList) return;
    
    tabsList.innerHTML = '';
    
    chatTabs.forEach(tab => {
        const tabElement = document.createElement('div');
        tabElement.className = `chat-tab ${tab.id === activeTabId ? 'active' : ''} ${tab.unread ? 'unread' : ''}`;
        tabElement.onclick = (e) => {
            if (e.target.classList.contains('chat-tab-close')) return;
            switchToTab(tab.id);
        };
        
        tabElement.innerHTML = `
            <span class="chat-tab-title" title="${tab.title}">${tab.title}</span>
            <button class="chat-tab-close" onclick="closeChatTab('${tab.id}', event)" title="Close tab (Ctrl+W)">×</button>
            <span class="chat-tab-unread"></span>
        `;
        
        tabsList.appendChild(tabElement);
    });
}

function switchToTab(tabId) {
    const tab = chatTabs.find(t => t.id === tabId);
    if (!tab) return;
    
    // Save current tab state
    if (activeTabId) {
        saveCurrentTabState();
    }
    
    // Switch to new tab
    activeTabId = tabId;
    currentConversationId = tab.conversationId;
    currentModel = tab.model || currentModel;
    
    // Update UI
    renderChatTabs();
    loadTabMessages(tab);
    updateModelSelectDisplay(currentModel);
    
    // Update conversation sidebar if needed
    if (tab.conversationId) {
        highlightConversation(tab.conversationId);
    }
    
    saveChatTabs();
}

function saveCurrentTabState() {
    if (!activeTabId) return;
    
    const tab = chatTabs.find(t => t.id === activeTabId);
    if (!tab) return;
    
    // Save messages from DOM
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        const messages = Array.from(chatMessages.querySelectorAll('.message')).map(msgEl => {
            const role = msgEl.classList.contains('user') ? 'user' : 'assistant';
            const textEl = msgEl.querySelector('.message-text');
            return {
                role: role,
                content: textEl ? textEl.textContent : ''
            };
        });
        tab.messages = messages;
    }
    
    tab.conversationId = currentConversationId;
    tab.model = currentModel;
    tab.unread = false; // Mark as read when switching to it
}

function loadTabMessages(tab) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Clear current messages
    chatMessages.innerHTML = '';
    
    if (tab.messages && tab.messages.length > 0) {
        // Restore messages
        tab.messages.forEach(msg => {
            addMessage(msg.role, msg.content, false, false);
        });
    } else {
        // Show welcome message
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to LocalMind</h2>
                <p>Select a model and start chatting! Your conversations stay local and private.</p>
                <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                    💡 Tip: Press <kbd>Ctrl+T</kbd> for new tab, <kbd>Ctrl+W</kbd> to close tab
                </p>
            </div>
        `;
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function closeChatTab(tabId, event) {
    if (event) {
        event.stopPropagation();
    }
    
    const tabIndex = chatTabs.findIndex(t => t.id === tabId);
    if (tabIndex === -1) return;
    
    // Don't allow closing the last tab
    if (chatTabs.length <= 1) {
        showToast('Cannot close the last tab', 'info');
        return;
    }
    
    // Save current tab state before closing
    saveCurrentTabState();
    
    // Remove tab
    chatTabs.splice(tabIndex, 1);
    
    // Switch to another tab
    if (activeTabId === tabId) {
        const newActiveIndex = Math.min(tabIndex, chatTabs.length - 1);
        activeTabId = chatTabs[newActiveIndex]?.id || null;
        if (activeTabId) {
            switchToTab(activeTabId);
        }
    } else {
        renderChatTabs();
    }
    
    saveChatTabs();
}

function saveChatTabs() {
    // Save current tab state first
    saveCurrentTabState();
    
    localStorage.setItem('chatTabs', JSON.stringify(chatTabs));
    if (activeTabId) {
        localStorage.setItem('activeTabId', activeTabId);
    }
}

function updateTabTitle(tabId, title) {
    const tab = chatTabs.find(t => t.id === tabId);
    if (tab) {
        tab.title = title;
        renderChatTabs();
        saveChatTabs();
    }
}

function markTabUnread(tabId) {
    const tab = chatTabs.find(t => t.id === tabId);
    if (tab && tab.id !== activeTabId) {
        tab.unread = true;
        renderChatTabs();
        saveChatTabs();
    }
}

function loadAutoRouting() {
    const saved = localStorage.getItem('autoRouting');
    if (saved === 'true') {
        autoRouting = true;
        const checkbox = document.getElementById('autoRouting');
        if (checkbox) {
            checkbox.checked = true;
        }
    }
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

// Backend display names and icons
const backendInfo = {
    'ollama': { name: 'Ollama (Local)', icon: '🖥️' },
    'openai': { name: 'OpenAI (ChatGPT)', icon: '🤖' },
    'anthropic': { name: 'Anthropic (Claude)', icon: '🧠' },
    'google': { name: 'Google (Gemini)', icon: '🔍' },
    'mistral-ai': { name: 'Mistral AI', icon: '🌊' },
    'cohere': { name: 'Cohere', icon: '💬' },
    'groq': { name: 'Groq (Fast)', icon: '⚡' },
    'transformers': { name: 'Transformers (Local)', icon: '🔧' },
    'gguf': { name: 'GGUF (Local)', icon: '📦' }
};

// Load models with folder-style dropdown
// Auto-select best model on startup
async function autoSelectModel(showNotification = false) {
    try {
        const response = await fetch('/api/models/auto-select');
        const data = await response.json();
        
        if (data.status === 'ok' && data.data.selected_model) {
            const selected = data.data.selected_model;
            
            // Only auto-select if no model is currently selected, or if explicitly requested
            if (!currentModel || showNotification) {
                currentModel = selected;
                document.getElementById('modelSelect').value = selected;
                updateModelSelectDisplay(selected);
                updateModelInfo();
                
                if (showNotification) {
                    showToast(`Auto-selected model: ${selected}`, 'success');
                } else {
                    console.log(`Auto-selected model: ${selected}`);
                }
                return true;
            }
        }
        return false;
    } catch (error) {
        console.error('Error in auto-select:', error);
        if (showNotification) {
            showToast('Failed to auto-select model', 'error');
        }
        return false;
    }
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        if (data.status === 'ok') {
            const modelSelect = document.getElementById('modelSelect');
            const dropdownContent = document.getElementById('modelDropdownContent');
            
            // Organize models by backend
            const modelsByBackend = {};
            const allModels = [];
            
            for (const [backend, models] of Object.entries(data.models)) {
                if (!modelsByBackend[backend]) {
                    modelsByBackend[backend] = [];
                }
                for (const model of models) {
                    modelsByBackend[backend].push(model);
                    allModels.push({ name: model, backend });
                }
            }
            
            if (allModels.length === 0) {
                dropdownContent.innerHTML = '<p style="padding: 1rem; color: var(--text-secondary);">No models available</p>';
                modelSelect.innerHTML = '<option value="">No models available</option>';
                return;
            }
            
            // Separate favorites by backend
            const favoritesByBackend = {};
            const regularModelsByBackend = {};
            
            for (const [backend, models] of Object.entries(modelsByBackend)) {
                favoritesByBackend[backend] = models.filter(m => favoriteModels.includes(m));
                regularModelsByBackend[backend] = models.filter(m => !favoriteModels.includes(m));
            }
            
            // Build folder-style dropdown
            let html = '';
            
            // Favorites section
            let hasFavorites = false;
            for (const [backend, models] of Object.entries(favoritesByBackend)) {
                if (models.length > 0) {
                    hasFavorites = true;
                    break;
                }
            }
            
            if (hasFavorites) {
                html += '<div class="model-favorites-section">';
                html += '<div class="model-section-header">⭐ Favorites</div>';
                
                for (const [backend, models] of Object.entries(favoritesByBackend)) {
                    if (models.length > 0) {
                        const backendInfo_data = backendInfo[backend] || { name: backend, icon: '🔹' };
                        html += createBackendFolder(backend, backendInfo_data, models, true, true); // Expanded by default
                    }
                }
                
                html += '</div>';
            }
            
            // All models section
            html += '<div class="model-all-section">';
            for (const [backend, models] of Object.entries(regularModelsByBackend)) {
                if (models.length > 0) {
                    const backendInfo_data = backendInfo[backend] || { name: backend, icon: '🔹' };
                    html += createBackendFolder(backend, backendInfo_data, models, false, false);
                }
            }
            html += '</div>';
            
            dropdownContent.innerHTML = html;
            
            // Also update hidden select for compatibility
            modelSelect.innerHTML = '<option value="">Select a model...</option>';
            for (const [backend, models] of Object.entries(modelsByBackend)) {
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    modelSelect.appendChild(option);
                });
            }
            
            // Set default model if available
            if (allModels.length > 0 && !currentModel) {
                let defaultModel = null;
                for (const [backend, models] of Object.entries(favoritesByBackend)) {
                    if (models.length > 0) {
                        defaultModel = models[0];
                        break;
                    }
                }
                if (!defaultModel) {
                    for (const [backend, models] of Object.entries(regularModelsByBackend)) {
                        if (models.length > 0) {
                            defaultModel = models[0];
                            break;
                        }
                    }
                }
                if (defaultModel) {
                    currentModel = defaultModel;
                    modelSelect.value = currentModel;
                    updateModelSelectDisplay(defaultModel);
                    updateModelInfo();
                }
            }
            
            updateFavoriteModelsList();
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        showToast('Failed to load models', 'error');
    }
}

function createBackendFolder(backend, backendInfo_data, models, isFavorite, isExpanded = false) {
    const folderId = `folder-${backend}-${isFavorite ? 'fav' : 'all'}`;
    let html = `<div class="model-backend-folder ${isExpanded ? 'expanded' : ''}" data-backend="${backend}">`;
    html += `<div class="model-backend-header" onclick="toggleBackendFolder('${folderId}')">`;
    html += `<div class="model-backend-name">`;
    html += `<span class="model-backend-arrow">▶</span>`;
    html += `<span class="model-backend-icon">${backendInfo_data.icon}</span>`;
    html += `<span>${backendInfo_data.name}</span>`;
    html += `<span style="margin-left: auto; color: var(--text-secondary); font-size: 0.75rem;">${models.length}</span>`;
    html += `</div></div>`;
    html += `<div class="model-backend-models" id="${folderId}">`;
    
    models.forEach(model => {
        const isModelFavorite = favoriteModels.includes(model);
        const isSelected = currentModel === model;
        html += `<div class="model-item ${isModelFavorite ? 'favorite' : ''} ${isSelected ? 'selected' : ''}" onclick="selectModel('${model}')" data-model="${model}">`;
        if (isModelFavorite) {
            html += `<span class="model-item-favorite-icon">⭐</span>`;
        }
        html += `<span>${model}</span>`;
        html += `</div>`;
    });
    
    html += `</div></div>`;
    return html;
}

function toggleBackendFolder(folderId) {
    const folder = document.getElementById(folderId).closest('.model-backend-folder');
    if (folder) {
        folder.classList.toggle('expanded');
    }
}

function selectModel(modelName) {
    currentModel = modelName;
    document.getElementById('modelSelect').value = modelName;
    updateModelSelectDisplay(modelName);
    updateModelInfo();
    closeModelDropdown();
    showToast(`Selected: ${modelName}`, 'success');
}

function updateModelSelectDisplay(modelName) {
    const display = document.getElementById('modelSelectText');
    if (display && modelName) {
        display.textContent = modelName;
    } else if (display) {
        display.textContent = 'Select a model...';
    }
    
    // Update selected state in dropdown
    document.querySelectorAll('.model-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.model === modelName) {
            item.classList.add('selected');
        }
    });
}

function toggleModelDropdown() {
    const dropdown = document.getElementById('modelDropdown');
    const display = document.getElementById('modelSelectDisplay');
    
    if (dropdown && display) {
        dropdown.classList.toggle('show');
        display.classList.toggle('active');
    }
}

function closeModelDropdown() {
    const dropdown = document.getElementById('modelDropdown');
    const display = document.getElementById('modelSelectDisplay');
    const searchInput = document.getElementById('modelSearchInput');
    
    if (dropdown && display) {
        dropdown.classList.remove('show');
        display.classList.remove('active');
    }
    
    // Clear search when closing
    if (searchInput) {
        searchInput.value = '';
        filterModelDropdown(''); // Reset filter
    }
}

function filterModelDropdown(searchTerm) {
    const term = searchTerm.toLowerCase();
    const folders = document.querySelectorAll('.model-backend-folder');
    
    folders.forEach(folder => {
        const models = folder.querySelectorAll('.model-item');
        let hasMatch = false;
        
        models.forEach(model => {
            const modelName = model.dataset.model.toLowerCase();
            if (modelName.includes(term)) {
                model.style.display = '';
                hasMatch = true;
            } else {
                model.style.display = 'none';
            }
        });
        
        // Expand folder if it has matches, hide if not
        if (hasMatch) {
            folder.style.display = '';
            if (term) {
                folder.classList.add('expanded');
            }
        } else {
            folder.style.display = term ? 'none' : '';
        }
    });
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const container = document.querySelector('.model-select-container');
    if (container && !container.contains(e.target)) {
        closeModelDropdown();
    }
});

// Model recommendations based on task
const modelRecommendations = {
    'code': ['codellama', 'deepseek-coder', 'gpt-4', 'claude-3-opus'],
    'writing': ['llama3', 'mistral', 'gpt-3.5-turbo', 'claude-3-sonnet'],
    'analysis': ['gpt-4', 'claude-3-opus', 'llama3', 'mistral-large'],
    'chat': ['llama3', 'mistral', 'gpt-3.5-turbo', 'claude-3-haiku'],
    'creative': ['gpt-4', 'claude-3-opus', 'mistral-large', 'llama3'],
    'fast': ['groq', 'gpt-3.5-turbo', 'claude-3-haiku', 'mistral-tiny']
};

function recommendModel(task) {
    const recommendations = modelRecommendations[task.toLowerCase()] || [];
    if (recommendations.length > 0) {
        // Check which recommended models are available
        const modelSelect = document.getElementById('modelSelect');
        const availableModels = Array.from(modelSelect.options).map(opt => opt.value).filter(v => v);
        
        for (const rec of recommendations) {
            if (availableModels.includes(rec)) {
                return rec;
            }
        }
    }
    return null;
}

// Update model info
async function updateModelInfo() {
    const modelInfo = document.getElementById('modelInfo');
    if (!currentModel) {
        modelInfo.innerHTML = '<span>No model selected</span>';
        modelInfo.title = '';
        return;
    }
    
    // Find backend for this model
    let backendName = 'Unknown';
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        if (data.status === 'ok') {
            for (const [backend, models] of Object.entries(data.models)) {
                if (models.includes(currentModel)) {
                    backendName = backend;
                    break;
                }
            }
        }
    } catch (error) {
        console.error('Failed to get model info:', error);
    }
    
    // Get backend display name
    const backendDisplayNames = {
        'ollama': 'Ollama (Local)',
        'openai': 'OpenAI (ChatGPT)',
        'anthropic': 'Anthropic (Claude)',
        'google': 'Google (Gemini)',
        'mistral-ai': 'Mistral AI',
        'cohere': 'Cohere',
        'groq': 'Groq (Fast Inference)',
        'transformers': 'Transformers (Local)',
        'gguf': 'GGUF (Local)'
    };
    
    const displayName = backendDisplayNames[backendName] || backendName;
    
    // Determine model type for recommendations
    let modelType = 'general';
    if (currentModel.includes('code') || currentModel.includes('coder')) {
        modelType = 'code';
    } else if (currentModel.includes('gpt-4') || currentModel.includes('claude-3-opus')) {
        modelType = 'analysis';
    }
    
    const tooltip = `Model: ${currentModel}\nBackend: ${displayName}\nType: ${modelType}\n\n💡 Tip: Use this model for ${modelType === 'code' ? 'coding tasks' : modelType === 'analysis' ? 'complex analysis' : 'general tasks'}`;
    
    modelInfo.innerHTML = `
        <span class="model-info-text" title="${tooltip.replace(/\n/g, ' ')}">
            Selected: <strong>${currentModel}</strong>
            <span class="model-backend-badge">${displayName}</span>
        </span>
    `;
    modelInfo.title = tooltip;
}

// Setup event listeners
function setupEventListeners() {
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const modelSelect = document.getElementById('modelSelect');
    const newConversationBtn = document.getElementById('newConversationBtn');
    const conversationsSearch = document.getElementById('conversationsSearch');
    
    // Model selection (for hidden select compatibility)
    modelSelect.addEventListener('change', (e) => {
        currentModel = e.target.value;
        updateModelSelectDisplay(currentModel);
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
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+T or Cmd+T: New tab
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            e.preventDefault();
            createNewChatTab();
        }
        // Ctrl+W or Cmd+W: Close current tab
        if ((e.ctrlKey || e.metaKey) && e.key === 'w') {
            e.preventDefault();
            if (activeTabId) {
                closeChatTab(activeTabId);
            }
        }
        // Ctrl+K or Cmd+K: New conversation
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            createNewConversation();
        }
        // Ctrl+L or Cmd+L: Clear chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
            e.preventDefault();
            clearChat();
        }
        // Ctrl+/ or Cmd+/: Show shortcuts (show about)
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showAbout();
        }
        // Ctrl+1-9: Switch to tab by number
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '9') {
            e.preventDefault();
            const tabIndex = parseInt(e.key) - 1;
            if (chatTabs[tabIndex]) {
                switchToTab(chatTabs[tabIndex].id);
            }
        }
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

// Comparison Mode Functions
function toggleComparisonMode() {
    comparisonMode = !comparisonMode;
    const btn = document.getElementById('comparisonModeBtn');
    const section = document.getElementById('comparisonModeSection');
    
    if (comparisonMode) {
        btn.classList.add('active');
        btn.style.background = 'var(--primary-color)';
        btn.style.color = 'white';
        if (section) section.style.display = 'block';
        updateComparisonModelsList();
    } else {
        btn.classList.remove('active');
        btn.style.background = '';
        btn.style.color = '';
        if (section) section.style.display = 'none';
        comparisonModels = [];
        updateComparisonModelsList();
    }
}

function addComparisonModel() {
    // Show model selector modal
    const modelName = prompt('Enter model name to compare (or select from dropdown):');
    if (modelName && modelName.trim()) {
        const trimmedName = modelName.trim();
        if (!comparisonModels.includes(trimmedName)) {
            if (comparisonModels.length >= 5) {
                showToast('Maximum 5 models can be compared', 'error');
                return;
            }
            comparisonModels.push(trimmedName);
            updateComparisonModelsList();
            saveComparisonModels();
            showToast(`Added ${trimmedName} to comparison`, 'success');
        } else {
            showToast('Model already added', 'info');
        }
    }
}

function addCurrentModelToComparison() {
    if (!currentModel) {
        showToast('Please select a model first', 'error');
        return;
    }
    
    if (comparisonModels.includes(currentModel)) {
        showToast('Model already in comparison', 'info');
        return;
    }
    
    if (comparisonModels.length >= 5) {
        showToast('Maximum 5 models can be compared', 'error');
        return;
    }
    
    comparisonModels.push(currentModel);
    updateComparisonModelsList();
    saveComparisonModels();
    showToast(`Added ${currentModel} to comparison`, 'success');
}

function removeComparisonModel(modelName) {
    comparisonModels = comparisonModels.filter(m => m !== modelName);
    updateComparisonModelsList();
    saveComparisonModels();
}

function clearComparisonModels() {
    comparisonModels = [];
    updateComparisonModelsList();
    saveComparisonModels();
}

function updateComparisonModelsList() {
    const list = document.getElementById('comparisonModelsList');
    if (!list) return;
    
    if (comparisonModels.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.875rem;">No models selected</p>';
        return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 0.5rem;">';
    comparisonModels.forEach(model => {
        html += `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: var(--surface-light); border-radius: 0.375rem; border: 1px solid var(--border-color);">
                <span style="font-size: 0.875rem;">${model}</span>
                <button class="btn-icon" onclick="removeComparisonModel('${model}')" style="padding: 0.25rem; font-size: 0.75rem;" title="Remove">×</button>
            </div>
        `;
    });
    html += '</div>';
    list.innerHTML = html;
    
    // Update counter
    const counter = document.getElementById('comparisonModelCount');
    if (counter) {
        counter.textContent = `${comparisonModels.length}/5 models`;
    }
}

function saveComparisonModels() {
    localStorage.setItem('comparisonModels', JSON.stringify(comparisonModels));
}

function loadComparisonModels() {
    const saved = localStorage.getItem('comparisonModels');
    if (saved) {
        try {
            comparisonModels = JSON.parse(saved);
            if (comparisonMode) {
                updateComparisonModelsList();
            }
        } catch (e) {
            console.error('Error loading comparison models:', e);
        }
    }
    
    // Load ensemble mode setting
    const ensembleMode = localStorage.getItem('ensembleMode') === 'true';
    const ensembleCheckbox = document.getElementById('ensembleMode');
    if (ensembleCheckbox) {
        ensembleCheckbox.checked = ensembleMode;
    }
    
    // Load ensemble method
    const ensembleMethod = localStorage.getItem('ensembleMethod') || 'majority_vote';
    const methodSelect = document.getElementById('ensembleMethod');
    if (methodSelect) {
        methodSelect.value = ensembleMethod;
    }
}

function updateEnsembleMode() {
    const checkbox = document.getElementById('ensembleMode');
    if (checkbox) {
        localStorage.setItem('ensembleMode', checkbox.checked);
    }
    
    const methodSelect = document.getElementById('ensembleMethod');
    if (methodSelect) {
        localStorage.setItem('ensembleMethod', methodSelect.value);
    }
}

// Ensemble Message Function
async function sendEnsembleMessage(prompt) {
    if (comparisonModels.length < 2) {
        showToast('Please select at least 2 models for ensemble', 'error');
        return;
    }
    
    if (comparisonModels.length > 5) {
        showToast('Maximum 5 models can be used in ensemble', 'error');
        return;
    }
    
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    // Disable input
    chatInput.disabled = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span> Generating ensemble...';
    
    // Add user message
    addMessage('user', prompt);
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    updateWordCount();
    
    // Get settings
    const temperature = parseFloat(document.getElementById('temperature').value);
    const systemPrompt = document.getElementById('systemPrompt').value || undefined;
    const method = document.getElementById('ensembleMethod')?.value || 'majority_vote';
    
    try {
        const response = await fetch('/api/chat/ensemble', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                models: comparisonModels,
                system_prompt: systemPrompt,
                temperature: temperature,
                method: method,
                disable_safety_filters: unrestrictedMode
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Ensemble generation failed');
        }
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            // Display ensemble result
            displayEnsembleResult(prompt, data.data);
        } else {
            throw new Error(data.message || 'Ensemble generation failed');
        }
    } catch (error) {
        console.error('Error in ensemble:', error);
        showToast(`Ensemble failed: ${error.message}`, 'error', 5000);
        addMessage('assistant', `**Error:** ${error.message}`, true);
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = '<span>Send</span>';
        chatInput.focus();
    }
}

function displayEnsembleResult(prompt, data) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Create ensemble container
    const ensembleDiv = document.createElement('div');
    ensembleDiv.className = 'ensemble-container';
    ensembleDiv.id = `ensemble-${Date.now()}`;
    
    const methodNames = {
        'majority_vote': 'Majority Vote',
        'best': 'Best Response',
        'longest': 'Longest Response',
        'concatenate': 'Concatenated',
        'average': 'All Responses'
    };
    
    let html = `
        <div class="ensemble-header">
            <h4>🔀 Ensemble Response</h4>
            <div style="display: flex; gap: 1rem; align-items: center; font-size: 0.875rem; color: var(--text-secondary);">
                <span>Method: <strong>${methodNames[data.method] || data.method}</strong></span>
                <span>Models: ${data.models_used.join(', ')}</span>
            </div>
        </div>
        <div class="ensemble-content">
            ${renderMarkdown(data.response)}
        </div>
    `;
    
    // Show individual responses in collapsible section
    if (data.individual_responses && data.individual_responses.length > 0) {
        html += `
            <div class="ensemble-individual" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                <details style="cursor: pointer;">
                    <summary style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                        View Individual Responses (${data.individual_responses.length})
                    </summary>
                    <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem;">
        `;
        
        data.individual_responses.forEach(resp => {
            html += `
                <div style="padding: 0.75rem; background: var(--surface-light); border-radius: 0.375rem; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.875rem;">
                        <strong>${resp.model}</strong>
                        <span style="color: var(--text-secondary);">${resp.response_time}s</span>
                    </div>
                    <div style="font-size: 0.875rem;">
                        ${renderMarkdown(resp.response)}
                    </div>
                </div>
            `;
        });
        
        html += `
                    </div>
                </details>
            </div>
        `;
    }
    
    html += '</div>';
    ensembleDiv.innerHTML = html;
    
    chatMessages.appendChild(ensembleDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Auto Routing Functions
function toggleAutoRouting(enabled) {
    autoRouting = enabled;
    localStorage.setItem('autoRouting', enabled);
    
    if (enabled) {
        showToast('Auto routing enabled - models will be selected automatically', 'success');
    } else {
        showToast('Auto routing disabled', 'info');
    }
}

async function routeToBestModel(prompt) {
    try {
        const response = await fetch('/api/chat/route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt
            })
        });
        
        if (!response.ok) {
            throw new Error('Routing failed');
        }
        
        const data = await response.json();
        if (data.status === 'ok' && data.data.recommended_model) {
            const recommended = data.data.recommended_model;
            const task = data.data.detected_task;
            const confidence = data.data.confidence;
            
            // Switch to recommended model
            if (recommended !== currentModel) {
                currentModel = recommended;
                document.getElementById('modelSelect').value = recommended;
                updateModelSelectDisplay(recommended);
                updateModelInfo();
                
                showToast(
                    `Auto-routed to ${recommended} (${task}, ${Math.round(confidence * 100)}% confidence)`,
                    'success',
                    3000
                );
            }
            
            return true;
        }
    } catch (error) {
        console.error('Error in auto routing:', error);
        // Don't show error to user, just fall back to current model
    }
    return false;
}

// Send message
async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Check if comparison mode is active
    if (comparisonMode && comparisonModels.length >= 2) {
        const ensembleMode = document.getElementById('ensembleMode')?.checked || false;
        if (ensembleMode) {
            await sendEnsembleMessage(message);
        } else {
            await sendComparisonMessage(message);
        }
        return;
    }
    
    // Auto routing
    if (autoRouting) {
        await routeToBestModel(message);
    }
    
    if (!currentModel) {
        showToast('Please select a model first', 'error');
        return;
    }
    
    // Disable input
    chatInput.disabled = true;
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span> Sending...';
    
    // Add user message to chat
    addMessage('user', message);
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    updateWordCount();
    
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
        const errorMsg = error.message || 'An unexpected error occurred. Please try again.';
        
        // Graceful degradation: try to provide helpful error message
        let helpfulMsg = `**Error:** ${errorMsg}\n\n`;
        
        if (errorMsg.includes('network') || errorMsg.includes('fetch') || errorMsg.includes('Failed to fetch')) {
            helpfulMsg += '**Network Error:**\n- Check your internet connection\n- For API models, verify your API key is configured\n- Try again in a moment';
        } else if (errorMsg.includes('model') || errorMsg.includes('backend') || errorMsg.includes('not available')) {
            helpfulMsg += '**Model Error:**\n- Verify the model is available and selected\n- Check if the backend is running (for local models)\n- Try selecting a different model';
        } else if (errorMsg.includes('429') || errorMsg.includes('rate limit')) {
            helpfulMsg += '**Rate Limit Error:**\n- Too many requests. Please wait a moment and try again\n- Consider using a different model or backend';
        } else {
            helpfulMsg += '**Troubleshooting:**\n- Check your model is selected and available\n- Verify your internet connection (for API models)\n- Check the server logs for more details';
        }
        
        addMessage('assistant', helpfulMsg, true);
        showToast(`Failed to send message: ${errorMsg}`, 'error', 5000);
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = '<span>Send</span>';
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
            conversation_id: currentConversationId,
            unrestricted_mode: unrestrictedMode
        })
    });
    
    if (!response.ok) {
        // Try to get error message from response
        let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.message || errorMsg;
        } catch (e) {
            // If response isn't JSON, use status text
        }
        throw new Error(errorMsg);
    }
    
    const data = await response.json();
    
    if (data.status === 'ok') {
        addMessage('assistant', data.response);
        
        // Show performance metrics if available
        if (data.metadata && data.metadata.response_time) {
            const metrics = data.metadata;
            const metricsText = `\n\n*Response time: ${metrics.response_time}s | Length: ${metrics.response_length} chars*`;
            // Could append to message or show in a tooltip
        }
        
        // Update conversation ID if returned
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            
            // Update current tab with conversation ID
            if (activeTabId) {
                const tab = chatTabs.find(t => t.id === activeTabId);
                if (tab) {
                    tab.conversationId = currentConversationId;
                    saveChatTabs();
                }
            }
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
            conversation_id: currentConversationId,
            unrestricted_mode: unrestrictedMode
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
            
            // Update current tab with conversation ID
            if (activeTabId) {
                const tab = chatTabs.find(t => t.id === activeTabId);
                if (tab) {
                    tab.conversationId = currentConversationId;
                    saveChatTabs();
                }
            }
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
    messageDiv.id = isStreaming ? `msg-${Date.now()}` : `msg-${Date.now()}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    // Render markdown for assistant messages, plain text for user
    if (role === 'assistant' && typeof marked !== 'undefined') {
        textDiv.innerHTML = marked.parse(text);
        // Highlight code blocks
        textDiv.querySelectorAll('pre code').forEach((block) => {
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(block);
            }
        });
    } else {
        textDiv.textContent = text;
    }
    
    // Add message actions
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'message-actions';
    
    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn-icon';
    copyBtn.innerHTML = '📋';
    copyBtn.title = 'Copy message';
    copyBtn.onclick = () => copyMessage(text, copyBtn);
    actionsDiv.appendChild(copyBtn);
    
    // Edit/Regenerate button (for assistant messages)
    if (role === 'assistant') {
        const regenerateBtn = document.createElement('button');
        regenerateBtn.className = 'btn-icon';
        regenerateBtn.innerHTML = '🔄';
        regenerateBtn.title = 'Regenerate response';
        regenerateBtn.onclick = () => regenerateMessage(messageDiv.id, text);
        actionsDiv.appendChild(regenerateBtn);
    }
    
    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-icon';
    deleteBtn.innerHTML = '🗑️';
    deleteBtn.title = 'Delete message';
    deleteBtn.onclick = () => deleteMessage(messageDiv.id);
    actionsDiv.appendChild(deleteBtn);
    
    content.appendChild(textDiv);
    content.appendChild(actionsDiv);
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
        // Get current text and append chunk
        const currentText = textDiv.textContent || '';
        const newText = currentText + chunk;
        
        // Re-render markdown
        if (typeof marked !== 'undefined') {
            textDiv.innerHTML = marked.parse(newText);
            // Re-highlight code blocks
            textDiv.querySelectorAll('pre code').forEach((block) => {
                if (typeof hljs !== 'undefined') {
                    hljs.highlightElement(block);
                }
            });
        } else {
            textDiv.textContent = newText;
        }
        
        // Update copy button
        const copyBtn = messageDiv.querySelector('.btn-icon');
        if (copyBtn) {
            copyBtn.onclick = () => copyMessage(newText, copyBtn);
        }
        
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
        desc.textContent = descText;
        
        // Add size badge if available
        if (model.size) {
            const sizeBadge = document.createElement('span');
            sizeBadge.className = 'model-size-badge';
            sizeBadge.textContent = `📦 ${model.size}`;
            sizeBadge.title = `Model size: ${model.size}`;
            desc.appendChild(document.createTextNode(' • '));
            desc.appendChild(sizeBadge);
        }
        
        // Add tags if available
        if (model.tags && model.tags.length > 0) {
            const tagsText = document.createTextNode(` • Tags: ${model.tags.join(', ')}`);
            desc.appendChild(tagsText);
        }
        
        // Add update indicator if update is available
        if (model.has_update) {
            const updateBadge = document.createElement('span');
            updateBadge.className = 'model-update-badge';
            updateBadge.textContent = '🔄 Update Available';
            updateBadge.title = `Update available: ${model.latest_version || 'latest version'}`;
            desc.appendChild(document.createTextNode(' • '));
            desc.appendChild(updateBadge);
        }
    } else {
        desc.textContent = `Backend: ${backend}`;
    }
    
    info.appendChild(name);
    info.appendChild(desc);
    
    const actions = document.createElement('div');
    actions.className = 'model-card-actions';
    
    // Favorite button
    const favoriteBtn = document.createElement('button');
    favoriteBtn.className = 'btn-icon';
    const isFavorite = favoriteModels.includes(modelName);
    favoriteBtn.innerHTML = isFavorite ? '⭐' : '☆';
    favoriteBtn.title = isFavorite ? 'Remove from favorites' : 'Add to favorites';
    favoriteBtn.onclick = (e) => {
        e.stopPropagation();
        toggleFavorite(modelName, favoriteBtn);
    };
    actions.appendChild(favoriteBtn);
    
    if (isInstalled) {
        const useBtn = document.createElement('button');
        useBtn.className = 'btn btn-primary btn-small';
        useBtn.textContent = 'Use';
        useBtn.onclick = () => {
            currentModel = modelName;
            document.getElementById('modelSelect').value = currentModel;
            updateModelInfo();
            closeModelManager();
            showToast(`Switched to ${currentModel}`, 'success');
        };
        actions.appendChild(useBtn);
        
        // Check update button
        const checkUpdateBtn = document.createElement('button');
        checkUpdateBtn.className = 'btn btn-secondary btn-small';
        checkUpdateBtn.textContent = 'Check Update';
        checkUpdateBtn.onclick = (e) => {
            e.stopPropagation();
            checkModelUpdate(modelName, backend, card);
        };
        actions.appendChild(checkUpdateBtn);
        
        // Delete button (only for local backends that support deletion)
        if (backend === 'ollama' || backend === 'transformers' || backend === 'gguf') {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-danger btn-small';
            deleteBtn.textContent = 'Delete';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteModel(modelName, backend);
            };
            actions.appendChild(deleteBtn);
        }
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

// Delete model
async function deleteModel(modelName, backendName = 'ollama') {
    if (!confirm(`Are you sure you want to delete "${modelName}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/models/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: modelName,
                backend: backendName
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showToast(`Model "${modelName}" deleted successfully`, 'success');
            // Reload models
            await loadInstalledModels();
            await loadAvailableModels();
            await loadModels(); // Refresh main model list
        } else {
            showToast(data.message || 'Failed to delete model', 'error');
        }
    } catch (error) {
        console.error('Failed to delete model:', error);
        showToast('Failed to delete model', 'error');
    }
}

// Check for model update
async function checkModelUpdate(modelName, backendName = 'ollama', cardElement = null) {
    try {
        const response = await fetch('/api/models/check-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: modelName,
                backend: backendName
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            const updateInfo = data.data;
            
            if (updateInfo.has_update) {
                const message = `Update available for "${modelName}"!\n\n` +
                              `Current: ${updateInfo.current_version || 'installed'}\n` +
                              `Latest: ${updateInfo.latest_version || 'latest'}\n\n` +
                              `Would you like to update now?`;
                
                if (confirm(message)) {
                    // Trigger download/update
                    await downloadModel(modelName, backendName);
                }
                
                // Update card if provided
                if (cardElement) {
                    const updateBadge = cardElement.querySelector('.model-update-badge');
                    if (!updateBadge) {
                        const desc = cardElement.querySelector('.model-card-info p');
                        if (desc) {
                            const badge = document.createElement('span');
                            badge.className = 'model-update-badge';
                            badge.textContent = '🔄 Update Available';
                            badge.title = `Update available: ${updateInfo.latest_version || 'latest version'}`;
                            desc.appendChild(document.createTextNode(' • '));
                            desc.appendChild(badge);
                        }
                    }
                }
            } else {
                showToast(`"${modelName}" is up to date`, 'success');
            }
        } else {
            showToast(data.message || 'Failed to check for updates', 'error');
        }
    } catch (error) {
        console.error('Failed to check for updates:', error);
        showToast('Failed to check for updates', 'error');
    }
}

// Check for updates for all installed models
async function checkAllUpdates(backendName = null) {
    try {
        showToast('Checking for updates...', 'info');
        
        // If backend is specified, check only that backend
        if (backendName) {
            const response = await fetch('/api/models/check-all-updates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    backend: backendName
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'ok') {
                const updateData = data.data;
                const modelsWithUpdates = updateData.models_with_updates || 0;
                
                if (modelsWithUpdates > 0) {
                    showToast(`${modelsWithUpdates} model(s) have updates available`, 'info', 5000);
                    // Reload models to show update indicators
                    await loadInstalledModels();
                    await loadAvailableModels();
                } else {
                    showToast('All models are up to date', 'success');
                }
            } else {
                showToast(data.message || 'Failed to check for updates', 'error');
            }
        } else {
            // Check all backends
            const response = await fetch('/api/status');
            const statusData = await response.json();
            
            if (statusData.status === 'ok') {
                let totalUpdates = 0;
                const backends = Object.keys(statusData.backends || {});
                
                for (const backend of backends) {
                    try {
                        const updateResponse = await fetch('/api/models/check-all-updates', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                backend: backend
                            })
                        });
                        
                        const updateData = await updateResponse.json();
                        if (updateData.status === 'ok') {
                            totalUpdates += updateData.data.models_with_updates || 0;
                        }
                    } catch (error) {
                        console.error(`Failed to check updates for ${backend}:`, error);
                    }
                }
                
                if (totalUpdates > 0) {
                    showToast(`${totalUpdates} model(s) have updates available`, 'info', 5000);
                    // Reload models to show update indicators
                    await loadInstalledModels();
                    await loadAvailableModels();
                } else {
                    showToast('All models are up to date', 'success');
                }
            }
        }
    } catch (error) {
        console.error('Failed to check for updates:', error);
        showToast('Failed to check for updates', 'error');
    }
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
    // Use toast system if available, otherwise fallback
    if (typeof showToast !== 'undefined') {
        showToast(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
        if (type === 'error') {
            alert(`Error: ${message}`);
        }
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
        title.title = 'Click to rename';
        title.style.cursor = 'pointer';
        title.onclick = (e) => {
            e.stopPropagation();
            renameConversation(conv.id, title);
        };
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
            
            // Update current tab with conversation ID
            if (activeTabId) {
                const tab = chatTabs.find(t => t.id === activeTabId);
                if (tab) {
                    tab.conversationId = currentConversationId;
                    saveChatTabs();
                }
            }
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

// Rename conversation
async function renameConversation(convId, titleElement) {
    const currentTitle = titleElement.textContent;
    const newTitle = prompt('Enter new conversation title:', currentTitle);
    
    if (!newTitle || newTitle.trim() === '' || newTitle === currentTitle) {
        return;
    }
    
    try {
        const response = await fetch(`/api/conversations/${convId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: newTitle.trim()
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            titleElement.textContent = newTitle.trim();
            showToast('Conversation renamed', 'success');
            await loadConversations(); // Refresh list
        } else {
            showToast(data.message || 'Failed to rename conversation', 'error');
        }
    } catch (error) {
        console.error('Failed to rename conversation:', error);
        showToast('Failed to rename conversation', 'error');
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
        showToast('Conversation exported', 'success');
    } catch (error) {
        console.error('Failed to export conversation:', error);
        showToast('Failed to export conversation', 'error');
    }
}

// Copy message to clipboard
// Load unrestricted mode setting
async function loadUnrestrictedMode() {
    try {
        const response = await fetch('/api/config/unrestricted-mode');
        const data = await response.json();
        if (data.status === 'ok') {
            unrestrictedMode = data.unrestricted_mode !== false; // Default to true
            const checkbox = document.getElementById('unrestrictedMode');
            if (checkbox) {
                checkbox.checked = unrestrictedMode;
            }
        }
    } catch (error) {
        console.error('Failed to load unrestricted mode setting:', error);
        // Default to unrestricted
        unrestrictedMode = true;
        const checkbox = document.getElementById('unrestrictedMode');
        if (checkbox) {
            checkbox.checked = true;
        }
    }
}

// Toggle unrestricted mode
async function toggleUnrestrictedMode(enabled) {
    unrestrictedMode = enabled;
    try {
        const response = await fetch('/api/config/unrestricted-mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                unrestricted_mode: enabled,
                disable_safety_filters: enabled
            })
        });
        
        const data = await response.json();
        if (data.status === 'ok') {
            showToast(
                enabled 
                    ? '🆓 Unrestricted mode enabled - Complete freedom' 
                    : '🔒 Restricted mode enabled - Safety filters active',
                'success'
            );
        } else {
            showToast('Failed to update unrestricted mode setting', 'error');
            // Revert checkbox
            const checkbox = document.getElementById('unrestrictedMode');
            if (checkbox) {
                checkbox.checked = !enabled;
            }
            unrestrictedMode = !enabled;
        }
    } catch (error) {
        console.error('Failed to update unrestricted mode:', error);
        showToast('Failed to update unrestricted mode setting', 'error');
        // Revert checkbox
        const checkbox = document.getElementById('unrestrictedMode');
        if (checkbox) {
            checkbox.checked = !enabled;
        }
        unrestrictedMode = !enabled;
    }
}

async function copyMessage(text, button) {
    try {
        await navigator.clipboard.writeText(text);
        const originalText = button.innerHTML;
        button.innerHTML = '✓';
        button.style.color = 'var(--success)';
        showToast('Message copied to clipboard!', 'success');
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.color = '';
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        showToast('Failed to copy message', 'error');
    }
}

// Clear chat
function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    const messages = chatMessages.querySelectorAll('.message');
    
    if (messages.length === 0) {
        showToast('Chat is already empty', 'info');
        return;
    }
    
    if (confirm('Are you sure you want to clear the chat? This will remove all messages from the current view.')) {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to LocalMind</h2>
                <p>Select a model and start chatting! Your conversations stay local and private.</p>
                <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                    💡 Tip: Press <kbd>Ctrl+K</kbd> for new chat, <kbd>Ctrl+/</kbd> for shortcuts
                </p>
            </div>
        `;
        conversationHistory = [];
        showToast('Chat cleared', 'success');
    }
}

// Toast notifications (improved version)
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) {
        // Fallback to old notification if container doesn't exist
        showNotification(message, type);
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// About modal
async function showAbout() {
    const modal = document.getElementById('aboutModal');
    if (modal) {
        modal.classList.add('active');
        await Promise.all([loadSystemInfo(), loadChangelog()]);
    }
}

// Load system information
async function loadSystemInfo() {
    const systemInfoDiv = document.getElementById('systemInfo');
    if (!systemInfoDiv) return;
    
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'ok' && data.system) {
            const sys = data.system;
            systemInfoDiv.innerHTML = `
                <p><strong>Platform:</strong> ${sys.platform} ${sys.platform_version || ''}</p>
                <p><strong>Python:</strong> ${sys.python_version}</p>
                <p><strong>Architecture:</strong> ${sys.architecture}</p>
                ${sys.processor && sys.processor !== 'N/A' ? `<p><strong>Processor:</strong> ${sys.processor}</p>` : ''}
            `;
        } else {
            systemInfoDiv.innerHTML = '<p style="color: var(--text-secondary);">System information unavailable</p>';
        }
    } catch (error) {
        console.error('Failed to load system info:', error);
        systemInfoDiv.innerHTML = '<p style="color: var(--error);">Failed to load system information</p>';
    }
}

// Load changelog
async function loadChangelog() {
    const changelogDiv = document.getElementById('changelogContent');
    if (!changelogDiv) return;
    
    try {
        const response = await fetch('/api/changelog');
        const data = await response.json();
        
        if (data.status === 'ok' && data.changelog) {
            // Convert markdown to HTML using marked if available
            if (typeof marked !== 'undefined') {
                changelogDiv.innerHTML = marked.parse(data.changelog);
            } else {
                // Fallback: simple text display with basic formatting
                changelogDiv.innerHTML = '<pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">' + 
                    data.changelog.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</pre>';
            }
        } else {
            changelogDiv.innerHTML = '<p style="color: var(--text-secondary);">Changelog unavailable</p>';
        }
    } catch (error) {
        console.error('Failed to load changelog:', error);
        changelogDiv.innerHTML = '<p style="color: var(--text-secondary);">Failed to load changelog</p>';
    }
}

function closeAbout() {
    const modal = document.getElementById('aboutModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modals on outside click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Show QR Code
function showQRCode() {
    const modal = document.getElementById('qrCodeModal');
    const qrDiv = document.getElementById('qrcode');
    const urlDiv = document.getElementById('qrCodeUrl');
    
    if (!modal || !qrDiv) return;
    
    // Get current URL
    const currentUrl = window.location.href;
    urlDiv.textContent = currentUrl;
    
    // Clear previous QR code
    qrDiv.innerHTML = '';
    
    // Generate QR code
    if (typeof QRCode !== 'undefined') {
        new QRCode(qrDiv, {
            text: currentUrl,
            width: 256,
            height: 256,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.H
        });
    } else {
        qrDiv.innerHTML = '<p style="color: var(--error);">QR Code library not loaded</p>';
    }
    
    modal.classList.add('active');
}

function closeQRCode() {
    const modal = document.getElementById('qrCodeModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function copyQRCodeUrl() {
    const urlDiv = document.getElementById('qrCodeUrl');
    if (urlDiv) {
        navigator.clipboard.writeText(urlDiv.textContent).then(() => {
            showToast('URL copied to clipboard!', 'success');
        });
    }
}

// File upload handling
function setupFileUpload() {
    const chatInputContainer = document.getElementById('chatInputContainer');
    const fileDropZone = document.getElementById('fileDropZone');
    const chatInput = document.getElementById('chatInput');
    
    if (!chatInputContainer || !fileDropZone || !chatInput) return;
    
    // Drag and drop
    chatInputContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileDropZone.style.display = 'block';
        fileDropZone.classList.add('dragover');
    });
    
    chatInputContainer.addEventListener('dragleave', (e) => {
        e.preventDefault();
        if (!chatInputContainer.contains(e.relatedTarget)) {
            fileDropZone.style.display = 'none';
            fileDropZone.classList.remove('dragover');
        }
    });
    
    chatInputContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        fileDropZone.style.display = 'none';
        fileDropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });
    
    // Click to show drop zone
    fileDropZone.addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        handleFiles(files);
    }
}

async function handleFiles(files) {
    for (const file of files) {
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            showToast(`File ${file.name} is too large (max 10MB)`, 'error');
            continue;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            const fileInfo = `\n\n[File: ${file.name} (${(file.size / 1024).toFixed(2)} KB)]\n`;
            
            // Add file info to chat input
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.value += fileInfo;
                if (file.type.startsWith('text/')) {
                    chatInput.value += `\nFile content:\n${content.substring(0, 5000)}${content.length > 5000 ? '... (truncated)' : ''}`;
                }
                updateWordCount();
            }
            
            showToast(`File ${file.name} attached`, 'success');
        };
        
        if (file.type.startsWith('text/')) {
            reader.readAsText(file);
        } else {
            // For binary files, just add the file info
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.value += `\n\n[File attached: ${file.name} (${(file.size / 1024).toFixed(2)} KB, type: ${file.type})]`;
                updateWordCount();
            }
            showToast(`File ${file.name} attached (binary file)`, 'success');
        }
    }
}

// Set temperature preset
function setTemperature(value) {
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('tempValue');
    if (tempSlider && tempValue) {
        tempSlider.value = value;
        tempValue.textContent = value;
        showToast(`Temperature set to ${value}`, 'success', 1500);
    }
}

// Update word/character count
function updateWordCount() {
    const chatInput = document.getElementById('chatInput');
    const charCount = document.getElementById('charCount');
    const wordCountNum = document.getElementById('wordCountNum');
    
    if (!chatInput || !charCount || !wordCountNum) return;
    
    const text = chatInput.value;
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    charCount.textContent = chars;
    wordCountNum.textContent = words;
}

// Regenerate message
async function regenerateMessage(messageId, originalText) {
    if (!confirm('Regenerate this response? The current response will be replaced.')) {
        return;
    }
    
    // Find the user message that prompted this response
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;
    
    // Find previous user message
    const chatMessages = document.getElementById('chatMessages');
    const messages = Array.from(chatMessages.querySelectorAll('.message'));
    const currentIndex = messages.indexOf(messageDiv);
    
    let userMessage = null;
    for (let i = currentIndex - 1; i >= 0; i--) {
        if (messages[i].classList.contains('user')) {
            userMessage = messages[i].querySelector('.message-text').textContent;
            break;
        }
    }
    
    if (!userMessage) {
        showToast('Could not find the original prompt', 'error');
        return;
    }
    
    // Remove the current assistant message
    messageDiv.remove();
    
    // Resend the message
    const chatInput = document.getElementById('chatInput');
    chatInput.value = userMessage;
    await sendMessage();
}

// Delete message
function deleteMessage(messageId) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;
    
    if (confirm('Delete this message?')) {
        messageDiv.remove();
        showToast('Message deleted', 'success');
        
        // If no messages left, show welcome message
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages.querySelectorAll('.message').length === 0) {
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h2>Welcome to LocalMind</h2>
                    <p>Select a model and start chatting! Your conversations stay local and private.</p>
                    <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                        💡 Tip: Press <kbd>Ctrl+K</kbd> for new chat, <kbd>Ctrl+/</kbd> for shortcuts
                    </p>
                </div>
            `;
        }
    }
}

// Toggle favorite model
function toggleFavorite(modelName, button) {
    const index = favoriteModels.indexOf(modelName);
    if (index > -1) {
        favoriteModels.splice(index, 1);
        button.innerHTML = '☆';
        button.title = 'Add to favorites';
        showToast('Removed from favorites', 'success', 2000);
    } else {
        favoriteModels.push(modelName);
        button.innerHTML = '⭐';
        button.title = 'Remove from favorites';
        showToast('Added to favorites', 'success', 2000);
    }
    localStorage.setItem('favoriteModels', JSON.stringify(favoriteModels));
    updateFavoriteModelsList();
    updateModelSelect();
}

// Update favorite models list
function updateFavoriteModelsList() {
    const listDiv = document.getElementById('favoriteModelsList');
    if (!listDiv) return;
    
    if (favoriteModels.length === 0) {
        listDiv.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.875rem; text-align: center; padding: 0.5rem;">No favorite models</p>';
        return;
    }
    
    listDiv.innerHTML = '';
    favoriteModels.forEach(modelName => {
        const item = document.createElement('div');
        item.className = 'favorite-model-item';
        item.innerHTML = `
            <span>⭐ ${modelName}</span>
            <button class="btn-icon" onclick="selectFavoriteModel('${modelName}')" title="Use this model">→</button>
        `;
        listDiv.appendChild(item);
    });
}

// Select favorite model
function selectFavoriteModel(modelName) {
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.value = modelName;
        currentModel = modelName;
        updateModelInfo();
        showToast(`Switched to ${modelName}`, 'success');
    }
}

// Toggle favorites view
function toggleFavoritesView() {
    const listDiv = document.getElementById('favoriteModelsList');
    const btn = document.getElementById('showFavoritesBtn');
    if (listDiv && btn) {
        const isVisible = listDiv.style.display !== 'none';
        listDiv.style.display = isVisible ? 'none' : 'block';
        btn.innerHTML = isVisible ? '⭐' : '⭐';
        if (!isVisible) {
            updateFavoriteModelsList();
        }
    }
}

// Update model select with favorites
function updateModelSelect() {
    const modelSelect = document.getElementById('modelSelect');
    if (!modelSelect) return;
    
    // Add favorites to the top of the select
    const options = Array.from(modelSelect.options);
    const favoriteOptions = options.filter(opt => favoriteModels.includes(opt.value));
    const otherOptions = options.filter(opt => !favoriteModels.includes(opt.value) && opt.value);
    
    // Clear and rebuild
    modelSelect.innerHTML = '<option value="">Select a model...</option>';
    
    // Add favorites group
    if (favoriteOptions.length > 0) {
        const favGroup = document.createElement('optgroup');
        favGroup.label = '⭐ Favorites';
        favoriteOptions.forEach(opt => {
            const newOpt = opt.cloneNode(true);
            newOpt.textContent = `⭐ ${newOpt.textContent}`;
            favGroup.appendChild(newOpt);
        });
        modelSelect.appendChild(favGroup);
    }
    
    // Add other models
    if (otherOptions.length > 0) {
        const otherGroup = document.createElement('optgroup');
        otherGroup.label = 'All Models';
        otherOptions.forEach(opt => otherGroup.appendChild(opt.cloneNode(true)));
        modelSelect.appendChild(otherGroup);
    }
}

// Export/Share Functions
function showExportOptions() {
    const modal = document.getElementById('exportShareModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('shareLinkContainer').style.display = 'none';
    }
}

function closeExportShare() {
    const modal = document.getElementById('exportShareModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function getSelectedExportFormat() {
    const selected = document.querySelector('input[name="exportFormat"]:checked');
    return selected ? selected.value : 'markdown';
}

function getChatData() {
    const chatMessages = document.getElementById('chatMessages');
    const messages = chatMessages.querySelectorAll('.message');
    
    if (messages.length === 0) {
        return null;
    }
    
    const chatData = {
        model: currentModel || 'Not selected',
        conversationId: currentConversationId || null,
        date: new Date().toISOString(),
        messages: []
    };
    
    messages.forEach(msg => {
        const role = msg.classList.contains('user') ? 'user' : 'assistant';
        const textDiv = msg.querySelector('.message-text');
        const text = textDiv ? textDiv.textContent : '';
        chatData.messages.push({
            role: role,
            content: text,
            timestamp: msg.dataset.timestamp || new Date().toISOString()
        });
    });
    
    return chatData;
}

function exportChat() {
    const chatData = getChatData();
    if (!chatData) {
        showToast('No messages to export', 'info');
        return;
    }
    
    const format = getSelectedExportFormat();
    let content = '';
    let filename = '';
    let mimeType = '';
    
    switch (format) {
        case 'markdown':
            content = exportAsMarkdown(chatData);
            filename = `localmind_chat_${Date.now()}.md`;
            mimeType = 'text/markdown';
            break;
        case 'txt':
            content = exportAsText(chatData);
            filename = `localmind_chat_${Date.now()}.txt`;
            mimeType = 'text/plain';
            break;
        case 'json':
            content = exportAsJSON(chatData);
            filename = `localmind_chat_${Date.now()}.json`;
            mimeType = 'application/json';
            break;
        case 'html':
            content = exportAsHTML(chatData);
            filename = `localmind_chat_${Date.now()}.html`;
            mimeType = 'text/html';
            break;
    }
    
    // Download file
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showToast(`Chat exported as ${format.toUpperCase()}`, 'success');
    closeExportShare();
}

function exportAsMarkdown(chatData) {
    let markdown = `# LocalMind Conversation\n\n`;
    markdown += `**Model:** ${chatData.model}\n`;
    markdown += `**Date:** ${new Date(chatData.date).toLocaleString()}\n`;
    if (chatData.conversationId) {
        markdown += `**Conversation ID:** ${chatData.conversationId}\n`;
    }
    markdown += `\n---\n\n`;
    
    chatData.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'User' : 'Assistant';
        markdown += `## ${role}\n\n${msg.content}\n\n---\n\n`;
    });
    
    return markdown;
}

function exportAsText(chatData) {
    let text = `LocalMind Conversation\n`;
    text += `Model: ${chatData.model}\n`;
    text += `Date: ${new Date(chatData.date).toLocaleString()}\n`;
    if (chatData.conversationId) {
        text += `Conversation ID: ${chatData.conversationId}\n`;
    }
    text += `\n${'='.repeat(50)}\n\n`;
    
    chatData.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'USER' : 'ASSISTANT';
        text += `${role}:\n${msg.content}\n\n${'-'.repeat(50)}\n\n`;
    });
    
    return text;
}

function exportAsJSON(chatData) {
    return JSON.stringify(chatData, null, 2);
}

function exportAsHTML(chatData) {
    let html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LocalMind Conversation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }
        .header { border-bottom: 2px solid #e2e8f0; padding-bottom: 1rem; margin-bottom: 2rem; }
        .message { margin-bottom: 2rem; padding: 1rem; border-radius: 0.5rem; }
        .user { background: #f1f5f9; }
        .assistant { background: #f8fafc; border-left: 3px solid #6366f1; }
        .role { font-weight: bold; margin-bottom: 0.5rem; color: #64748b; }
        .content { white-space: pre-wrap; }
        pre { background: #1e293b; color: #f1f5f9; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; }
        code { background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>LocalMind Conversation</h1>
        <p><strong>Model:</strong> ${chatData.model}</p>
        <p><strong>Date:</strong> ${new Date(chatData.date).toLocaleString()}</p>
        ${chatData.conversationId ? `<p><strong>Conversation ID:</strong> ${chatData.conversationId}</p>` : ''}
    </div>
    <div class="messages">
`;
    
    chatData.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'User' : 'Assistant';
        const className = msg.role === 'user' ? 'user' : 'assistant';
        html += `
        <div class="message ${className}">
            <div class="role">${role}</div>
            <div class="content">${escapeHtml(msg.content)}</div>
        </div>
`;
    });
    
    html += `
    </div>
</body>
</html>`;
    
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function copyChatToClipboard() {
    const chatData = getChatData();
    if (!chatData) {
        showToast('No messages to copy', 'info');
        return;
    }
    
    const format = getSelectedExportFormat();
    let content = '';
    
    switch (format) {
        case 'markdown':
            content = exportAsMarkdown(chatData);
            break;
        case 'txt':
            content = exportAsText(chatData);
            break;
        case 'json':
            content = exportAsJSON(chatData);
            break;
        case 'html':
            content = exportAsHTML(chatData);
            break;
    }
    
    navigator.clipboard.writeText(content).then(() => {
        showToast('Chat copied to clipboard', 'success');
        closeExportShare();
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy to clipboard', 'error');
    });
}

function generateShareableLink() {
    const chatData = getChatData();
    if (!chatData) {
        showToast('No messages to share', 'info');
        return;
    }
    
    // Encode chat data as base64 in URL
    const jsonData = JSON.stringify(chatData);
    const encoded = btoa(unescape(encodeURIComponent(jsonData)));
    const shareUrl = `${window.location.origin}${window.location.pathname}?share=${encoded}`;
    
    // Show share link
    const container = document.getElementById('shareLinkContainer');
    const input = document.getElementById('shareLinkInput');
    if (container && input) {
        input.value = shareUrl;
        container.style.display = 'block';
    }
}

function copyShareLink() {
    const input = document.getElementById('shareLinkInput');
    if (input) {
        input.select();
        navigator.clipboard.writeText(input.value).then(() => {
            showToast('Share link copied to clipboard', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy link', 'error');
        });
    }
}

// Import Conversation Functions
function showImportOptions() {
    const modal = document.getElementById('importConversationModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('importResultContainer').style.display = 'none';
        document.getElementById('importFileInput').value = '';
        document.getElementById('importContentInput').value = '';
    }
}

function closeImportConversation() {
    const modal = document.getElementById('importConversationModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function getSelectedImportFormat() {
    const selected = document.querySelector('input[name="importFormat"]:checked');
    return selected ? selected.value : 'auto';
}

async function importConversation() {
    const fileInput = document.getElementById('importFileInput');
    const contentInput = document.getElementById('importContentInput');
    const format = getSelectedImportFormat();
    const resultContainer = document.getElementById('importResultContainer');
    const resultMessage = document.getElementById('importResultMessage');
    
    let content = '';
    let importFormat = format;
    
    // Check if file is selected
    if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        try {
            content = await file.text();
            // Auto-detect format from file extension if auto is selected
            if (format === 'auto') {
                const ext = file.name.split('.').pop().toLowerCase();
                if (ext === 'json') importFormat = 'json';
                else if (ext === 'md' || ext === 'markdown') importFormat = 'markdown';
                else if (ext === 'txt') importFormat = 'txt';
            }
        } catch (error) {
            showToast('Error reading file: ' + error.message, 'error');
            return;
        }
    } else if (contentInput.value.trim()) {
        // Use pasted content
        content = contentInput.value.trim();
        if (format === 'auto') {
            // Try to auto-detect
            if (content.trim().startsWith('{')) {
                importFormat = 'json';
            } else if (content.trim().startsWith('#')) {
                importFormat = 'markdown';
            } else {
                importFormat = 'txt';
            }
        }
    } else {
        showToast('Please select a file or paste content', 'info');
        return;
    }
    
    if (!content) {
        showToast('No content to import', 'error');
        return;
    }
    
    try {
        // Show loading state
        resultContainer.style.display = 'block';
        resultMessage.innerHTML = '<div style="color: var(--text-secondary);">⏳ Importing conversation...</div>';
        
        // Prepare form data
        const formData = new FormData();
        const blob = new Blob([content], { type: 'text/plain' });
        formData.append('file', blob, 'imported_conversation.txt');
        formData.append('format', importFormat);
        
        // Send to server
        const response = await fetch('/api/conversations/import', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const imported = data.data.imported_data;
            resultMessage.innerHTML = `
                <div style="color: var(--success);">
                    ✅ <strong>Conversation imported successfully!</strong>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                    • Model: ${imported.model || 'Unknown'}<br>
                    • Messages: ${imported.message_count}<br>
                    • Format: ${imported.format || 'auto'}
                </div>
                <button class="btn btn-primary btn-small" onclick="loadConversation('${data.data.conversation_id}'); closeImportConversation();" style="margin-top: 0.75rem;">
                    Open Conversation
                </button>
            `;
            
            // Reload conversations list
            await loadConversations();
            
            showToast('Conversation imported successfully', 'success');
        } else {
            resultMessage.innerHTML = `
                <div style="color: var(--error);">
                    ❌ <strong>Import failed:</strong> ${data.error || 'Unknown error'}
                </div>
            `;
            showToast('Failed to import conversation: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Import error:', error);
        resultMessage.innerHTML = `
            <div style="color: var(--error);">
                ❌ <strong>Error:</strong> ${error.message}
            </div>
        `;
        showToast('Error importing conversation: ' + error.message, 'error');
    }
}

// Backup/Restore Configuration Functions
function showBackupOptions() {
    const modal = document.getElementById('backupConfigModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('backupResultContainer').style.display = 'none';
        document.getElementById('backupIncludeConversations').checked = false;
        document.getElementById('backupIncludeModels').checked = false;
    }
}

function closeBackupConfig() {
    const modal = document.getElementById('backupConfigModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showRestoreOptions() {
    const modal = document.getElementById('restoreConfigModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('restoreResultContainer').style.display = 'none';
        document.getElementById('restoreFileInput').value = '';
        document.getElementById('restoreIncludeConversations').checked = false;
        document.getElementById('restoreIncludeModels').checked = false;
    }
}

function closeRestoreConfig() {
    const modal = document.getElementById('restoreConfigModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function createBackup() {
    const includeConversations = document.getElementById('backupIncludeConversations').checked;
    const includeModels = document.getElementById('backupIncludeModels').checked;
    const resultContainer = document.getElementById('backupResultContainer');
    const resultMessage = document.getElementById('backupResultMessage');
    
    try {
        resultContainer.style.display = 'block';
        resultMessage.innerHTML = '<div style="color: var(--text-secondary);">⏳ Creating backup...</div>';
        
        const response = await fetch('/api/config/backup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                include_conversations: includeConversations,
                include_models: includeModels,
                format: 'download'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const backupInfo = data.data.backup_info;
            const downloadUrl = data.data.download_url;
            
            resultMessage.innerHTML = `
                <div style="color: var(--success);">
                    ✅ <strong>Backup created successfully!</strong>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                    • Created: ${new Date(backupInfo.created_at).toLocaleString()}<br>
                    • Includes conversations: ${backupInfo.includes_conversations ? 'Yes' : 'No'}<br>
                    • Includes models: ${backupInfo.includes_models ? 'Yes' : 'No'}
                </div>
                <a href="${downloadUrl}" class="btn btn-primary btn-small" style="margin-top: 0.75rem; display: inline-block;">
                    📥 Download Backup
                </a>
            `;
            
            showToast('Backup created successfully', 'success');
        } else {
            resultMessage.innerHTML = `
                <div style="color: var(--error);">
                    ❌ <strong>Backup failed:</strong> ${data.error || 'Unknown error'}
                </div>
            `;
            showToast('Failed to create backup: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Backup error:', error);
        resultMessage.innerHTML = `
            <div style="color: var(--error);">
                ❌ <strong>Error:</strong> ${error.message}
            </div>
        `;
        showToast('Error creating backup: ' + error.message, 'error');
    }
}

async function restoreBackup() {
    const fileInput = document.getElementById('restoreFileInput');
    const restoreConversations = document.getElementById('restoreIncludeConversations').checked;
    const restoreModels = document.getElementById('restoreIncludeModels').checked;
    const resultContainer = document.getElementById('restoreResultContainer');
    const resultMessage = document.getElementById('restoreResultMessage');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a backup file', 'info');
        return;
    }
    
    if (!confirm('Are you sure you want to restore from backup? This will overwrite your current configuration.')) {
        return;
    }
    
    try {
        resultContainer.style.display = 'block';
        resultMessage.innerHTML = '<div style="color: var(--text-secondary);">⏳ Restoring backup...</div>';
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('restore_conversations', restoreConversations);
        formData.append('restore_models', restoreModels);
        
        const response = await fetch('/api/config/restore', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const results = data.data.results;
            const errors = results.errors || [];
            
            let resultHtml = `
                <div style="color: var(--success);">
                    ✅ <strong>Configuration restored successfully!</strong>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                    • Config: ${results.config ? '✅ Restored' : '❌ Failed'}<br>
                    • Conversations: ${results.conversations ? '✅ Restored' : '❌ Failed'}<br>
                    • Model Registry: ${results.model_registry ? '✅ Restored' : '❌ Failed'}
                </div>
            `;
            
            if (errors.length > 0) {
                resultHtml += `
                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: var(--error-light); border-radius: 0.375rem; font-size: 0.875rem;">
                        <strong>Errors:</strong><br>
                        ${errors.map(e => `• ${e}`).join('<br>')}
                    </div>
                `;
            }
            
            resultMessage.innerHTML = resultHtml;
            
            showToast('Configuration restored successfully. Please restart the server for changes to take effect.', 'success');
            
            // Close modal after a delay
            setTimeout(() => {
                closeRestoreConfig();
            }, 3000);
        } else {
            resultMessage.innerHTML = `
                <div style="color: var(--error);">
                    ❌ <strong>Restore failed:</strong> ${data.error || 'Unknown error'}
                </div>
            `;
            showToast('Failed to restore backup: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Restore error:', error);
        resultMessage.innerHTML = `
            <div style="color: var(--error);">
                ❌ <strong>Error:</strong> ${error.message}
            </div>
        `;
        showToast('Error restoring backup: ' + error.message, 'error');
    }
}

// Migration Tools Functions
function showMigrationTools() {
    const modal = document.getElementById('migrationToolsModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('migrationResultContainer').style.display = 'none';
        detectMigrationSources();
    }
}

function closeMigrationTools() {
    const modal = document.getElementById('migrationToolsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function detectMigrationSources() {
    const sourcesList = document.getElementById('migrationSourcesList');
    
    try {
        sourcesList.innerHTML = '<div style="text-align: center; padding: 1rem; color: var(--text-secondary);">🔍 Detecting...</div>';
        
        const response = await fetch('/api/migration/detect');
        const data = await response.json();
        
        if (data.success) {
            const sources = data.data.sources || [];
            
            if (sources.length === 0) {
                sourcesList.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                        <div style="margin-bottom: 0.5rem;">📭 No migration sources detected</div>
                        <div style="font-size: 0.875rem;">Use manual migration below to import from a file</div>
                    </div>
                `;
            } else {
                let html = '<div style="display: flex; flex-direction: column; gap: 0.75rem;">';
                sources.forEach(source => {
                    html += `
                        <div style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; background: var(--surface-light);">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                                <div>
                                    <strong>${source.name}</strong>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                                        ${source.path}
                                    </div>
                                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
                                        ${source.conversation_count || 0} conversations
                                    </div>
                                </div>
                                <button class="btn btn-primary btn-small" onclick="migrateFromSource('${source.type}', '${source.path.replace(/'/g, "\\'")}')">
                                    Migrate
                                </button>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                sourcesList.innerHTML = html;
            }
        } else {
            sourcesList.innerHTML = `
                <div style="text-align: center; padding: 1rem; color: var(--error);">
                    ❌ Error detecting sources: ${data.error || 'Unknown error'}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error detecting sources:', error);
        sourcesList.innerHTML = `
            <div style="text-align: center; padding: 1rem; color: var(--error);">
                ❌ Error: ${error.message}
            </div>
        `;
    }
}

async function migrateFromSource(sourceType, sourcePath) {
    if (!confirm(`Migrate from ${sourceType}? This will import conversations into LocalMind.`)) {
        return;
    }
    
    const resultContainer = document.getElementById('migrationResultContainer');
    const resultMessage = document.getElementById('migrationResultMessage');
    
    try {
        resultContainer.style.display = 'block';
        resultMessage.innerHTML = '<div style="color: var(--text-secondary);">⏳ Migrating...</div>';
        
        const response = await fetch('/api/migration/migrate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source_type: sourceType,
                source_path: sourcePath,
                options: {}
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const results = data.data.results;
            const migrated = results.conversations_migrated || 0;
            const errors = results.errors || [];
            const warnings = results.warnings || [];
            
            let resultHtml = `
                <div style="color: var(--success);">
                    ✅ <strong>Migration completed!</strong>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                    • Conversations migrated: ${migrated}
                </div>
            `;
            
            if (warnings.length > 0) {
                resultHtml += `
                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: var(--warning-light); border-radius: 0.375rem; font-size: 0.875rem;">
                        <strong>Warnings:</strong><br>
                        ${warnings.map(w => `• ${w}`).join('<br>')}
                    </div>
                `;
            }
            
            if (errors.length > 0) {
                resultHtml += `
                    <div style="margin-top: 0.75rem; padding: 0.5rem; background: var(--error-light); border-radius: 0.375rem; font-size: 0.875rem;">
                        <strong>Errors:</strong><br>
                        ${errors.map(e => `• ${e}`).join('<br>')}
                    </div>
                `;
            }
            
            resultMessage.innerHTML = resultHtml;
            
            // Reload conversations
            await loadConversations();
            
            showToast(`Migration completed: ${migrated} conversations migrated`, 'success');
        } else {
            resultMessage.innerHTML = `
                <div style="color: var(--error);">
                    ❌ <strong>Migration failed:</strong> ${data.error || 'Unknown error'}
                </div>
            `;
            showToast('Migration failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Migration error:', error);
        resultMessage.innerHTML = `
            <div style="color: var(--error);">
                ❌ <strong>Error:</strong> ${error.message}
            </div>
        `;
        showToast('Error during migration: ' + error.message, 'error');
    }
}

async function startMigration() {
    const sourceType = document.getElementById('migrationSourceType').value;
    const fileInput = document.getElementById('migrationFileInput');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a file to migrate', 'info');
        return;
    }
    
    // For file upload, we'll need to handle it differently
    // For now, show a message that file upload migration needs to be done via import
    showToast('For file uploads, please use the Import feature in the chat interface', 'info');
    closeMigrationTools();
}

// Load shared conversation from URL
function loadSharedConversation() {
    const urlParams = new URLSearchParams(window.location.search);
    const shareParam = urlParams.get('share');
    
    if (shareParam) {
        try {
            const decoded = decodeURIComponent(escape(atob(shareParam)));
            const chatData = JSON.parse(decoded);
            
            // Create a new tab with shared conversation
            const tabId = createNewChatTab(chatData.model || 'Shared Conversation');
            const tab = chatTabs.find(t => t.id === tabId);
            
            if (tab && chatData.messages) {
                // Set model if available
                if (chatData.model && chatData.model !== 'Not selected') {
                    currentModel = chatData.model;
                    selectModel(chatData.model);
                }
                
                // Load messages
                setTimeout(() => {
                    const chatMessages = document.getElementById('chatMessages');
                    if (chatMessages) {
                        chatMessages.innerHTML = '';
                        chatData.messages.forEach(msg => {
                            addMessage(msg.role, msg.content, false, false);
                        });
                    }
                }, 100);
                
                showToast('Shared conversation loaded', 'success');
                
                // Clean URL
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        } catch (e) {
            console.error('Error loading shared conversation:', e);
            showToast('Invalid share link', 'error');
        }
    }
}

// Comparison Mode Functions
async function sendComparisonMessage(prompt) {
    if (comparisonModels.length < 2) {
        showToast('Please select at least 2 models to compare', 'error');
        return;
    }
    
    if (comparisonModels.length > 5) {
        showToast('Maximum 5 models can be compared at once', 'error');
        return;
    }
    
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    // Disable input
    chatInput.disabled = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span> Comparing...';
    
    // Add user message
    addMessage('user', prompt);
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    updateWordCount();
    
    // Get settings
    const temperature = parseFloat(document.getElementById('temperature').value);
    const systemPrompt = document.getElementById('systemPrompt').value || undefined;
    
    try {
        const response = await fetch('/api/chat/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                models: comparisonModels,
                system_prompt: systemPrompt,
                temperature: temperature,
                disable_safety_filters: unrestrictedMode
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Comparison failed');
        }
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            // Display comparison results
            displayComparisonResults(prompt, data.data);
        } else {
            throw new Error(data.message || 'Comparison failed');
        }
    } catch (error) {
        console.error('Error in comparison:', error);
        showToast(`Comparison failed: ${error.message}`, 'error', 5000);
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = '<span>Send</span>';
        chatInput.focus();
    }
}

function displayComparisonResults(prompt, data) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Create comparison container
    const comparisonDiv = document.createElement('div');
    comparisonDiv.className = 'comparison-container';
    comparisonDiv.id = `comparison-${Date.now()}`;
    
    let html = `
        <div class="comparison-header">
            <h4>🔀 Model Comparison</h4>
            <span style="font-size: 0.875rem; color: var(--text-secondary);">
                ${data.successful}/${data.total_models} models responded
            </span>
        </div>
        <div class="comparison-results">
    `;
    
    // Sort by response time
    const sortedResults = [...data.results].sort((a, b) => a.response_time - b.response_time);
    
    sortedResults.forEach((result, index) => {
        const isFastest = index === 0;
        html += `
            <div class="comparison-item ${isFastest ? 'fastest' : ''}">
                <div class="comparison-item-header">
                    <div>
                        <strong>${result.model}</strong>
                        <span style="font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.5rem;">
                            ${result.backend}
                        </span>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        ${isFastest ? '<span style="color: var(--success); font-size: 0.75rem;">⚡ Fastest</span>' : ''}
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">
                            ${result.response_time}s
                        </span>
                    </div>
                </div>
                <div class="comparison-item-content">
                    ${renderMarkdown(result.response)}
                </div>
                ${result.metadata && Object.keys(result.metadata).length > 0 ? `
                    <div class="comparison-item-metadata" style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color);">
                        ${result.metadata.prompt_tokens ? `Tokens: ${result.metadata.prompt_tokens} in / ${result.metadata.completion_tokens || 0} out` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    // Show errors if any
    if (data.errors && data.errors.length > 0) {
        html += '<div class="comparison-errors">';
        html += '<h5 style="color: var(--error); margin-bottom: 0.5rem;">Errors:</h5>';
        data.errors.forEach(error => {
            html += `
                <div style="padding: 0.5rem; background: var(--surface-light); border-radius: 0.375rem; margin-bottom: 0.5rem;">
                    <strong>${error.model}:</strong> ${error.error}
                </div>
            `;
        });
        html += '</div>';
    }
    
    html += '</div></div>';
    comparisonDiv.innerHTML = html;
    
    chatMessages.appendChild(comparisonDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Ensemble Message Function
async function sendEnsembleMessage(prompt) {
    if (comparisonModels.length < 2) {
        showToast('Please select at least 2 models for ensemble', 'error');
        return;
    }
    
    if (comparisonModels.length > 5) {
        showToast('Maximum 5 models can be used in ensemble', 'error');
        return;
    }
    
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    // Disable input
    chatInput.disabled = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span> Generating ensemble...';
    
    // Add user message
    addMessage('user', prompt);
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    updateWordCount();
    
    // Get settings
    const temperature = parseFloat(document.getElementById('temperature').value);
    const systemPrompt = document.getElementById('systemPrompt').value || undefined;
    const method = document.getElementById('ensembleMethod')?.value || 'majority_vote';
    
    try {
        const response = await fetch('/api/chat/ensemble', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                models: comparisonModels,
                system_prompt: systemPrompt,
                temperature: temperature,
                method: method,
                disable_safety_filters: unrestrictedMode
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Ensemble generation failed');
        }
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            // Display ensemble result
            displayEnsembleResult(prompt, data.data);
        } else {
            throw new Error(data.message || 'Ensemble generation failed');
        }
    } catch (error) {
        console.error('Error in ensemble:', error);
        showToast(`Ensemble failed: ${error.message}`, 'error', 5000);
        addMessage('assistant', `**Error:** ${error.message}`, true);
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = '<span>Send</span>';
        chatInput.focus();
    }
}

function displayEnsembleResult(prompt, data) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Create ensemble container
    const ensembleDiv = document.createElement('div');
    ensembleDiv.className = 'ensemble-container';
    ensembleDiv.id = `ensemble-${Date.now()}`;
    
    const methodNames = {
        'majority_vote': 'Majority Vote',
        'best': 'Best Response',
        'longest': 'Longest Response',
        'concatenate': 'Concatenated',
        'average': 'All Responses'
    };
    
    let html = `
        <div class="ensemble-header">
            <h4>🔀 Ensemble Response</h4>
            <div style="display: flex; gap: 1rem; align-items: center; font-size: 0.875rem; color: var(--text-secondary); flex-wrap: wrap;">
                <span>Method: <strong>${methodNames[data.method] || data.method}</strong></span>
                <span>Models: ${data.models_used.join(', ')}</span>
            </div>
        </div>
        <div class="ensemble-content">
            ${renderMarkdown(data.response)}
        </div>
    `;
    
    // Show individual responses in collapsible section
    if (data.individual_responses && data.individual_responses.length > 0) {
        html += `
            <div class="ensemble-individual" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                <details style="cursor: pointer;">
                    <summary style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                        View Individual Responses (${data.individual_responses.length})
                    </summary>
                    <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem;">
        `;
        
        data.individual_responses.forEach(resp => {
            html += `
                <div style="padding: 0.75rem; background: var(--surface-light); border-radius: 0.375rem; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.875rem;">
                        <strong>${resp.model}</strong>
                        <span style="color: var(--text-secondary);">${resp.response_time}s</span>
                    </div>
                    <div style="font-size: 0.875rem;">
                        ${renderMarkdown(resp.response)}
                    </div>
                </div>
            `;
        });
        
        html += `
                    </div>
                </details>
            </div>
        `;
    }
    
    html += '</div>';
    ensembleDiv.innerHTML = html;
    
    chatMessages.appendChild(ensembleDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Usage Dashboard Functions
function showUsageDashboard() {
    const modal = document.getElementById('usageDashboardModal');
    if (modal) {
        modal.style.display = 'flex';
        loadUsageStatistics();
        loadBudgetStatus();
    }
}

function closeUsageDashboard() {
    const modal = document.getElementById('usageDashboardModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showUsageTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const tabContent = document.getElementById(`usage${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`);
    const tabBtn = event.target;
    
    if (tabContent) {
        tabContent.classList.add('active');
    }
    if (tabBtn) {
        tabBtn.classList.add('active');
    }
    
    if (tabName === 'statistics') {
        loadUsageStatistics();
    } else if (tabName === 'budget') {
        loadBudgetStatus();
    } else if (tabName === 'resources') {
        loadResourceMonitoring();
    }
}

async function loadUsageStatistics() {
    const content = document.getElementById('usageStatisticsContent');
    if (!content) return;
    
    content.innerHTML = '<p>Loading statistics...</p>';
    
    try {
        const days = document.getElementById('usageDaysFilter')?.value || '';
        const url = `/api/usage/statistics${days ? `?days=${days}` : ''}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'ok') {
            const stats = data.data;
            renderUsageStatistics(stats);
        } else {
            content.innerHTML = `<p style="color: var(--error);">Error loading statistics: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Failed to load usage statistics:', error);
        content.innerHTML = `<p style="color: var(--error);">Failed to load statistics</p>`;
    }
}

function renderUsageStatistics(stats) {
    const content = document.getElementById('usageStatisticsContent');
    if (!content) return;
    
    const formatCurrency = (amount) => `$${amount.toFixed(4)}`;
    const formatNumber = (num) => num.toLocaleString();
    
    let html = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.875rem;">Total Calls</h4>
                <p style="margin: 0; font-size: 1.5rem; font-weight: bold;">${formatNumber(stats.total_calls)}</p>
            </div>
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.875rem;">Total Cost</h4>
                <p style="margin: 0; font-size: 1.5rem; font-weight: bold; color: var(--primary-color);">${formatCurrency(stats.total_cost)}</p>
            </div>
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.875rem;">Total Tokens</h4>
                <p style="margin: 0; font-size: 1.5rem; font-weight: bold;">${formatNumber(stats.total_tokens)}</p>
            </div>
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.875rem;">Avg Response Time</h4>
                <p style="margin: 0; font-size: 1.5rem; font-weight: bold;">${stats.average_response_time.toFixed(2)}s</p>
            </div>
        </div>
        
        <div style="margin-bottom: 2rem;">
            <h3>By Backend</h3>
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
    `;
    
    for (const [backend, data] of Object.entries(stats.by_backend || {})) {
        html += `
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${backend}</strong>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                            ${formatNumber(data.calls)} calls • ${formatNumber(data.tokens)} tokens
                        </div>
                    </div>
                    <div style="font-size: 1.25rem; font-weight: bold; color: var(--primary-color);">
                        ${formatCurrency(data.cost)}
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
        
        <div>
            <h3>By Model</h3>
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
    `;
    
    for (const [model, data] of Object.entries(stats.by_model || {})) {
        html += `
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${model}</strong>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                            ${formatNumber(data.calls)} calls • ${formatNumber(data.tokens)} tokens
                        </div>
                    </div>
                    <div style="font-size: 1.25rem; font-weight: bold; color: var(--primary-color);">
                        ${formatCurrency(data.cost)}
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    content.innerHTML = html;
}

async function loadBudgetStatus() {
    const content = document.getElementById('budgetStatusContent');
    if (!content) return;
    
    content.innerHTML = '<p>Loading budget status...</p>';
    
    try {
        const response = await fetch('/api/usage/budget');
        const data = await response.json();
        
        if (data.status === 'ok') {
            const budget = data.data;
            renderBudgetStatus(budget);
            
            // Populate form fields
            if (budget.daily.budget) {
                document.getElementById('dailyBudget').value = budget.daily.budget;
            }
            if (budget.monthly.budget) {
                document.getElementById('monthlyBudget').value = budget.monthly.budget;
            }
            document.getElementById('alertThreshold').value = (budget.alert_threshold * 100).toFixed(1);
            document.getElementById('alertsEnabled').checked = budget.alerts_enabled;
        } else {
            content.innerHTML = `<p style="color: var(--error);">Error loading budget: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Failed to load budget status:', error);
        content.innerHTML = `<p style="color: var(--error);">Failed to load budget status</p>`;
    }
}

function renderBudgetStatus(budget) {
    const content = document.getElementById('budgetStatusContent');
    if (!content) return;
    
    const formatCurrency = (amount) => `$${amount.toFixed(4)}`;
    
    let html = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
    `;
    
    // Daily budget
    if (budget.daily.budget) {
        const percentage = budget.daily.percentage || 0;
        const isExceeded = budget.daily.exceeded;
        html += `
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0;">Daily Budget</h4>
                <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: ${isExceeded ? 'var(--error)' : 'var(--primary-color)'};">
                    ${formatCurrency(budget.daily.cost)} / ${formatCurrency(budget.daily.budget)}
                </p>
                <div style="margin-top: 0.5rem; background: var(--background); height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: ${isExceeded ? 'var(--error)' : 'var(--primary-color)'}; height: 100%; width: ${Math.min(percentage, 100)}%;"></div>
                </div>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);">
                    ${percentage.toFixed(1)}% used
                    ${budget.daily.remaining !== null ? `• ${formatCurrency(budget.daily.remaining)} remaining` : ''}
                </p>
            </div>
        `;
    } else {
        html += `
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0;">Daily Budget</h4>
                <p style="margin: 0; color: var(--text-secondary);">Not set</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);">
                    Today: ${formatCurrency(budget.daily.cost)}
                </p>
            </div>
        `;
    }
    
    // Monthly budget
    if (budget.monthly.budget) {
        const percentage = budget.monthly.percentage || 0;
        const isExceeded = budget.monthly.exceeded;
        html += `
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0;">Monthly Budget</h4>
                <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: ${isExceeded ? 'var(--error)' : 'var(--primary-color)'};">
                    ${formatCurrency(budget.monthly.cost)} / ${formatCurrency(budget.monthly.budget)}
                </p>
                <div style="margin-top: 0.5rem; background: var(--background); height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: ${isExceeded ? 'var(--error)' : 'var(--primary-color)'}; height: 100%; width: ${Math.min(percentage, 100)}%;"></div>
                </div>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);">
                    ${percentage.toFixed(1)}% used
                    ${budget.monthly.remaining !== null ? `• ${formatCurrency(budget.monthly.remaining)} remaining` : ''}
                </p>
            </div>
        `;
    } else {
        html += `
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 0.5rem 0;">Monthly Budget</h4>
                <p style="margin: 0; color: var(--text-secondary);">Not set</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: var(--text-secondary);">
                    This month: ${formatCurrency(budget.monthly.cost)}
                </p>
            </div>
        `;
    }
    
    html += `</div>`;
    
    content.innerHTML = html;
}

async function saveBudgetSettings() {
    const dailyBudget = document.getElementById('dailyBudget').value;
    const monthlyBudget = document.getElementById('monthlyBudget').value;
    const alertThreshold = document.getElementById('alertThreshold').value;
    const alertsEnabled = document.getElementById('alertsEnabled').checked;
    
    try {
        const response = await fetch('/api/usage/budget', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                daily_budget: dailyBudget ? parseFloat(dailyBudget) : null,
                monthly_budget: monthlyBudget ? parseFloat(monthlyBudget) : null,
                alert_threshold: parseFloat(alertThreshold) / 100,
                alerts_enabled: alertsEnabled
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showToast('Budget settings saved successfully', 'success');
            loadBudgetStatus();
        } else {
            showToast(data.message || 'Failed to save budget settings', 'error');
        }
    } catch (error) {
        console.error('Failed to save budget settings:', error);
        showToast('Failed to save budget settings', 'error');
    }
}

// Resource Monitoring Functions
let resourceAutoRefreshInterval = null;

async function loadResourceMonitoring() {
    const content = document.getElementById('resourcesContent');
    if (!content) return;
    
    content.innerHTML = '<p>Loading resource information...</p>';
    
    try {
        const response = await fetch('/api/resources?type=all');
        const data = await response.json();
        
        if (data.status === 'ok') {
            renderResourceMonitoring(data.data);
        } else {
            content.innerHTML = `<p style="color: var(--error);">Error loading resources: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Failed to load resource monitoring:', error);
        content.innerHTML = `<p style="color: var(--error);">Failed to load resource information</p>`;
    }
}

function renderResourceMonitoring(resources) {
    const content = document.getElementById('resourcesContent');
    if (!content) return;
    
    const formatGB = (gb) => `${gb.toFixed(2)} GB`;
    const formatPercent = (pct) => `${pct.toFixed(1)}%`;
    
    let html = '';
    
    // CPU
    if (resources.cpu && resources.cpu.available) {
        const cpu = resources.cpu;
        html += `
            <div style="margin-bottom: 2rem;">
                <h3>CPU</h3>
                <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span><strong>Usage:</strong> ${formatPercent(cpu.usage_percent)}</span>
                        <span>${cpu.cores} cores (${cpu.physical_cores} physical)</span>
                    </div>
                    <div style="background: var(--background); height: 20px; border-radius: 4px; overflow: hidden; margin-bottom: 0.5rem;">
                        <div style="background: var(--primary-color); height: 100%; width: ${cpu.usage_percent}%; transition: width 0.3s;"></div>
                    </div>
                    ${cpu.frequency_mhz ? `<div style="font-size: 0.875rem; color: var(--text-secondary);">Frequency: ${cpu.frequency_mhz.toFixed(0)} MHz</div>` : ''}
                </div>
            </div>
        `;
    }
    
    // Memory
    if (resources.memory && resources.memory.available) {
        const mem = resources.memory;
        html += `
            <div style="margin-bottom: 2rem;">
                <h3>Memory</h3>
                <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span><strong>Usage:</strong> ${formatPercent(mem.percent)}</span>
                        <span>${formatGB(mem.used_gb)} / ${formatGB(mem.total_gb)}</span>
                    </div>
                    <div style="background: var(--background); height: 20px; border-radius: 4px; overflow: hidden; margin-bottom: 0.5rem;">
                        <div style="background: var(--primary-color); height: 100%; width: ${mem.percent}%; transition: width 0.3s;"></div>
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">
                        Available: ${formatGB(mem.available_gb)}
                        ${mem.swap_total_gb > 0 ? ` • Swap: ${formatGB(mem.swap_used_gb)} / ${formatGB(mem.swap_total_gb)} (${formatPercent(mem.swap_percent)})` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    // GPU
    if (resources.gpu && resources.gpu.available) {
        html += `
            <div style="margin-bottom: 2rem;">
                <h3>GPU${resources.gpu.gpu_count > 1 ? 's' : ''} (${resources.gpu.gpu_count})</h3>
        `;
        
        resources.gpu.gpus.forEach((gpu, index) => {
            html += `
                <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong>${gpu.name}</strong>
                        ${gpu.temperature_c !== null ? `<span>🌡️ ${gpu.temperature_c}°C</span>` : ''}
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span>GPU Utilization:</span>
                            <span>${formatPercent(gpu.utilization_percent)}</span>
                        </div>
                        <div style="background: var(--background); height: 12px; border-radius: 4px; overflow: hidden;">
                            <div style="background: var(--primary-color); height: 100%; width: ${gpu.utilization_percent}%; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span>Memory:</span>
                            <span>${formatGB(gpu.memory_used_gb)} / ${formatGB(gpu.memory_total_gb)} (${formatPercent(gpu.memory_percent)})</span>
                        </div>
                        <div style="background: var(--background); height: 12px; border-radius: 4px; overflow: hidden;">
                            <div style="background: var(--secondary-color); height: 100%; width: ${gpu.memory_percent}%; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    ${gpu.power_watts !== null ? `<div style="font-size: 0.875rem; color: var(--text-secondary);">Power: ${gpu.power_watts.toFixed(1)} W</div>` : ''}
                </div>
            `;
        });
        
        html += `</div>`;
    } else if (resources.gpu) {
        html += `
            <div style="margin-bottom: 2rem;">
                <h3>GPU</h3>
                <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                    <p style="color: var(--text-secondary);">${resources.gpu.message || 'GPU monitoring not available'}</p>
                </div>
            </div>
        `;
    }
    
    // Disk
    if (resources.disk && resources.disk.available) {
        const disk = resources.disk;
        html += `
            <div style="margin-bottom: 2rem;">
                <h3>Disk (${disk.path})</h3>
                <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span><strong>Usage:</strong> ${formatPercent(disk.percent)}</span>
                        <span>${formatGB(disk.used_gb)} / ${formatGB(disk.total_gb)}</span>
                    </div>
                    <div style="background: var(--background); height: 20px; border-radius: 4px; overflow: hidden; margin-bottom: 0.5rem;">
                        <div style="background: var(--primary-color); height: 100%; width: ${disk.percent}%; transition: width 0.3s;"></div>
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">
                        Free: ${formatGB(disk.free_gb)}
                    </div>
                </div>
            </div>
        `;
    }
    
    // System Info
    html += `
        <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color);">
            <h3>System Information</h3>
            <div style="background: var(--surface-light); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem; font-size: 0.875rem;">
                    <div><strong>Platform:</strong> ${resources.platform || 'Unknown'}</div>
                    <div><strong>Architecture:</strong> ${resources.architecture || 'Unknown'}</div>
                    ${resources.platform_release ? `<div><strong>Release:</strong> ${resources.platform_release}</div>` : ''}
                    ${resources.processor ? `<div><strong>Processor:</strong> ${resources.processor}</div>` : ''}
                </div>
            </div>
        </div>
    `;
    
    content.innerHTML = html;
}

function toggleResourceAutoRefresh() {
    const checkbox = document.getElementById('autoRefreshResources');
    if (!checkbox) return;
    
    if (checkbox.checked) {
        resourceAutoRefreshInterval = setInterval(loadResourceMonitoring, 5000);
    } else {
        if (resourceAutoRefreshInterval) {
            clearInterval(resourceAutoRefreshInterval);
            resourceAutoRefreshInterval = null;
        }
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const usageModal = document.getElementById('usageDashboardModal');
    if (usageModal && e.target === usageModal) {
        closeUsageDashboard();
        // Stop auto-refresh when closing
        if (resourceAutoRefreshInterval) {
            clearInterval(resourceAutoRefreshInterval);
            resourceAutoRefreshInterval = null;
        }
    }
    
    // Close chat templates modal
    const templatesModal = document.getElementById('chatTemplatesModal');
    if (templatesModal && e.target === templatesModal) {
        closeChatTemplates();
    }
});

// Chat Templates Functions
function loadChatTemplates() {
    const saved = localStorage.getItem('customChatTemplates');
    if (saved) {
        try {
            chatTemplates.custom = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading custom templates:', e);
        }
    }
}

function saveChatTemplates() {
    localStorage.setItem('customChatTemplates', JSON.stringify(chatTemplates.custom));
}

function showChatTemplates() {
    const modal = document.getElementById('chatTemplatesModal');
    if (modal) {
        modal.style.display = 'flex';
        showTemplateTab('presets');
        renderPresetTemplates();
        renderCustomTemplates();
    }
}

function closeChatTemplates() {
    const modal = document.getElementById('chatTemplatesModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showTemplateTab(tab) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(content => {
        if (content.id.includes('template')) {
            content.classList.remove('active');
        }
    });
    document.querySelectorAll('.tab-btn').forEach((btn, idx) => {
        const tabsContainer = btn.closest('.tabs');
        if (tabsContainer && tabsContainer.parentElement.id === 'chatTemplatesModal') {
            btn.classList.remove('active');
        }
    });
    
    // Show selected tab
    if (tab === 'presets') {
        const presetsTab = document.getElementById('templatePresetsTab');
        const customTab = document.getElementById('templateCustomTab');
        if (presetsTab) presetsTab.classList.add('active');
        if (customTab) customTab.classList.remove('active');
        const tabs = document.querySelectorAll('#chatTemplatesModal .tab-btn');
        if (tabs[0]) tabs[0].classList.add('active');
        if (tabs[1]) tabs[1].classList.remove('active');
        renderPresetTemplates();
    } else {
        const presetsTab = document.getElementById('templatePresetsTab');
        const customTab = document.getElementById('templateCustomTab');
        if (presetsTab) presetsTab.classList.remove('active');
        if (customTab) customTab.classList.add('active');
        const tabs = document.querySelectorAll('#chatTemplatesModal .tab-btn');
        if (tabs[0]) tabs[0].classList.remove('active');
        if (tabs[1]) tabs[1].classList.add('active');
        renderCustomTemplates();
    }
}

function renderPresetTemplates() {
    const list = document.getElementById('presetTemplatesList');
    if (!list) return;
    
    list.innerHTML = '';
    
    chatTemplates.presets.forEach(template => {
        const card = document.createElement('div');
        card.className = 'template-card';
        card.style.cssText = 'padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; background: var(--surface-light);';
        card.onmouseenter = () => {
            card.style.background = 'var(--surface)';
            card.style.borderColor = 'var(--primary-color)';
        };
        card.onmouseleave = () => {
            card.style.background = 'var(--surface-light)';
            card.style.borderColor = 'var(--border-color)';
        };
        card.onclick = () => applyTemplate(template);
        
        card.innerHTML = `
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">${template.icon}</div>
            <h4 style="margin: 0.5rem 0;">${template.name}</h4>
            <p style="font-size: 0.875rem; color: var(--text-secondary); margin: 0.5rem 0;">${template.description}</p>
            ${template.suggestedModel ? `<div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.5rem;">💡 Suggested: ${template.suggestedModel}</div>` : ''}
        `;
        
        list.appendChild(card);
    });
}

function renderCustomTemplates() {
    const list = document.getElementById('customTemplatesList');
    if (!list) return;
    
    list.innerHTML = '';
    
    if (chatTemplates.custom.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary); grid-column: 1 / -1;">No custom templates yet. Create one above!</p>';
        return;
    }
    
    chatTemplates.custom.forEach((template, index) => {
        const card = document.createElement('div');
        card.className = 'template-card';
        card.style.cssText = 'padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; background: var(--surface-light); position: relative;';
        card.onmouseenter = () => {
            card.style.background = 'var(--surface)';
            card.style.borderColor = 'var(--primary-color)';
        };
        card.onmouseleave = () => {
            card.style.background = 'var(--surface-light)';
            card.style.borderColor = 'var(--border-color)';
        };
        
        card.innerHTML = `
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
            <h4 style="margin: 0.5rem 0;">${template.name}</h4>
            <p style="font-size: 0.875rem; color: var(--text-secondary); margin: 0.5rem 0;">${template.description || 'Custom template'}</p>
            ${template.suggestedModel ? `<div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.5rem;">💡 Suggested: ${template.suggestedModel}</div>` : ''}
            <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">
                <button class="btn btn-primary btn-small" onclick="applyCustomTemplate(${index})" style="flex: 1;">Apply</button>
                <button class="btn btn-secondary btn-small" onclick="deleteCustomTemplate(${index}, event)" title="Delete">🗑️</button>
            </div>
        `;
        
        list.appendChild(card);
    });
}

function applyCustomTemplate(index) {
    const template = chatTemplates.custom[index];
    if (template) {
        applyTemplate(template);
    }
}

function applyTemplate(template) {
    // Apply system prompt
    const systemPrompt = document.getElementById('systemPrompt');
    if (systemPrompt) {
        systemPrompt.value = template.systemPrompt;
    }
    
    // Apply temperature
    const temperature = document.getElementById('temperature');
    const tempValue = document.getElementById('tempValue');
    if (temperature && tempValue) {
        temperature.value = template.temperature;
        tempValue.textContent = template.temperature;
    }
    
    // Suggest model if provided
    if (template.suggestedModel) {
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            const option = Array.from(modelSelect.options).find(opt => opt.value === template.suggestedModel);
            if (option) {
                selectModel(template.suggestedModel);
                showToast(`Applied template: ${template.name}. Model suggested: ${template.suggestedModel}`, 'success');
            } else {
                showToast(`Applied template: ${template.name}. Model ${template.suggestedModel} not available`, 'info');
            }
        }
    } else {
        showToast(`Applied template: ${template.name}`, 'success');
    }
    
    closeChatTemplates();
}

function saveCustomTemplate() {
    const name = document.getElementById('customTemplateName')?.value.trim();
    const prompt = document.getElementById('customTemplatePrompt')?.value.trim();
    const model = document.getElementById('customTemplateModel')?.value.trim() || null;
    const temp = parseFloat(document.getElementById('customTemplateTemp')?.value) || 0.7;
    
    if (!name || !prompt) {
        showToast('Name and system prompt are required', 'error');
        return;
    }
    
    const template = {
        id: `custom-${Date.now()}`,
        name: name,
        icon: '📝',
        description: 'Custom template',
        systemPrompt: prompt,
        suggestedModel: model,
        temperature: temp
    };
    
    chatTemplates.custom.push(template);
    saveChatTemplates();
    renderCustomTemplates();
    
    // Clear form
    const nameInput = document.getElementById('customTemplateName');
    const promptInput = document.getElementById('customTemplatePrompt');
    const modelInput = document.getElementById('customTemplateModel');
    const tempInput = document.getElementById('customTemplateTemp');
    if (nameInput) nameInput.value = '';
    if (promptInput) promptInput.value = '';
    if (modelInput) modelInput.value = '';
    if (tempInput) tempInput.value = '0.7';
    
    showToast('Custom template saved!', 'success');
}

function deleteCustomTemplate(index, event) {
    if (event) {
        event.stopPropagation();
    }
    if (confirm('Delete this custom template?')) {
        chatTemplates.custom.splice(index, 1);
        saveChatTemplates();
        renderCustomTemplates();
        showToast('Template deleted', 'success');
    }
}

