"""
Test intervention analysis with AI therapy efficacy engine.

T4: Intervention Analysis
TEST: Given persona with hoarding + ACT therapy → 
      assert efficacy_match > 0.8, symptoms reduced
"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def persona_with_symptoms():
    """Create a persona with existing symptoms."""
    from app.models import Persona
    
    persona = Persona(
        name="Test Person",
        baseline_age=25,
        current_age=30,
        baseline_gender="female",
        baseline_background="Experienced childhood trauma",
        current_personality={
            "openness": 0.5,
            "conscientiousness": 0.4,
            "extraversion": 0.4,
            "agreeableness": 0.5,
            "neuroticism": 0.7
        },
        current_attachment_style="insecure-anxious",
        current_trauma_markers=["hoarding", "anxiety", "avoidance"]
    )
    return persona


@pytest.mark.asyncio
async def test_analyze_intervention_high_efficacy_match(persona_with_symptoms):
    """Test intervention with high efficacy match (ACT for hoarding)."""
    from app.services.intervention_engine import analyze_intervention
    
    # Mock AI response for ACT treating hoarding
    mock_response = {
        "efficacy_match": 0.9,
        "symptom_changes": {
            "before": {"hoarding": 8, "anxiety": 6, "avoidance": 7},
            "after": {"hoarding": 4, "anxiety": 5, "avoidance": 4},
            "percentage_improvement": {"hoarding": 50, "anxiety": 17, "avoidance": 43}
        },
        "personality_changes": {
            "neuroticism": 0.6
        },
        "coping_skills_gained": [
            "mindful acceptance of discomfort",
            "values-based decision making",
            "defusion from attachment to objects"
        ],
        "sustained_effects": [
            "Behavioral changes in hoarding maintained",
            "Anxiety reduction partial (root trauma unaddressed)"
        ],
        "limitations": [
            "Does not address underlying trauma",
            "Attachment anxiety persists",
            "Requires ongoing practice"
        ],
        "reasoning": "ACT is evidence-based for hoarding through psychological flexibility"
    }
    
    with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_intervention(
            persona=persona_with_symptoms,
            therapy_type="ACT",
            duration=16,
            intensity="weekly",
            age_at_intervention=30
        )
        
        # Verify high efficacy match
        assert result["efficacy_match"] >= 0.8
        
        # Verify symptom reduction
        assert result["symptom_changes"]["after"]["hoarding"] < result["symptom_changes"]["before"]["hoarding"]


@pytest.mark.asyncio
async def test_analyze_intervention_poor_efficacy_match(persona_with_symptoms):
    """Test intervention with poor efficacy match (EMDR for hoarding)."""
    from app.services.intervention_engine import analyze_intervention
    
    # Mock AI response for EMDR treating hoarding (wrong therapy)
    mock_response = {
        "efficacy_match": 0.3,
        "symptom_changes": {
            "before": {"hoarding": 8, "anxiety": 6},
            "after": {"hoarding": 7, "anxiety": 4},
            "percentage_improvement": {"hoarding": 12, "anxiety": 33}
        },
        "personality_changes": {"neuroticism": 0.65},
        "coping_skills_gained": ["trauma processing"],
        "sustained_effects": ["Anxiety improved but hoarding persists"],
        "limitations": [
            "EMDR not designed for behavioral compulsions",
            "Hoarding requires exposure-based approaches",
            "Root trauma addressed but behavior unchanged"
        ],
        "reasoning": "EMDR reduces anxiety but doesn't target hoarding mechanism"
    }
    
    with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_intervention(
            persona=persona_with_symptoms,
            therapy_type="EMDR",
            duration=12,
            intensity="weekly",
            age_at_intervention=30
        )
        
        # Verify low efficacy match
        assert result["efficacy_match"] < 0.5
        
        # Verify hoarding barely improved
        hoarding_improvement = (
            result["symptom_changes"]["before"]["hoarding"] - 
            result["symptom_changes"]["after"]["hoarding"]
        )
        assert hoarding_improvement < 2  # Minimal improvement


def test_generate_intervention_prompt_includes_therapy_metadata(persona_with_symptoms):
    """Test that intervention prompt includes therapy database metadata."""
    from app.services.intervention_engine import generate_intervention_prompt
    
    prompt = generate_intervention_prompt(
        persona=persona_with_symptoms,
        therapy_type="ACT",
        duration=16,
        intensity="weekly",
        age_at_intervention=30
    )
    
    # Should include therapy metadata from T5
    assert "acceptance" in prompt.lower() or "commitment" in prompt.lower()
    assert "hoarding" in prompt.lower()  # ACT treats hoarding
    
    # Should include persona symptoms
    assert "anxiety" in prompt.lower() or "neuroticism" in prompt.lower()


def test_generate_intervention_prompt_includes_developmental_context(persona_with_symptoms):
    """Test that prompt includes age-appropriate context."""
    from app.services.intervention_engine import generate_intervention_prompt
    
    # Child therapy
    child_prompt = generate_intervention_prompt(
        persona=persona_with_symptoms,
        therapy_type="CBT",
        duration=12,
        intensity="weekly",
        age_at_intervention=10
    )
    
    assert "child" in child_prompt.lower() or "age 10" in child_prompt.lower()
    
    # Adult therapy
    adult_prompt = generate_intervention_prompt(
        persona=persona_with_symptoms,
        therapy_type="CBT",
        duration=12,
        intensity="weekly",
        age_at_intervention=30
    )
    
    assert "adult" in adult_prompt.lower() or "age 30" in adult_prompt.lower()


def test_calculate_baseline_efficacy_match():
    """Test baseline efficacy calculation using therapy database."""
    from app.services.intervention_engine import calculate_baseline_efficacy_match
    
    # Perfect match: hoarding → ACT
    efficacy = calculate_baseline_efficacy_match("ACT", ["hoarding", "avoidance"])
    assert efficacy > 0.7
    
    # Poor match: hoarding → EMDR
    efficacy = calculate_baseline_efficacy_match("EMDR", ["hoarding"])
    assert efficacy < 0.5
    
    # Good match: PTSD → EMDR
    efficacy = calculate_baseline_efficacy_match("EMDR", ["ptsd", "trauma"])
    assert efficacy > 0.8


def test_apply_symptom_changes():
    """Test applying symptom changes to persona."""
    from app.services.intervention_engine import apply_symptom_changes
    
    current_severity = {
        "anxiety": 8,
        "hoarding": 7,
        "depression": 6
    }
    
    changes = {
        "after": {
            "anxiety": 5,
            "hoarding": 4,
            "depression": 6
        }
    }
    
    updated = apply_symptom_changes(current_severity, changes)
    
    assert updated["anxiety"] == 5
    assert updated["hoarding"] == 4
    assert updated["depression"] == 6


@pytest.mark.asyncio
async def test_analyze_intervention_saves_to_database(persona_with_symptoms):
    """Test that analysis results are properly structured for database."""
    from app.services.intervention_engine import analyze_intervention
    
    mock_response = {
        "efficacy_match": 0.8,
        "symptom_changes": {
            "before": {"anxiety": 6},
            "after": {"anxiety": 4},
            "percentage_improvement": {"anxiety": 33}
        },
        "personality_changes": {"neuroticism": 0.6},
        "coping_skills_gained": ["skill1"],
        "sustained_effects": ["effect1"],
        "limitations": ["limitation1"],
        "reasoning": "Test reasoning"
    }
    
    with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_intervention(
            persona=persona_with_symptoms,
            therapy_type="CBT",
            duration=12,
            intensity="weekly",
            age_at_intervention=30
        )
        
        # Verify all required database fields present
        assert "efficacy_match" in result
        assert "symptom_changes" in result
        assert "personality_changes" in result
        assert "coping_skills_gained" in result
        assert "sustained_effects" in result
        assert "limitations" in result
        assert "reasoning" in result


def test_calculate_duration_impact():
    """Test that therapy duration affects efficacy."""
    from app.services.intervention_engine import calculate_duration_impact
    
    # Short duration
    short_impact = calculate_duration_impact(duration=4, recommended_duration=12)
    assert short_impact < 1.0  # Reduced efficacy
    
    # Appropriate duration
    appropriate_impact = calculate_duration_impact(duration=12, recommended_duration=12)
    assert appropriate_impact == 1.0  # Full efficacy
    
    # Extended duration
    extended_impact = calculate_duration_impact(duration=24, recommended_duration=12)
    assert extended_impact > 1.0  # Enhanced efficacy


@pytest.mark.asyncio
async def test_realistic_therapy_outcomes(persona_with_symptoms):
    """Test that therapy outcomes are realistic (not magic cures)."""
    from app.services.intervention_engine import analyze_intervention
    
    mock_response = {
        "efficacy_match": 0.9,
        "symptom_changes": {
            "before": {"hoarding": 8, "attachment_anxiety": 7},
            "after": {"hoarding": 4, "attachment_anxiety": 6},
            "percentage_improvement": {"hoarding": 50, "attachment_anxiety": 14}
        },
        "personality_changes": {"neuroticism": 0.65},
        "coping_skills_gained": ["behavioral strategies"],
        "sustained_effects": [
            "Hoarding behavior reduced significantly",
            "Underlying attachment anxiety persists - requires long-term work"
        ],
        "limitations": [
            "Behavioral change ≠ trauma resolution",
            "Root attachment wounds require deeper therapy (IFS, Psychodynamic)",
            "Maintenance requires ongoing practice"
        ],
        "reasoning": "ACT addresses symptoms not root causes"
    }
    
    with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_response
        
        result = await analyze_intervention(
            persona=persona_with_symptoms,
            therapy_type="ACT",
            duration=16,
            intensity="weekly",
            age_at_intervention=30
        )
        
        # Verify realistic: symptoms improve but don't disappear
        assert result["symptom_changes"]["after"]["hoarding"] > 0  # Not cured
        assert result["symptom_changes"]["after"]["attachment_anxiety"] > 5  # Deep wounds persist
        
        # Verify limitations acknowledged
        assert len(result["limitations"]) > 0
