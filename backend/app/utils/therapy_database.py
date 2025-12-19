"""
Therapy Database - Evidence-based therapeutic modalities.

Contains metadata for 8 major therapy types used in the Persona Evolution Simulator
to calculate efficacy matches for interventions.
"""
from typing import Dict, List, Optional


THERAPY_MODALITIES: Dict[str, Dict] = {
    "CBT": {
        "name": "Cognitive Behavioral Therapy",
        "best_for": [
            "depression",
            "anxiety",
            "negative_thought_patterns",
            "phobias",
            "panic_disorder",
            "social_anxiety"
        ],
        "mechanism": "Challenges and restructures maladaptive thoughts and beliefs through systematic cognitive reframing and behavioral experiments",
        "limitations": [
            "Does not directly address trauma memory processing",
            "Limited effectiveness for deep attachment wounds",
            "Requires cognitive capacity and insight",
            "May not address root causes in complex trauma"
        ],
        "typical_duration": "12-20 weeks",
        "evidence_base": "Extensive RCT support for anxiety and depression"
    },
    
    "ACT": {
        "name": "Acceptance & Commitment Therapy",
        "best_for": [
            "hoarding",
            "ocd",
            "chronic_pain",
            "avoidance_behaviors",
            "experiential_avoidance",
            "anxiety"
        ],
        "mechanism": "Increases psychological flexibility through acceptance of difficult thoughts/feelings while committing to values-based action",
        "limitations": [
            "Requires cognitive capacity for metaphors and exercises",
            "Less effective for acute trauma without stabilization",
            "May be challenging for highly dissociative individuals",
            "Not designed for deep trauma processing"
        ],
        "typical_duration": "8-16 weeks",
        "evidence_base": "Strong evidence for OCD, chronic pain, and behavioral avoidance"
    },
    
    "EMDR": {
        "name": "Eye Movement Desensitization & Reprocessing",
        "best_for": [
            "ptsd",
            "trauma",
            "phobias",
            "intrusive_memories",
            "single_incident_trauma",
            "panic_attacks"
        ],
        "mechanism": "Uses bilateral stimulation to facilitate reprocessing of traumatic memories, reducing emotional charge and maladaptive cognitions",
        "limitations": [
            "Not appropriate during active psychosis",
            "Requires emotional stability to process trauma",
            "Less effective for complex developmental trauma without preparation",
            "May initially increase distress before improvement"
        ],
        "typical_duration": "6-12 sessions for single trauma, longer for complex trauma",
        "evidence_base": "Gold standard for PTSD, WHO-recommended"
    },
    
    "IFS": {
        "name": "Internal Family Systems",
        "best_for": [
            "complex_trauma",
            "dissociation",
            "inner_conflict",
            "self_criticism",
            "childhood_trauma",
            "parts_work"
        ],
        "mechanism": "Works with different 'parts' of self to heal internal conflicts, access Self-energy, and unburd traumatized parts",
        "limitations": [
            "Requires introspective capacity and imagination",
            "Slower for immediate behavioral change",
            "May be abstract for concrete thinkers",
            "Requires skilled therapist for complex cases"
        ],
        "typical_duration": "6 months - 2 years",
        "evidence_base": "Growing research base, particularly strong for complex trauma and eating disorders"
    },
    
    "DBT": {
        "name": "Dialectical Behavior Therapy",
        "best_for": [
            "emotion_dysregulation",
            "bpd",
            "self_harm",
            "suicidal_ideation",
            "impulsivity",
            "relationship_instability"
        ],
        "mechanism": "Teaches distress tolerance, emotion regulation, interpersonal effectiveness, and mindfulness skills through structured program",
        "limitations": [
            "Requires commitment to skills practice and homework",
            "Intensive program may not be accessible to all",
            "May feel overly structured for some individuals",
            "Requires both individual and group components for full model"
        ],
        "typical_duration": "6 months - 1 year (structured program)",
        "evidence_base": "Gold standard for BPD, strong evidence for suicidal behaviors"
    },
    
    "Somatic_Experiencing": {
        "name": "Somatic Experiencing",
        "best_for": [
            "trauma",
            "hypervigilance",
            "chronic_anxiety",
            "nervous_system_dysregulation",
            "body_based_trauma",
            "freeze_response"
        ],
        "mechanism": "Bottom-up processing through body sensations to release trapped survival energy and restore nervous system regulation",
        "limitations": [
            "Slower progress than some approaches",
            "Requires body awareness and tolerance of sensations",
            "May be challenging for highly dissociated individuals",
            "Less research support than top-down approaches"
        ],
        "typical_duration": "Variable (months to years)",
        "evidence_base": "Moderate research support, strong clinical endorsement"
    },
    
    "Psychodynamic": {
        "name": "Psychodynamic Therapy",
        "best_for": [
            "attachment_wounds",
            "relationship_patterns",
            "insight_seeking",
            "transference_patterns",
            "unconscious_conflicts",
            "personality_patterns"
        ],
        "mechanism": "Explores unconscious patterns, early relationships, and defenses to increase insight and transform relational templates",
        "limitations": [
            "Slow behavioral change",
            "May activate defenses and resistance",
            "Requires tolerance for ambiguity and exploration",
            "Less structured than other approaches"
        ],
        "typical_duration": "1+ years (long-term)",
        "evidence_base": "Solid evidence for depression and personality disorders, particularly long-term outcomes"
    },
    
    "ERP": {
        "name": "Exposure & Response Prevention",
        "best_for": [
            "ocd",
            "specific_phobias",
            "panic_disorder",
            "contamination_fears",
            "compulsive_behaviors",
            "health_anxiety"
        ],
        "mechanism": "Gradual exposure to feared stimuli while preventing compulsive responses, leading to habituation and extinction",
        "limitations": [
            "Can be distressing during exposure exercises",
            "Not appropriate for complex trauma without preparation",
            "Requires high motivation and distress tolerance",
            "May not address underlying trauma or attachment issues"
        ],
        "typical_duration": "12-16 weeks",
        "evidence_base": "Gold standard for OCD, strong evidence for specific phobias"
    }
}


