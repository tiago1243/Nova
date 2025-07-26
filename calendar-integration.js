// Calendar Integration for Nova AI Assistant
class CalendarIntegration {
    constructor() {
        this.modal = null;
        this.setupModal = null;
        this.calendarData = null;
        this.isConnected = false;
        
        this.initializeModals();
        this.checkConnectionStatus();
        
        logger.info("Calendar Integration initialized");
    }

    initializeModals() {
        // Main calendar view modal
        this.modal = new bootstrap.Modal(document.getElementById('calendarModal'), {
            backdrop: 'static',
            keyboard: false
        });

        // Setup modal (will be created dynamically)
        this.createSetupModal();
    }

    createSetupModal() {
        // Create setup modal HTML
        const setupModalHtml = `
            <div class="modal fade" id="calendarSetupModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content bg-dark">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-calendar-plus me-2"></i>Calendar Integration Setup
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="calendarSetupContent">
                                <!-- Setup content will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add to document if not exists
        if (!document.getElementById('calendarSetupModal')) {
            document.body.insertAdjacentHTML('beforeend', setupModalHtml);
        }

        this.setupModal = new bootstrap.Modal(document.getElementById('calendarSetupModal'));
    }

    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/config/calendar-setup', {
                method: 'GET'
            });

            if (response.ok) {
                const status = await response.json();
                this.isConnected = status.active_provider !== null;
                this.updateConnectionStatus();
            }
        } catch (error) {
            console.error('Error checking calendar connection status:', error);
        }
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('calendar-status');
        if (statusElement) {
            if (this.isConnected) {
                statusElement.textContent = 'Connected';
                statusElement.parentElement.querySelector('.fas').className = 'fas fa-circle text-success me-1';
            } else {
                statusElement.textContent = 'Setup Required';
                statusElement.parentElement.querySelector('.fas').className = 'fas fa-circle text-warning me-1';
            }
        }
    }

    async openCalendarView() {
        try {
            if (!this.isConnected) {
                this.showSetupModal();
                return;
            }

            // Show loading state
            this.showCalendarLoadingState();
            this.modal.show();
            
            // Load calendar data
            await this.loadCalendarData();
            
            // Render calendar view
            this.renderCalendarView();
            
        } catch (error) {
            console.error('Error opening calendar view:', error);
            this.showCalendarErrorState('Failed to load calendar data');
        }
    }

    showCalendarLoadingState() {
        const content = document.getElementById('calendarContent');
        content.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-3">Loading calendar events...</div>
            </div>
        `;
    }

