import json
import os
import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class SmartCache:
    """Simple file-based caching system for API responses"""
    
    def __init__(self, cache_file: str = "api_cache.json"):
        self.cache_file = cache_file
        self.cache_data = {}
        self.load_cache()
    
    def load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache_data = json.load(f)
                    
                # Clean expired entries on load
                self._clean_expired()
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache_data = {}
    
    def save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache_data:
            entry = self.cache_data[key]
            current_time = time.time()
            
            if current_time < entry['expires_at']:
                logger.debug(f"Cache hit for key: {key}")
                return entry['data']
            else:
                # Remove expired entry
                del self.cache_data[key]
                logger.debug(f"Cache expired for key: {key}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in cache with TTL (time to live)"""
        expires_at = time.time() + ttl_seconds
        
        self.cache_data[key] = {
            'data': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        self.save_cache()
        logger.debug(f"Cache set for key: {key}, TTL: {ttl_seconds}s")
    
    def delete(self, key: str):
        """Delete specific key from cache"""
        if key in self.cache_data:
            del self.cache_data[key]
            self.save_cache()
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self):
        """Clear all cache"""
        self.cache_data = {}
        self.save_cache()
        logger.info("Cache cleared")
    
    def _clean_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache_data.items():
            if current_time >= entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache_data[key]
        
        if expired_keys:
            self.save_cache()
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = 0
        expired_entries = 0
        
        for entry in self.cache_data.values():
            if current_time < entry['expires_at']:
                active_entries += 1
            else:
                expired_entries += 1
        
        return {
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'total_entries': len(self.cache_data)
        }
