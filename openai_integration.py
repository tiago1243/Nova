import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenAIIntegration:
    """OpenAI integration for enhanced AI capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI integration initialized")
            except ImportError:
                logger.warning("OpenAI library not available")
            except Exception as e:
                logger.error(f"Error initializing OpenAI: {e}")
        else:
            logger.info("No OpenAI API key provided - using fallback responses")
    
    def enhance_response(self, context: str, user_message: str, category: str) -> Optional[str]:
        """Enhance responses using OpenAI when available"""
        if not self.client:
            return None
        
        try:
            prompt = f"""You are Nova, an intelligent AI assistant. 
            Context: {context}
            User message: {user_message}
            Category: {category}
            
            Provide a helpful, concise response that matches Nova's personality - friendly, intelligent, and proactive."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Nova, a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logger.error(f"Error enhancing response with OpenAI: {e}")
            return None
    
    def generate_summary(self, entries: list) -> Optional[str]:
        """Generate summary of memory entries"""
        if not self.client or not entries:
            return None
        
        try:
            entries_text = "\n".join([f"- {entry['category']}: {entry['text']}" for entry in entries[-10:]])
            
            prompt = f"""Analyze these recent memory entries and provide a brief summary of the user's activities and patterns:

{entries_text}

Provide insights about their productivity, focus areas, and any notable patterns."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Nova, analyzing user activity patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if OpenAI integration is available"""
        return self.client is not None
