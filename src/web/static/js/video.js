// LocalMind Video Generation JavaScript

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global state
let videoModels = [];
let currentVideoModel = null;
let generatedVideos = [];
let socket = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeVideoPage();
});

async function initializeVideoPage() {
    await loadVideoModels();
    await loadVideoTemplates();
    await loadVideosFromServer();
    await populateBackendFilter();
    setupEventListeners();
    setupPromptEnhancement();
    setupWebSocket();
}

function setupWebSocket() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', () => {
            console.log('Connected to video WebSocket');
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from video WebSocket');
        });
        
        socket.on('video_progress', (data) => {
            updateVideoProgress(data.video_id, data.progress, data.status);
        });
        
        socket.on('video_complete', (data) => {
            handleVideoComplete(data.video_id, data.result);
        });
        
        socket.on('video_error', (data) => {
            handleVideoError(data.video_id, data.error);
        });
    }
}

function updateVideoProgress(videoId, progress, status) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    
    if (progressBar) {
        progressBar.style.width = `${progress * 100}%`;
    }
    if (progressPercent) {
        progressPercent.textContent = `${Math.round(progress * 100)}%`;
    }
    if (progressStatus) {
        progressStatus.textContent = status || 'Processing...';
    }
}

function handleVideoComplete(videoId, result) {
    const progressDiv = document.getElementById('videoProgress');
    const progressStatus = document.getElementById('progressStatus');
    
    if (progressStatus) {
        progressStatus.textContent = 'Video generated successfully!';
    }
    if (progressDiv) {
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 2000);
    }
    
    // Add to gallery
    const video = {
        id: videoId,
        url: result.video_url,
        path: result.video_path,
        status: 'completed',
        prompt: '', // Will be loaded from server
        model: '',
        backend: ''
    };
    
    // Reload video from server to get full details
    loadVideoFromServer(videoId);
    
    showNotification('Video generated successfully!', 'success');
}

function handleVideoError(videoId, error) {
    const progressStatus = document.getElementById('progressStatus');
    if (progressStatus) {
        progressStatus.textContent = `Error: ${error}`;
    }
    showNotification(`Video generation failed: ${error}`, 'error');
}

async function loadVideoFromServer(videoId) {
    try {
        const response = await fetch(`/api/videos/${videoId}`);
        const data = await response.json();
        
        if (data.status === 'ok' && data.video) {
            const video = {
                id: data.video.id,
                url: data.video.video_url,
                path: data.video.video_path,
                status: data.video.status || 'completed',
                prompt: data.video.prompt,
                model: data.video.model,
                backend: data.video.backend,
                duration: data.video.duration,
                aspect_ratio: data.video.aspect_ratio,
                resolution: data.video.resolution,
                created_at: data.video.created_at
            };
            
            addVideoToGallery(video);
        }
    } catch (error) {
        console.error('Error loading video from server:', error);
    }
}

async function loadVideoModels() {
    try {
        const response = await fetch('/api/video/models');
        const data = await response.json();
        
        if (data.status === 'ok') {
            videoModels = data.models || [];
            populateModelSelect(data.models_by_backend || {});
        } else {
            showNotification('Failed to load video models', 'error');
        }
    } catch (error) {
        console.error('Error loading video models:', error);
        showNotification('Error loading video models', 'error');
    }
}

function populateModelSelect(modelsByBackend) {
    const select = document.getElementById('videoModelSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select a video model...</option>';
    
    // Group by backend
    for (const [backend, models] of Object.entries(modelsByBackend)) {
        if (models.length === 0) continue;
        
        const optgroup = document.createElement('optgroup');
        optgroup.label = backend.charAt(0).toUpperCase() + backend.slice(1);
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = `${backend}:${model}`;
            option.textContent = `${model} (${backend})`;
            optgroup.appendChild(option);
        });
        
        select.appendChild(optgroup);
    }
}