    showCalendarErrorState(message) {
        const content = document.getElementById('calendarContent');
        content.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
                <div class="mt-2">
                    <button class="btn btn-outline-danger btn-sm" onclick="window.calendarIntegration.openCalendarView()">
                        <i class="fas fa-redo me-1"></i>Retry
                    </button>
                </div>
            </div>
        `;
    }

    async loadCalendarData() {
        try {
            const [eventsResponse, statusResponse] = await Promise.all([
                fetch('/api/calendar/events?range=week'),
                fetch('/api/external/status')
            ]);

            this.calendarData = {
                events: eventsResponse.ok ? await eventsResponse.json() : null,
                status: statusResponse.ok ? await statusResponse.json() : null
            };

        } catch (error) {
            console.error('Error loading calendar data:', error);
            throw error;
        }
    }

    renderCalendarView() {
        if (!this.calendarData) {
            this.showCalendarErrorState('No calendar data available');
            return;
        }

        const content = document.getElementById('calendarContent');
        content.innerHTML = `
            <div class="calendar-container">
                ${this.renderCalendarHeader()}
                ${this.renderCalendarControls()}
                ${this.renderCalendarEvents()}
                ${this.renderSmartScheduling()}
            </div>
        `;
    }

    renderCalendarHeader() {
        const now = new Date();
        const weekStart = new Date(now.setDate(now.getDate() - now.getDay()));
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        return `
            <div class="calendar-header mb-4">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-1">
                            <i class="fas fa-calendar-week me-2"></i>
                            Week of ${weekStart.toLocaleDateString()}
                        </h5>
                        <small class="text-muted">
                            ${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}
                        </small>
                    </div>
                    <div>
                        <button class="btn btn-outline-primary btn-sm" onclick="window.calendarIntegration.refreshCalendar()">
                            <i class="fas fa-sync-alt me-1"></i>Refresh
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderCalendarControls() {
        return `
            <div class="calendar-controls mb-4">
                <div class="row g-2">
                    <div class="col-md-4">
                        <button class="btn btn-outline-info btn-sm w-100" onclick="window.calendarIntegration.showTimeRange('day')">
                            <i class="fas fa-calendar-day me-1"></i>Today
                        </button>
                    </div>
                    <div class="col-md-4">
                        <button class="btn btn-info btn-sm w-100" onclick="window.calendarIntegration.showTimeRange('week')">
                            <i class="fas fa-calendar-week me-1"></i>This Week
                        </button>
                    </div>
                    <div class="col-md-4">
                        <button class="btn btn-outline-info btn-sm w-100" onclick="window.calendarIntegration.showTimeRange('month')">
                            <i class="fas fa-calendar me-1"></i>This Month
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderCalendarEvents() {
        const events = this.calendarData.events;
        
        if (!events || !events.events || events.events.length === 0) {
            return `
                <div class="calendar-events mb-4">
                    <h6><i class="fas fa-calendar-check me-2"></i>Upcoming Events</h6>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        No events found for this time period.
                    </div>
                </div>
            `;
        }

        // Group events by date
        const groupedEvents = this.groupEventsByDate(events.events);

        let eventsHtml = `
            <div class="calendar-events mb-4">
                <h6><i class="fas fa-calendar-check me-2"></i>Upcoming Events</h6>
        `;

        Object.entries(groupedEvents).forEach(([date, dayEvents]) => {
            const dateObj = new Date(date);
            const isToday = dateObj.toDateString() === new Date().toDateString();
            
            eventsHtml += `
                <div class="day-events mb-3">
                    <div class="day-header">
                        <h6 class="mb-2 ${isToday ? 'text-primary' : ''}">
                            <i class="fas fa-calendar-day me-2"></i>
                            ${dateObj.toLocaleDateString('en-US', { 
                                weekday: 'long', 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                            })}
                            ${isToday ? '<span class="badge bg-primary ms-2">Today</span>' : ''}
                        </h6>
                    </div>
                    <div class="day-events-list">
                        ${dayEvents.map(event => this.renderEventCard(event)).join('')}
                    </div>
                </div>
            `;
        });

        eventsHtml += '</div>';
        return eventsHtml;
    }

    renderEventCard(event) {
        const startTime = new Date(event.start_time);
        const endTime = new Date(event.end_time);
        const duration = Math.round((endTime - startTime) / (1000 * 60)); // minutes

        return `
            <div class="event-card">
                <div class="event-time-info">
                    <div class="event-time">
                        <i class="fas fa-clock me-2"></i>
                        ${startTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})} - 
                        ${endTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                    </div>
                    <small class="text-muted">${duration} minutes</small>
                </div>
                <div class="event-details">
                    <div class="event-title">${this.escapeHtml(event.title)}</div>
                    ${event.description ? `<div class="event-description">${this.escapeHtml(event.description)}</div>` : ''}
                    ${event.location ? `
                        <div class="event-location">
                            <i class="fas fa-map-marker-alt me-1"></i>
                            ${this.escapeHtml(event.location)}
                        </div>
                    ` : ''}
                    ${event.attendees && event.attendees.length > 0 ? `
                        <div class="event-attendees">
                            <i class="fas fa-users me-1"></i>
                            ${event.attendees.length} attendee${event.attendees.length > 1 ? 's' : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="event-actions">
                    <button class="btn btn-outline-info btn-sm" onclick="window.calendarIntegration.analyzeEvent('${event.id}')">
                        <i class="fas fa-chart-line me-1"></i>Analyze
                    </button>
                </div>
            </div>
        `;
    }

    renderSmartScheduling() {
        return `
            <div class="smart-scheduling">
                <h6><i class="fas fa-magic me-2"></i>Smart Scheduling</h6>
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="scheduling-card">
                            <div class="card-header">
                                <i class="fas fa-search me-2"></i>
                                Find Optimal Time
                            </div>
                            <div class="card-body">
                                <form id="findTimeForm">
                                    <div class="mb-3">
                                        <label class="form-label">Task/Meeting</label>
                                        <input type="text" class="form-control" id="taskName" placeholder="e.g., Team meeting">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Duration (minutes)</label>
                                        <select class="form-select" id="taskDuration">
                                            <option value="30">30 minutes</option>
                                            <option value="60" selected>1 hour</option>
                                            <option value="90">1.5 hours</option>
                                            <option value="120">2 hours</option>
                                        </select>
                                    </div>
                                    <button type="button" class="btn btn-primary btn-sm w-100" onclick="window.calendarIntegration.findOptimalTime()">
                                        <i class="fas fa-search me-1"></i>Find Best Time
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="scheduling-card">
                            <div class="card-header">
                                <i class="fas fa-cogs me-2"></i>
                                Schedule Optimization
                            </div>
                            <div class="card-body">
                                <p class="small text-muted mb-3">
                                    Let AI optimize your schedule for maximum productivity.
                                </p>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-outline-success btn-sm" onclick="window.calendarIntegration.optimizeSchedule()">
                                        <i class="fas fa-magic me-1"></i>Optimize Week
                                    </button>
                                    <button class="btn btn-outline-info btn-sm" onclick="window.calendarIntegration.detectConflicts()">
                                        <i class="fas fa-exclamation-triangle me-1"></i>Check Conflicts
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    groupEventsByDate(events) {
        const grouped = {};
        
        events.forEach(event => {
            const date = new Date(event.start_time).toDateString();
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(event);
        });

        // Sort events within each day by start time
        Object.keys(grouped).forEach(date => {
            grouped[date].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        });

        return grouped;
    }

    showSetupModal() {
        const setupContent = document.getElementById('calendarSetupContent');
        setupContent.innerHTML = `
            <div class="setup-container">
                <div class="setup-intro mb-4">
                    <div class="text-center mb-3">
                        <i class="fas fa-calendar-plus text-primary" style="font-size: 3rem;"></i>
                    </div>
                    <h5 class="text-center mb-3">Connect Your Calendar</h5>
                    <p class="text-muted text-center">
                        Integrate your calendar to enable smart scheduling, conflict detection, 
                        and AI-powered time optimization.
                    </p>
                </div>

                <div class="provider-selection">
                    <h6 class="mb-3">Choose your calendar provider:</h6>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="provider-card" onclick="window.calendarIntegration.selectProvider('google')">
                                <div class="provider-icon">
                                    <i class="fab fa-google"></i>
                                </div>
                                <div class="provider-info">
                                    <div class="provider-name">Google Calendar</div>
                                    <div class="provider-description">Connect your Google Calendar account</div>
                                </div>
                                <div class="provider-status">
                                    <i class="fas fa-arrow-right"></i>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="provider-card" onclick="window.calendarIntegration.selectProvider('outlook')">
                                <div class="provider-icon">
                                    <i class="fab fa-microsoft"></i>
                                </div>
                                <div class="provider-info">
                                    <div class="provider-name">Microsoft Outlook</div>
                                    <div class="provider-description">Connect your Outlook calendar</div>
                                </div>
                                <div class="provider-status">
                                    <i class="fas fa-arrow-right"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="setup-benefits mt-4">
                    <h6 class="mb-3">Benefits of calendar integration:</h6>
                    <div class="row g-2">
                        <div class="col-md-6">
                            <div class="benefit-item">
                                <i class="fas fa-magic text-info me-2"></i>
                                Smart scheduling suggestions
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="benefit-item">
                                <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                                Automatic conflict detection
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="benefit-item">
                                <i class="fas fa-chart-line text-success me-2"></i>
                                Productivity optimization
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="benefit-item">
                                <i class="fas fa-brain text-primary me-2"></i>
                                AI-powered insights
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.setupModal.show();
    }

    selectProvider(provider) {
        // For demo purposes, show OAuth simulation
        const setupContent = document.getElementById('calendarSetupContent');
        setupContent.innerHTML = `
            <div class="oauth-simulation">
                <div class="text-center mb-4">
                    <i class="fab fa-${provider === 'google' ? 'google' : 'microsoft'} text-primary" style="font-size: 3rem;"></i>
                    <h5 class="mt-3">Connect ${provider === 'google' ? 'Google' : 'Microsoft'} Calendar</h5>
                </div>

                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Demo Mode:</strong> In a production environment, this would redirect you to 
                    ${provider === 'google' ? 'Google' : 'Microsoft'}'s OAuth authorization page.
                </div>

                <div class="oauth-form">
                    <h6 class="mb-3">OAuth Configuration</h6>
                    <form id="oauthForm">
                        <div class="mb-3">
                            <label class="form-label">Client ID</label>
                            <input type="text" class="form-control" id="clientId" 
                                   placeholder="Enter your ${provider} OAuth Client ID">
                            <small class="text-muted">
                                Get this from your ${provider === 'google' ? 'Google Cloud Console' : 'Azure App Registration'}
                            </small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Client Secret</label>
                            <input type="password" class="form-control" id="clientSecret" 
                                   placeholder="Enter your OAuth Client Secret">
                        </div>
                        ${provider === 'outlook' ? `
                            <div class="mb-3">
                                <label class="form-label">Tenant ID</label>
                                <input type="text" class="form-control" id="tenantId" 
                                       placeholder="Enter your Azure Tenant ID">
                            </div>
                        ` : ''}
                        <div class="d-grid gap-2">
                            <button type="button" class="btn btn-primary" onclick="window.calendarIntegration.connectProvider('${provider}')">
                                <i class="fas fa-link me-1"></i>Connect Calendar
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="window.calendarIntegration.showSetupModal()">
                                <i class="fas fa-arrow-left me-1"></i>Back to Providers
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }

    async connectProvider(provider) {
        const clientId = document.getElementById('clientId').value.trim();
        const clientSecret = document.getElementById('clientSecret').value.trim();
        const tenantId = document.getElementById('tenantId')?.value.trim();

        if (!clientId || !clientSecret) {
            alert('Please enter both Client ID and Client Secret');
            return;
        }

        if (provider === 'outlook' && !tenantId) {
            alert('Please enter Tenant ID for Microsoft Outlook');
            return;
        }

        try {
            const credentials = {
                client_id: clientId,
                client_secret: clientSecret
            };

            if (provider === 'outlook') {
                credentials.tenant_id = tenantId;
            }

            const response = await fetch('/api/config/calendar-setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    provider: provider,
                    credentials: credentials
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.isConnected = true;
                this.updateConnectionStatus();
                
                // Close setup modal
                this.setupModal.hide();
                
                // Show success message
                if (window.novaApp) {
                    window.novaApp.addMessage('nova', 
                        `${provider === 'google' ? 'Google' : 'Microsoft'} Calendar connected successfully! You can now use smart scheduling features.`, 
                        'success');
                }
                
                // Open calendar view
                setTimeout(() => {
                    this.openCalendarView();
                }, 1000);
                
            } else {
                alert(result.error || 'Failed to connect calendar');
            }

        } catch (error) {
            console.error('Error connecting calendar provider:', error);
            alert('Failed to connect calendar provider');
        }
    }

    async refreshCalendar() {
        try {
            await this.loadCalendarData();
            this.renderCalendarView();
        } catch (error) {
            console.error('Error refreshing calendar:', error);
            this.showCalendarErrorState('Failed to refresh calendar data');
        }
    }

    async showTimeRange(range) {
        try {
            const response = await fetch(`/api/calendar/events?range=${range}`);
            if (response.ok) {
                this.calendarData.events = await response.json();
                this.renderCalendarView();
            }
        } catch (error) {
            console.error('Error loading time range:', error);
        }
    }

    async findOptimalTime() {
        const taskName = document.getElementById('taskName').value.trim();
        const duration = parseInt(document.getElementById('taskDuration').value);

        if (!taskName) {
            alert('Please enter a task name');
            return;
        }

        try {
            const response = await fetch('/api/calendar/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task: {
                        name: taskName,
                        duration: duration
                    },
                    preferences: {
                        default_duration: duration
                    }
                })
            });

            const result = await response.json();

            if (response.ok && window.novaApp) {
                window.novaApp.addMessage('nova', result.response, 'schedule_suggestion', result);
                
                // Clear form
                document.getElementById('taskName').value = '';
                document.getElementById('taskDuration').value = '60';
            } else {
                alert(result.error || 'Failed to find optimal time');
            }

        } catch (error) {
            console.error('Error finding optimal time:', error);
            alert('Failed to find optimal time');
        }
    }

    async optimizeSchedule() {
        try {
            if (window.novaApp) {
                window.novaApp.sendMessage('optimize schedule');
            }
        } catch (error) {
            console.error('Error optimizing schedule:', error);
        }
    }

    async detectConflicts() {
        try {
            // This would call the conflict detection API
            if (window.novaApp) {
                window.novaApp.addMessage('nova', 
                    'Analyzing your calendar for conflicts... This feature will detect overlapping events and suggest resolutions.', 
                    'info');
            }
        } catch (error) {
            console.error('Error detecting conflicts:', error);
        }
    }

    analyzeEvent(eventId) {
        if (window.novaApp) {
            window.novaApp.addMessage('nova', 
                `Analyzing event ${eventId}... This feature would provide insights about the event's impact on your productivity.`, 
                'info');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// CSS for calendar components (injected into page)
const calendarStyles = `
    <style>
        .calendar-container {
            max-height: 70vh;
            overflow-y: auto;
        }
        
        .calendar-header {
            background: var(--darker-bg);
            border-radius: 0.5rem;
            padding: 1rem;
            border: 1px solid rgba(13, 110, 253, 0.2);
        }
        
        .calendar-controls .btn {
            transition: all 0.3s ease;
        }
        
        .day-events {
            background: var(--dark-bg);
            border-radius: 0.5rem;
            padding: 1rem;
            border: 1px solid rgba(13, 110, 253, 0.2);
        }
        
        .day-header h6 {
            border-bottom: 1px solid rgba(13, 110, 253, 0.3);
            padding-bottom: 0.5rem;
        }
        
        .event-card {
            background: var(--darker-bg);
            border: 1px solid rgba(13, 110, 253, 0.2);
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 0.75rem;
            transition: all 0.3s ease;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        
        .event-card:hover {
            border-color: var(--primary-color);
            transform: translateX(5px);
            box-shadow: 0 2px 10px rgba(13, 110, 253, 0.2);
        }
        
        .event-card:last-child {
            margin-bottom: 0;
        }
        
        .event-time-info {
            flex-shrink: 0;
            margin-right: 1rem;
        }
        
        .event-time {
            font-weight: 600;
            color: var(--info-color);
            font-size: 0.9rem;
        }
        
        .event-details {
            flex-grow: 1;
        }
        
        .event-title {
            font-weight: 600;
            color: var(--bs-gray-100);
            margin-bottom: 0.25rem;
        }
        
        .event-description {
            color: var(--bs-gray-300);
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }
        
        .event-location, .event-attendees {
            color: var(--bs-gray-400);
            font-size: 0.8rem;
            margin-bottom: 0.25rem;
        }
        
        .event-actions {
            flex-shrink: 0;
        }
        
        .scheduling-card {
            background: var(--dark-bg);
            border: 1px solid rgba(13, 110, 253, 0.2);
            border-radius: 0.5rem;
            height: 100%;
        }
        
        .scheduling-card .card-header {
            background: var(--darker-bg);
            border-bottom: 1px solid rgba(13, 110, 253, 0.2);
            padding: 0.75rem 1rem;
            font-weight: 600;
            color: var(--bs-gray-100);
        }
        
        .scheduling-card .card-body {
            padding: 1rem;
        }
        
        .provider-card {
            background: var(--dark-bg);
            border: 2px solid rgba(13, 110, 253, 0.2);
            border-radius: 0.75rem;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .provider-card:hover {
            border-color: var(--primary-color);
            background: rgba(13, 110, 253, 0.05);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(13, 110, 253, 0.2);
        }
        
        .provider-icon {
            font-size: 2rem;
            margin-right: 1rem;
            color: var(--primary-color);
        }
        
        .provider-info {
            flex-grow: 1;
        }
        
        .provider-name {
            font-weight: 600;
            color: var(--bs-gray-100);
            margin-bottom: 0.25rem;
        }
        
        .provider-description {
            color: var(--bs-gray-400);
            font-size: 0.9rem;
        }
        
        .provider-status {
            color: var(--primary-color);
            font-size: 1.2rem;
        }
        
        .benefit-item {
            color: var(--bs-gray-300);
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .oauth-simulation {
            max-width: 500px;
            margin: 0 auto;
        }
        
        .oauth-form {
            background: var(--dark-bg);
            border-radius: 0.5rem;
            padding: 1.5rem;
            border: 1px solid rgba(13, 110, 253, 0.2);
        }
        
        @media (max-width: 768px) {
            .event-card {
                flex-direction: column;
            }
            
            .event-time-info {
                margin-right: 0;
                margin-bottom: 0.5rem;
            }
            
            .event-actions {
                margin-top: 0.5rem;
                align-self: flex-start;
            }
            
            .provider-card {
                text-align: center;
                flex-direction: column;
            }
            
            .provider-icon {
                margin-right: 0;
                margin-bottom: 1rem;
            }
        }
    </style>
`;

// Inject styles
if (!document.getElementById('calendar-styles')) {
    document.head.insertAdjacentHTML('beforeend', calendarStyles.replace('<style>', '<style id="calendar-styles">'));
}
