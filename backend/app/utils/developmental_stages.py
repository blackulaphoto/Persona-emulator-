"""
Developmental Stages - Age-based trauma impact and developmental psychology.

Provides context for how life experiences affect people differently based on
their developmental stage (early childhood vs adolescence vs adulthood).
"""
from typing import Dict, List, Tuple


# Developmental stage definitions based on developmental psychology research
DEVELOPMENTAL_STAGES = {
    "early_childhood": {
        "name": "early_childhood",
        "age_range": (0, 5),
        "key_tasks": [
            "attachment_formation",
            "basic_trust_development",
            "emotional_regulation_foundation",
            "sense_of_safety"
        ],
        "vulnerability_factors": [
            "Complete dependency on caregivers",
            "Attachment patterns being formed",
            "Limited cognitive capacity to understand events",
            "No developed coping mechanisms",
            "Preverbal trauma can become somatized"
        ],
        "resilience_factors": [
            "Brain plasticity is very high",
            "Strong capacity for healing with secure attachment",
            "Present-focused (less rumination about past)",
            "Responsive to environmental changes"
        ],
        "trauma_impact_multiplier": 1.8,
        "positive_impact_multiplier": 1.4
    },
    
    "middle_childhood": {
        "name": "middle_childhood",
        "age_range": (6, 11),
        "key_tasks": [
            "identity_formation",
            "self_concept_development",
            "peer_relationships",
            "academic_competence",
            "social_skills"
        ],
        "vulnerability_factors": [
            "Self-concept still forming (trauma affects identity)",
            "Limited abstract thinking to process complex events",
            "Peer influence beginning to matter",
            "Still highly dependent on family stability",
            "Prone to self-blame for family events"
        ],
        "resilience_factors": [
            "Developing coping skills",
            "Can articulate feelings (unlike early childhood)",
            "Peer support becomes available",
            "School provides stability and structure",
            "Growing sense of agency"
        ],
        "trauma_impact_multiplier": 1.5,
        "positive_impact_multiplier": 1.3
    },
    
    "adolescence": {
        "name": "adolescence",
        "age_range": (12, 18),
        "key_tasks": [
            "identity_consolidation",
            "autonomy_development",
            "peer_belonging",
            "sexual_identity",
            "separation_from_parents"
        ],
        "vulnerability_factors": [
            "Identity in flux (trauma can derail identity formation)",
            "Peer influence at peak (social rejection highly impactful)",
            "Risk-taking behavior increases",
            "Emotional intensity and volatility",
            "Questioning authority and support systems"
        ],
        "resilience_factors": [
            "Abstract thinking allows processing",
            "Can access external support (friends, mentors)",
            "Growing independence provides options",
            "Peer support network available",
            "Emerging adult capacities"
        ],
        "trauma_impact_multiplier": 1.3,
        "positive_impact_multiplier": 1.2
    },
    
    "young_adult": {
        "name": "young_adult",
        "age_range": (19, 25),
        "key_tasks": [
            "attachment_style_crystallization",
            "career_identity",
            "intimate_relationships",
            "independence_consolidation",
            "life_direction_setting"
        ],
        "vulnerability_factors": [
            "Attachment patterns crystallizing (harder to change later)",
            "Relationship trauma affects future partnership patterns",
            "Career/identity setbacks feel catastrophic",
            "First time fully independent (fewer safety nets)",
            "Emerging adult stressors (finances, career, relationships)"
        ],
        "resilience_factors": [
            "Fully developed cognitive capacity",
            "Can actively seek therapy and support",
            "Life experience provides context",
            "Social support networks established",
            "Agency to make life changes"
        ],
        "trauma_impact_multiplier": 1.1,
        "positive_impact_multiplier": 1.1
    },
    
    "adult": {
        "name": "adult",
        "age_range": (26, 120),
        "key_tasks": [
            "pattern_maintenance_or_change",
            "generativity",
            "relationship_maintenance",
            "career_advancement",
            "meaning_making"
        ],
        "vulnerability_factors": [
            "Established patterns harder to change",
            "May have dependents (children) affected by trauma",
            "Career/financial stakes higher",
            "Less neuroplasticity than younger ages",
            "Accumulated prior trauma compounds"
        ],
        "resilience_factors": [
            "Life experience provides perspective",
            "Developed coping strategies",
            "Established support networks",
            "Resources (financial, social) for help-seeking",
            "Capacity to consciously choose change",
            "Wisdom from past experiences"
        ],
        "trauma_impact_multiplier": 1.0,
        "positive_impact_multiplier": 1.0
    }
}


def get_developmental_stage(age: int) -> Dict:
    """
    Get developmental stage information for a given age.
    
    Args:
        age: Person's age in years
        
    Returns:
        Dict with stage information (name, age_range, key_tasks, etc.)
    """
    for stage_data in DEVELOPMENTAL_STAGES.values():
        min_age, max_age = stage_data["age_range"]
        if min_age <= age <= max_age:
            return stage_data
    
    # Default to adult if outside range
    return DEVELOPMENTAL_STAGES["adult"]