async function generateVideo() {
    const promptInput = document.getElementById('videoPrompt');
    const modelSelect = document.getElementById('videoModelSelect');
    const durationInput = document.getElementById('videoDuration');
    const aspectRatioSelect = document.getElementById('videoAspectRatio');
    const resolutionSelect = document.getElementById('videoResolution');
    const generateBtn = document.getElementById('generateVideoBtn');
    const generateBtnText = document.getElementById('generateBtnText');
    const progressDiv = document.getElementById('videoProgress');
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    const progressPercent = document.getElementById('progressPercent');
    
    if (!promptInput || !modelSelect) return;
    
    const prompt = promptInput.value.trim();
    const model = modelSelect.value;
    const duration = durationInput ? parseInt(durationInput.value) : null;
    const aspectRatio = aspectRatioSelect ? aspectRatioSelect.value : null;
    const resolution = resolutionSelect ? resolutionSelect.value : null;
    
    if (!prompt) {
        showNotification('Please enter a video prompt', 'error');
        return;
    }
    
    if (!model) {
        showNotification('Please select a video model', 'error');
        return;
    }
    
    // Disable button and show progress
    if (generateBtn) {
        generateBtn.disabled = true;
    }
    if (generateBtnText) {
        generateBtnText.textContent = '⏳ Generating...';
    }
    if (progressDiv) {
        progressDiv.style.display = 'block';
    }
    if (progressBar) {
        progressBar.style.width = '0%';
    }
    if (progressStatus) {
        progressStatus.textContent = 'Starting generation...';
    }
    if (progressPercent) {
        progressPercent.textContent = '0%';
    }
    
    try {
        const response = await fetch('/api/video/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                model: model,
                duration: duration,
                aspect_ratio: aspectRatio,
                resolution: resolution
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok' && data.video) {
            const video = data.video;
            const videoId = video.id;
            
            // Join WebSocket room for this video
            if (socket && videoId) {
                socket.emit('join_video_room', { video_id: videoId });
            }
            
            // If video is queued, show progress
            if (video.status === 'pending' || video.status === 'processing') {
                if (progressStatus) {
                    progressStatus.textContent = 'Video queued for generation...';
                }
                // Progress will be updated via WebSocket
            } else {
                // Immediate completion (fallback mode)
                if (progressBar) {
                    progressBar.style.width = '100%';
                }
                if (progressStatus) {
                    progressStatus.textContent = 'Video generated successfully!';
                }
                if (progressPercent) {
                    progressPercent.textContent = '100%';
                }
                
                // Add to gallery
                addVideoToGallery(video);
                
                // Reset form after a delay
                setTimeout(() => {
                    if (progressDiv) {
                        progressDiv.style.display = 'none';
                    }
                    if (promptInput) {
                        promptInput.value = '';
                    }
                }, 2000);
            }
        } else {
            const errorMsg = data.error || data.message || 'Failed to generate video';
            if (progressStatus) {
                progressStatus.textContent = `Error: ${errorMsg}`;
            }
            showNotification(errorMsg, 'error');
        }
    } catch (error) {
        console.error('Error generating video:', error);
        if (progressStatus) {
            progressStatus.textContent = `Error: ${error.message}`;
        }
        showNotification('Error generating video: ' + error.message, 'error');
    } finally {
        // Re-enable button
        if (generateBtn) {
            generateBtn.disabled = false;
        }
        if (generateBtnText) {
            generateBtnText.textContent = '🎬 Generate Video';
        }
    }
}

