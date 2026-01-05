// API Configuration JavaScript

let providers = [];
let videoProviders = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadProviders();
    loadVideoProviders();
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

// Load providers from API
async function loadProviders() {
    try {
        const response = await fetch('/api/config/providers');
        const data = await response.json();
        
        if (data.status === 'ok') {
            providers = data.providers;
            renderProviders();
        }
    } catch (error) {
        console.error('Failed to load providers:', error);
        document.getElementById('providersList').innerHTML = 
            '<p style="color: var(--error);">Failed to load providers</p>';
    }
}

// Render providers
function renderProviders() {
    const container = document.getElementById('providersList');
    container.innerHTML = '';
    
    providers.forEach(provider => {
        const card = createProviderCard(provider);
        container.appendChild(card);
    });
}

// Create provider card
function createProviderCard(provider) {
    const card = document.createElement('div');
    card.className = 'provider-card';
    
    const header = document.createElement('div');
    header.className = 'provider-header';
    
    const title = document.createElement('h3');
    title.textContent = provider.display_name;
    
    const status = document.createElement('span');
    status.className = `status-badge ${provider.enabled ? 'status-enabled' : 'status-disabled'}`;
    status.textContent = provider.enabled ? 'Enabled' : 'Disabled';
    
    header.appendChild(title);
    header.appendChild(status);
    
    const form = document.createElement('div');
    form.className = 'config-form';
    
    const apiKeyGroup = document.createElement('div');
    apiKeyGroup.className = 'form-group';
    
    const apiKeyLabel = document.createElement('label');
    apiKeyLabel.textContent = 'API Key';
    apiKeyLabel.htmlFor = `api-key-${provider.name}`;
    
    const apiKeyInput = document.createElement('input');
    apiKeyInput.type = 'password';
    apiKeyInput.id = `api-key-${provider.name}`;
    apiKeyInput.placeholder = provider.api_key ? '••••••••' : 'Enter API key';
    apiKeyInput.value = provider.api_key || '';
    
    apiKeyGroup.appendChild(apiKeyLabel);
    apiKeyGroup.appendChild(apiKeyInput);
    
    const setupLink = document.createElement('a');
    setupLink.href = provider.setup_url;
    setupLink.target = '_blank';
    setupLink.textContent = `Get API key from ${provider.display_name}`;
    setupLink.style.color = 'var(--primary-color)';
    setupLink.style.fontSize = '0.875rem';
    setupLink.style.marginTop = '-0.5rem';
    
    const actions = document.createElement('div');
    actions.className = 'form-actions';
    
    const enableCheckbox = document.createElement('label');
    enableCheckbox.style.display = 'flex';
    enableCheckbox.style.alignItems = 'center';
    enableCheckbox.style.gap = '0.5rem';
    enableCheckbox.style.cursor = 'pointer';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = provider.enabled;
    checkbox.id = `enable-${provider.name}`;
    
    const checkboxLabel = document.createElement('span');
    checkboxLabel.textContent = 'Enable this backend';
    
    enableCheckbox.appendChild(checkbox);
    enableCheckbox.appendChild(checkboxLabel);
    
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary';
    saveBtn.textContent = 'Save';
    saveBtn.onclick = () => saveProvider(provider.name, apiKeyInput.value, checkbox.checked);
    
    actions.appendChild(enableCheckbox);
    actions.appendChild(saveBtn);
    
    form.appendChild(apiKeyGroup);
    form.appendChild(setupLink);
    form.appendChild(actions);
    
    card.appendChild(header);
    card.appendChild(form);
    
    return card;
}

// Save provider configuration
async function saveProvider(providerName, apiKey, enabled) {
    try {
        const response = await fetch('/api/config/providers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: providerName,
                api_key: apiKey,
                enabled: enabled
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showNotification('Configuration saved! Restart the server for changes to take effect.', 'success');
            // Reload providers
            loadProviders();
        } else {
            showNotification(data.message || 'Failed to save configuration', 'error');
        }
    } catch (error) {
        console.error('Error saving provider:', error);
        showNotification('Failed to save configuration', 'error');
    }
}

// Load video providers from API
async function loadVideoProviders() {
    try {
        const response = await fetch('/api/config/video-providers');
        const data = await response.json();
        
        if (data.status === 'ok') {
            videoProviders = data.providers;
            renderVideoProviders();
        }
    } catch (error) {
        console.error('Failed to load video providers:', error);
        document.getElementById('videoProvidersList').innerHTML = 
            '<p style="color: var(--error);">Failed to load video providers</p>';
    }
}