def get_therapy_info(therapy_type: str) -> Optional[Dict]:
    """
    Get information about a specific therapy type.
    
    Args:
        therapy_type: Therapy type code (e.g., "ACT", "CBT")
        
    Returns:
        Therapy information dict or None if not found
    """
    # Case-insensitive lookup
    therapy_type_upper = therapy_type.upper()
    return THERAPY_MODALITIES.get(therapy_type_upper)


def find_therapies_for_symptom(symptom: str) -> List[str]:
    """
    Find all therapies that treat a specific symptom.
    
    Args:
        symptom: Symptom to search for (e.g., "hoarding", "ptsd")
        
    Returns:
        List of therapy type codes that treat this symptom
    """
    symptom_lower = symptom.lower()
    matching_therapies = []
    
    for therapy_type, data in THERAPY_MODALITIES.items():
        if symptom_lower in data["best_for"]:
            matching_therapies.append(therapy_type)
    
    return matching_therapies


def calculate_therapy_match_score(therapy_type: str, symptoms: List[str]) -> float:
    """
    Calculate how well a therapy matches a list of symptoms.
    
    Args:
        therapy_type: Therapy type code
        symptoms: List of symptoms to match against
        
    Returns:
        Match score from 0.0 (no match) to 1.0 (perfect match)
    """
    therapy_info = get_therapy_info(therapy_type)
    if not therapy_info:
        return 0.0
    
    if not symptoms:
        return 0.0
    
    # Count how many symptoms this therapy treats
    symptoms_lower = [s.lower() for s in symptoms]
    best_for = therapy_info["best_for"]
    
    matches = sum(1 for symptom in symptoms_lower if symptom in best_for)
    
    # Score is ratio of matched symptoms to total symptoms
    match_ratio = matches / len(symptoms)
    
    # Bonus if therapy treats ANY of the symptoms (evidence-based)
    if matches > 0:
        # Base score on match ratio with generous bonus
        if match_ratio >= 0.75:
            return min(1.0, match_ratio + 0.2)
        elif match_ratio >= 0.5:
            return min(1.0, match_ratio + 0.25)  # More generous
        else:
            # Even 1 match should give a decent score
            return min(1.0, match_ratio + 0.3)
    
    return 0.0


def get_all_therapy_types() -> List[str]:
    """
    Get list of all available therapy type codes.
    
    Returns:
        List of therapy type codes
    """
    return list(THERAPY_MODALITIES.keys())


def get_all_treatable_symptoms() -> List[str]:
    """
    Get comprehensive list of all symptoms that can be treated.
    
    Returns:
        Deduplicated list of all symptoms across all therapies
    """
    all_symptoms = set()
    for data in THERAPY_MODALITIES.values():
        all_symptoms.update(data["best_for"])
    return sorted(list(all_symptoms))
