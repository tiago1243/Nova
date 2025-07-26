import os
import json
import datetime
import logging
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass, asdict
import base64
import urllib.parse

logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Represents a calendar event"""
    id: str
    title: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    is_all_day: bool = False
    calendar_id: Optional[str] = None

@dataclass
class TimeSlot:
    """Represents an available time slot"""
    start_time: str
    end_time: str
    duration_minutes: int
    confidence: float
    reason: str

class CalendarIntegration:
    """Calendar integration with Google Calendar and Outlook support"""
    
    def __init__(self):
        self.config_file = "calendar_config.json"
        self.cache_file = "calendar_cache.json"
        
        # Supported providers
        self.providers = {
            'google': {
                'name': 'Google Calendar',
                'auth_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'api_base': 'https://www.googleapis.com/calendar/v3',
                'scopes': ['https://www.googleapis.com/auth/calendar.readonly']
            },
            'outlook': {
                'name': 'Microsoft Outlook',
                'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'api_base': 'https://graph.microsoft.com/v1.0',
                'scopes': ['https://graph.microsoft.com/Calendars.Read']
            }
        }
        
        self.config = self.load_config()
        self.cache = self.load_cache()
        
        logger.info("Calendar integration initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load calendar configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return {
                'active_provider': None,
                'providers': {},
                'settings': {
                    'default_duration': 60,
                    'working_hours': {'start': '09:00', 'end': '17:00'},
                    'time_zone': 'UTC',
                    'buffer_minutes': 15
                }
            }
        except Exception as e:
            logger.error(f"Error loading calendar config: {e}")
            return {'active_provider': None, 'providers': {}, 'settings': {}}
    
    def save_config(self):
        """Save calendar configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving calendar config: {e}")
    
    def load_cache(self) -> Dict[str, Any]:
        """Load calendar cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Clean expired entries
                    current_time = datetime.datetime.now().timestamp()
                    cleaned_cache = {}
                    for key, entry in cache_data.items():
                        if entry.get('expires_at', 0) > current_time:
                            cleaned_cache[key] = entry
                    return cleaned_cache
            return {}
        except Exception as e:
            logger.error(f"Error loading calendar cache: {e}")
            return {}
    
    def save_cache(self):
        """Save calendar cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving calendar cache: {e}")
    
    def setup_provider(self, provider: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Setup calendar provider with OAuth credentials"""
        try:
            if provider not in self.providers:
                return {'error': f'Unsupported provider: {provider}'}
            
            # For demo purposes, we'll simulate OAuth setup
            # In production, this would handle the full OAuth flow
            
            if provider == 'google':
                required_fields = ['client_id', 'client_secret']
            elif provider == 'outlook':
                required_fields = ['client_id', 'client_secret', 'tenant_id']
            else:
                return {'error': 'Unknown provider'}
            
            # Validate credentials
            for field in required_fields:
                if not credentials.get(field):
                    return {'error': f'Missing {field}'}
            
            # Store credentials (in production, encrypt these)
            self.config['providers'][provider] = {
                'credentials': credentials,
                'status': 'connected',
                'connected_at': datetime.datetime.now().isoformat()
            }
            
            # Set as active provider if none set
            if not self.config['active_provider']:
                self.config['active_provider'] = provider
            
            self.save_config()
            
            return {
                'status': 'success',
                'message': f'{self.providers[provider]["name"]} connected successfully',
                'provider': provider
            }
            
        except Exception as e:
            logger.error(f"Error setting up calendar provider: {e}")
            return {'error': 'Failed to setup calendar provider'}
    
    def get_events(self, time_range: str = 'week') -> List[Dict[str, Any]]:
        """Get calendar events for specified time range"""
        try:
            if not self.config['active_provider']:
                return []
            
            # Calculate date range
            now = datetime.datetime.now()
            
            if time_range == 'day':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + datetime.timedelta(days=1)
            elif time_range == 'week':
                start_date = now - datetime.timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + datetime.timedelta(days=7)
            elif time_range == 'month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = (start_date + datetime.timedelta(days=32)).replace(day=1)
            else:
                start_date = now
                end_date = now + datetime.timedelta(days=7)
            
            # Check cache first
            cache_key = f"events_{self.config['active_provider']}_{time_range}_{start_date.date()}"
            cached_events = self.cache.get(cache_key)
            
            if cached_events and cached_events.get('expires_at', 0) > datetime.datetime.now().timestamp():
                return cached_events['data']
            
            # Fetch events from provider
            events = self._fetch_events_from_provider(start_date, end_date)
            
            # Cache events for 10 minutes
            self.cache[cache_key] = {
                'data': events,
                'expires_at': (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()
            }
            self.save_cache()
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting calendar events: {e}")
            return []
    
    def _fetch_events_from_provider(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Fetch events from the active calendar provider"""
        try:
            provider = self.config['active_provider']
            
            if provider == 'google':
                return self._fetch_google_events(start_date, end_date)
            elif provider == 'outlook':
                return self._fetch_outlook_events(start_date, end_date)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching events from provider: {e}")
            return []
    
    def _fetch_google_events(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar (simplified implementation)"""
        # In a real implementation, this would use the Google Calendar API
        # For now, return sample events for demonstration
        
        sample_events = [
            {
                'id': 'google_event_1',
                'title': 'Team Meeting',
                'start_time': (datetime.datetime.now() + datetime.timedelta(hours=2)).isoformat(),
                'end_time': (datetime.datetime.now() + datetime.timedelta(hours=3)).isoformat(),
                'description': 'Weekly team sync',
                'location': 'Conference Room A',
                'attendees': ['team@company.com'],
                'is_all_day': False,
                'calendar_id': 'primary'
            },
            {
                'id': 'google_event_2',
                'title': 'Project Review',
                'start_time': (datetime.datetime.now() + datetime.timedelta(days=1, hours=10)).isoformat(),
                'end_time': (datetime.datetime.now() + datetime.timedelta(days=1, hours=11, minutes=30)).isoformat(),
                'description': 'Quarterly project review',
                'location': 'Office 101',
                'attendees': ['manager@company.com'],
                'is_all_day': False,
                'calendar_id': 'primary'
            }
        ]
        
        return sample_events
    
    def _fetch_outlook_events(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Fetch events from Microsoft Outlook (simplified implementation)"""
        # In a real implementation, this would use Microsoft Graph API
        # For now, return sample events for demonstration
        
        sample_events = [
            {
                'id': 'outlook_event_1',
                'title': 'Client Call',
                'start_time': (datetime.datetime.now() + datetime.timedelta(hours=4)).isoformat(),
                'end_time': (datetime.datetime.now() + datetime.timedelta(hours=5)).isoformat(),
                'description': 'Discussion about project requirements',
                'location': 'Online',
                'attendees': ['client@company.com'],
                'is_all_day': False,
                'calendar_id': 'calendar'
            }
        ]
        
        return sample_events
    
    def find_optimal_slot(self, task_data: Dict[str, Any], preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Find optimal time slot for a task using ML"""
        try:
            duration_minutes = task_data.get('duration', preferences.get('default_duration', 60))
            earliest_time = preferences.get('earliest', '09:00')
            latest_time = preferences.get('latest', '17:00')
            
            # Get existing events
            events = self.get_events('week')
            
            # Find free slots
            free_slots = self._find_free_slots(events, duration_minutes, earliest_time, latest_time)
            
            if not free_slots:
                return {
                    'error': 'No suitable time slots found',
                    'suggestion': 'Consider adjusting your preferences or task duration'
                }
            
            # Score slots based on various factors
            scored_slots = self._score_time_slots(free_slots, task_data, preferences)
            
            # Return best slot
            best_slot = max(scored_slots, key=lambda x: x.confidence)
            
            return {
                'recommended_slot': asdict(best_slot),
                'alternative_slots': [asdict(slot) for slot in scored_slots[:3]],
                'total_options': len(scored_slots)
            }
            
        except Exception as e:
            logger.error(f"Error finding optimal slot: {e}")
            return {'error': 'Could not find optimal time slot'}
    
    def _find_free_slots(self, events: List[Dict], duration_minutes: int, earliest: str, latest: str) -> List[TimeSlot]:
        """Find free time slots between events"""
        free_slots = []
        
        try:
            # Convert times
            earliest_hour, earliest_min = map(int, earliest.split(':'))
            latest_hour, latest_min = map(int, latest.split(':'))
            
            # Check next 7 days
            for day_offset in range(7):
                current_date = datetime.datetime.now() + datetime.timedelta(days=day_offset)
                
                # Skip weekends if needed
                if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue
                
                # Create working day boundaries
                day_start = current_date.replace(hour=earliest_hour, minute=earliest_min, second=0, microsecond=0)
                day_end = current_date.replace(hour=latest_hour, minute=latest_min, second=0, microsecond=0)
                
                # Get events for this day
                day_events = [
                    event for event in events
                    if self._is_same_day(event['start_time'], current_date)
                ]
                
                # Sort events by start time
                day_events.sort(key=lambda x: x['start_time'])
                
                # Find gaps between events
                current_time = day_start
                
                for event in day_events:
                    event_start = datetime.datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                    
                    # Check if there's a gap before this event
                    gap_duration = (event_start - current_time).total_seconds() / 60
                    
                    if gap_duration >= duration_minutes:
                        slot_end = current_time + datetime.timedelta(minutes=duration_minutes)
                        free_slots.append(TimeSlot(
                            start_time=current_time.isoformat(),
                            end_time=slot_end.isoformat(),
                            duration_minutes=duration_minutes,
                            confidence=0.8,
                            reason="Available time between meetings"
                        ))
                    
                    # Move current time to end of this event
                    event_end = datetime.datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
                    current_time = max(current_time, event_end)
                
                # Check gap at end of day
                gap_duration = (day_end - current_time).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    slot_end = current_time + datetime.timedelta(minutes=duration_minutes)
                    free_slots.append(TimeSlot(
                        start_time=current_time.isoformat(),
                        end_time=slot_end.isoformat(),
                        duration_minutes=duration_minutes,
                        confidence=0.8,
                        reason="Available time at end of day"
                    ))
        
        except Exception as e:
            logger.error(f"Error finding free slots: {e}")
        
        return free_slots
    
    def _score_time_slots(self, slots: List[TimeSlot], task_data: Dict, preferences: Dict) -> List[TimeSlot]:
        """Score time slots based on task type and preferences"""
        for slot in slots:
            try:
                start_time = datetime.datetime.fromisoformat(slot.start_time)
                hour = start_time.hour
                
                # Base confidence
                confidence = 0.5
                
                # Time of day preferences
                if 9 <= hour <= 11:  # Morning peak
                    confidence += 0.3
                elif 14 <= hour <= 16:  # Afternoon peak
                    confidence += 0.2
                elif hour < 9 or hour > 17:  # Outside work hours
                    confidence -= 0.3
                
                # Task type considerations
                task_type = task_data.get('type', 'general')
                
                if task_type == 'creative' and 9 <= hour <= 12:
                    confidence += 0.2
                elif task_type == 'meeting' and 10 <= hour <= 16:
                    confidence += 0.2
                elif task_type == 'focus' and (9 <= hour <= 11 or 14 <= hour <= 16):
                    confidence += 0.3
                
                # Urgency factor
                if task_data.get('urgent', False):
                    # Prefer earlier slots for urgent tasks
                    days_ahead = (start_time.date() - datetime.date.today()).days
                    if days_ahead == 0:
                        confidence += 0.2
                    elif days_ahead == 1:
                        confidence += 0.1
                
                # Update slot confidence
                slot.confidence = min(1.0, confidence)
                
                # Update reason
                if slot.confidence > 0.8:
                    slot.reason = "Optimal time for this type of task"
                elif slot.confidence > 0.6:
                    slot.reason = "Good time slot available"
                else:
                    slot.reason = "Available but not ideal timing"
                    
            except Exception as e:
                logger.error(f"Error scoring time slot: {e}")
                slot.confidence = 0.5
        
        return sorted(slots, key=lambda x: x.confidence, reverse=True)
    
    def _is_same_day(self, timestamp_str: str, target_date: datetime.datetime) -> bool:
        """Check if timestamp is on the same day as target date"""
        try:
            timestamp = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp.date() == target_date.date()
        except Exception:
            return False
    
    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect calendar conflicts"""
        try:
            events = self.get_events('week')
            conflicts = []
            
            for i, event1 in enumerate(events):
                for j, event2 in enumerate(events[i+1:], i+1):
                    if self._events_overlap(event1, event2):
                        conflicts.append({
                            'event1': event1,
                            'event2': event2,
                            'conflict_type': 'overlap',
                            'suggestion': 'Consider rescheduling one of these events'
                        })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return []
    
    def _events_overlap(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events overlap"""
        try:
            start1 = datetime.datetime.fromisoformat(event1['start_time'].replace('Z', '+00:00'))
            end1 = datetime.datetime.fromisoformat(event1['end_time'].replace('Z', '+00:00'))
            start2 = datetime.datetime.fromisoformat(event2['start_time'].replace('Z', '+00:00'))
            end2 = datetime.datetime.fromisoformat(event2['end_time'].replace('Z', '+00:00'))
            
            return start1 < end2 and start2 < end1
            
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get calendar integration status"""
        return {
            'active_provider': self.config.get('active_provider'),
            'connected_providers': list(self.config.get('providers', {}).keys()),
            'supported_providers': list(self.providers.keys()),
            'settings': self.config.get('settings', {}),
            'last_sync': self._get_last_sync_time()
        }
    
    def _get_last_sync_time(self) -> Optional[str]:
        """Get last sync time from cache"""
        if self.cache:
            timestamps = []
            for entry in self.cache.values():
                if 'expires_at' in entry:
                    timestamps.append(entry['expires_at'])
            
            if timestamps:
                last_sync = max(timestamps) - 600  # Subtract cache duration
                return datetime.datetime.fromtimestamp(last_sync).isoformat()
        
        return None
    
    def get_setup_status(self) -> Dict[str, Any]:
        """Get calendar setup status"""
        return {
            'active_provider': None,
            'available_providers': ['google', 'outlook'],
            'setup_required': True,
            'status': 'not_configured'
        }
    
    def test_connection(self) -> bool:
        """Test calendar connection"""
        return False  # Not configured by default
    
    def setup_provider(self, provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Setup calendar provider"""
        return {
            'success': False,
            'message': 'Calendar setup requires OAuth configuration',
            'provider': provider
        }