// Render video providers
function renderVideoProviders() {
    const container = document.getElementById('videoProvidersList');
    container.innerHTML = '';
    
    if (videoProviders.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No video providers available</p>';
        return;
    }
    
    videoProviders.forEach(provider => {
        const card = createVideoProviderCard(provider);
        container.appendChild(card);
    });
}

// Create video provider card
function createVideoProviderCard(provider) {
    const card = document.createElement('div');
    card.className = 'provider-card';
    
    const header = document.createElement('div');
    header.className = 'provider-header';
    
    const titleDiv = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = provider.display_name;
    title.style.margin = '0';
    
    const description = document.createElement('p');
    description.textContent = provider.description || '';
    description.style.margin = '0.25rem 0 0 0';
    description.style.fontSize = '0.875rem';
    description.style.color = 'var(--text-secondary)';
    
    titleDiv.appendChild(title);
    titleDiv.appendChild(description);
    
    const status = document.createElement('span');
    status.className = `status-badge ${provider.enabled ? 'status-enabled' : 'status-disabled'}`;
    status.textContent = provider.enabled ? 'Enabled' : 'Disabled';
    
    header.appendChild(titleDiv);
    header.appendChild(status);
    
    const form = document.createElement('div');
    form.className = 'config-form';
    
    const apiKeyGroup = document.createElement('div');
    apiKeyGroup.className = 'form-group';
    
    const apiKeyLabel = document.createElement('label');
    apiKeyLabel.textContent = 'API Key';
    apiKeyLabel.htmlFor = `video-api-key-${provider.name}`;
    
    const apiKeyInput = document.createElement('input');
    apiKeyInput.type = 'password';
    apiKeyInput.id = `video-api-key-${provider.name}`;
    apiKeyInput.placeholder = provider.api_key ? '••••••••' : 'Enter API key';
    apiKeyInput.value = provider.api_key || '';
    
    apiKeyGroup.appendChild(apiKeyLabel);
    apiKeyGroup.appendChild(apiKeyInput);
    
    const setupLink = document.createElement('a');
    setupLink.href = provider.setup_url;
    setupLink.target = '_blank';
    setupLink.textContent = `Get API key from ${provider.display_name}`;
    setupLink.style.color = 'var(--primary-color)';
    setupLink.style.fontSize = '0.875rem';
    setupLink.style.marginTop = '-0.5rem';
    
    const envVarInfo = document.createElement('p');
    envVarInfo.textContent = `Environment variable: ${provider.env_var}`;
    envVarInfo.style.fontSize = '0.75rem';
    envVarInfo.style.color = 'var(--text-secondary)';
    envVarInfo.style.marginTop = '0.25rem';
    envVarInfo.style.fontFamily = 'monospace';
    
    const actions = document.createElement('div');
    actions.className = 'form-actions';
    
    const enableCheckbox = document.createElement('label');
    enableCheckbox.style.display = 'flex';
    enableCheckbox.style.alignItems = 'center';
    enableCheckbox.style.gap = '0.5rem';
    enableCheckbox.style.cursor = 'pointer';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = provider.enabled;
    checkbox.id = `video-enable-${provider.name}`;
    
    const checkboxLabel = document.createElement('span');
    checkboxLabel.textContent = 'Enable this video backend';
    
    enableCheckbox.appendChild(checkbox);
    enableCheckbox.appendChild(checkboxLabel);
    
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary';
    saveBtn.textContent = 'Save';
    saveBtn.onclick = () => saveVideoProvider(provider.name, apiKeyInput.value, checkbox.checked);
    
    actions.appendChild(enableCheckbox);
    actions.appendChild(saveBtn);
    
    form.appendChild(apiKeyGroup);
    form.appendChild(setupLink);
    form.appendChild(envVarInfo);
    form.appendChild(actions);
    
    card.appendChild(header);
    card.appendChild(form);
    
    return card;
}

// Save video provider configuration
async function saveVideoProvider(providerName, apiKey, enabled) {
    try {
        const response = await fetch('/api/config/video-providers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: providerName,
                api_key: apiKey,
                enabled: enabled
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showNotification('Video provider configuration saved! Restart the server for changes to take effect.', 'success');
            // Reload video providers
            loadVideoProviders();
        } else {
            showNotification(data.message || 'Failed to save video provider configuration', 'error');
        }
    } catch (error) {
        console.error('Error saving video provider:', error);
        showNotification('Failed to save video provider configuration', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this
    alert(message);
}

