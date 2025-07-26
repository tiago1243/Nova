# Nova AI Assistant

## Overview

Nova is a comprehensive AI assistant inspired by Jarvis, designed as a modular Flask web application with autonomous agent capabilities. The system combines memory management, external API integrations, smart caching, and OpenAI-powered responses to create an intelligent personal assistant that can handle tasks, reminders, ideas, and knowledge queries.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Flask architecture with clear separation of concerns and autonomous agent capabilities:

### Frontend Architecture
- **Framework**: Pure HTML/CSS/JavaScript with Bootstrap for styling
- **Interface**: Single-page chat application with responsive sidebar navigation
- **Voice Features**: Web Speech API for voice recognition and text-to-speech synthesis
- **Styling**: Bootstrap with dark theme optimized for Replit environment
- **Real-time Updates**: JavaScript-driven interface with auto-scrolling and status indicators

### Backend Architecture
- **Framework**: Flask web framework with minimal dependencies
- **Structure**: Modular design with dedicated files for specific functionalities
- **Session Management**: Flask sessions with environment-configurable secret keys
- **Proxy Support**: ProxyFix middleware for deployment compatibility
- **Logging**: Comprehensive logging throughout all components

## Key Components

### Core Framework Components

1. **app.py**: Flask application factory
   - Centralizes application creation and configuration
   - Manages environment-based secret key configuration
   - Handles circular import prevention through delayed route imports

2. **routes.py**: API endpoint management
   - Primary chat endpoint for message processing
   - Statistics and analytics endpoints
   - Error handling and response formatting

### AI and Intelligence Layer

3. **nova_core.py**: Core AI logic and memory management
   - Keyword-based categorization system for user inputs (tasks, ideas, reminders, notes)
   - Persistent JSON-based memory storage
   - Hashtag-based tagging and content filtering
   - Integration with external APIs and caching systems

4. **agent_core.py**: Autonomous agent capabilities
   - Proactive monitoring and pattern analysis
   - Action generation and scheduling system
   - User preference management and adaptive behavior
   - Background workflow orchestration

5. **openai_integration.py**: AI enhancement layer
   - Optional OpenAI API integration for enhanced responses
   - Fallback mechanisms when API is unavailable
   - Context-aware prompt engineering
   - Error handling and graceful degradation

### External Integration Layer

6. **api_integrations.py**: External service management
   - Weather API integration (OpenWeatherMap)
   - News API integration for current events
   - Wikipedia API for knowledge queries
   - Automatic API connectivity testing
   - Graceful handling of API failures

7. **smart_cache.py**: Intelligent caching system
   - File-based caching for API responses
   - Automatic expiration and cleanup
   - Performance optimization for external API calls
   - JSON-based storage with error recovery

## Data Flow

### Message Processing Flow
1. User input received through web interface or voice recognition
2. Nova core processes and categorizes the message
3. External APIs consulted if knowledge query detected
4. OpenAI enhancement applied when available
5. Response cached and returned to user
6. Agent monitors for proactive follow-up opportunities

### Memory Management Flow
1. All interactions stored in persistent JSON memory
2. Smart categorization applied automatically
3. Hashtag extraction and indexing
4. Memory statistics generated for analytics
5. Periodic cleanup and optimization

### External API Flow
1. Query type detection in nova_core
2. Cache check for recent responses
3. API call with timeout and error handling
4. Response processing and formatting
5. Cache storage for future requests
6. Fallback responses when APIs unavailable

## External Dependencies

### Required Dependencies
- **Flask**: Web framework for HTTP handling
- **Werkzeug**: WSGI utilities and proxy support

### Optional Dependencies
- **OpenAI**: Enhanced AI responses (graceful degradation without)
- **Requests**: HTTP client for external API calls

### External APIs
- **OpenWeatherMap**: Weather data and forecasts
- **NewsAPI**: Current news and headlines
- **Wikipedia**: Knowledge base and reference information

### Environment Variables
- `SESSION_SECRET`: Flask session security
- `OPENAI_API_KEY`: OpenAI integration (optional)
- `OPENWEATHER_API_KEY`: Weather API access
- `NEWS_API_KEY`: News API access

## Deployment Strategy

### Development Environment
- Flask development server with debug mode
- File-based storage for all persistent data
- Environment variable configuration
- Real-time code reloading

### Production Considerations
- WSGI server deployment (Gunicorn recommended)
- Persistent volume mounts for JSON data files
- Environment-based configuration management
- Proxy configuration for reverse proxy setups

### Data Persistence
- JSON file storage for memory, cache, and agent data
- Automatic file creation and recovery
- Regular backup through file system
- No database dependencies for simplified deployment

### Scalability Notes
- Single-instance design suitable for personal use
- File-based storage may require optimization for heavy usage
- API rate limiting considerations for external services
- Memory management for long-running sessions

The architecture prioritizes simplicity, modularity, and graceful degradation, making it suitable for personal AI assistant use cases while maintaining extensibility for future enhancements.