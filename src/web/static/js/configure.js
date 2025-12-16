// API Configuration JavaScript

let providers = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadProviders();
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

// Show notification
function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this
    alert(message);
}