function addVideoToGallery(video) {
    const gallery = document.getElementById('videoGallery');
    if (!gallery) return;
    
    // Check if video already exists in gallery
    const existingCard = gallery.querySelector(`[data-video-id="${video.id}"]`);
    if (existingCard) {
        return; // Already displayed
    }
    
    // Remove "no videos" message if present
    const noVideosMsg = gallery.querySelector('p');
    if (noVideosMsg && noVideosMsg.textContent.includes('No videos')) {
        noVideosMsg.remove();
    }
    
    const videoCard = document.createElement('div');
    videoCard.className = 'video-card';
    videoCard.setAttribute('data-video-id', video.id || `video-${Date.now()}`);
    if (video.backend) {
        videoCard.setAttribute('data-backend', video.backend);
    }
    videoCard.style.cssText = 'background: var(--surface); border-radius: 0.5rem; padding: 1rem; box-shadow: 0 2px 10px var(--shadow); transition: transform 0.2s;';
    videoCard.onmouseenter = () => videoCard.style.transform = 'translateY(-2px)';
    videoCard.onmouseleave = () => videoCard.style.transform = 'translateY(0)';
    
    const videoId = video.id || `video-${Date.now()}`;
    const videoUrl = video.url || video.video_url;
    const videoPath = video.path || video.video_path;
    const displayPrompt = video.prompt || '';
    const displayModel = video.model || 'Unknown';
    const displayBackend = video.backend || '';
    const createdAt = video.created_at ? new Date(video.created_at).toLocaleString() : '';
    
    videoCard.innerHTML = `
        <div style="margin-bottom: 0.75rem; position: relative;">
            ${videoUrl ? `
                <video controls style="width: 100%; border-radius: 0.375rem; background: var(--surface-light);" preload="metadata">
                    <source src="${escapeHtml(videoUrl)}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            ` : videoPath ? `
                <video controls style="width: 100%; border-radius: 0.375rem; background: var(--surface-light);" preload="metadata">
                    <source src="/videos/${escapeHtml(videoPath)}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            ` : `
                <div style="width: 100%; aspect-ratio: 16/9; background: var(--surface-light); border-radius: 0.375rem; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); flex-direction: column; gap: 0.5rem;">
                    <div style="font-size: 2rem;">⏳</div>
                    <div>Video processing...</div>
                </div>
            `}
        </div>
        <div style="margin-bottom: 0.5rem;">
            <strong style="display: block; margin-bottom: 0.25rem; font-size: 0.875rem;">Prompt:</strong>
            <p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0; line-height: 1.4;">${escapeHtml(displayPrompt)}</p>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
            <span>${displayBackend ? `${displayBackend} - ` : ''}${escapeHtml(displayModel)}</span>
            ${createdAt ? `<span>${createdAt}</span>` : ''}
        </div>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            ${videoUrl || videoPath ? `
                <button onclick="downloadVideo('${videoId}', '${escapeHtml(videoUrl || videoPath)}')" class="btn btn-small btn-secondary" style="flex: 1; min-width: 80px;">
                    📥 Download
                </button>
            ` : ''}
            <button onclick="regenerateVideo('${escapeHtml(displayPrompt)}')" class="btn btn-small btn-secondary" style="flex: 1; min-width: 80px;">
                🔄 Regenerate
            </button>
            <button onclick="deleteVideo('${videoId}')" class="btn btn-small" style="background: var(--error); color: white; flex: 1; min-width: 80px;">
                🗑️ Delete
            </button>
        </div>
    `;
    
    gallery.insertBefore(videoCard, gallery.firstChild);
}

async function deleteVideo(videoId) {
    if (!confirm('Are you sure you want to delete this video?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/videos/${videoId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            // Remove from gallery
            const videoCard = document.querySelector(`[data-video-id="${videoId}"]`);
            if (videoCard) {
                videoCard.remove();
            }
            
            // Remove from local array
            generatedVideos = generatedVideos.filter(v => v.id !== videoId);
            
            showNotification('Video deleted', 'success');
        } else {
            showNotification('Failed to delete video', 'error');
        }
    } catch (error) {
        console.error('Error deleting video:', error);
        showNotification('Error deleting video', 'error');
    }
}

