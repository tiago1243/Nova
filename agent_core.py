import datetime
import json
import logging
import threading
import time
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AgentAction:
    """Represents an action the agent can take"""
    action_type: str
    description: str
    target: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 5  # 1-10, 10 being highest
    scheduled_time: Optional[str] = None
    requires_approval: bool = False
    action_id: Optional[str] = None

@dataclass
class ProactiveInsight:
    """Represents a proactive insight or suggestion"""
    insight_type: str
    title: str
    description: str
    confidence: float
    timestamp: str

class NovaAgent:
    """Enhanced AI agent capabilities for Nova with API integration"""
    
    def __init__(self, nova_core, openai_integration=None):
        self.nova_core = nova_core
        self.ai = openai_integration
        self.is_active = False
        self.monitoring_thread = None
        self.agent_memory_file = "agent_memory.json"
        
        self.pending_actions = []
        self.completed_actions = []
        self.insights = []
        
        self.user_preferences = {
            "proactive_level": "medium",  # low, medium, high
            "auto_execute": False,
            "notification_frequency": "hourly",
            "work_hours": {"start": "09:00", "end": "17:00"},
            "timezone": "UTC",
            "preferred_news_topics": ["technology", "science"],
            "weather_location": "New York"
        }
        
        self.load_agent_memory()
        
    def load_agent_memory(self):
        """Load agent-specific memory and state"""
        try:
            with open(self.agent_memory_file, 'r') as f:
                data = json.load(f)
                self.pending_actions = [AgentAction(**action) for action in data.get('pending_actions', [])]
                self.completed_actions = data.get('completed_actions', [])
                self.insights = data.get('insights', [])
                self.user_preferences.update(data.get('user_preferences', {}))
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No agent memory found, starting fresh")
    
    def save_agent_memory(self):
        """Save agent state and memory"""
        try:
            data = {
                'pending_actions': [asdict(action) for action in self.pending_actions],
                'completed_actions': self.completed_actions[-100:],  # Keep last 100
                'insights': self.insights[-50:],  # Keep last 50
                'user_preferences': self.user_preferences,
                'last_updated': datetime.datetime.now().isoformat()
            }
            with open(self.agent_memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving agent memory: {e}")
    
    def start_monitoring(self):
        """Start proactive monitoring"""
        if self.is_active:
            return
        
        self.is_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Nova agent monitoring started")
    
    def stop_monitoring(self):
        """Stop proactive monitoring"""
        self.is_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Nova agent monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for proactive behavior"""
        last_check = datetime.datetime.now()
        
        while self.is_active:
            try:
                current_time = datetime.datetime.now()
                
                # Run checks every 5 minutes
                if (current_time - last_check).seconds >= 300:
                    self._perform_proactive_checks()
                    last_check = current_time
                
                # Sleep for 60 seconds before next iteration
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _perform_proactive_checks(self):
        """Perform proactive analysis and generate insights"""
        try:
            # Check for overdue items
            self._check_overdue_items()
            
            # Generate API-enhanced insights
            self._generate_enhanced_insights()
            
            # Check for daily briefing opportunity
            self._check_daily_briefing()
            
        except Exception as e:
            logger.error(f"Error in proactive checks: {e}")
    
    def _check_overdue_items(self):
        """Check for overdue tasks and reminders"""
        current_time = datetime.datetime.now()
        overdue_items = []
        
        for entry in self.nova_core.memory_log:
            if entry.get('due_date'):
                try:
                    due_date = datetime.datetime.strptime(entry['due_date'], "%Y-%m-%d %H:%M:%S")
                    if due_date < current_time and entry['category'] in ['task', 'reminder']:
                        overdue_items.append(entry)
                except ValueError:
                    continue
        
        if overdue_items:
            action = AgentAction(
                action_type="notification",
                description=f"You have {len(overdue_items)} overdue items",
                parameters={"items": overdue_items, "type": "overdue"},
                priority=8,
                action_id=f"overdue_{int(time.time())}"
            )
            self.add_pending_action(action)
    
    def _generate_enhanced_insights(self):
        """Generate insights enhanced with API data"""
        current_time = datetime.datetime.now()
        
        # Morning insights with weather and news
        if current_time.hour == 8 and len(self.insights) == 0:  # Once per day
            weather_data = self.nova_core.api_integrations.get_weather(
                self.user_preferences.get('weather_location', 'New York')
            )
            
            insight_text = "Good morning! "
            if weather_data:
                insight_text += f"Today's weather: {weather_data['temperature']}°C, {weather_data['description']}. "
            
            # Add task suggestions
            today_tasks = self._get_today_tasks()
            if today_tasks:
                insight_text += f"You have {len(today_tasks)} tasks scheduled for today."
            else:
                insight_text += "No tasks scheduled - great time for planning!"
            
            insight = ProactiveInsight(
                insight_type="daily_briefing",
                title="Morning Briefing",
                description=insight_text,
                confidence=0.9,
                timestamp=current_time.isoformat()
            )
            self.insights.append(asdict(insight))
    
    def _check_daily_briefing(self):
        """Check if user might want a daily briefing"""
        current_time = datetime.datetime.now()
        
        # Suggest daily briefing in the morning
        if current_time.hour == 9 and current_time.minute < 5:
            action = AgentAction(
                action_type="suggestion",
                description="Would you like your daily briefing with weather, news, and task overview?",
                parameters={"type": "daily_briefing"},
                priority=6,
                action_id=f"briefing_{int(time.time())}"
            )
            self.add_pending_action(action)
    
    def _get_today_tasks(self) -> List[Dict]:
        """Get tasks due today"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return [
            entry for entry in self.nova_core.memory_log
            if entry.get('due_date', '').startswith(today) and entry['category'] == 'task'
        ]
    
    def add_pending_action(self, action: AgentAction):
        """Add a pending action"""
        # Avoid duplicates
        for existing in self.pending_actions:
            if existing.action_type == action.action_type and existing.description == action.description:
                return
        
        self.pending_actions.append(action)
        self.save_agent_memory()
        logger.info(f"Added pending action: {action.description}")
    
    def execute_action(self, action_id: str) -> Dict[str, Any]:
        """Execute a specific action"""
        try:
            action = None
            for a in self.pending_actions:
                if a.action_id == action_id:
                    action = a
                    break
            
            if not action:
                return {'error': 'Action not found'}
            
            # Execute based on action type
            if action.action_type == "suggestion" and (action.parameters or {}).get("type") == "daily_briefing":
                result = self.generate_daily_briefing()
            else:
                result = {'response': f'Executed: {action.description}'}
            
            # Move to completed actions
            self.pending_actions.remove(action)
            self.completed_actions.append({
                'action': asdict(action),
                'executed_at': datetime.datetime.now().isoformat(),
                'result': result
            })
            self.save_agent_memory()
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action {action_id}: {e}")
            return {'error': 'Failed to execute action'}
    
    def generate_daily_plan(self) -> Dict[str, Any]:
        """Generate AI-enhanced daily plan"""
        try:
            current_time = datetime.datetime.now()
            today_str = current_time.strftime("%Y-%m-%d")
            
            # Get today's tasks and overdue items
            today_tasks = self._get_today_tasks()
            overdue_tasks = []
            
            for entry in self.nova_core.memory_log:
                if entry.get('due_date') and entry['category'] == 'task':
                    try:
                        due_date = datetime.datetime.strptime(entry['due_date'], "%Y-%m-%d %H:%M:%S")
                        if due_date < current_time:
                            overdue_tasks.append(entry)
                    except ValueError:
                        continue
            
            # Get weather for planning
            weather_data = self.nova_core.api_integrations.get_weather(
                self.user_preferences.get('weather_location', 'New York')
            )
            
            plan = {
                'date': today_str,
                'weather': weather_data,
                'priority_tasks': today_tasks,
                'overdue_items': overdue_tasks,
                'suggestions': [],
                'time_blocks': self._generate_time_blocks(today_tasks)
            }
            
            # Add contextual suggestions
            if weather_data and weather_data.get('temperature', 0) > 25:
                plan['suggestions'].append("Perfect weather for outdoor activities!")
            
            if not today_tasks:
                plan['suggestions'].append("No scheduled tasks - consider planning some goals for today.")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating daily plan: {e}")
            return {'error': 'Could not generate daily plan'}
    
    def generate_daily_briefing(self) -> Dict[str, Any]:
        """Generate comprehensive daily briefing"""
        try:
            # Get weather
            weather_data = self.nova_core.api_integrations.get_weather(
                self.user_preferences.get('weather_location', 'New York')
            )
            
            # Get news
            news_data = self.nova_core.api_integrations.get_news()
            
            # Get tasks for today
            today_tasks = self._get_today_tasks()
            
            briefing = {
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'weather': weather_data,
                'news_headlines': news_data[:3] if news_data else [],
                'tasks_today': today_tasks,
                'insights': self.insights[-3:] if self.insights else []
            }
            
            # Generate briefing text
            briefing_text = "Here's your daily briefing:\n\n"
            
            if weather_data:
                briefing_text += f"🌤️ Weather: {weather_data['temperature']}°C, {weather_data['description']}\n\n"
            
            if news_data:
                briefing_text += "📰 Top Headlines:\n"
                for i, article in enumerate(news_data[:3], 1):
                    briefing_text += f"{i}. {article['title']}\n"
                briefing_text += "\n"
            
            if today_tasks:
                briefing_text += f"📋 You have {len(today_tasks)} tasks scheduled for today\n\n"
            else:
                briefing_text += "📋 No tasks scheduled - perfect for spontaneous productivity!\n\n"
            
            briefing_text += "Have a great day! 🚀"
            
            return {
                'response': briefing_text,
                'type': 'daily_briefing',
                'data': briefing
            }
            
        except Exception as e:
            logger.error(f"Error generating daily briefing: {e}")
            return {'error': 'Could not generate briefing'}
    
    def _generate_time_blocks(self, tasks: List[Dict]) -> List[Dict]:
        """Generate suggested time blocks for tasks"""
        time_blocks = []
        current_hour = datetime.datetime.now().hour
        
        # Start from next available hour
        start_hour = max(current_hour + 1, 9)  # Don't start before 9 AM
        
        for i, task in enumerate(tasks):
            if start_hour + i < 18:  # Don't schedule past 6 PM
                time_blocks.append({
                    'time': f"{start_hour + i}:00",
                    'task': task['text'],
                    'duration': '1 hour',
                    'priority': task.get('priority', 'medium')
                })
        
        return time_blocks
    
    def get_recent_insights(self) -> List[Dict]:
        """Get recent insights"""
        return self.insights[-10:] if self.insights else []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'is_active': self.is_active,
            'pending_actions': len(self.pending_actions),
            'recent_insights': len(self.insights),
            'actions': [asdict(action) for action in self.pending_actions],
            'api_status': self.nova_core.api_integrations.get_all_status()
        }
