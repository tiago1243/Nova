// Enhanced Nova AI Assistant - Frontend JavaScript with API integrations

class NovaApp {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.voiceBtn = document.getElementById('voiceBtn');
        this.voiceBtnMain = document.getElementById('voiceBtnMain');
        this.speakToggle = document.getElementById('speakToggle');
        this.statusIndicator = document.getElementById('statusIndicator');
        
        this.isRecording = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.shouldSpeak = true;
        
        this.initializeVoiceRecognition();
        this.loadStats();
        this.loadApiStatus();
        this.setupEventListeners();
        
        // Auto-focus input
        this.messageInput.focus();
        
        // Refresh API status every 5 minutes
        setInterval(() => this.loadApiStatus(), 300000);
    }

    setupEventListeners() {
        // Voice button
        this.voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());
        
        // TTS toggle
        this.speakToggle.addEventListener('click', () => this.toggleTTS());
        
        // Auto-scroll when typing
        this.messageInput.addEventListener('input', () => {
            this.scrollToBottom();
        });
    }

    initializeVoiceRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported');
            this.voiceBtn.disabled = true;
            this.voiceBtn.innerHTML = '<i class="fas fa-microphone-slash me-1"></i>Not Supported';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            this.isRecording = true;
            this.updateVoiceButton(true);
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.messageInput.value = transcript;
            this.sendMessage();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.addMessage('nova', `Voice recognition error: ${event.error}`, 'error');
            this.resetVoiceButton();
        };

        this.recognition.onend = () => {
            this.resetVoiceButton();
        };
    }

    updateVoiceButton(recording) {
        if (recording) {
            // Update sidebar button
            this.voiceBtn.classList.add('recording', 'btn-danger');
            this.voiceBtn.classList.remove('btn-outline-primary');
            this.voiceBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Stop Recording';
            
            // Update main button
            this.voiceBtnMain.classList.add('recording', 'btn-danger');
            this.voiceBtnMain.classList.remove('btn-outline-primary');
            this.voiceBtnMain.innerHTML = '<i class="fas fa-stop"></i>';
            this.voiceBtnMain.title = 'Stop Recording';
        } else {
            this.resetVoiceButton();
        }
    }

    toggleVoiceRecording() {
        if (!this.recognition) return;

        if (this.isRecording) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    resetVoiceButton() {
        this.isRecording = false;
        
        // Reset sidebar button
        this.voiceBtn.classList.remove('recording', 'btn-danger');
        this.voiceBtn.classList.add('btn-outline-primary');
        this.voiceBtn.innerHTML = '<i class="fas fa-microphone me-1"></i><span id="voiceBtnText">Start Voice</span>';
        
        // Reset main button
        this.voiceBtnMain.classList.remove('recording', 'btn-danger');
        this.voiceBtnMain.classList.add('btn-outline-primary');
        this.voiceBtnMain.innerHTML = '<i class="fas fa-microphone"></i>';
        this.voiceBtnMain.title = 'Voice Input';
    }

    toggleTTS() {
        this.shouldSpeak = !this.shouldSpeak;
        const toggleText = document.getElementById('speakToggleText');
        const icon = this.speakToggle.querySelector('i');
        
        if (this.shouldSpeak) {
            toggleText.textContent = 'TTS: On';
            icon.className = 'fas fa-volume-up me-1';
            this.speakToggle.classList.remove('btn-outline-secondary');
            this.speakToggle.classList.add('btn-outline-primary');
        } else {
            toggleText.textContent = 'TTS: Off';
            icon.className = 'fas fa-volume-mute me-1';
            this.speakToggle.classList.remove('btn-outline-primary');
            this.speakToggle.classList.add('btn-outline-secondary');
        }
    }

    speak(text) {
        if (!this.shouldSpeak || !this.synthesis) return;

        // Stop any ongoing speech
        this.synthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;

        // Try to use a more natural voice
        const voices = this.synthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.name.includes('Natural') || 
            voice.name.includes('Enhanced') ||
            voice.name.includes('Premium')
        ) || voices.find(voice => voice.lang.startsWith('en'));

        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        this.synthesis.speak(utterance);
    }

    async sendMessage(message = null) {
        let text = message || this.messageInput.value.trim();
        if (!text) return;

        // Handle Wikipedia mode - prefix with "wikipedia:" to force Wikipedia search
        if (wikipediaMode && !text.toLowerCase().startsWith('wikipedia:') && !text.toLowerCase().startsWith('wiki:')) {
            text = 'wikipedia: ' + text;
            // Exit Wikipedia mode after sending the message
            exitWikipediaMode();
        }

        // Add user message to chat (show original text)
        this.addMessage('user', message || this.messageInput.value.trim());
        
        // Clear input
        if (!message) {
            this.messageInput.value = '';
        }

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.hideTypingIndicator();

            if (response.ok) {
                this.addMessage('nova', data.response, data.type, data);
                
                // Speak response if enabled
                if (data.should_speak || data.type === 'voice_success') {
                    this.speak(data.response);
                }
                
                // Refresh stats if memory was modified
                if (data.type === 'success' || data.type === 'system') {
                    this.loadStats();
                }
            } else {
                this.addMessage('nova', data.error || 'Something went wrong', 'error');
            }
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Error sending message:', error);
            this.addMessage('nova', 'Connection error. Please try again.', 'error');
        }
    }

    addMessage(sender, text, type = 'normal', data = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-text">${this.escapeHtml(text)}</div>
                </div>
            `;
        } else {
            let messageContent = this.renderNovaMessage(text, type, data);

            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="d-flex align-items-start">
                        <div class="avatar bg-primary me-3">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="message-header">
                                <strong class="text-primary">Nova</strong>
                                <small class="text-muted ms-2">${timeStr}</small>
                            </div>
                            ${messageContent}
                        </div>
                    </div>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    renderNovaMessage(text, type, data) {
        let content = `<div class="message-text">${this.formatText(text)}</div>`;

        // Enhanced message rendering based on type
        switch (type) {
            case 'knowledge':
                content += this.renderKnowledgeResponse(data);
                break;
            case 'weather':
                content += this.renderWeatherResponse(data);
                break;
            case 'news':
                content += this.renderNewsResponse(data);
                break;
            case 'daily_plan':
                content += this.renderDailyPlan(data);
                break;
            case 'daily_briefing':
                content += this.renderDailyBriefing(data);
                break;
            case 'memory':
                content += this.renderMemoryEntries(data);
                break;
            case 'agent_status':
                content += this.renderAgentStatus(data);
                break;
            case 'insights':
                content += this.renderInsights(data);
                break;
            case 'error':
                content = `<div class="error-message">${this.escapeHtml(text)}</div>`;
                break;
            case 'help':
                content = `<div class="message-text">${this.formatHelpText(text)}</div>`;
                break;
        }

        return content;
    }

    renderKnowledgeResponse(data) {
        if (!data || !data.title) return '';
        
        return `
            <div class="knowledge-response">
                <h6 class="mb-2"><i class="fas fa-brain me-2"></i>${this.escapeHtml(data.title)}</h6>
                <div class="knowledge-source">
                    <i class="fas fa-external-link-alt me-1"></i>Source: ${data.source}
                    ${data.url ? `<a href="${data.url}" target="_blank" class="knowledge-url">Read more</a>` : ''}
                </div>
            </div>
        `;
    }

    renderWeatherResponse(data) {
        if (!data || !data.data) return '';
        
        const weather = data.data;
        return `
            <div class="weather-response">
                <div class="weather-details">
                    <div>
                        <h6 class="mb-1"><i class="fas fa-map-marker-alt me-2"></i>${weather.location}</h6>
                        <small>${weather.description}</small>
                    </div>
                    <div class="weather-temp">${weather.temperature}°C</div>
                </div>
                <div class="mt-2 small">
                    <i class="fas fa-tint me-1"></i>Humidity: ${weather.humidity}%
                    ${weather.wind_speed ? `<i class="fas fa-wind ms-3 me-1"></i>Wind: ${weather.wind_speed} m/s` : ''}
                </div>
            </div>
        `;
    }

    renderNewsResponse(data) {
        if (!data || !data.articles) return '';
        
        let newsHtml = '<div class="news-response">';
        data.articles.forEach((article, index) => {
            newsHtml += `
                <div class="news-article">
                    <div class="news-title">${index + 1}. ${this.escapeHtml(article.title)}</div>
                    <div class="news-source">${article.source}</div>
                    ${article.url ? `<a href="${article.url}" target="_blank" class="small">Read more</a>` : ''}
                </div>
            `;
        });
        newsHtml += '</div>';
        
        return newsHtml;
    }

    renderDailyPlan(data) {
        if (!data || !data.plan) return '';
        
        const plan = data.plan;
        let planHtml = '<div class="daily-plan-container">';
        
        planHtml += `<h6 class="mb-3"><i class="fas fa-calendar-day me-2"></i>Daily Plan for ${plan.date}</h6>`;
        
        if (plan.weather) {
            planHtml += `
                <div class="mb-3">
                    <strong>Weather:</strong> ${plan.weather.temperature}°C, ${plan.weather.description}
                </div>
            `;
        }
        
        if (plan.priority_tasks && plan.priority_tasks.length > 0) {
            planHtml += '<div class="mb-3"><strong>Priority Tasks:</strong></div>';
            plan.priority_tasks.forEach(task => {
                planHtml += `<div class="time-block">📋 ${this.escapeHtml(task.text)}</div>`;
            });
        }
        
        if (plan.time_blocks && plan.time_blocks.length > 0) {
            planHtml += '<div class="mb-3"><strong>Suggested Schedule:</strong></div>';
            plan.time_blocks.forEach(block => {
                planHtml += `
                    <div class="time-block">
                        <div class="time-block-time">${block.time}</div>
                        <div>${this.escapeHtml(block.task)}</div>
                    </div>
                `;
            });
        }
        
        if (plan.suggestions && plan.suggestions.length > 0) {
            planHtml += '<div class="mt-3"><strong>Suggestions:</strong></div>';
            plan.suggestions.forEach(suggestion => {
                planHtml += `<div class="small text-muted">💡 ${this.escapeHtml(suggestion)}</div>`;
            });
        }
        
        planHtml += '</div>';
        return planHtml;
    }

    renderDailyBriefing(data) {
        if (!data || !data.data) return '';
        
        const briefing = data.data;
        let briefingHtml = '<div class="daily-briefing">';
        
        briefingHtml += `<h6 class="mb-3"><i class="fas fa-newspaper me-2"></i>Daily Briefing</h6>`;
        
        if (briefing.weather) {
            briefingHtml += `
                <div class="briefing-section">
                    <h6>🌤️ Weather</h6>
                    <p>${briefing.weather.temperature}°C, ${briefing.weather.description} in ${briefing.weather.location}</p>
                </div>
            `;
        }
        
        if (briefing.news_headlines && briefing.news_headlines.length > 0) {
            briefingHtml += '<div class="briefing-section"><h6>📰 Top Headlines</h6>';
            briefing.news_headlines.forEach((article, index) => {
                briefingHtml += `<p class="small">${index + 1}. ${this.escapeHtml(article.title)}</p>`;
            });
            briefingHtml += '</div>';
        }
        
        if (briefing.tasks_today && briefing.tasks_today.length > 0) {
            briefingHtml += `<div class="briefing-section"><h6>📋 Today's Tasks</h6>`;
            briefingHtml += `<p>You have ${briefing.tasks_today.length} tasks scheduled for today.</p></div>`;
        }
        
        briefingHtml += '</div>';
        return briefingHtml;
    }

    renderMemoryEntries(data) {
        if (!data || !data.entries) return '';
        
        let html = '';
        
        if (data.summary) {
            html += `<div class="mb-3 p-2 bg-info text-white rounded">
                <i class="fas fa-lightbulb me-2"></i><strong>Summary:</strong> ${this.escapeHtml(data.summary)}
            </div>`;
        }

        if (data.entries.length > 0) {
            html += '<div class="mt-3">';
            data.entries.forEach(entry => {
                const categoryColor = this.getCategoryColor(entry.category);
                const tags = entry.tags.map(tag => `<span class="tag-badge">${tag}</span>`).join('');
                
                html += `
                    <div class="memory-entry">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="category-badge badge ${categoryColor}">${entry.category}</span>
                            <small class="text-muted">${entry.timestamp}</small>
                        </div>
                        <div class="entry-text">${this.escapeHtml(entry.text)}</div>
                        <div class="entry-meta mt-2">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>${tags}</div>
                                <div class="small text-muted">
                                    ${entry.due_date ? `Due: ${entry.due_date}` : ''}
                                    ${entry.recurring ? `• Recurring: ${entry.recurring}` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        return html;
    }

    renderAgentStatus(data) {
        if (!data || !data.status) return '';
        
        const status = data.status;
        let html = '<div class="agent-status-container">';
        
        html += `<h6 class="mb-3"><i class="fas fa-cog me-2"></i>Agent Status</h6>`;
        html += `<p><strong>Active:</strong> ${status.is_active ? 'Yes' : 'No'}</p>`;
        html += `<p><strong>Pending Actions:</strong> ${status.pending_actions}</p>`;
        html += `<p><strong>Recent Insights:</strong> ${status.recent_insights}</p>`;
        
        if (status.actions && status.actions.length > 0) {
            html += '<h6 class="mt-3 mb-2">Pending Actions:</h6>';
            status.actions.forEach((action, index) => {
                html += `
                    <div class="agent-action action-priority-${action.priority > 7 ? 'high' : action.priority > 4 ? 'medium' : 'low'}" 
                         onclick="executeAgentAction('${action.action_id}')">
                        <div class="fw-bold">${this.escapeHtml(action.description)}</div>
                        <div class="small text-muted">Priority: ${action.priority}/10</div>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        return html;
    }

    renderInsights(data) {
        if (!data || !data.insights) return '';
        
        let html = '<div class="insights-container">';
        html += `<h6 class="mb-3"><i class="fas fa-chart-line me-2"></i>Recent Insights</h6>`;
        
        if (data.insights.length === 0) {
            html += '<p class="text-muted">No insights available yet. Keep using Nova to generate insights!</p>';
        } else {
            data.insights.forEach(insight => {
                html += `
                    <div class="insight-item">
                        <div class="fw-bold">${this.escapeHtml(insight.title)}</div>
                        <div class="small">${this.escapeHtml(insight.description)}</div>
                        <div class="small text-muted">Confidence: ${Math.round(insight.confidence * 100)}%</div>
                    </div>
                `;
            });
        }
        
        html += '</div>';
        return html;
    }

    getCategoryColor(category) {
        const colors = {
            'task': 'bg-warning',
            'idea': 'bg-info',
            'reminder': 'bg-danger',
            'note': 'bg-secondary',
            'recurring_reminder': 'bg-primary',
            'uncategorized': 'bg-dark'
        };
        return colors[category] || 'bg-secondary';
    }

    formatHelpText(text) {
        return text
            .replace(/\n/g, '<br>')
            .replace(/•/g, '<i class="fas fa-chevron-right me-2 text-primary"></i>')
            .replace(/🎯|💡|🌤️|📰|🔍|🤖|🎤/g, '');
    }

    formatText(text) {
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/#(\w+)/g, '<span class="tag-badge">#$1</span>');
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'message nova-message';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="d-flex align-items-start">
                    <div class="avatar bg-primary me-3">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="typing-indicator">
                            <span class="me-2">Nova is thinking</span>
                            <div class="typing-dots">
                                <div class="typing-dot"></div>
                                <div class="typing-dot"></div>
                                <div class="typing-dot"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            const statsContent = document.getElementById('statsContent');
            if (stats.error) {
                statsContent.innerHTML = '<span class="text-danger">Error loading stats</span>';
                return;
            }
            
            let statsHtml = `<div class="small">
                <div><strong>Total Entries:</strong> ${stats.total_entries}</div>
            `;
            
            if (stats.categories && Object.keys(stats.categories).length > 0) {
                statsHtml += '<div class="mt-2"><strong>Categories:</strong></div>';
                for (const [category, count] of Object.entries(stats.categories)) {
                    statsHtml += `<div class="ms-2">• ${category}: ${count}</div>`;
                }
            }
            
            if (stats.recent_activity) {
                statsHtml += `<div class="mt-2"><strong>Recent:</strong></div>`;
                statsHtml += `<div class="ms-2 text-muted small">${stats.recent_activity}</div>`;
            }
            
            statsHtml += '</div>';
            statsContent.innerHTML = statsHtml;
            
        } catch (error) {
            console.error('Error loading stats:', error);
            document.getElementById('statsContent').innerHTML = '<span class="text-danger">Error loading stats</span>';
        }
    }

    async loadApiStatus() {
        try {
            const response = await fetch('/api/external/status');
            const status = await response.json();
            
            this.updateApiStatusDisplay(status);
            
        } catch (error) {
            console.error('Error loading API status:', error);
            this.updateApiStatusDisplay({
                wikipedia: 'offline',
                weather: 'offline',
                news: 'offline'
            });
        }
    }

    updateApiStatusDisplay(status) {
        const statusElements = {
            'wikipedia': document.getElementById('wikipedia-status'),
            'weather': document.getElementById('weather-status'),
            'news': document.getElementById('news-status')
        };

        for (const [api, element] of Object.entries(statusElements)) {
            if (element) {
                const statusText = status[api] || 'unknown';
                const parentDiv = element.closest('.api-status-item');
                const icon = parentDiv.querySelector('.fas');
                
                element.textContent = statusText.charAt(0).toUpperCase() + statusText.slice(1);
                
                // Update icon color based on status
                icon.className = 'fas fa-circle text-muted me-1';
                if (statusText === 'online') {
                    icon.className = 'fas fa-circle text-success me-1';
                } else if (statusText === 'offline') {
                    icon.className = 'fas fa-circle text-danger me-1';
                } else if (statusText === 'no_key') {
                    icon.className = 'fas fa-circle text-warning me-1';
                }
            }
        }
    }
}

// Helper functions for quick actions
function sendQuickMessage(message) {
    if (window.app) {
        window.app.sendMessage(message);
    }
}

async function requestDailyPlan() {
    try {
        const response = await fetch('/api/agent/daily-plan');
        const data = await response.json();
        
        if (window.app) {
            window.app.addMessage('nova', data.response, data.type || 'daily_plan', data);
        }
    } catch (error) {
        console.error('Error requesting daily plan:', error);
    }
}

async function requestDailyBriefing() {
    try {
        const response = await fetch('/api/agent/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_id: 'daily_briefing_request' })
        });
        
        // If that fails, try the generate briefing method
        if (!response.ok) {
            window.app.sendMessage('daily briefing');
            return;
        }
        
        const data = await response.json();
        if (window.app) {
            window.app.addMessage('nova', data.response, data.type || 'daily_briefing', data);
        }
    } catch (error) {
        console.error('Error requesting daily briefing:', error);
        if (window.app) {
            window.app.sendMessage('daily briefing');
        }
    }
}

