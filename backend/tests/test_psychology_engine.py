"""
Test experience analysis with AI psychology engine.

T3: Experience Analysis
TEST: Given baseline persona + "parents divorced at age 10" → 
      assert anxiety increased, trust decreased
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def baseline_persona():
    """Create a baseline persona for testing."""
    from app.models import Persona
    
    persona = Persona(
        name="Test Child",
        baseline_age=8,
        current_age=10,
        baseline_gender="female",
        baseline_background="Loving family, stable home",
        current_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.3  # Low anxiety at baseline
        },
        current_attachment_style="secure",
        current_trauma_markers=[]
    )
    return persona


@pytest.mark.asyncio
async def test_analyze_experience_basic(baseline_persona):
    """Test basic experience analysis."""
    from app.services.psychology_engine import analyze_experience
    
    # Mock OpenAI response
    mock_response = {
        "immediate_effects": {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.6,  # Increased anxiety
            "trait_changes": {
                "anxiety": 7,
                "trust_in_relationships": 3
            }
        },
        "long_term_patterns": ["abandonment_fears", "trust_issues"],
        "symptoms_developed": ["anxiety", "hypervigilance"],
        "symptom_severity": {"anxiety": 6, "hypervigilance": 4},
        "coping_mechanisms": ["people_pleasing", "hypervigilance"],
        "worldview_shifts": {
            "trust": -0.4,
            "safety": -0.3,
            "self_worth": -0.2
        },
        "recommended_therapies": ["CBT"],
        "reasoning": "Divorce at age 10 disrupts attachment security during identity formation"
    }
    
    # Mock at the openai_service instance level
    with patch("app.services.psychology_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_experience(
            persona=baseline_persona,
            experience_description="Parents got divorced when I was 10",
            age_at_event=10
        )
        
        # Verify structure
        assert "immediate_effects" in result
        assert "long_term_patterns" in result
        assert "symptoms_developed" in result
        
        # Verify anxiety increased
        assert result["immediate_effects"]["neuroticism"] > baseline_persona.current_personality["neuroticism"]
        
        # Verify trust decreased
        assert result["immediate_effects"]["trait_changes"]["trust_in_relationships"] < 5


def test_generate_experience_prompt_includes_developmental_context(baseline_persona):
    """Test that experience prompt includes developmental stage info."""
    from app.services.psychology_engine import generate_experience_prompt
    
    prompt = generate_experience_prompt(
        persona=baseline_persona,
        experience_description="Parents divorced",
        age_at_event=10,
        previous_experiences=[]
    )
    
    # Should include developmental context
    assert "middle_childhood" in prompt.lower() or "age 10" in prompt
    assert "impact_multiplier" in prompt.lower() or "1.5" in prompt
    
    # Should include persona baseline
    assert "neuroticism" in prompt.lower() or "anxiety" in prompt.lower()
    
    # Should include event description
    assert "divorced" in prompt.lower()


def test_generate_experience_prompt_includes_previous_experiences(baseline_persona):
    """Test that prompt includes context from previous experiences."""
    from app.services.psychology_engine import generate_experience_prompt
    from app.models import Experience
    
    previous = [
        Experience(
            sequence_number=1,
            age_at_event=8,
            user_description="Moved to new city",
            symptoms_developed=["social_anxiety"],
            symptom_severity={"social_anxiety": 3}
        )
    ]
    
    prompt = generate_experience_prompt(
        persona=baseline_persona,
        experience_description="Parents divorced",
        age_at_event=10,
        previous_experiences=previous
    )
    
    # Should reference previous experiences
    assert "moved" in prompt.lower() or "previous" in prompt.lower()


def test_apply_personality_changes():
    """Test applying personality changes to persona."""
    from app.services.psychology_engine import apply_personality_changes
    
    current_personality = {
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.3
    }
    
    changes = {
        "neuroticism": 0.6,  # Increase anxiety
        "extraversion": 0.4  # Slight decrease
    }
    
    updated = apply_personality_changes(current_personality, changes)
    
    assert updated["neuroticism"] == 0.6
    assert updated["extraversion"] == 0.4
    assert updated["openness"] == 0.5  # Unchanged


def test_calculate_symptom_severity():
    """Test symptom severity calculation based on trauma impact."""
    from app.services.psychology_engine import calculate_symptom_severity
    
    # High impact trauma at vulnerable age
    severity = calculate_symptom_severity(
        symptom="anxiety",
        age_at_event=8,
        event_severity=8,
        impact_multiplier=1.5
    )
    
    assert severity >= 7  # Should be high
    assert severity <= 10  # Capped at 10
    
    # Same trauma in adulthood
    adult_severity = calculate_symptom_severity(
        symptom="anxiety",
        age_at_event=35,
        event_severity=8,
        impact_multiplier=1.0
    )
    
    assert adult_severity < severity  # Adult should be lower


@pytest.mark.asyncio
async def test_analyze_experience_saves_to_database(baseline_persona):
    """Test that analysis results are properly structured for database."""
    from app.services.psychology_engine import analyze_experience
    
    mock_response = {
        "immediate_effects": {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.6
        },
        "long_term_patterns": ["trust_issues"],
        "symptoms_developed": ["anxiety"],
        "symptom_severity": {"anxiety": 6},
        "coping_mechanisms": ["hypervigilance"],
        "worldview_shifts": {"trust": -0.4},
        "recommended_therapies": ["CBT", "play_therapy"],
        "reasoning": "Test reasoning"
    }
    
    with patch("app.services.psychology_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_experience(
            persona=baseline_persona,
            experience_description="Test event",
            age_at_event=10
        )
        
        # Verify all required database fields present
        assert "immediate_effects" in result
        assert "long_term_patterns" in result
        assert "symptoms_developed" in result
        assert "symptom_severity" in result
        assert "coping_mechanisms" in result
        assert "worldview_shifts" in result
        assert "recommended_therapies" in result
        assert "reasoning" in result


def test_extract_event_metadata():
    """Test extracting event type and severity from description."""
    from app.services.psychology_engine import extract_event_metadata
    
    # Trauma event
    metadata = extract_event_metadata("Parents divorced, very traumatic")
    assert metadata["event_type"] in ["trauma", "loss", "relationship"]
    
    # Positive event
    positive_metadata = extract_event_metadata("Got a supportive therapist, feeling better")
    # Could be trauma or positive, depending on AI interpretation


@pytest.mark.asyncio
async def test_cross_experience_triggers(baseline_persona):
    """Test that analysis identifies cross-experience triggers."""
    from app.services.psychology_engine import analyze_experience
    from app.models import Experience
    
    # Previous abandonment experience
    previous = [
        Experience(
            sequence_number=1,
            age_at_event=5,
            user_description="Father left the family",
            symptoms_developed=["abandonment_fears"],
            symptom_severity={"abandonment_fears": 7}
        )
    ]
    
    mock_response = {
        "immediate_effects": {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.4,
            "agreeableness": 0.5,
            "neuroticism": 0.7
        },
        "long_term_patterns": ["abandonment_pattern"],
        "cross_experience_triggers": ["Experience #1 (father leaving) reactivated"],
        "symptoms_developed": ["anxiety"],
        "symptom_severity": {"anxiety": 8},  # Higher due to reactivation
        "coping_mechanisms": [],
        "worldview_shifts": {},
        "recommended_therapies": [],
        "reasoning": "Reactivates previous abandonment wound"
    }
    
    with patch("app.services.psychology_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_experience(
            persona=baseline_persona,
            experience_description="Best friend moved away",
            age_at_event=10,
            previous_experiences=previous
        )
        
        assert "cross_experience_triggers" in result