def calculate_trauma_impact_multiplier(age: int, event_type: str = "trauma") -> float:
    """
    Calculate impact multiplier based on developmental stage.
    
    Younger ages have higher multipliers because:
    - Attachment patterns forming
    - Identity developing
    - Fewer coping resources
    - Greater neuroplasticity (cuts both ways)
    
    Args:
        age: Person's age when event occurred
        event_type: "trauma" or "positive" (positive events have smaller multipliers)
        
    Returns:
        Multiplier (1.0 = baseline adult impact, >1.0 = higher impact)
    """
    stage = get_developmental_stage(age)
    
    if event_type.lower() in ["positive", "achievement", "healing"]:
        return stage["positive_impact_multiplier"]
    else:
        return stage["trauma_impact_multiplier"]


def get_stage_context_for_event(age: int, event_type: str = "trauma") -> Dict:
    """
    Get comprehensive context for how an event affects someone at a specific age.
    
    Args:
        age: Person's age
        event_type: Type of event ("trauma", "positive", etc.)
        
    Returns:
        Dict with stage, impact_multiplier, vulnerability_factors, resilience_factors
    """
    stage = get_developmental_stage(age)
    multiplier = calculate_trauma_impact_multiplier(age, event_type)
    
    return {
        "stage": stage,
        "impact_multiplier": multiplier,
        "vulnerability_factors": stage["vulnerability_factors"],
        "resilience_factors": stage["resilience_factors"],
        "key_developmental_tasks": stage["key_tasks"]
    }


def explain_developmental_impact(age: int, event_type: str, event_description: str = "") -> str:
    """
    Generate human-readable explanation of developmental impact.
    
    Args:
        age: Person's age
        event_type: Type of event
        event_description: Optional description of the event
        
    Returns:
        Explanation string suitable for AI prompt context
    """
    context = get_stage_context_for_event(age, event_type)
    stage = context["stage"]
    
    explanation = f"""DEVELOPMENTAL CONTEXT (Age {age} - {stage['name'].replace('_', ' ').title()}):

Impact Multiplier: {context['impact_multiplier']}x (1.0 = adult baseline)

Key Developmental Tasks at This Age:
{chr(10).join(f'- {task.replace("_", " ").title()}' for task in stage['key_tasks'])}

Why This Age Is Particularly Vulnerable:
{chr(10).join(f'- {factor}' for factor in context['vulnerability_factors'])}

Available Resilience Factors:
{chr(10).join(f'- {factor}' for factor in context['resilience_factors'])}

Clinical Implications:
- Trauma at this age has {context['impact_multiplier']}x the impact of the same event in adulthood
- Affects core {stage['key_tasks'][0].replace('_', ' ')} development
- Requires age-appropriate interventions
"""
    
    return explanation


def get_age_appropriate_coping_capacity(age: int) -> Dict[str, any]:
    """
    Estimate age-appropriate coping capacity.
    
    Args:
        age: Person's age
        
    Returns:
        Dict with coping capacity indicators
    """
    stage = get_developmental_stage(age)
    
    # Rough estimates based on developmental psychology
    if stage["name"] == "early_childhood":
        return {
            "cognitive_processing": 0.2,  # 0.0-1.0 scale
            "emotional_regulation": 0.1,
            "social_support_access": 0.3,
            "verbal_articulation": 0.1,
            "agency": 0.1
        }
    elif stage["name"] == "middle_childhood":
        return {
            "cognitive_processing": 0.5,
            "emotional_regulation": 0.4,
            "social_support_access": 0.6,
            "verbal_articulation": 0.6,
            "agency": 0.3
        }
    elif stage["name"] == "adolescence":
        return {
            "cognitive_processing": 0.8,
            "emotional_regulation": 0.5,  # Lower due to volatility
            "social_support_access": 0.8,
            "verbal_articulation": 0.9,
            "agency": 0.6
        }
    elif stage["name"] == "young_adult":
        return {
            "cognitive_processing": 1.0,
            "emotional_regulation": 0.7,
            "social_support_access": 0.9,
            "verbal_articulation": 1.0,
            "agency": 0.9
        }
    else:  # adult
        return {
            "cognitive_processing": 1.0,
            "emotional_regulation": 0.8,
            "social_support_access": 1.0,
            "verbal_articulation": 1.0,
            "agency": 1.0
        }


def get_recommended_interventions_by_age(age: int) -> List[str]:
    """
    Get age-appropriate therapeutic interventions.
    
    Args:
        age: Person's age
        
    Returns:
        List of recommended intervention types
    """
    stage = get_developmental_stage(age)
    
    if stage["name"] == "early_childhood":
        return ["play_therapy", "parent_child_interaction_therapy", "attachment_based_family_therapy"]
    elif stage["name"] == "middle_childhood":
        return ["play_therapy", "art_therapy", "CBT_adapted_for_children", "family_therapy"]
    elif stage["name"] == "adolescence":
        return ["CBT", "DBT", "family_therapy", "group_therapy", "EMDR"]
    elif stage["name"] == "young_adult":
        return ["CBT", "ACT", "EMDR", "IFS", "DBT", "psychodynamic"]
    else:  # adult
        return ["CBT", "ACT", "EMDR", "IFS", "DBT", "psychodynamic", "somatic_experiencing"]
