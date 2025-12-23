"""
Fixed OpenAI Service - Proper Client Initialization

Replace backend/app/services/openai_service.py with this
"""
import os
from openai import AsyncOpenAI
from app.core.config import settings


class OpenAIService:
    """OpenAI API service with proper client initialization"""
    
    def __init__(self):
        # Initialize client immediately with API key from settings
        api_key = settings.openai_api_key or os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key not found in settings or environment")
        
        # Create client on initialization (not lazy)
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def chat_completion(self, messages: list, model: str = "gpt-4o-mini", **kwargs):
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: OpenAI model to use
            **kwargs: Additional parameters for chat completion
        
        Returns:
            str: Response content from the model
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI chat completion failed: {str(e)}")
    
    async def generate_narrative(self, prompt: str, model: str = "gpt-4o", max_tokens: int = 4000):
        """
        Generate long-form narrative content.
        
        Args:
            prompt: The prompt for narrative generation
            model: OpenAI model to use (gpt-4o for better quality)
            max_tokens: Maximum tokens to generate
        
        Returns:
            str: Generated narrative
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI narrative generation failed: {str(e)}")


# Create singleton instance
_openai_service = None


def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service singleton"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
