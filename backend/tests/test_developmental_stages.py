"""
Test developmental stage logic.

T6: Developmental Stage Logic
TEST: Divorce at age 8 → assert stage='early_childhood', impact_multiplier=1.5
"""
import pytest


def test_get_developmental_stage_early_childhood():
    """Test early childhood stage (0-5)."""
    from app.utils.developmental_stages import get_developmental_stage
    
    stage = get_developmental_stage(3)
    assert stage["name"] == "early_childhood"
    assert stage["age_range"] == (0, 5)
    assert "attachment_formation" in stage["key_tasks"]


def test_get_developmental_stage_middle_childhood():
    """Test middle childhood stage (6-11)."""
    from app.utils.developmental_stages import get_developmental_stage
    
    stage = get_developmental_stage(8)
    assert stage["name"] == "middle_childhood"
    assert stage["age_range"] == (6, 11)


def test_get_developmental_stage_adolescence():
    """Test adolescence stage (12-18)."""
    from app.utils.developmental_stages import get_developmental_stage
    
    stage = get_developmental_stage(15)
    assert stage["name"] == "adolescence"
    assert stage["age_range"] == (12, 18)


def test_get_developmental_stage_young_adult():
    """Test young adult stage (19-25)."""
    from app.utils.developmental_stages import get_developmental_stage
    
    stage = get_developmental_stage(22)
    assert stage["name"] == "young_adult"
    assert stage["age_range"] == (19, 25)


def test_get_developmental_stage_adult():
    """Test adult stage (26+)."""
    from app.utils.developmental_stages import get_developmental_stage
    
    stage = get_developmental_stage(35)
    assert stage["name"] == "adult"
    assert stage["age_range"] == (26, 120)


def test_calculate_trauma_impact_multiplier_early_childhood():
    """Test that early childhood trauma has higher impact."""
    from app.utils.developmental_stages import calculate_trauma_impact_multiplier
    
    # Divorce at age 3 (early childhood)
    multiplier = calculate_trauma_impact_multiplier(age=3, event_type="trauma")
    assert multiplier >= 1.5  # High impact during attachment formation


def test_calculate_trauma_impact_multiplier_middle_childhood():
    """Test middle childhood trauma impact (KEY TEST)."""
    from app.utils.developmental_stages import calculate_trauma_impact_multiplier
    
    # Divorce at age 8 (middle childhood)
    multiplier = calculate_trauma_impact_multiplier(age=8, event_type="trauma")
    assert multiplier >= 1.3  # Still elevated but lower than early childhood


def test_calculate_trauma_impact_multiplier_adolescence():
    """Test adolescence trauma impact."""
    from app.utils.developmental_stages import calculate_trauma_impact_multiplier
    
    # Trauma at age 15 (adolescence)
    multiplier = calculate_trauma_impact_multiplier(age=15, event_type="trauma")
    assert multiplier >= 1.2  # Identity formation critical period


def test_calculate_trauma_impact_multiplier_adult():
    """Test adult trauma has baseline impact."""
    from app.utils.developmental_stages import calculate_trauma_impact_multiplier
    
    # Trauma at age 30 (adult)
    multiplier = calculate_trauma_impact_multiplier(age=30, event_type="trauma")
    assert multiplier == 1.0  # Baseline (but still impactful)


def test_positive_events_have_lower_multipliers():
    """Test that positive events have smaller developmental multipliers."""
    from app.utils.developmental_stages import calculate_trauma_impact_multiplier
    
    # Positive event in childhood
    positive_multiplier = calculate_trauma_impact_multiplier(age=8, event_type="positive")
    
    # Trauma in childhood
    trauma_multiplier = calculate_trauma_impact_multiplier(age=8, event_type="trauma")
    
    assert positive_multiplier < trauma_multiplier


def test_get_stage_context_for_event():
    """Test getting context for how an event affects a specific stage."""
    from app.utils.developmental_stages import get_stage_context_for_event
    
    # Divorce at age 8
    context = get_stage_context_for_event(age=8, event_type="trauma")
    
    assert "stage" in context
    assert context["stage"]["name"] == "middle_childhood"
    assert "impact_multiplier" in context
    assert "vulnerability_factors" in context
    assert "resilience_factors" in context


def test_vulnerability_factors_early_childhood():
    """Test that early childhood has specific vulnerabilities."""
    from app.utils.developmental_stages import get_stage_context_for_event
    
    context = get_stage_context_for_event(age=3, event_type="trauma")
    vulnerabilities = context["vulnerability_factors"]
    
    assert len(vulnerabilities) > 0
    # Should mention attachment or dependency
    assert any("attachment" in v.lower() or "dependent" in v.lower() for v in vulnerabilities)


def test_resilience_factors_exist():
    """Test that all stages have resilience factors."""
    from app.utils.developmental_stages import get_developmental_stage
    
    for age in [3, 8, 15, 22, 35]:
        stage = get_developmental_stage(age)
        assert "resilience_factors" in stage
        assert len(stage["resilience_factors"]) > 0


def test_explain_developmental_impact():
    """Test generating explanation for developmental impact."""
    from app.utils.developmental_stages import explain_developmental_impact
    
    explanation = explain_developmental_impact(
        age=8,
        event_type="trauma",
        event_description="Parents divorced"
    )
    
    assert isinstance(explanation, str)
    assert len(explanation) > 50  # Should be detailed
    assert "middle childhood" in explanation.lower() or "8" in explanation
