"""
Test OpenAI service - OFFLINE TESTS ONLY

These tests verify code logic without external network calls.
Full integration tests require network access and will be run separately.
"""
import pytest
import json


def test_extract_json_from_markdown():
    """Test extracting JSON from markdown code blocks."""
    from app.services.openai_service import extract_json_from_response
    
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
    from app.services.openai_service import extract_json_from_response
    
    response = '{"immediate_effects": {"anxiety": 5}, "reasoning": "Test"}'
    result = extract_json_from_response(response)
    assert result["immediate_effects"]["anxiety"] == 5


def test_extract_json_with_generic_code_block():
    """Test JSON in generic code block (no 'json' label)."""
    from app.services.openai_service import extract_json_from_response
    
    response = """
```
{"test": "value", "number": 42}
```
"""
    result = extract_json_from_response(response)
    assert result["test"] == "value"
    assert result["number"] == 42


def test_extract_json_invalid_raises_error():
    """Test that invalid JSON raises ValueError."""
    from app.services.openai_service import extract_json_from_response
    
    with pytest.raises(ValueError):
        extract_json_from_response("This is not JSON at all")


def test_openai_service_initialization():
    """Test that OpenAIService can be initialized."""
    from app.services.openai_service import OpenAIService
    
    service = OpenAIService(api_key="test-key", model="gpt-4", max_retries=3)
    assert service.api_key == "test-key"
    assert service.model == "gpt-4"
    assert service.max_retries == 3


def test_cost_estimation():
    """Test cost estimation for API calls."""
    from app.services.openai_service import OpenAIService
    
    service = OpenAIService(api_key="test-key")
    
    # GPT-4 pricing: $0.03/1K input, $0.06/1K output
    cost = service.estimate_cost(prompt_tokens=1000, completion_tokens=500)
    
    expected = (1000/1000 * 0.03) + (500/1000 * 0.06)
    assert cost == expected  # $0.03 + $0.03 = $0.06
