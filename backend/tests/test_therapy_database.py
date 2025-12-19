"""
Test therapy database.

T5: Therapy Database (Hardcoded)
TEST: Query therapy_database['ACT'] → assert best_for includes 'hoarding'
"""
import pytest


def test_therapy_database_structure():
    """Test that therapy database has correct structure."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    assert isinstance(THERAPY_MODALITIES, dict)
    assert len(THERAPY_MODALITIES) >= 8  # At least 8 modalities
    
    # Check all modalities have required fields
    for therapy_type, data in THERAPY_MODALITIES.items():
        assert "name" in data
        assert "best_for" in data
        assert "mechanism" in data
        assert "limitations" in data
        assert "typical_duration" in data
        assert isinstance(data["best_for"], list)
        assert isinstance(data["limitations"], list)


def test_act_therapy_for_hoarding():
    """Test that ACT is recommended for hoarding (key requirement)."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    act = THERAPY_MODALITIES["ACT"]
    assert "hoarding" in act["best_for"]
    assert act["name"] == "Acceptance & Commitment Therapy"


def test_emdr_for_ptsd():
    """Test that EMDR is recommended for PTSD."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    emdr = THERAPY_MODALITIES["EMDR"]
    assert "ptsd" in emdr["best_for"]
    assert "trauma" in emdr["best_for"]


def test_cbt_therapy():
    """Test CBT has correct metadata."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    cbt = THERAPY_MODALITIES["CBT"]
    assert cbt["name"] == "Cognitive Behavioral Therapy"
    assert "anxiety" in cbt["best_for"] or "depression" in cbt["best_for"]
    assert len(cbt["limitations"]) > 0


def test_ifs_for_complex_trauma():
    """Test that IFS is recommended for complex trauma."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    ifs = THERAPY_MODALITIES["IFS"]
    assert "complex_trauma" in ifs["best_for"]
    assert ifs["name"] == "Internal Family Systems"


def test_dbt_for_emotion_dysregulation():
    """Test that DBT is recommended for emotion dysregulation."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    dbt = THERAPY_MODALITIES["DBT"]
    assert "emotion_dysregulation" in dbt["best_for"]


def test_get_therapy_info_function():
    """Test helper function to get therapy info."""
    from app.utils.therapy_database import get_therapy_info
    
    act_info = get_therapy_info("ACT")
    assert act_info is not None
    assert "hoarding" in act_info["best_for"]
    
    # Test case insensitivity
    cbt_info = get_therapy_info("cbt")
    assert cbt_info is not None
    
    # Test invalid therapy
    invalid = get_therapy_info("INVALID_THERAPY")
    assert invalid is None


def test_find_therapies_for_symptom():
    """Test finding therapies that treat a specific symptom."""
    from app.utils.therapy_database import find_therapies_for_symptom
    
    # Find therapies for hoarding
    hoarding_therapies = find_therapies_for_symptom("hoarding")
    assert "ACT" in hoarding_therapies
    
    # Find therapies for PTSD
    ptsd_therapies = find_therapies_for_symptom("ptsd")
    assert "EMDR" in ptsd_therapies
    
    # Find therapies for anxiety
    anxiety_therapies = find_therapies_for_symptom("anxiety")
    assert len(anxiety_therapies) > 0


def test_calculate_therapy_match_score():
    """Test calculating match score between symptoms and therapy."""
    from app.utils.therapy_database import calculate_therapy_match_score
    
    # Perfect match: hoarding → ACT
    score = calculate_therapy_match_score("ACT", ["hoarding", "avoidance"])
    assert score > 0.7  # High match
    
    # Poor match: hoarding → EMDR (trauma-focused)
    score = calculate_therapy_match_score("EMDR", ["hoarding"])
    assert score < 0.5  # Low match
    
    # Good match: PTSD → EMDR
    score = calculate_therapy_match_score("EMDR", ["ptsd", "trauma"])
    assert score > 0.8  # Very high match


def test_all_therapies_have_unique_names():
    """Test that all therapy types have unique full names."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    names = [data["name"] for data in THERAPY_MODALITIES.values()]
    assert len(names) == len(set(names))  # No duplicates


def test_typical_duration_format():
    """Test that typical_duration is properly formatted."""
    from app.utils.therapy_database import THERAPY_MODALITIES
    
    for therapy_type, data in THERAPY_MODALITIES.items():
        duration = data["typical_duration"]
        assert isinstance(duration, str)
        assert len(duration) > 0
