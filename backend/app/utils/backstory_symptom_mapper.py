"""
Backstory Symptom Mapper

Analyzes persona backstory text to identify initial disorders and symptoms
BEFORE any experiences are added.

This ensures "Current Symptoms" box is populated immediately upon persona creation.
"""

from typing import Dict, List, Tuple
import re


def analyze_backstory_for_symptoms(
    backstory: str,
    baseline_age: int
) -> List[Dict]:
    """
    Analyze backstory text and return initial disorders/symptoms.

    Args:
        backstory: The baseline_background text from persona creation
        baseline_age: Age when persona is created

    Returns:
        List of dicts with {disorder_name, severity, category, symptom_details}
    """
    if not backstory:
        return []

    backstory_lower = backstory.lower()
    initial_symptoms = []

    # ========================================
    # SUBSTANCE USE IN CAREGIVERS
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "meth", "methamphetamine", "heroin", "cocaine", "crack",
        "drug addict", "alcoholic", "drinking", "drunk",
        "substance abuse", "drug use", "overdose"
    ]):
        # Attachment disorder - CRITICAL for children with addicted parents
        if baseline_age <= 12:
            initial_symptoms.append({
                "disorder_name": "reactive_attachment_disorder",
                "severity": 0.75,
                "category": "Trauma and Stress-Related Disorders",
                "symptom_details": {
                    "emotional_withdrawal": 0.8,
                    "minimal_social_responsiveness": 0.7,
                    "limited_positive_affect": 0.75,
                    "unexplained_irritability": 0.7
                },
                "onset_age": baseline_age
            })

        # Complex PTSD from chaotic environment
        initial_symptoms.append({
            "disorder_name": "complex_ptsd",
            "severity": 0.65,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "hypervigilance": 0.8,
                "emotional_dysregulation": 0.7,
                "negative_self_concept": 0.6,
                "relationship_difficulties": 0.7
            },
            "onset_age": baseline_age
        })

        # Generalized anxiety from unpredictability
        initial_symptoms.append({
            "disorder_name": "generalized_anxiety",
            "severity": 0.6,
            "category": "Anxiety Disorders",
            "symptom_details": {
                "excessive_worry": 0.75,
                "restlessness": 0.65,
                "difficulty_concentrating": 0.6,
                "sleep_disturbance": 0.7
            },
            "onset_age": baseline_age
        })

    # ========================================
    # SEXUAL ABUSE / MOLESTATION
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "molest", "sexual abuse", "raped", "assault", "fondled",
        "inappropriate touch", "sexually abused"
    ]):
        # PTSD - PRIMARY diagnosis for sexual trauma
        initial_symptoms.append({
            "disorder_name": "ptsd",
            "severity": 0.85,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "intrusive_memories": 0.9,
                "avoidance": 0.8,
                "negative_alterations_in_cognition": 0.75,
                "hyperarousal": 0.85
            },
            "onset_age": baseline_age
        })

        # Complex PTSD for chronic/multiple incidents
        initial_symptoms.append({
            "disorder_name": "complex_ptsd",
            "severity": 0.8,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "affect_dysregulation": 0.85,
                "negative_self_concept": 0.9,
                "relationship_disturbances": 0.8
            },
            "onset_age": baseline_age
        })

        # Depression from trauma
        initial_symptoms.append({
            "disorder_name": "depression",
            "severity": 0.7,
            "category": "Mood Disorders",
            "symptom_details": {
                "depressed_mood": 0.75,
                "anhedonia": 0.7,
                "worthlessness": 0.8,
                "suicidal_ideation": 0.5
            },
            "onset_age": baseline_age
        })

    # ========================================
    # PHYSICAL ABUSE
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "hit", "beaten", "whipped", "physical abuse", "violence",
        "bruises", "hurt", "punched", "kicked"
    ]):
        initial_symptoms.append({
            "disorder_name": "ptsd",
            "severity": 0.7,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "intrusive_memories": 0.75,
                "avoidance": 0.7,
                "hyperarousal": 0.8
            },
            "onset_age": baseline_age
        })

        initial_symptoms.append({
            "disorder_name": "depression",
            "severity": 0.6,
            "category": "Mood Disorders",
            "symptom_details": {
                "depressed_mood": 0.65,
                "worthlessness": 0.7,
                "fatigue": 0.6
            },
            "onset_age": baseline_age
        })

    # ========================================
    # NEGLECT
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "neglect", "ignored", "abandoned", "left alone",
        "no food", "starving", "dirty", "uncared for"
    ]):
        if baseline_age <= 12:
            initial_symptoms.append({
                "disorder_name": "reactive_attachment_disorder",
                "severity": 0.7,
                "category": "Trauma and Stress-Related Disorders",
                "symptom_details": {
                    "emotional_withdrawal": 0.75,
                    "minimal_social_responsiveness": 0.7,
                    "limited_positive_affect": 0.7
                },
                "onset_age": baseline_age
            })

        initial_symptoms.append({
            "disorder_name": "depression",
            "severity": 0.55,
            "category": "Mood Disorders",
            "symptom_details": {
                "depressed_mood": 0.6,
                "anhedonia": 0.55,
                "worthlessness": 0.65
            },
            "onset_age": baseline_age
        })

    # ========================================
    # DOMESTIC VIOLENCE (WITNESSED)
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "domestic violence", "parents fighting", "hit my mother",
        "witnessed violence", "saw violence"
    ]):
        initial_symptoms.append({
            "disorder_name": "ptsd",
            "severity": 0.65,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "intrusive_memories": 0.7,
                "hyperarousal": 0.75,
                "avoidance": 0.6
            },
            "onset_age": baseline_age
        })

        initial_symptoms.append({
            "disorder_name": "generalized_anxiety",
            "severity": 0.6,
            "category": "Anxiety Disorders",
            "symptom_details": {
                "excessive_worry": 0.7,
                "hypervigilance": 0.75,
                "sleep_disturbance": 0.65
            },
            "onset_age": baseline_age
        })

    # ========================================
    # BULLYING / PEER VICTIMIZATION
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "bullied", "picked on", "teased", "excluded",
        "rejected by peers", "no friends"
    ]):
        initial_symptoms.append({
            "disorder_name": "social_anxiety",
            "severity": 0.6,
            "category": "Anxiety Disorders",
            "symptom_details": {
                "fear_of_social_situations": 0.7,
                "avoidance_of_social_interaction": 0.65,
                "fear_of_negative_evaluation": 0.75
            },
            "onset_age": baseline_age
        })

        initial_symptoms.append({
            "disorder_name": "depression",
            "severity": 0.5,
            "category": "Mood Disorders",
            "symptom_details": {
                "depressed_mood": 0.55,
                "low_self_esteem": 0.65,
                "social_withdrawal": 0.6
            },
            "onset_age": baseline_age
        })

    # ========================================
    # POVERTY / FINANCIAL INSTABILITY
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "poor", "poverty", "homeless", "no money",
        "couldn't afford", "financial stress"
    ]):
        initial_symptoms.append({
            "disorder_name": "generalized_anxiety",
            "severity": 0.45,
            "category": "Anxiety Disorders",
            "symptom_details": {
                "excessive_worry": 0.55,
                "restlessness": 0.5,
                "sleep_disturbance": 0.45
            },
            "onset_age": baseline_age
        })

    # ========================================
    # CHRONIC ILLNESS (SELF OR CAREGIVER)
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "sick", "illness", "disease", "disability",
        "cancer", "chronic condition"
    ]):
        initial_symptoms.append({
            "disorder_name": "adjustment_disorder",
            "severity": 0.5,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "anxiety": 0.55,
                "depressed_mood": 0.5,
                "difficulty_coping": 0.6
            },
            "onset_age": baseline_age
        })

    # ========================================
    # LOSS / DEATH OF CAREGIVER
    # ========================================
    if any(keyword in backstory_lower for keyword in [
        "died", "death", "passed away", "lost my",
        "orphaned", "funeral"
    ]):
        initial_symptoms.append({
            "disorder_name": "prolonged_grief_disorder",
            "severity": 0.65,
            "category": "Trauma and Stress-Related Disorders",
            "symptom_details": {
                "intense_yearning": 0.7,
                "preoccupation_with_deceased": 0.65,
                "difficulty_accepting_death": 0.6
            },
            "onset_age": baseline_age
        })

        initial_symptoms.append({
            "disorder_name": "depression",
            "severity": 0.6,
            "category": "Mood Disorders",
            "symptom_details": {
                "depressed_mood": 0.7,
                "anhedonia": 0.6,
                "sleep_disturbance": 0.55
            },
            "onset_age": baseline_age
        })

    return initial_symptoms


def deduplicate_symptoms(symptoms: List[Dict]) -> List[Dict]:
    """
    If multiple backstory elements trigger the same disorder, keep highest severity.
    """
    seen = {}

    for symptom in symptoms:
        disorder_name = symptom["disorder_name"]

        if disorder_name not in seen:
            seen[disorder_name] = symptom
        else:
            # Keep whichever has higher severity
            if symptom["severity"] > seen[disorder_name]["severity"]:
                seen[disorder_name] = symptom

    return list(seen.values())
