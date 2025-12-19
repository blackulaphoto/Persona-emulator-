"""
Test OpenAI service integration.

T2: OpenAI Service (Core Integration)
TEST: Mock GPT-4 response → call analyze() → assert JSON parsed correctly
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.openai_service import OpenAIService, count_tokens, extract_json_from_response


def test_count_tokens():
    """Test token counting for different texts."""
    text = "Hello, how are you today?"
    tokens = count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)
    
    # Longer text should have more tokens
    long_text = text * 10
    long_tokens = count_tokens(long_text)
    assert long_tokens > tokens


def test_extract_json_from_markdown():
    """Test extracting JSON from markdown code blocks."""
    # JSON in markdown
    response = """Here's the analysis:
```json
{
  "immediate_effects": {"anxiety": 5},
  "reasoning": "Test reasoning"
}
```
That's it!"""
    
    result = extract_json_from_response(response)
    assert result["immediate_effects"]["anxiety"] == 5
    assert result["reasoning"] == "Test reasoning"


def test_extract_json_plain():
    """Test extracting plain JSON."""
    response = '{"immediate_effects": {"anxiety": 5}, "reasoning": "Test"}'
    result = extract_json_from_response(response)
    assert result["immediate_effects"]["anxiety"] == 5


@pytest.mark.asyncio
async def test_openai_service_analyze_success():
    """Test successful OpenAI API call with mocked response."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = """
```json
{
  "immediate_effects": {
    "neuroticism": 0.6,
    "trait_changes": {"anxiety": 5}
  },
  "long_term_patterns": ["trust_issues"],
  "reasoning": "Divorce at age 10 increases anxiety"
}
```
"""
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_response.usage.total_tokens = 150
    
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance
        
        service = OpenAIService(api_key="test-key")
        result = await service.analyze(
            prompt="Test prompt",
            system_message="You are a psychologist"
        )
        
        # Verify result
        assert result["immediate_effects"]["neuroticism"] == 0.6
        assert result["immediate_effects"]["trait_changes"]["anxiety"] == 5
        assert "trust_issues" in result["long_term_patterns"]
        assert result["reasoning"] == "Divorce at age 10 increases anxiety"


@pytest.mark.asyncio
async def test_openai_service_retry_on_rate_limit():
    """Test retry logic on rate limit error."""
    from openai import RateLimitError
    
    # First call fails, second succeeds
    mock_success = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"result": "success"}'
    mock_choice.message = mock_message
    mock_success.choices = [mock_choice]
    mock_success.usage.total_tokens = 50
    
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_instance = AsyncMock()
        # First call raises error, second succeeds
        mock_instance.chat.completions.create = AsyncMock(
            side_effect=[
                RateLimitError("Rate limit exceeded", response=MagicMock(), body={}),
                mock_success
            ]
        )
        mock_client.return_value = mock_instance
        
        service = OpenAIService(api_key="test-key", max_retries=3)
        result = await service.analyze(prompt="Test", system_message="Test")
        
        assert result["result"] == "success"
        # Verify retry happened
        assert mock_instance.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_openai_service_max_retries_exceeded():
    """Test that max retries are respected."""
    from openai import RateLimitError
    
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=MagicMock(), body={})
        )
        mock_client.return_value = mock_instance
        
        service = OpenAIService(api_key="test-key", max_retries=2)
        
        with pytest.raises(RateLimitError):
            await service.analyze(prompt="Test", system_message="Test")
        
        # Should have tried 2 times
        assert mock_instance.chat.completions.create.call_count == 2


def test_truncate_to_token_limit():
    """Test truncating text to token limit."""
    from app.services.openai_service import truncate_to_token_limit
    
    long_text = "This is a test. " * 1000  # Very long text
    
    truncated = truncate_to_token_limit(long_text, max_tokens=50)
    truncated_tokens = count_tokens(truncated)
    
    assert truncated_tokens <= 50
    assert len(truncated) < len(long_text)