function downloadVideo(videoId, videoUrl) {
    if (videoUrl) {
        const a = document.createElement('a');
        a.href = videoUrl;
        a.download = `video-${videoId}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
}

function regenerateVideo(prompt) {
    const promptInput = document.getElementById('videoPrompt');
    if (promptInput) {
        promptInput.value = prompt;
        promptInput.focus();
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadVideosFromServer() {
    try {
        const response = await fetch('/api/videos?limit=50');
        const data = await response.json();
        
        if (data.status === 'ok' && data.videos) {
            generatedVideos = data.videos.map(v => ({
                id: v.id,
                url: v.video_url || null,
                path: v.video_path || null,
                status: v.status || 'completed',
                model: v.model,
                prompt: v.prompt,
                backend: v.backend,
                duration: v.duration,
                aspect_ratio: v.aspect_ratio,
                resolution: v.resolution,
                created_at: v.created_at
            }));
            
            // Display videos in gallery
            generatedVideos.forEach(video => {
                if (video.url || video.status === 'completed') {
                    addVideoToGallery(video);
                }
            });
        }
    } catch (error) {
        console.error('Error loading videos from server:', error);
        // Fallback to localStorage
        loadGeneratedVideos();
    }
}

function loadGeneratedVideos() {
    try {
        const saved = localStorage.getItem('generatedVideos');
        if (saved) {
            const localVideos = JSON.parse(saved);
            localVideos.forEach(video => {
                if (video.url || video.status === 'completed') {
                    addVideoToGallery(video);
                }
            });
        }
    } catch (error) {
        console.error('Error loading generated videos:', error);
    }
}

function saveGeneratedVideos() {
    try {
        // Keep only last 50 videos
        const videosToSave = generatedVideos.slice(-50);
        localStorage.setItem('generatedVideos', JSON.stringify(videosToSave));
    } catch (error) {
        console.error('Error saving generated videos:', error);
    }
}

function filterVideos(searchTerm) {
    const gallery = document.getElementById('videoGallery');
    if (!gallery) return;
    
    const cards = gallery.querySelectorAll('.video-card');
    const term = searchTerm.toLowerCase();
    
    cards.forEach(card => {
        const prompt = card.textContent.toLowerCase();
        if (prompt.includes(term) || term === '') {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function filterVideosByBackend(backend) {
    const gallery = document.getElementById('videoGallery');
    if (!gallery) return;
    
    const cards = gallery.querySelectorAll('.video-card');
    
    cards.forEach(card => {
        if (!backend || backend === '') {
            card.style.display = '';
            return;
        }
        
        const cardBackend = card.getAttribute('data-backend');
        if (cardBackend === backend) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

async function populateBackendFilter() {
    try {
        const response = await fetch('/api/video/models');
        const data = await response.json();
        
        if (data.status === 'ok' && data.backends) {
            const filterSelect = document.getElementById('videoFilterBackend');
            if (filterSelect) {
                data.backends.forEach(backend => {
                    const option = document.createElement('option');
                    option.value = backend;
                    option.textContent = backend.charAt(0).toUpperCase() + backend.slice(1);
                    filterSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading backends for filter:', error);
    }
}

async function loadVideoTemplates() {
    try {
        const response = await fetch('/api/video/templates');
        const data = await response.json();
        
        if (data.status === 'ok' && data.templates) {
            const templateSelect = document.getElementById('videoTemplateSelect');
            if (templateSelect) {
                // Group by category
                const categories = {};
                data.templates.forEach(template => {
                    if (!categories[template.category]) {
                        categories[template.category] = [];
                    }
                    categories[template.category].push(template);
                });
                
                // Add templates grouped by category
                Object.keys(categories).sort().forEach(category => {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = category.charAt(0).toUpperCase() + category.slice(1);
                    
                    categories[category].forEach(template => {
                        const option = document.createElement('option');
                        option.value = template.id;
                        option.textContent = `${template.name} - ${template.description}`;
                        option.dataset.template = JSON.stringify(template);
                        optgroup.appendChild(option);
                    });
                    
                    templateSelect.appendChild(optgroup);
                });
            }
        }
    } catch (error) {
        console.error('Error loading video templates:', error);
    }
}

function loadTemplate() {
    const templateSelect = document.getElementById('videoTemplateSelect');
    const promptInput = document.getElementById('videoPrompt');
    const durationInput = document.getElementById('videoDuration');
    const aspectRatioSelect = document.getElementById('videoAspectRatio');
    const resolutionSelect = document.getElementById('videoResolution');
    
    if (!templateSelect || !promptInput) return;
    
    const selectedOption = templateSelect.options[templateSelect.selectedIndex];
    if (!selectedOption || !selectedOption.value) {
        showNotification('Please select a template', 'error');
        return;
    }
    
    try {
        const template = JSON.parse(selectedOption.dataset.template);
        
        // Fill in prompt with template
        promptInput.value = template.prompt_template;
        
        // Set default values
        if (durationInput && template.default_duration) {
            durationInput.value = template.default_duration;
        }
        if (aspectRatioSelect && template.default_aspect_ratio) {
            aspectRatioSelect.value = template.default_aspect_ratio;
        }
        if (resolutionSelect && template.default_resolution) {
            resolutionSelect.value = template.default_resolution;
        }
        
        showNotification(`Template "${template.name}" loaded!`, 'success');
    } catch (error) {
        console.error('Error loading template:', error);
        showNotification('Error loading template', 'error');
    }
}

function setupEventListeners() {
    // Enter key to generate (Ctrl+Enter or Cmd+Enter)
    const promptInput = document.getElementById('videoPrompt');
    if (promptInput) {
        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                generateVideo();
            }
        });
    }
}

function setupPromptEnhancement() {
    const promptInput = document.getElementById('videoPrompt');
    if (!promptInput) return;
    
    // Add prompt enhancement button
    const promptContainer = promptInput.parentElement;
    if (promptContainer) {
        const enhanceBtn = document.createElement('button');
        enhanceBtn.type = 'button';
        enhanceBtn.className = 'btn btn-small btn-secondary';
        enhanceBtn.style.cssText = 'margin-top: 0.5rem;';
        enhanceBtn.innerHTML = '✨ Enhance Prompt';
        enhanceBtn.onclick = enhancePrompt;
        promptContainer.appendChild(enhanceBtn);
    }
}

function enhancePrompt() {
    const promptInput = document.getElementById('videoPrompt');
    if (!promptInput) return;
    
    const currentPrompt = promptInput.value.trim();
    if (!currentPrompt) {
        showNotification('Please enter a prompt first', 'error');
        return;
    }
    
    // Simple prompt enhancement (can be improved with AI later)
    const enhancements = [
        'cinematic',
        'high quality',
        'detailed',
        'professional',
        '4K resolution'
    ];
    
    // Check if prompt already has enhancement keywords
    const hasEnhancements = enhancements.some(e => 
        currentPrompt.toLowerCase().includes(e.toLowerCase())
    );
    
    if (hasEnhancements) {
        showNotification('Prompt already enhanced!', 'info');
        return;
    }
    
    // Add enhancement suggestions
    const enhanced = `${currentPrompt}, cinematic, high quality, detailed, professional`;
    promptInput.value = enhanced;
    showNotification('Prompt enhanced!', 'success');
}

// Notification function (reuse from app.js if available, otherwise define)
function showNotification(message, type = 'info') {
    if (typeof showToast === 'function') {
        showToast(message, type);
    } else {
        // Fallback notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'error' ? 'var(--error)' : type === 'success' ? 'var(--success)' : 'var(--primary-color)'};
            color: white;
            border-radius: 0.5rem;
            box-shadow: 0 4px 12px var(--shadow);
            z-index: 10000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

