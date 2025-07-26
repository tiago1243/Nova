import os
import requests
import logging
from typing import Dict, List, Optional, Any
from smart_cache import SmartCache

logger = logging.getLogger(__name__)

class APIIntegrations:
    """Handles external API integrations for Nova"""
    
    def __init__(self, cache: SmartCache):
        self.cache = cache
        
        # API configurations
        self.apis = {
            'weather': {
                'base_url': 'http://api.openweathermap.org/data/2.5',
                'api_key': os.getenv('OPENWEATHER_API_KEY', 'demo_key'),
                'status': 'unknown'
            },
            'news': {
                'base_url': 'https://newsapi.org/v2',
                'api_key': os.getenv('47cddc1ec3e94e87ab29841a1538f6fc', 'demo_key'),
                'status': 'unknown'
            },
            'wikipedia': {
                'base_url': 'https://en.wikipedia.org/api/rest_v1',
                'api_key': None,  # No key required
                'status': 'unknown'
            }
        }
        
        # Test API connectivity
        self._test_api_connectivity()
    
    def _test_api_connectivity(self):
        """Test connectivity to all APIs"""
        # Test Wikipedia (no key required)
        try:
            response = requests.get(f"{self.apis['wikipedia']['base_url']}/page/summary/Python", timeout=5)
            self.apis['wikipedia']['status'] = 'online' if response.status_code == 200 else 'offline'
        except:
            self.apis['wikipedia']['status'] = 'offline'
        
        # Test Weather API
        try:
            if self.apis['weather']['api_key'] != 'demo_key':
                response = requests.get(
                    f"{self.apis['weather']['base_url']}/weather",
                    params={'q': 'London', 'appid': self.apis['weather']['api_key']},
                    timeout=5
                )
                self.apis['weather']['status'] = 'online' if response.status_code == 200 else 'offline'
            else:
                self.apis['weather']['status'] = 'no_key'
        except:
            self.apis['weather']['status'] = 'offline'
        
        # Test News API
        try:
            if self.apis['news']['api_key'] != 'demo_key':
                response = requests.get(
                    f"{self.apis['news']['base_url']}/top-headlines",
                    params={'country': 'us', 'pageSize': 1, 'apiKey': self.apis['news']['api_key']},
                    timeout=5
                )
                self.apis['news']['status'] = 'online' if response.status_code == 200 else 'offline'
            else:
                self.apis['news']['status'] = 'no_key'
        except:
            self.apis['news']['status'] = 'offline'
    
    def search_wikipedia(self, query: str) -> Optional[Dict[str, Any]]:
        """Search Wikipedia for information"""
        try:
            # Check cache first
            cache_key = f"wiki_{query.lower().replace(' ', '_')}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Wikipedia cache hit for: {query}")
                return cached_result
            
            if self.apis['wikipedia']['status'] == 'offline':
                return None
            
            # Extract the main topic from the query
            topic = self._extract_topic_from_query(query)
            
            # Properly encode the topic for Wikipedia URL
            encoded_topic = topic.replace(' ', '_')
            
            # Search for the topic
            search_url = f"{self.apis['wikipedia']['base_url']}/page/summary/{encoded_topic}"
            
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'title': data.get('title', topic),
                    'summary': data.get('extract', 'No summary available.'),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'source': 'Wikipedia'
                }
                
                # Cache the result for 1 hour
                self.cache.set(cache_key, result, 3600)
                logger.info(f"Wikipedia search successful for: {query}")
                return result
            elif response.status_code == 404:
                # Return a simple fallback response instead of making more API calls
                return {
                    'title': query.title(),
                    'summary': f"I couldn't find specific information about '{query}' on Wikipedia. This might be a specialized topic that requires more specific search terms.",
                    'url': f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    'source': 'Wikipedia (fallback)'
                }
            else:
                logger.warning(f"Wikipedia API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return None
    
    def _extract_topic_from_query(self, query: str) -> str:
        """Extract the main topic from a natural language query"""
        # Remove common question words and phrases more carefully
        stop_words = ['what is', 'who is', 'tell me about', 'explain', 'define', 
                      'how does', 'when did', 'where is', 'why does']
        
        query_lower = query.lower().strip()
        
        # Remove stop words from the beginning of the query
        for stop_word in stop_words:
            if query_lower.startswith(stop_word):
                query_lower = query_lower[len(stop_word):].strip()
                break
        
        # Remove leading articles
        for article in ['the ', 'a ', 'an ']:
            if query_lower.startswith(article):
                query_lower = query_lower[len(article):].strip()
                break
        
        # Clean up extra spaces and return properly formatted topic
        topic = ' '.join(query_lower.split())
        
        # Capitalize first letter for Wikipedia format
        if topic:
            topic = topic[0].upper() + topic[1:]
        
        return topic if topic else query
    
    def _create_fallback_response(self, query: str, service: str) -> Dict[str, Any]:
        """Create a helpful fallback response when APIs are unavailable"""
        if service == 'wikipedia':
            return {
                'title': query.title(),
                'summary': f"I would normally search Wikipedia for information about '{query}', but the service is currently unavailable. You can search directly at https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                'url': f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                'source': 'Wikipedia (offline)'
            }
        elif service == 'weather':
            return {
                'location': query or 'your location',
                'temperature': 'N/A',
                'description': 'Weather service unavailable - please provide an API key',
                'humidity': 'N/A'
            }
        elif service == 'news':
            return []
        
        return {}
    
    def get_weather(self, location: str = "London") -> Optional[Dict[str, Any]]:
        """Get weather information for a location"""
        try:
            # Check cache first
            cache_key = f"weather_{location.lower().replace(' ', '_')}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Weather cache hit for: {location}")
                return cached_result
            
            if self.apis['weather']['status'] != 'online':
                return None
            
            url = f"{self.apis['weather']['base_url']}/weather"
            params = {
                'q': location,
                'appid': self.apis['weather']['api_key'],
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'location': data.get('name', location),
                    'temperature': round(data['main']['temp']),
                    'description': data['weather'][0]['description'].title(),
                    'humidity': data['main']['humidity'],
                    'wind_speed': data.get('wind', {}).get('speed', 0),
                    'country': data.get('sys', {}).get('country', '')
                }
                
                # Cache for 10 minutes (weather changes frequently)
                self.cache.set(cache_key, result, 600)
                logger.info(f"Weather data retrieved for: {location}")
                return result
            else:
                logger.warning(f"Weather API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return None
    
    def get_news(self, country: str = "us", category: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get latest news headlines"""
        try:
            # Check cache first
            cache_key = f"news_{country}_{category or 'general'}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"News cache hit")
                return cached_result
            
            if self.apis['news']['status'] != 'online':
                return None
            
            url = f"{self.apis['news']['base_url']}/top-headlines"
            params = {
                'country': country,
                'pageSize': 10,
                'apiKey': self.apis['news']['api_key']
            }
            
            if category:
                params['category'] = category
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', 'No title'),
                        'description': article.get('description', 'No description'),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt', '')
                    })
                
                # Cache for 15 minutes
                self.cache.set(cache_key, articles, 900)
                logger.info(f"News data retrieved: {len(articles)} articles")
                return articles
            else:
                logger.warning(f"News API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return None
    
    def get_all_status(self) -> Dict[str, str]:
        """Get status of all APIs"""
        return {
            'wikipedia': self.apis['wikipedia']['status'],
            'weather': self.apis['weather']['status'],
            'news': self.apis['news']['status']
        }
    
    def refresh_status(self):
        """Refresh API connectivity status"""
        self._test_api_connectivity()
