import datetime
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from api_integrations import APIIntegrations
from smart_cache import SmartCache
from agent_core import NovaAgent

logger = logging.getLogger(__name__)

class NovaCore:
    """Enhanced Nova core with external API capabilities"""
    
    def __init__(self, openai_integration=None):
        self.memory_file = "nova_memory.json"
        self.memory_log = []
        self.awaiting_clarification = False
        self.current_entry = None
        
        # Initialize components
        self.cache = SmartCache()
        self.api_integrations = APIIntegrations(self.cache)
        self.agent = NovaAgent(self, openai_integration)
        
        # Enhanced category keywords
        self.category_keywords = {
            "task": [
                "do", "complete", "make", "build", "create", "finish", "setup", "develop",
                "design", "get done", "finish up", "carry out", "execute", "work on",
                "resolve", "fix", "implement", "write", "code", "plan", "organize"
            ],
            "idea": [
                "idea", "think", "concept", "invention", "vision", "plan", "brainstorm",
                "imagine", "suggestion", "proposal", "possibility", "consider", "dream"
            ],
            "reminder": [
                "remind", "remember", "note", "don't forget", "ping me", "set a reminder",
                "alert me", "notify me", "alarm", "prompt me"
            ],
            "note": [
                "note", "log", "write down", "record", "jot down", "memo", "capture",
                "document", "save this"
            ],
            "recurring_reminder": [
                "every", "daily", "weekly", "monthly", "annually", "each day", "each week",
                "each month", "each year", "repeat", "recur", "recurring"
            ],
            "knowledge_query": [
                "what is", "who is", "tell me about", "explain", "define", "how does",
                "when did", "where is", "why does", "search for", "look up", "find information",
                "wikipedia:", "wiki:", "search wikipedia", "look up on wikipedia"
            ],
            "weather": [
                "weather", "temperature", "forecast", "rain", "sunny", "cloudy", "storm",
                "hot", "cold", "climate", "humidity", "wind"
            ],
            "news": [
                "news", "headlines", "current events", "what's happening", "latest news",
                "breaking news", "today's news", "recent news"
            ]
        }
        
        self.load_memory()
        self.agent.start_monitoring()
        
    def load_memory(self):
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.memory_log = json.load(f)
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            self.memory_log = []
    
    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_log, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Enhanced message processing with API integration"""
        try:
            # Check for Wikipedia mode queries first (highest priority)
            if message.lower().startswith(('wikipedia:', 'wiki:')):
                # Force Wikipedia search
                query = message.split(':', 1)[1].strip()
                if query:
                    result = self.api_integrations.search_wikipedia(query)
                    if result:
                        # Log this as a knowledge query
                        self.log_entry('note', f"Asked about: {query}", [])
                        return {
                            'response': result['summary'],
                            'type': 'knowledge',
                            'data': result,
                            'should_speak': True
                        }
                    else:
                        return {
                            'response': f"I couldn't find specific information about '{query}' on Wikipedia. Try rephrasing your question or being more specific.",
                            'type': 'error'
                        }
            
            # Check for special commands
            if message.lower().startswith('show'):
                return self.handle_memory_commands(message)
            elif message.lower() == 'help':
                return self.get_help_response()
            elif message.lower() == 'clear memory':
                return self.clear_memory()
            
            # Detect category and intent
            category = self.detect_category(message)
            
            # Handle API-enhanced queries
            if category in ['knowledge_query', 'weather', 'news']:
                return self.handle_api_query(message, category)
            
            # Handle traditional memory operations
            return self.handle_memory_operation(message, category)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'response': "I encountered an error processing your message. Please try again.",
                'type': 'error'
            }
    
    def handle_api_query(self, message: str, category: str) -> Dict[str, Any]:
        """Handle queries that require external API calls"""
        try:
            if category == 'knowledge_query':
                # Use Wikipedia API for knowledge queries
                result = self.api_integrations.search_wikipedia(message)
                if result:
                    # Also log this as a note for future reference
                    self.log_entry('note', f"Asked about: {message}", [])
                    return {
                        'response': result['summary'],
                        'type': 'knowledge',
                        'source': 'Wikipedia',
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'should_speak': True
                    }
                else:
                    return {
                        'response': "I couldn't find information about that. Could you try rephrasing your question?",
                        'type': 'error'
                    }
            
            elif category == 'weather':
                # Extract location from message or use default
                location = self.extract_location(message) or "current location"
                weather_data = self.api_integrations.get_weather(location)
                
                if weather_data:
                    response = self.format_weather_response(weather_data)
                    return {
                        'response': response,
                        'type': 'weather',
                        'data': weather_data,
                        'should_speak': True
                    }
                else:
                    # Check API status to provide better error message
                    weather_status = self.api_integrations.apis['weather']['status']
                    if weather_status == 'no_key':
                        return {
                            'response': f"I'd love to get weather information for {location}, but I need a weather API key to access current conditions. You can get a free API key from OpenWeatherMap and add it to your environment variables.",
                            'type': 'error'
                        }
                    else:
                        return {
                            'response': f"I couldn't get weather information for {location}. The weather service might be temporarily unavailable.",
                            'type': 'error'
                        }
            
            elif category == 'news':
                # Get latest news
                news_data = self.api_integrations.get_news()
                
                if news_data:
                    response = self.format_news_response(news_data)
                    return {
                        'response': response,
                        'type': 'news',
                        'articles': news_data[:5],  # Top 5 articles
                        'should_speak': True
                    }
                else:
                    # Check API status to provide better error message
                    news_status = self.api_integrations.apis['news']['status']
                    if news_status == 'no_key':
                        return {
                            'response': "I'd love to get the latest news for you, but I need a news API key to access current headlines. You can get a free API key from NewsAPI and add it to your environment variables.",
                            'type': 'error'
                        }
                    else:
                        return {
                            'response': "I couldn't retrieve the latest news right now. The news service might be temporarily unavailable.",
                            'type': 'error'
                        }
            
        except Exception as e:
            logger.error(f"Error handling API query: {e}")
            return {
                'response': "I had trouble accessing external information. Please try again.",
                'type': 'error'
            }
    
    def handle_memory_operation(self, message: str, category: str) -> Dict[str, Any]:
        """Handle traditional memory operations"""
        tags = self.extract_tags(message)
        due_date = self.parse_due_date(message)
        recurring = self.extract_recurring(message)
        
        # Log the entry
        self.log_entry(category, message, tags, due_date, recurring)
        
        # Generate appropriate response
        if category == 'task':
            response = f"✓ Task logged: {message}"
            if due_date:
                response += f" (Due: {due_date})"
        elif category == 'reminder':
            response = f"🔔 Reminder set: {message}"
            if due_date:
                response += f" (On: {due_date})"
        elif category == 'idea':
            response = f"💡 Idea captured: {message}"
        elif category == 'note':
            response = f"📝 Note saved: {message}"
        elif category == 'recurring_reminder':
            response = f"🔄 Recurring reminder set: {message}"
        else:
            response = f"📋 Logged: {message}"
        
        return {
            'response': response,
            'type': 'success',
            'category': category,
            'tags': tags,
            'due_date': due_date
        }
    
    def handle_memory_commands(self, command: str) -> Dict[str, Any]:
        """Handle memory retrieval commands"""
        command_lower = command.lower()
        
        if command_lower == "show memory":
            entries = self.memory_log[-20:]  # Last 20 entries
            return {
                'response': f"Showing your recent memory ({len(entries)} entries):",
                'type': 'memory',
                'entries': entries,
                'summary': f"You have {len(self.memory_log)} total entries in memory."
            }
        
        elif command_lower.startswith("show category:"):
            category = command_lower.split(":")[-1].strip()
            entries = [e for e in self.memory_log if e['category'] == category]
            return {
                'response': f"Showing entries in category '{category}':",
                'type': 'memory',
                'entries': entries[-10:],  # Last 10 in category
                'summary': f"Found {len(entries)} entries in '{category}' category."
            }
        
        elif command_lower.startswith("show #"):
            tags = re.findall(r'#\w+', command_lower)
            entries = [e for e in self.memory_log if any(tag in e.get('tags', []) for tag in tags)]
            return {
                'response': f"Showing entries with tags {', '.join(tags)}:",
                'type': 'memory',
                'entries': entries[-10:],
                'summary': f"Found {len(entries)} entries with these tags."
            }
        
        else:
            return {
                'response': "I don't recognize that command. Try 'show memory', 'show category:task', or 'show #tag'.",
                'type': 'error'
            }
    
    def detect_category(self, text: str) -> str:
        """Enhanced category detection with API categories"""
        text_lower = text.lower()
        
        # Check for recurring reminder keywords first
        for keyword in self.category_keywords["recurring_reminder"]:
            if keyword in text_lower:
                return "recurring_reminder"
        
        # Check knowledge query patterns
        for keyword in self.category_keywords["knowledge_query"]:
            if keyword in text_lower:
                return "knowledge_query"
        
        # Check weather patterns
        for keyword in self.category_keywords["weather"]:
            if keyword in text_lower:
                return "weather"
        
        # Check news patterns
        for keyword in self.category_keywords["news"]:
            if keyword in text_lower:
                return "news"
        
        # Check other categories
        for category, keywords in self.category_keywords.items():
            if category in ["recurring_reminder", "knowledge_query", "weather", "news"]:
                continue
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return "uncategorized"
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#\w+', text)
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from weather queries"""
        # Simple location extraction - can be enhanced
        location_patterns = [
            r'in (\w+(?:\s+\w+)*)',
            r'for (\w+(?:\s+\w+)*)',
            r'at (\w+(?:\s+\w+)*)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text.lower())
            if match:
                location = match.group(1).strip()
                # Filter out common non-location words
                if location not in ['today', 'tomorrow', 'now', 'me', 'us', 'here']:
                    return location
        
        return None
    
    def parse_due_date(self, text: str) -> Optional[str]:
        """Enhanced due date parsing"""
        text = text.lower()
        now = datetime.datetime.now()
        
        # Simple relative dates
        if "today" in text:
            due = now
        elif "tomorrow" in text:
            due = now + datetime.timedelta(days=1)
        elif "day after tomorrow" in text:
            due = now + datetime.timedelta(days=2)
        elif "next week" in text:
            due = now + datetime.timedelta(weeks=1)
        elif "in " in text:
            # Try to find "in X days/hours/weeks/months"
            match = re.search(r'in (\d+) (day|days|hour|hours|week|weeks|month|months)', text)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                if "day" in unit:
                    due = now + datetime.timedelta(days=amount)
                elif "hour" in unit:
                    due = now + datetime.timedelta(hours=amount)
                elif "week" in unit:
                    due = now + datetime.timedelta(weeks=amount)
                elif "month" in unit:
                    due = now + datetime.timedelta(days=30*amount)
                else:
                    due = None
            else:
                due = None
        else:
            due = None
        
        # Extract time if present
        if due:
            time_match = re.search(r'at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                ampm = time_match.group(3)
                if ampm:
                    if ampm.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif ampm.lower() == 'am' and hour == 12:
                        hour = 0
                due = due.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if due:
            return due.strftime("%Y-%m-%d %H:%M:%S")
        return None
    
    def extract_recurring(self, text: str) -> Optional[str]:
        """Extract recurring pattern from text"""
        text_lower = text.lower()
        patterns = ['daily', 'weekly', 'monthly', 'annually']
        
        for pattern in patterns:
            if pattern in text_lower:
                return pattern
        
        match = re.search(r'every (\w+)', text_lower)
        if match:
            return f"every {match.group(1)}"
        
        return None
    
    def log_entry(self, category: str, content: str, tags: List[str], due_date: str = None, recurring: str = None):
        """Log entry to memory"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "category": category,
            "text": content,
            "tags": tags,
            "due_date": due_date
        }
        if recurring:
            entry["recurring"] = recurring
        
        self.memory_log.append(entry)
        self.save_memory()
        logger.info(f"Logged entry: {category} - {content}")
    
    def format_weather_response(self, weather_data: Dict) -> str:
        """Format weather data into readable response"""
        location = weather_data.get('location', 'your location')
        temp = weather_data.get('temperature', 'N/A')
        description = weather_data.get('description', 'N/A')
        humidity = weather_data.get('humidity', 'N/A')
        
        response = f"Weather in {location}: {temp}°C, {description}"
        if humidity != 'N/A':
            response += f", humidity {humidity}%"
        
        return response
    
    def format_news_response(self, news_data: List[Dict]) -> str:
        """Format news data into readable response"""
        if not news_data:
            return "No news available at the moment."
        
        response = "Here are the latest headlines:\n\n"
        for i, article in enumerate(news_data[:3], 1):
            title = article.get('title', 'No title')
            response += f"{i}. {title}\n"
        
        return response
    
    def get_help_response(self) -> Dict[str, Any]:
        """Get help information"""
        help_text = """Nova Commands & Capabilities:

🎯 **Task Management:**
• "Remind me to call John tomorrow at 3pm"
• "I need to finish the report by Friday #work"
• "Set a daily reminder to exercise"

💡 **Knowledge Queries:**
• "What is artificial intelligence?"
• "Tell me about quantum physics"
• "Who is Albert Einstein?"

🌤️ **Weather Information:**
• "What's the weather like today?"
• "Weather forecast for New York"
• "Is it going to rain tomorrow?"

📰 **News & Current Events:**
• "What's in the news today?"
• "Show me latest headlines"
• "Current events"

🔍 **Memory Commands:**
• "show memory" - View recent entries
• "show category:task" - Filter by category
• "show #project" - Filter by tags
• "clear memory" - Clear all entries

🤖 **Agent Features:**
• Smart daily planning
• Proactive insights and suggestions
• Pattern analysis and learning
• Automated reminders and workflows

🎤 **Voice Control:**
• Click microphone for voice input
• Toggle text-to-speech on/off
• Natural voice conversations"""
        
        return {
            'response': help_text,
            'type': 'help'
        }
    
    def clear_memory(self) -> Dict[str, Any]:
        """Clear all memory"""
        self.memory_log.clear()
        self.save_memory()
        return {
            'response': "Memory cleared successfully.",
            'type': 'system'
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self.memory_log:
            return {
                'total_entries': 0,
                'categories': {},
                'recent_activity': 'No activity yet',
                'api_status': self.api_integrations.get_all_status()
            }
        
        categories = {}
        for entry in self.memory_log:
            cat = entry['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        recent_entry = self.memory_log[-1]
        recent_activity = f"Last: {recent_entry['category']} - {recent_entry['text'][:50]}..."
        
        return {
            'total_entries': len(self.memory_log),
            'categories': categories,
            'recent_activity': recent_activity,
            'api_status': self.api_integrations.get_all_status()
        }
