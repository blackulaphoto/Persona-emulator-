"""
OpenAI service for GPT-4 integration with retry logic and error handling.
"""
import json
import asyncio
import logging
import os
from typing import Dict, Any, Optional
import tiktoken
import httpx
from openai import AsyncOpenAI, RateLimitError, APIError
from app.core.config import settings

logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for encoding (default: gpt-4)
        
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for GPT-4
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def truncate_to_token_limit(text: str, max_tokens: int = 8000, model: str = "gpt-4") -> str:
    """
    Truncate text to maximum token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        model: Model name for encoding
        
    Returns:
        Truncated text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from OpenAI response, handling markdown code blocks.
    
    Args:
        response: Raw response text from OpenAI
        
    Returns:
        Parsed JSON dict
        
    Raises:
        ValueError: If JSON cannot be parsed
    """
    # Remove markdown code blocks if present
    response = response.strip()
    
    # Check for ```json ... ``` pattern
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end != -1:
            response = response[start:end].strip()
    elif "```" in response:
        # Generic code block
        start = response.find("```") + 3
        end = response.find("```", start)
        if end != -1:
            response = response[start:end].strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from response: {response[:200]}")
        raise ValueError(f"Invalid JSON in response: {e}")


class OpenAIService:
    """
    Service for interacting with OpenAI GPT-4 API.
    
    Features:
    - Automatic retry with exponential backoff
    - Token counting and truncation
    - JSON response parsing
    - Error handling
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_retries: int = 5,
        base_delay: float = 1.0
    ):
        """
        Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model to use (default: gpt-4)
            max_retries: Maximum retry attempts on rate limit
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.api_key = (
            api_key
            or settings.openai_api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("OPENAI_KEY")
        )
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._client: Optional[AsyncOpenAI] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> AsyncOpenAI:
        """
        Lazily construct the OpenAI client so the service can start
        even when the API key is not configured (e.g., health checks).
        Raises a clear error when a key is required but missing.
        """
        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured. Set OPENAI_API_KEY or OPENAI_KEY.")

        if self._client is None:
            # Explicitly provide an httpx client so openai doesn't construct one with
            # legacy kwargs incompatible with httpx 0.28+ (firebase_admin pins httpx 0.28.1).
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=600.0,
                    write=600.0,
                    pool=600.0,
                ),
            )
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                http_client=self._http_client,
            )

        return self._client

    @property
    def client(self) -> AsyncOpenAI:
        """
        Provide a client attribute for callers that expect it.
        Ensures lazy initialization via _get_client.
        """
        return self._get_client()
    
    async def analyze(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Send prompt to GPT-4 and return parsed JSON response.
        
        Args:
            prompt: User prompt
            system_message: System message for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed JSON response
            
        Raises:
            RateLimitError: If max retries exceeded
            APIError: If API error occurs
            ValueError: If response is not valid JSON
        """
        client = self._get_client()

        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                
                logger.info(f"OpenAI API call successful. Tokens used: {tokens_used}")
                
                # Parse JSON from response
                result = extract_json_from_response(content)
                return result
                
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit. Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise
                    
            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise
    
    async def analyze_with_context(
        self,
        prompt: str,
        context: str,
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context_token_limit: int = 6000
    ) -> Dict[str, Any]:
        """
        Send prompt with context, automatically truncating context if needed.
        
        Args:
            prompt: User prompt
            context: Additional context (will be truncated if too long)
            system_message: System message
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            context_token_limit: Maximum tokens for context
            
        Returns:
            Parsed JSON response
        """
        # Truncate context if needed
        truncated_context = truncate_to_token_limit(context, max_tokens=context_token_limit)
        
        full_prompt = f"{truncated_context}\n\n{prompt}"
        
        return await self.analyze(
            prompt=full_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost of API call based on token usage.
        
        GPT-4 pricing (as of 2024):
        - Input: $0.03 / 1K tokens
        - Output: $0.06 / 1K tokens
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (prompt_tokens / 1000) * 0.03
        output_cost = (completion_tokens / 1000) * 0.06
        return input_cost + output_cost