async function getInsights() {
    try {
        const response = await fetch('/api/agent/insights');
        const data = await response.json();
        
        if (window.app) {
            window.app.addMessage('nova', data.response, data.type || 'insights', data);
        }
    } catch (error) {
        console.error('Error getting insights:', error);
    }
}

async function showAgentStatus() {
    try {
        const response = await fetch('/api/agent/status');
        const data = await response.json();
        
        if (window.app) {
            window.app.addMessage('nova', data.response, data.type || 'agent_status', data);
        }
    } catch (error) {
        console.error('Error getting agent status:', error);
    }
}

async function executeAgentAction(actionId) {
    try {
        const response = await fetch('/api/agent/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_id: actionId })
        });
        
        const data = await response.json();
        
        if (window.app) {
            window.app.addMessage('nova', data.response || 'Action executed', data.type || 'system', data);
            // Refresh agent status
            showAgentStatus();
        }
    } catch (error) {
        console.error('Error executing agent action:', error);
    }
}

function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    // Keep only the welcome message
    const welcomeMessage = chatMessages.firstElementChild;
    chatMessages.innerHTML = '';
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }
}

// Wikipedia Mode Management
let wikipediaMode = false;

function enterWikipediaMode() {
    wikipediaMode = true;
    document.getElementById('wikipediaMode').style.display = 'block';
    document.getElementById('wikipediaBtn').classList.add('active');
    document.getElementById('messageInput').placeholder = 'Ask me anything and I\'ll search Wikipedia...';
    document.getElementById('messageInput').focus();
}

