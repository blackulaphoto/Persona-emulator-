"""
Comprehensive Mental Health Symptom Taxonomy
Based on DSM-5-TR and ICD-11 classifications

This taxonomy covers:
- Mood disorders
- Anxiety disorders
- Trauma disorders
- Personality disorders
- Substance use disorders
- Impulse control disorders
- Somatic disorders
- Eating disorders
- Psychotic disorders
- Sexual disorders
- And more...

Each disorder includes:
- Symptoms (measurable on 0-1 scale)
- Risk factors
- Common comorbidities
- Treatment responses
"""

SYMPTOM_TAXONOMY = {
    # ============================================
    # MOOD DISORDERS
    # ============================================
    "depression": {
        "category": "Mood Disorders",
        "dsm_code": "F32.x / F33.x",
        "full_name": "Major Depressive Disorder",
        "symptoms": [
            "depressed_mood",
            "anhedonia",
            "fatigue",
            "worthlessness",
            "concentration_difficulty",
            "sleep_disturbance",
            "appetite_change",
            "psychomotor_changes",
            "suicidal_ideation"
        ],
        "severity_levels": ["mild", "moderate", "severe", "severe_with_psychotic_features"],
        "common_comorbidities": ["anxiety", "substance_use", "personality_disorders"]
    },
    
    "bipolar_disorder": {
        "category": "Mood Disorders",
        "dsm_code": "F31.x",
        "full_name": "Bipolar I/II Disorder",
        "symptoms": [
            "manic_episodes",
            "hypomanic_episodes",
            "depressive_episodes",
            "racing_thoughts",
            "grandiosity",
            "decreased_need_for_sleep",
            "increased_goal_directed_activity",
            "risky_behavior",
            "irritability"
        ],
        "subtypes": ["bipolar_i", "bipolar_ii", "cyclothymic"],
        "common_comorbidities": ["anxiety", "substance_use", "adhd"]
    },
    
    "persistent_depressive_disorder": {
        "category": "Mood Disorders",
        "dsm_code": "F34.1",
        "full_name": "Persistent Depressive Disorder (Dysthymia)",
        "symptoms": [
            "chronic_low_mood",
            "low_energy",
            "poor_concentration",
            "hopelessness",
            "low_self_esteem"
        ]
    },
    
    # ============================================
    # ANXIETY DISORDERS
    # ============================================
    "generalized_anxiety": {
        "category": "Anxiety Disorders",
        "dsm_code": "F41.1",
        "full_name": "Generalized Anxiety Disorder",
        "symptoms": [
            "excessive_worry",
            "restlessness",
            "fatigue",
            "concentration_difficulty",
            "irritability",
            "muscle_tension",
            "sleep_disturbance"
        ]
    },
    
    "panic_disorder": {
        "category": "Anxiety Disorders",
        "dsm_code": "F41.0",
        "full_name": "Panic Disorder",
        "symptoms": [
            "panic_attacks",
            "fear_of_future_attacks",
            "avoidance_behavior",
            "heart_palpitations",
            "sweating",
            "trembling",
            "shortness_of_breath",
            "derealization",
            "fear_of_losing_control"
        ]
    },
    
    "social_anxiety": {
        "category": "Anxiety Disorders",
        "dsm_code": "F40.10",
        "full_name": "Social Anxiety Disorder",
        "symptoms": [
            "fear_of_social_situations",
            "fear_of_judgment",
            "avoidance_of_social_events",
            "performance_anxiety",
            "blushing",
            "trembling_in_social_contexts"
        ]
    },
    
    "specific_phobias": {
        "category": "Anxiety Disorders",
        "dsm_code": "F40.2x",
        "full_name": "Specific Phobia",
        "symptoms": [
            "intense_fear_of_specific_object",
            "avoidance_behavior",
            "immediate_anxiety_response"
        ],
        "subtypes": [
            "animal_phobia",
            "natural_environment_phobia",
            "blood_injection_injury_phobia",
            "situational_phobia"
        ]
    },
    
    # ============================================
    # TRAUMA AND STRESS DISORDERS
    # ============================================
    "ptsd": {
        "category": "Trauma and Stress Disorders",
        "dsm_code": "F43.10",
        "full_name": "Post-Traumatic Stress Disorder",
        "symptoms": [
            "intrusive_memories",
            "flashbacks",
            "nightmares",
            "avoidance_of_reminders",
            "negative_mood_changes",
            "hypervigilance",
            "exaggerated_startle_response",
            "emotional_numbing",
            "dissociation"
        ],
        "subtypes": ["acute", "chronic", "delayed_onset"]
    },
    
    "complex_ptsd": {
        "category": "Trauma and Stress Disorders",
        "dsm_code": "ICD-11: 6B41",
        "full_name": "Complex PTSD",
        "symptoms": [
            "ptsd_symptoms",
            "emotion_regulation_difficulties",
            "negative_self_concept",
            "relationship_difficulties",
            "dissociation",
            "somatic_symptoms"
        ]
    },
    
    "acute_stress_disorder": {
        "category": "Trauma and Stress Disorders",
        "dsm_code": "F43.0",
        "full_name": "Acute Stress Disorder",
        "symptoms": [
            "intrusive_symptoms",
            "negative_mood",
            "dissociative_symptoms",
            "avoidance",
            "hyperarousal"
        ]
    },

    "adjustment_disorder": {
        "category": "Trauma and Stress Disorders",
        "dsm_code": "F43.2x",
        "full_name": "Adjustment Disorder",
        "symptoms": [
            "emotional_distress",
            "anxiety",
            "depressed_mood",
            "difficulty_functioning",
            "social_withdrawal",
            "sleep_disturbance"
        ]
    },

    "prolonged_grief_disorder": {
        "category": "Trauma and Stress Disorders",
        "dsm_code": "F43.81",
        "full_name": "Prolonged Grief Disorder",
        "symptoms": [
            "intense_yearning",
            "preoccupation_with_deceased",
            "difficulty_accepting_death",
            "emotional_pain",
            "avoidance_of_reminders",
            "identity_disruption"
        ]
    },

    "reactive_attachment_disorder": {
        "category": "Trauma and Stress Disorders",
        "dsm_code": "F94.1",
        "full_name": "Reactive Attachment Disorder",
        "symptoms": [
            "emotional_withdrawal",
            "limited_positive_affect",
            "minimal_social_responsiveness",
            "unexplained_irritability",
            "sadness_or_fearfulness",
            "difficulty_seeking_comfort"
        ]
    },
    
    # ============================================
    # PERSONALITY DISORDERS - CLUSTER A
    # ============================================
    "paranoid_personality": {
        "category": "Personality Disorders (Cluster A)",
        "dsm_code": "F60.0",
        "full_name": "Paranoid Personality Disorder",
        "symptoms": [
            "pervasive_distrust",
            "suspiciousness",
            "interpreting_benign_remarks_as_threatening",
            "holding_grudges",
            "perceiving_attacks",
            "doubts_about_loyalty"
        ]
    },
    
    "schizoid_personality": {
        "category": "Personality Disorders (Cluster A)",
        "dsm_code": "F60.1",
        "full_name": "Schizoid Personality Disorder",
        "symptoms": [
            "detachment_from_relationships",
            "restricted_emotional_expression",
            "lack_of_desire_for_relationships",
            "preference_for_solitary_activities",
            "emotional_coldness"
        ]
    },
    
    "schizotypal_personality": {
        "category": "Personality Disorders (Cluster A)",
        "dsm_code": "F21",
        "full_name": "Schizotypal Personality Disorder",
        "symptoms": [
            "odd_beliefs",
            "unusual_perceptual_experiences",
            "eccentric_behavior",
            "social_anxiety",
            "paranoid_ideation",
            "constricted_affect"
        ]
    },
    
    # ============================================
    # PERSONALITY DISORDERS - CLUSTER B
    # ============================================
    "antisocial_personality": {
        "category": "Personality Disorders (Cluster B)",
        "dsm_code": "F60.2",
        "full_name": "Antisocial Personality Disorder",
        "symptoms": [
            "disregard_for_rights_of_others",
            "deceitfulness",
            "impulsivity",
            "irritability",
            "aggression",
            "reckless_disregard_for_safety",
            "lack_of_remorse"
        ],
        "related_constructs": ["psychopathy", "conduct_disorder"]
    },
    
    "borderline_personality": {
        "category": "Personality Disorders (Cluster B)",
        "dsm_code": "F60.3",
        "full_name": "Borderline Personality Disorder",
        "symptoms": [
            "fear_of_abandonment",
            "unstable_relationships",
            "identity_disturbance",
            "impulsivity",
            "self_harm",
            "suicidal_behavior",
            "affective_instability",
            "chronic_emptiness",
            "anger_regulation_difficulty",
            "dissociation_under_stress"
        ]
    },
    
    "histrionic_personality": {
        "category": "Personality Disorders (Cluster B)",
        "dsm_code": "F60.4",
        "full_name": "Histrionic Personality Disorder",
        "symptoms": [
            "excessive_emotionality",
            "attention_seeking",
            "inappropriately_seductive",
            "shallow_emotions",
            "dramatic_behavior",
            "suggestibility",
            "considering_relationships_more_intimate_than_they_are"
        ]
    },
    
    "narcissistic_personality": {
        "category": "Personality Disorders (Cluster B)",
        "dsm_code": "F60.81",
        "full_name": "Narcissistic Personality Disorder",
        "symptoms": [
            "grandiosity",
            "need_for_admiration",
            "lack_of_empathy",
            "sense_of_entitlement",
            "exploitation_of_others",
            "envy",
            "arrogance",
            "preoccupation_with_fantasies_of_success"
        ],
        "subtypes": ["grandiose", "vulnerable"]
    },
    
    # ============================================
    # PERSONALITY DISORDERS - CLUSTER C
    # ============================================
    "avoidant_personality": {
        "category": "Personality Disorders (Cluster C)",
        "dsm_code": "F60.6",
        "full_name": "Avoidant Personality Disorder",
        "symptoms": [
            "social_inhibition",
            "feelings_of_inadequacy",
            "hypersensitivity_to_criticism",
            "avoidance_of_interpersonal_contact",
            "reluctance_to_take_risks",
            "views_self_as_socially_inept"
        ]
    },
    
    "dependent_personality": {
        "category": "Personality Disorders (Cluster C)",
        "dsm_code": "F60.7",
        "full_name": "Dependent Personality Disorder",
        "symptoms": [
            "excessive_need_to_be_taken_care_of",
            "submissive_behavior",
            "fear_of_separation",
            "difficulty_making_decisions",
            "difficulty_disagreeing",
            "urgency_to_obtain_new_relationship_when_one_ends"
        ]
    },
    
    "obsessive_compulsive_personality": {
        "category": "Personality Disorders (Cluster C)",
        "dsm_code": "F60.5",
        "full_name": "Obsessive-Compulsive Personality Disorder",
        "symptoms": [
            "preoccupation_with_orderliness",
            "perfectionism",
            "need_for_control",
            "rigidity",
            "stubbornness",
            "overconscient iousness",
            "difficulty_delegating",
            "hoarding_worthless_objects"
        ]
    },
    
    # ============================================
    # IMPULSE CONTROL DISORDERS
    # ============================================
    "kleptomania": {
        "category": "Impulse Control Disorders",
        "dsm_code": "F63.2",
        "full_name": "Kleptomania",
        "symptoms": [
            "recurrent_failure_to_resist_stealing",
            "tension_before_theft",
            "pleasure_during_theft",
            "guilt_after_theft",
            "stealing_not_motivated_by_need"
        ]
    },
    
    "pyromania": {
        "category": "Impulse Control Disorders",
        "dsm_code": "F63.1",
        "full_name": "Pyromania",
        "symptoms": [
            "deliberate_fire_setting",
            "tension_before_act",
            "fascination_with_fire",
            "pleasure_from_fire_setting",
            "not_motivated_by_monetary_gain"
        ]
    },
    
    "pathological_gambling": {
        "category": "Impulse Control Disorders",
        "dsm_code": "F63.0",
        "full_name": "Gambling Disorder",
        "symptoms": [
            "preoccupation_with_gambling",
            "need_to_gamble_with_increasing_amounts",
            "restlessness_when_cutting_down",
            "gambling_to_escape_problems",
            "chasing_losses",
            "lying_about_gambling",
            "jeopardizing_relationships_for_gambling",
            "relying_on_others_for_money"
        ]
    },
    
    "intermittent_explosive_disorder": {
        "category": "Impulse Control Disorders",
        "dsm_code": "F63.81",
        "full_name": "Intermittent Explosive Disorder",
        "symptoms": [
            "recurrent_behavioral_outbursts",
            "verbal_aggression",
            "physical_aggression",
            "rage_disproportionate_to_situation",
            "impulsive_aggression"
        ]
    },
    
    # ============================================
    # SUBSTANCE USE DISORDERS
    # ============================================
    "alcohol_use_disorder": {
        "category": "Substance Use Disorders",
        "dsm_code": "F10.xx",
        "full_name": "Alcohol Use Disorder",
        "symptoms": [
            "tolerance",
            "withdrawal",
            "consuming_more_than_intended",
            "unsuccessful_efforts_to_cut_down",
            "time_spent_obtaining_alcohol",
            "craving",
            "failure_to_fulfill_obligations",
            "continued_use_despite_problems",
            "giving_up_activities",
            "use_in_hazardous_situations"
        ],
        "severity": ["mild", "moderate", "severe"]
    },
    
    "opioid_use_disorder": {
        "category": "Substance Use Disorders",
        "dsm_code": "F11.xx",
        "full_name": "Opioid Use Disorder",
        "symptoms": [
            "tolerance",
            "withdrawal",
            "using_more_than_intended",
            "unsuccessful_efforts_to_cut_down",
            "time_spent_obtaining_opioids",
            "craving",
            "continued_use_despite_problems"
        ]
    },
    
    "cannabis_use_disorder": {
        "category": "Substance Use Disorders",
        "dsm_code": "F12.xx",
        "full_name": "Cannabis Use Disorder",
        "symptoms": [
            "tolerance",
            "withdrawal",
            "using_more_than_intended",
            "craving",
            "failure_to_fulfill_obligations"
        ]
    },
    
    "stimulant_use_disorder": {
        "category": "Substance Use Disorders",
        "dsm_code": "F14.xx / F15.xx",
        "full_name": "Stimulant Use Disorder (Cocaine/Amphetamine)",
        "symptoms": [
            "tolerance",
            "withdrawal",
            "using_more_than_intended",
            "craving",
            "risky_use",
            "continued_use_despite_problems"
        ]
    },

    "substance_use_disorder": {
        "category": "Substance Use Disorders",
        "dsm_code": "F1x.xx",
        "full_name": "Substance Use Disorder (Unspecified)",
        "symptoms": [
            "tolerance",
            "withdrawal",
            "using_more_than_intended",
            "unsuccessful_efforts_to_cut_down",
            "time_spent_obtaining_substances",
            "craving",
            "continued_use_despite_problems",
            "failure_to_fulfill_obligations"
        ]
    },
    
    # ============================================
    # SOMATIC SYMPTOM DISORDERS
    # ============================================
    "illness_anxiety_disorder": {
        "category": "Somatic Symptom Disorders",
        "dsm_code": "F45.21",
        "full_name": "Illness Anxiety Disorder (Hypochondriasis)",
        "symptoms": [
            "preoccupation_with_having_serious_illness",
            "high_health_anxiety",
            "excessive_health_related_behaviors",
            "frequent_medical_visits",
            "checking_for_signs_of_illness",
            "avoidance_of_medical_care"
        ]
    },
    
    "somatic_symptom_disorder": {
        "category": "Somatic Symptom Disorders",
        "dsm_code": "F45.1",
        "full_name": "Somatic Symptom Disorder",
        "symptoms": [
            "one_or_more_somatic_symptoms",
            "excessive_thoughts_about_symptoms",
            "high_anxiety_about_health",
            "excessive_time_devoted_to_symptoms"
        ]
    },
    
    "conversion_disorder": {
        "category": "Somatic Symptom Disorders",
        "dsm_code": "F44.x",
        "full_name": "Conversion Disorder (Functional Neurological Symptom Disorder)",
        "symptoms": [
            "altered_motor_function",
            "altered_sensory_function",
            "seizures",
            "symptoms_incompatible_with_medical_condition"
        ]
    },
    
    "factitious_disorder": {
        "category": "Somatic Symptom Disorders",
        "dsm_code": "F68.10",
        "full_name": "Factitious Disorder (Munchausen Syndrome)",
        "symptoms": [
            "falsification_of_symptoms",
            "deceptive_behavior",
            "presenting_self_as_ill",
            "absence_of_external_rewards"
        ],
        "subtypes": ["imposed_on_self", "imposed_on_another"]
    },
    
    # ============================================
    # EATING DISORDERS
    # ============================================
    "anorexia_nervosa": {
        "category": "Eating Disorders",
        "dsm_code": "F50.0x",
        "full_name": "Anorexia Nervosa",
        "symptoms": [
            "restriction_of_energy_intake",
            "intense_fear_of_weight_gain",
            "disturbance_in_body_image",
            "low_body_weight",
            "denial_of_seriousness"
        ],
        "subtypes": ["restricting", "binge_eating_purging"]
    },
    
    "bulimia_nervosa": {
        "category": "Eating Disorders",
        "dsm_code": "F50.2",
        "full_name": "Bulimia Nervosa",
        "symptoms": [
            "recurrent_binge_eating",
            "compensatory_behaviors",
            "self_evaluation_influenced_by_body_shape",
            "vomiting",
            "laxative_use",
            "excessive_exercise"
        ]
    },
    
    "binge_eating_disorder": {
        "category": "Eating Disorders",
        "dsm_code": "F50.81",
        "full_name": "Binge Eating Disorder",
        "symptoms": [
            "recurrent_binge_eating",
            "eating_rapidly",
            "eating_until_uncomfortably_full",
            "eating_when_not_hungry",
            "distress_about_binge_eating",
            "no_compensatory_behaviors"
        ]
    },
    
    # ============================================
    # OCD AND RELATED DISORDERS
    # ============================================
    "obsessive_compulsive_disorder": {
        "category": "OCD and Related Disorders",
        "dsm_code": "F42.x",
        "full_name": "Obsessive-Compulsive Disorder",
        "symptoms": [
            "obsessions",
            "compulsions",
            "time_consuming_rituals",
            "distress_from_obsessions",
            "attempts_to_suppress_thoughts"
        ],
        "common_themes": [
            "contamination",
            "symmetry",
            "forbidden_thoughts",
            "harm"
        ]
    },
    
    "hoarding_disorder": {
        "category": "OCD and Related Disorders",
        "dsm_code": "F42.3",
        "full_name": "Hoarding Disorder",
        "symptoms": [
            "difficulty_discarding_possessions",
            "perceived_need_to_save_items",
            "distress_at_discarding",
            "accumulation_of_possessions",
            "cluttered_living_spaces",
            "impairment_in_functioning"
        ]
    },
    
    "body_dysmorphic_disorder": {
        "category": "OCD and Related Disorders",
        "dsm_code": "F45.22",
        "full_name": "Body Dysmorphic Disorder",
        "symptoms": [
            "preoccupation_with_perceived_defect",
            "repetitive_behaviors",
            "mirror_checking",
            "excessive_grooming",
            "skin_picking",
            "reassurance_seeking"
        ]
    },
    
    "trichotillomania": {
        "category": "OCD and Related Disorders",
        "dsm_code": "F63.3",
        "full_name": "Trichotillomania (Hair-Pulling Disorder)",
        "symptoms": [
            "recurrent_hair_pulling",
            "attempts_to_decrease_pulling",
            "distress_from_pulling",
            "noticeable_hair_loss"
        ]
    },
    
    "excoriation_disorder": {
        "category": "OCD and Related Disorders",
        "dsm_code": "F42.4",
        "full_name": "Excoriation Disorder (Skin-Picking)",
        "symptoms": [
            "recurrent_skin_picking",
            "skin_lesions",
            "attempts_to_decrease_picking",
            "distress_from_picking"
        ]
    },
    
    # ============================================
    # SEXUAL DISORDERS
    # ============================================
    "hypersexuality": {
        "category": "Sexual Disorders",
        "dsm_code": "ICD-11: 6C72",
        "full_name": "Compulsive Sexual Behavior Disorder",
        "symptoms": [
            "persistent_pattern_of_sexual_behavior",
            "unsuccessful_efforts_to_control",
            "continued_despite_consequences",
            "sexual_behavior_becomes_central_focus",
            "distress_from_behavior"
        ],
        "related_terms": ["sex_addiction", "hypersexual_disorder"]
    },
    
    "paraphilic_disorders": {
        "category": "Sexual Disorders",
        "dsm_code": "F65.x",
        "full_name": "Paraphilic Disorders",
        "symptoms": [
            "recurrent_intense_sexual_arousal",
            "acting_on_urges",
            "distress_from_urges",
            "impairment_in_functioning"
        ],
        "subtypes": [
            "voyeuristic",
            "exhibitionistic",
            "frotteuristic",
            "sexual_masochism",
            "sexual_sadism",
            "pedophilic",
            "fetishistic",
            "transvestic"
        ]
    },

    "sexual_dysfunction": {
        "category": "Sexual Disorders",
        "dsm_code": "F52.x",
        "full_name": "Sexual Dysfunction (Unspecified)",
        "symptoms": [
            "low_sexual_desire",
            "arousal_difficulty",
            "pain_during_sex",
            "anxiety_about_sex",
            "avoidance_of_sexual_activity"
        ]
    },
    
    # ============================================
    # PSYCHOTIC DISORDERS
    # ============================================
    "schizophrenia": {
        "category": "Psychotic Disorders",
        "dsm_code": "F20.x",
        "full_name": "Schizophrenia",
        "symptoms": [
            "delusions",
            "hallucinations",
            "disorganized_speech",
            "disorganized_behavior",
            "negative_symptoms",
            "social_withdrawal",
            "flat_affect",
            "avolition"
        ],
        "subtypes": ["paranoid", "disorganized", "catatonic", "undifferentiated", "residual"]
    },
    
    "schizoaffective_disorder": {
        "category": "Psychotic Disorders",
        "dsm_code": "F25.x",
        "full_name": "Schizoaffective Disorder",
        "symptoms": [
            "psychotic_symptoms",
            "mood_episodes",
            "delusions_or_hallucinations_for_2_weeks",
            "mood_symptoms_for_majority_of_illness"
        ],
        "subtypes": ["bipolar_type", "depressive_type"]
    },
    
    "delusional_disorder": {
        "category": "Psychotic Disorders",
        "dsm_code": "F22",
        "full_name": "Delusional Disorder",
        "symptoms": [
            "non_bizarre_delusions",
            "functioning_not_markedly_impaired",
            "behavior_not_obviously_bizarre"
        ],
        "subtypes": [
            "erotomanic",
            "grandiose",
            "jealous",
            "persecutory",
            "somatic"
        ]
    },
    
    # ============================================
    # NEURODEVELOPMENTAL DISORDERS
    # ============================================
    "adhd": {
        "category": "Neurodevelopmental Disorders",
        "dsm_code": "F90.x",
        "full_name": "Attention-Deficit/Hyperactivity Disorder",
        "symptoms": [
            "inattention",
            "hyperactivity",
            "impulsivity",
            "difficulty_sustaining_attention",
            "easily_distracted",
            "forgetfulness",
            "fidgeting",
            "inability_to_stay_seated",
            "interrupting_others"
        ],
        "subtypes": ["predominantly_inattentive", "predominantly_hyperactive", "combined"]
    },
    
    "autism_spectrum_disorder": {
        "category": "Neurodevelopmental Disorders",
        "dsm_code": "F84.0",
        "full_name": "Autism Spectrum Disorder",
        "symptoms": [
            "social_communication_deficits",
            "restricted_interests",
            "repetitive_behaviors",
            "sensory_sensitivities",
            "difficulty_with_social_reciprocity"
        ],
        "severity_levels": ["level_1", "level_2", "level_3"]
    }
}


# Export for use in application
def get_all_disorders():
    """Return list of all disorder names"""
    return list(SYMPTOM_TAXONOMY.keys())


def get_disorders_by_category(category):
    """Get all disorders in a specific category"""
    return {
        name: info 
        for name, info in SYMPTOM_TAXONOMY.items() 
        if info["category"] == category
    }


def get_disorder_symptoms(disorder_name):
    """Get all symptoms for a specific disorder"""
    if disorder_name in SYMPTOM_TAXONOMY:
        return SYMPTOM_TAXONOMY[disorder_name]["symptoms"]
    return []


def get_all_categories():
    """Return unique list of all disorder categories"""
    return list(set(d["category"] for d in SYMPTOM_TAXONOMY.values()))