function exitWikipediaMode() {
    wikipediaMode = false;
    document.getElementById('wikipediaMode').style.display = 'none';
    document.getElementById('wikipediaBtn').classList.remove('active');
    document.getElementById('messageInput').placeholder = 'Ask me anything - knowledge, weather, news, or manage your tasks...';
}

// API Key Management
async function saveApiKey(service) {
    try {
        let apiKey;
        let inputId;
        
        if (service === 'weather') {
            inputId = 'weatherApiKey';
            apiKey = document.getElementById(inputId).value.trim();
        } else if (service === 'news') {
            inputId = 'newsApiKey';
            apiKey = document.getElementById(inputId).value.trim();
        }
        
        if (!apiKey) {
            alert('Please enter an API key');
            return;
        }
        
        const response = await fetch('/api/config/api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                service: service,
                api_key: apiKey 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Clear the input field
            document.getElementById(inputId).value = '';
            
            // Show success message
            if (window.app) {
                window.app.addMessage('nova', `✓ ${service.charAt(0).toUpperCase() + service.slice(1)} API key saved successfully! You can now use ${service} features.`, 'success');
            }
            
            // Refresh API status
            window.app.loadApiStatus();
        } else {
            alert(`Error saving API key: ${data.error}`);
        }
    } catch (error) {
        console.error('Error saving API key:', error);
        alert('Failed to save API key. Please try again.');
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (window.app) {
            window.app.sendMessage();
        }
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.app = new NovaApp();
});
