"""
Seed Clinical Templates Database Script

This script converts TypeScript psychological templates into the clinical_templates database table.
It handles all 6 major disorder templates: NPD, Schizophrenia, SUD, MDD, Anorexia, and OCD.

Run from backend directory:
    python scripts/seed_psych_templates.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal, Base
from app.models.clinical_template import ClinicalTemplate
from sqlalchemy.orm import Session


def map_personality_to_big_five(traits_list):
    """
    Convert TypeScript personality traits array to Big Five dict.

    Args:
        traits_list: List of trait objects with name, value, description

    Returns:
        Dict with Big Five traits normalized to 0-1 scale
    """
    # Map trait names to standard Big Five
    trait_mapping = {
        'Openness': 'openness',
        'Conscientiousness': 'conscientiousness',
        'Extraversion': 'extraversion',
        'Agreeableness': 'agreeableness',
        'Emotional Sensitivity': 'neuroticism',  # Emotional Sensitivity maps to Neuroticism
        'Neuroticism': 'neuroticism'
    }

    big_five = {
        'openness': 0.5,
        'conscientiousness': 0.5,
        'extraversion': 0.5,
        'agreeableness': 0.5,
        'neuroticism': 0.5
    }

    for trait in traits_list:
        trait_name = trait['name']
        if trait_name in trait_mapping:
            big_five_key = trait_mapping[trait_name]
            # Convert 0-100 scale to 0-1 scale
            big_five[big_five_key] = trait['value'] / 100.0

    return big_five


def map_life_events_to_experiences(life_events):
    """
    Convert TypeScript lifeEvents array to predefined_experiences format.

    Args:
        life_events: Array of life event objects

    Returns:
        Array of experience objects matching the database schema
    """
    experiences = []

    for event in life_events:
        # Skip therapy events - they go in predefined_interventions
        if event.get('type') == 'therapy':
            continue

        # Map event type to valence
        valence_mapping = {
            'challenge': 'negative',
            'growth': 'positive',
            'neutral': 'neutral',
            'trauma': 'negative'
        }

        # Determine intensity from symptoms severity if available
        intensity = 'moderate'
        if 'symptoms' in event:
            avg_severity = sum(s.get('severity', 5) for s in event['symptoms']) / len(event['symptoms'])
            if avg_severity >= 8:
                intensity = 'severe'
            elif avg_severity >= 6:
                intensity = 'moderate'
            else:
                intensity = 'mild'

        experience = {
            'age': event['age'],
            'category': 'psychological_stress',  # Default category
            'valence': valence_mapping.get(event.get('type'), 'neutral'),
            'intensity': intensity,
            'description': event['description'],
            'title': event['title'],
            'impact': event.get('impact', ''),
            'clinical_note': event.get('impact', '')
        }

        # Add symptom information if present
        if 'symptoms' in event:
            experience['symptoms_developed'] = event['symptoms']

        # Add personality changes if present
        if 'personalityChanges' in event:
            experience['personality_changes'] = event['personalityChanges']

        experiences.append(experience)

    return experiences


def map_therapy_events_to_interventions(life_events):
    """
    Convert therapy-type lifeEvents to predefined_interventions format.

    Args:
        life_events: Array of life event objects

    Returns:
        Array of intervention objects matching the database schema
    """
    interventions = []

    for event in life_events:
        # Only process therapy events
        if event.get('type') != 'therapy':
            continue

        intervention = {
            'age': event['age'],
            'therapy_type': event.get('therapyApproach', 'Unknown'),
            'duration': f"{event.get('sessionCount', 0)}_sessions",
            'intensity': 'weekly',  # Default assumption
            'rationale': event.get('impact', ''),
            'description': event.get('description', ''),
            'outcomes': event.get('therapyOutcomes', [])
        }

        interventions.append(intervention)

    return interventions


def create_npd_template():
    """Create Narcissistic Personality Disorder template."""
    return ClinicalTemplate(
        name="Marcus - Narcissistic Personality Disorder",
        disorder_type="NPD",
        description="Marcus presents as a highly successful young professional with a carefully curated image of confidence and achievement. This template demonstrates the classic developmental pathway to NPD through excessive childhood praise combined with emotional neglect.",
        clinical_rationale="""This template demonstrates the classic developmental pathway to Narcissistic Personality Disorder.

Key developmental factors:
1. Excessive praise without genuine emotional attunement (ages 5-10)
2. Conditional love based on achievement rather than inherent worth
3. Lack of empathy development due to emotional distance from caregivers
4. Narcissistic injuries during adolescence reinforcing defensive grandiosity
5. Transactional relationships that prevent authentic intimacy

The pattern shows how children who are simultaneously idealized and emotionally neglected develop a fragile self-esteem requiring constant external validation. Each narcissistic injury (failure, criticism, rejection) triggers defensive rage and increased grandiosity rather than self-reflection, creating a rigid personality structure resistant to change.""",
        baseline_age=5,
        baseline_gender="male",
        baseline_background="Marcus grew up as an only child in an affluent family. His parents showered him with praise for every accomplishment while being emotionally distant. He learned early that his worth came from being 'special' and superior to others. Criticism was rare but devastating when it occurred.",
        baseline_personality={
            'openness': 0.50,
            'conscientiousness': 0.60,
            'extraversion': 0.50,
            'agreeableness': 0.50,
            'neuroticism': 0.60
        },
        baseline_attachment_style="anxious",
        predefined_experiences=[
            {
                'age': 5,
                'category': 'family_dynamics',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'The Golden Child',
                'description': "Marcus's parents constantly praised him as 'gifted' and 'special.' Every drawing was a masterpiece, every achievement celebrated extravagantly. He was told he was destined for greatness.",
                'impact': "Developed inflated sense of self-importance and belief that he was inherently superior to others. Learned that his value came from being exceptional.",
                'clinical_note': 'Excessive praise without emotional attunement creates narcissistic vulnerability',
                'symptoms_developed': [
                    {'name': 'Grandiose fantasies', 'severity': 5},
                    {'name': 'Need for admiration', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Extraversion', 'before': 50, 'after': 65},
                    {'trait': 'Agreeableness', 'before': 50, 'after': 40}
                ]
            },
            {
                'age': 10,
                'category': 'achievement_failure',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'The First Failure',
                'description': "Marcus didn't make the elite soccer team. His parents' disappointment was palpable. He experienced his first narcissistic injury - a threat to his special status.",
                'impact': 'Developed intense fear of failure and criticism. Learned to deflect blame and make excuses. Began devaluing others who succeeded where he failed.',
                'clinical_note': 'First narcissistic injury establishes defensive pattern of blame and devaluation',
                'symptoms_developed': [
                    {'name': 'Rage at criticism', 'severity': 7},
                    {'name': 'Devaluing others', 'severity': 6},
                    {'name': 'Grandiosity', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Emotional Sensitivity', 'before': 60, 'after': 75},
                    {'trait': 'Agreeableness', 'before': 40, 'after': 30}
                ]
            },
            {
                'age': 16,
                'category': 'social_achievement',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Social Dominance',
                'description': 'Marcus became student body president and captain of the debate team. He learned to charm and manipulate others to maintain his superior position.',
                'impact': "Reinforced belief in his superiority. Developed skills in exploiting others' admiration. Relationships became transactional - people were either useful or worthless.",
                'clinical_note': 'Success without empathy development crystallizes narcissistic personality structure',
                'symptoms_developed': [
                    {'name': 'Interpersonal exploitation', 'severity': 7},
                    {'name': 'Lack of empathy', 'severity': 8},
                    {'name': 'Need for admiration', 'severity': 9}
                ],
                'personality_changes': [
                    {'trait': 'Extraversion', 'before': 65, 'after': 80},
                    {'trait': 'Conscientiousness', 'before': 60, 'after': 75},
                    {'trait': 'Agreeableness', 'before': 30, 'after': 25}
                ]
            },
            {
                'age': 22,
                'category': 'relationship_loss',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'First Serious Relationship Ends',
                'description': "Marcus's girlfriend left him, saying he was 'incapable of real intimacy' and 'only cared about himself.' He was devastated but publicly blamed her.",
                'impact': 'Experienced narcissistic injury from rejection. Increased defensive grandiosity and devaluation of others. Reinforced belief that vulnerability equals weakness.',
                'clinical_note': 'Inability to process rejection without defensive rage confirms NPD diagnosis',
                'symptoms_developed': [
                    {'name': 'Rage at criticism', 'severity': 9},
                    {'name': 'Grandiosity', 'severity': 9},
                    {'name': 'Lack of empathy', 'severity': 8},
                    {'name': 'Envy of others', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Emotional Sensitivity', 'before': 75, 'after': 85}
                ]
            },
            {
                'age': 25,
                'category': 'career_success',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Career Success',
                'description': "Marcus became the youngest manager at his firm. His success reinforced his belief in his superiority, but he struggled with colleagues who didn't admire him.",
                'impact': 'Career success validated grandiose self-image but increased interpersonal conflicts. Difficulty accepting feedback from superiors. Exploited subordinates.',
                'clinical_note': 'Success without insight reinforces maladaptive patterns',
                'symptoms_developed': [
                    {'name': 'Grandiosity', 'severity': 10},
                    {'name': 'Need for admiration', 'severity': 10},
                    {'name': 'Arrogant behavior', 'severity': 8},
                    {'name': 'Interpersonal exploitation', 'severity': 7}
                ]
            }
        ],
        predefined_interventions=[],
        expected_outcomes={
            'personality_changes': {
                'openness': 0.55,
                'conscientiousness': 0.75,
                'extraversion': 0.80,
                'agreeableness': 0.25,
                'neuroticism': 0.85
            },
            'symptoms_developed': [
                'Grandiosity',
                'Need for admiration',
                'Lack of empathy',
                'Interpersonal exploitation',
                'Envy of others',
                'Arrogant behavior'
            ],
            'attachment_changes': 'anxious',
            'trauma_markers': [
                'Narcissistic vulnerability to criticism',
                'Inability to form intimate relationships',
                'Defensive rage patterns',
                'Exploitative interpersonal style'
            ]
        },
        citations=[
            "Kernberg, O. (1975). Borderline Conditions and Pathological Narcissism",
            "Kohut, H. (1971). The Analysis of the Self",
            "Miller, A. (1981). The Drama of the Gifted Child",
            "Ronningstam, E. (2005). Identifying and Understanding the Narcissistic Personality"
        ],
        remix_suggestions=[
            {
                'title': 'Early Empathy Development',
                'changes': ['Add emotionally attuned parenting at age 5-8', 'Include peer friendship experiences'],
                'hypothesis': 'Emotional attunement during critical period could prevent NPD development despite achievement focus'
            },
            {
                'title': 'Therapy After First Narcissistic Injury',
                'changes': ['Add psychotherapy at age 10 after soccer team rejection'],
                'hypothesis': 'Early intervention teaching emotional processing could reduce defensive grandiosity pattern'
            }
        ]
    )


def create_schizophrenia_template():
    """Create Schizophrenia template."""
    return ClinicalTemplate(
        name="Daniel - Schizophrenia",
        disorder_type="Schizophrenia",
        description="Daniel's journey illustrates the typical neurodevelopmental trajectory of schizophrenia, from subtle premorbid features through prodromal phase to first episode psychosis. Shows the progressive nature and devastating impact of this illness.",
        clinical_rationale="""This template demonstrates the neurodevelopmental model of schizophrenia.

Key features:
1. Premorbid phase (age 15): Subtle personality quirks, introversion, schizoid traits
2. Prodromal phase (ages 17-19): Attenuated psychotic symptoms, functional decline
3. First episode psychosis (age 21): Full break from reality requiring hospitalization
4. Chronic phase (age 22+): Residual symptoms, negative symptoms more disabling than positive

The progression shows how genetic vulnerability interacts with neurodevelopmental changes during adolescence/early adulthood. Early intervention during prodrome could potentially delay or reduce severity of first episode. Negative symptoms (flat affect, avolition, social withdrawal) prove more treatment-resistant and disabling than positive symptoms (hallucinations, delusions).""",
        baseline_age=15,
        baseline_gender="male",
        baseline_background="Daniel was a bright, somewhat shy teenager who loved computer programming. Around age 17, his friends noticed he was becoming more withdrawn and 'spacey.' By age 19, he was experiencing unusual perceptual experiences and paranoid thoughts.",
        baseline_personality={
            'openness': 0.60,
            'conscientiousness': 0.60,
            'extraversion': 0.40,
            'agreeableness': 0.50,
            'neuroticism': 0.60
        },
        baseline_attachment_style="secure",
        predefined_experiences=[
            {
                'age': 15,
                'category': 'baseline_functioning',
                'valence': 'neutral',
                'intensity': 'mild',
                'title': 'The Quiet Kid',
                'description': "Daniel was always a bit introverted and preferred computers to socializing. He had a few close friends and did well in school, though teachers noted he seemed 'in his own world' sometimes.",
                'impact': 'Baseline personality with schizoid traits that would later be recognized as premorbid features. Genetic vulnerability present but not yet manifest.',
                'clinical_note': 'Premorbid schizoid features common in schizophrenia development',
                'personality_changes': [
                    {'trait': 'Extraversion', 'before': 40, 'after': 35}
                ]
            },
            {
                'age': 17,
                'category': 'prodromal_symptoms',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': "Something's Changing",
                'description': "Daniel began experiencing odd perceptual experiences - sounds seemed louder, colors more intense. He had fleeting thoughts that people were talking about him. His concentration declined, and he started skipping classes.",
                'impact': "Onset of prodromal phase. Attenuated psychotic symptoms emerged. Social withdrawal increased. Academic performance declined. Friends noticed he seemed 'different.'",
                'clinical_note': 'Prodromal phase with attenuated psychotic symptoms - early intervention window',
                'symptoms_developed': [
                    {'name': 'Perceptual disturbances', 'severity': 4},
                    {'name': 'Ideas of reference', 'severity': 5},
                    {'name': 'Social withdrawal', 'severity': 6},
                    {'name': 'Concentration problems', 'severity': 7},
                    {'name': 'Anxiety', 'severity': 8}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 60, 'after': 45},
                    {'trait': 'Extraversion', 'before': 35, 'after': 25},
                    {'trait': 'Emotional Sensitivity', 'before': 60, 'after': 75}
                ]
            },
            {
                'age': 19,
                'category': 'prodromal_symptoms',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'The Prodrome Deepens',
                'description': "Daniel dropped out of college. He spent days in his room, convinced his computer was being monitored. He heard whispers when alone. His hygiene declined. His speech became vague and hard to follow.",
                'impact': "Full prodromal syndrome. Brief limited intermittent psychotic symptoms (BLIPS). Significant functional decline. Family became concerned but didn't know what was happening.",
                'clinical_note': 'BLIPS indicate imminent risk of first episode psychosis - urgent intervention needed',
                'symptoms_developed': [
                    {'name': 'Paranoid thoughts', 'severity': 6},
                    {'name': 'Auditory hallucinations (brief)', 'severity': 5},
                    {'name': 'Disorganized thinking', 'severity': 5},
                    {'name': 'Social withdrawal', 'severity': 8},
                    {'name': 'Avolition', 'severity': 7},
                    {'name': 'Blunted affect', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 45, 'after': 30},
                    {'trait': 'Extraversion', 'before': 25, 'after': 15},
                    {'trait': 'Emotional Sensitivity', 'before': 75, 'after': 85}
                ]
            },
            {
                'age': 21,
                'category': 'psychotic_break',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'First Episode Psychosis',
                'description': "Daniel became convinced that government agents were monitoring him through his devices. He heard multiple voices commenting on his actions. He believed he had special powers. His parents found him talking to people who weren't there.",
                'impact': 'First episode of psychosis. Clear hallucinations and delusions. Complete break from reality. Hospitalized involuntarily. Started antipsychotic medication.',
                'clinical_note': 'First episode psychosis - acute treatment critical to prevent progressive deterioration',
                'symptoms_developed': [
                    {'name': 'Auditory hallucinations', 'severity': 9},
                    {'name': 'Paranoid delusions', 'severity': 10},
                    {'name': 'Disorganized thinking', 'severity': 8},
                    {'name': 'Disorganized behavior', 'severity': 7},
                    {'name': 'Flat affect', 'severity': 8},
                    {'name': 'Avolition', 'severity': 9}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 30, 'after': 20},
                    {'trait': 'Extraversion', 'before': 15, 'after': 10}
                ]
            },
            {
                'age': 22,
                'category': 'chronic_phase',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Living with Schizophrenia',
                'description': "Daniel lives with his parents and attends a day program. He still hears occasional voices and struggles with motivation. He's learning to manage his illness but mourns the life he thought he'd have.",
                'impact': 'Chronic phase with residual symptoms. Significant functional impairment. Negative symptoms more disabling than positive symptoms. Grief over lost potential.',
                'clinical_note': 'Negative symptoms often more treatment-resistant and disabling than positive symptoms',
                'symptoms_developed': [
                    {'name': 'Auditory hallucinations', 'severity': 3},
                    {'name': 'Paranoid thoughts', 'severity': 4},
                    {'name': 'Flat affect', 'severity': 7},
                    {'name': 'Avolition', 'severity': 8},
                    {'name': 'Social withdrawal', 'severity': 9},
                    {'name': 'Cognitive deficits', 'severity': 7}
                ]
            }
        ],
        predefined_interventions=[
            {
                'age': 21,
                'therapy_type': 'Antipsychotic medication + supportive therapy',
                'duration': '15_sessions',
                'intensity': 'daily_inpatient',
                'rationale': 'Acute symptoms partially controlled with medication. Entered post-acute phase. Negative symptoms prominent. Beginning to process what happened.',
                'description': "After 3 weeks in the hospital, Daniel's acute psychotic symptoms reduced with antipsychotic medication. The voices quieted but didn't disappear completely. He felt emotionally numb and exhausted.",
                'outcomes': [
                    {'metric': 'Hallucination intensity', 'improvement': 60},
                    {'metric': 'Delusion conviction', 'improvement': 50},
                    {'metric': 'Reality testing', 'improvement': 40}
                ]
            }
        ],
        expected_outcomes={
            'personality_changes': {
                'openness': 0.70,
                'conscientiousness': 0.20,
                'extraversion': 0.10,
                'agreeableness': 0.50,
                'neuroticism': 0.85
            },
            'symptoms_developed': [
                'Auditory hallucinations',
                'Paranoid delusions',
                'Disorganized thinking',
                'Flat affect',
                'Avolition',
                'Social withdrawal',
                'Cognitive deficits'
            ],
            'attachment_changes': 'fearful',
            'trauma_markers': [
                'Loss of reality testing capacity',
                'Chronic negative symptoms',
                'Significant functional impairment',
                'Grief over lost potential'
            ]
        },
        citations=[
            "McGorry, P. (1998). Preventive strategies in early psychosis",
            "Andreasen, N. (1999). A unitary model of schizophrenia",
            "Tandon, R. et al. (2009). Schizophrenia - Just the Facts",
            "Lieberman, J. et al. (2001). Time course and biologic correlates of treatment response in first-episode schizophrenia"
        ],
        remix_suggestions=[
            {
                'title': 'Early Intervention During Prodrome',
                'changes': ['Add specialized early psychosis intervention at age 17', 'Include family psychoeducation'],
                'hypothesis': 'Early intervention could delay or reduce severity of first episode by 40-50%'
            }
        ]
    )


def create_sud_template():
    """Create Substance Use Disorder (Self-Medication Pathway) template."""
    return ClinicalTemplate(
        name="Aisha - Substance Use Disorder (Self-Medication)",
        disorder_type="SUD",
        description="Aisha's journey exemplifies the self-medication pathway from trauma to addiction. Sexual assault at 16 triggered PTSD, alcohol became her coping mechanism, and physical dependence developed within 5 years. Multiple treatment attempts show the challenge of treating addiction without addressing underlying trauma.",
        clinical_rationale="""This template demonstrates the self-medication model of substance use disorder.

Key pathway:
1. Traumatic event (age 16): Sexual assault triggers PTSD symptoms
2. Discovery of relief (age 17): Alcohol temporarily silences intrusive thoughts
3. Negative reinforcement loop: Alcohol use reinforced by symptom relief
4. Escalation (age 19): Daily use as primary coping mechanism, tolerance develops
5. Physical dependence (age 21): Withdrawal symptoms, loss of control
6. Severe addiction (age 23): Compulsive use despite devastating consequences
7. Failed treatment (age 24): Standard addiction treatment without trauma focus
8. Integrated treatment (age 26): Trauma-focused approach addressing both PTSD and SUD

Critical insight: Addiction served a function - it made unbearable PTSD symptoms bearable. Treatment addressing only addiction without trauma processing typically fails. Integrated treatment for co-occurring PTSD and SUD is essential.""",
        baseline_age=14,
        baseline_gender="female",
        baseline_background="Aisha was a bright, outgoing teenager on the volleyball team with dreams of becoming a teacher. She had close friends and good academic performance. At age 16, sexual assault shattered her sense of safety and changed her life trajectory.",
        baseline_personality={
            'openness': 0.60,
            'conscientiousness': 0.65,
            'extraversion': 0.70,
            'agreeableness': 0.55,
            'neuroticism': 0.60
        },
        baseline_attachment_style="secure",
        predefined_experiences=[
            {
                'age': 14,
                'category': 'healthy_development',
                'valence': 'positive',
                'intensity': 'mild',
                'title': 'Before the Trauma',
                'description': "Aisha was a bright, outgoing teenager. She was on the volleyball team, had close friends, and dreamed of becoming a teacher. She occasionally tried alcohol at parties but it wasn't important to her.",
                'impact': 'Baseline functioning before trauma. Healthy social connections, good academic performance, age-appropriate experimentation with alcohol.',
                'clinical_note': 'Pre-trauma baseline shows no vulnerability factors for substance use disorder',
                'personality_changes': [
                    {'trait': 'Extraversion', 'before': 70, 'after': 70},
                    {'trait': 'Conscientiousness', 'before': 65, 'after': 65}
                ]
            },
            {
                'age': 16,
                'category': 'sexual_trauma',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'The Assault',
                'description': "Aisha was sexually assaulted at a party by someone she trusted. She didn't tell anyone for months. She experienced intrusive memories, nightmares, and felt constantly on edge.",
                'impact': 'Traumatic event triggered PTSD symptoms. Developed hypervigilance, intrusive thoughts, emotional numbing. Began avoiding social situations. Academic performance declined.',
                'clinical_note': 'Untreated PTSD creates vulnerability for self-medication with substances',
                'symptoms_developed': [
                    {'name': 'Intrusive memories', 'severity': 9},
                    {'name': 'Hypervigilance', 'severity': 8},
                    {'name': 'Emotional numbing', 'severity': 7},
                    {'name': 'Anxiety', 'severity': 9},
                    {'name': 'Sleep disturbance', 'severity': 8}
                ],
                'personality_changes': [
                    {'trait': 'Emotional Sensitivity', 'before': 60, 'after': 85},
                    {'trait': 'Extraversion', 'before': 70, 'after': 50},
                    {'trait': 'Conscientiousness', 'before': 65, 'after': 55}
                ]
            },
            {
                'age': 17,
                'category': 'substance_initiation',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Discovery of Relief',
                'description': 'Aisha went to a party and drank heavily. For the first time since the assault, she felt relaxed. The intrusive memories faded. She felt like herself again. She started drinking every weekend.',
                'impact': 'Discovered alcohol as self-medication for PTSD symptoms. Negative reinforcement loop began - alcohol temporarily relieved distress, reinforcing use. Moved from experimentation to regular use.',
                'clinical_note': 'Critical moment where substance becomes functional coping mechanism for trauma',
                'symptoms_developed': [
                    {'name': 'Regular alcohol use', 'severity': 5},
                    {'name': 'PTSD symptoms', 'severity': 7},
                    {'name': 'Anxiety', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 55, 'after': 50}
                ]
            },
            {
                'age': 19,
                'category': 'substance_escalation',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Escalation',
                'description': 'Aisha started college but struggled with flashbacks and anxiety. She began drinking daily to cope. She drank before class to calm her nerves, after class to relax. Her tolerance increased - she needed more to feel the same relief.',
                'impact': 'Progression to risky use/abuse. Tolerance developed. Drinking became primary coping mechanism. Academic and social consequences emerged. Negative reinforcement loop intensified.',
                'clinical_note': 'Transition from regular use to abuse - tolerance and functional impairment emerge',
                'symptoms_developed': [
                    {'name': 'Daily alcohol use', 'severity': 7},
                    {'name': 'Tolerance', 'severity': 6},
                    {'name': 'Using in risky situations', 'severity': 6},
                    {'name': 'Academic problems', 'severity': 7},
                    {'name': 'PTSD symptoms', 'severity': 8}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 50, 'after': 40},
                    {'trait': 'Extraversion', 'before': 50, 'after': 45},
                    {'trait': 'Emotional Sensitivity', 'before': 85, 'after': 90}
                ]
            },
            {
                'age': 21,
                'category': 'physical_dependence',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Physical Dependence',
                'description': 'Aisha tried to stop drinking for a week and experienced severe withdrawal - shaking, sweating, anxiety, nausea. She was terrified and started drinking again immediately. She realized she was physically dependent.',
                'impact': 'Crossed threshold into physical dependence. Withdrawal symptoms emerged. Loss of control - unable to stop despite wanting to. Life began revolving around obtaining and using alcohol.',
                'clinical_note': 'Physical dependence indicates neurobiological changes - now requires medical detox to quit safely',
                'symptoms_developed': [
                    {'name': 'Physical dependence', 'severity': 8},
                    {'name': 'Withdrawal symptoms', 'severity': 8},
                    {'name': 'Loss of control', 'severity': 8},
                    {'name': 'Failed quit attempts', 'severity': 7},
                    {'name': 'Depression', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 40, 'after': 30}
                ]
            },
            {
                'age': 23,
                'category': 'severe_addiction',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Severe Addiction',
                'description': "Aisha dropped out of college. She lost her job for showing up intoxicated. Her family staged an intervention. She drank from the moment she woke up to prevent withdrawal. She knew she was destroying her life but couldn't stop.",
                'impact': 'Full addiction/severe SUD. Compulsive use despite devastating consequences. Neurobiological changes made quitting feel impossible. Shame and hopelessness intensified.',
                'clinical_note': 'Severe SUD with complete life disruption - requires intensive treatment',
                'symptoms_developed': [
                    {'name': 'Severe alcohol dependence', 'severity': 10},
                    {'name': 'Compulsive use', 'severity': 10},
                    {'name': 'Continued use despite harm', 'severity': 10},
                    {'name': 'Withdrawal symptoms', 'severity': 9},
                    {'name': 'Depression', 'severity': 8},
                    {'name': 'Shame and guilt', 'severity': 10}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 30, 'after': 25},
                    {'trait': 'Extraversion', 'before': 45, 'after': 40}
                ]
            }
        ],
        predefined_interventions=[
            {
                'age': 24,
                'therapy_type': 'Inpatient rehab + 12-step',
                'duration': '30_sessions',
                'intensity': 'daily_inpatient',
                'rationale': 'First treatment episode. Achieved initial sobriety but relapsed quickly. Learned about disease model and coping skills. Underlying PTSD not adequately addressed.',
                'description': 'Aisha entered inpatient treatment. She completed medical detox and 30 days of rehab. She learned about trauma and addiction. She felt hopeful. She relapsed 2 weeks after discharge.',
                'outcomes': [
                    {'metric': 'Days of sobriety', 'improvement': 100},
                    {'metric': 'Coping skills', 'improvement': 40},
                    {'metric': 'PTSD symptoms', 'improvement': 20}
                ]
            },
            {
                'age': 26,
                'therapy_type': 'Trauma-focused CBT + EMDR + MAT',
                'duration': '60_sessions',
                'intensity': 'weekly_intensive',
                'rationale': 'Current treatment addressing both trauma and addiction. Learning to process trauma without alcohol. Developing alternative coping mechanisms. Fragile but hopeful.',
                'description': "After multiple relapses, Aisha entered a program specializing in trauma and addiction. She's working on PTSD with EMDR therapy while maintaining sobriety. It's the hardest thing she's ever done.",
                'outcomes': [
                    {'metric': 'Days of sobriety', 'improvement': 80},
                    {'metric': 'PTSD symptoms', 'improvement': 50},
                    {'metric': 'Coping skills', 'improvement': 60},
                    {'metric': 'Quality of life', 'improvement': 45}
                ]
            }
        ],
        expected_outcomes={
            'personality_changes': {
                'openness': 0.60,
                'conscientiousness': 0.30,
                'extraversion': 0.40,
                'agreeableness': 0.55,
                'neuroticism': 0.90
            },
            'symptoms_developed': [
                'Alcohol dependence (in recovery)',
                'Cravings',
                'PTSD symptoms (improving)',
                'Anxiety',
                'Depression'
            ],
            'attachment_changes': 'fearful',
            'trauma_markers': [
                'Self-medication pattern',
                'Physical dependence history',
                'Trauma-addiction cycle',
                'Recovery fragility'
            ]
        },
        citations=[
            "Khantzian, E. (1997). The self-medication hypothesis of substance use disorders",
            "Najavits, L. (2002). Seeking Safety: A treatment manual for PTSD and substance abuse",
            "Brady, K. et al. (2004). Comorbidity of psychiatric disorders and posttraumatic stress disorder",
            "Ouimette, P. & Brown, P. (2003). Trauma and Substance Abuse: Causes, Consequences, and Treatment"
        ],
        remix_suggestions=[
            {
                'title': 'Early Trauma Treatment',
                'changes': ['Add trauma-focused therapy at age 16 immediately after assault'],
                'hypothesis': 'Early PTSD treatment could prevent self-medication pathway entirely'
            },
            {
                'title': 'Integrated Treatment from Start',
                'changes': ['Replace age 24 standard rehab with trauma-informed integrated treatment'],
                'hypothesis': 'Integrated approach at first treatment could prevent multiple relapses'
            }
        ]
    )


def create_mdd_template():
    """Create Major Depressive Disorder (Kindling Model) template."""
    return ClinicalTemplate(
        name="Sofia - Major Depressive Disorder (Kindling)",
        disorder_type="MDD",
        description="Sofia's story illustrates the kindling/stress-sensitization model of recurrent depression. Her first episode at 19 required major stress (father's death). Each subsequent episode required less stress to trigger. By age 30, depression has become chronic with minimal triggers needed.",
        clinical_rationale="""This template demonstrates the kindling or stress-sensitization model of recurrent major depression.

Key progression:
1. Cognitive vulnerability (age 16): Perfectionism, self-criticism, rumination
2. First episode (age 19): Triggered by severe stress (bereavement)
3. Recovery (age 20): Full remission with treatment
4. Second episode (age 23): Triggered by moderate stress (relationship breakup)
5. Partial recovery (age 24): Residual symptoms persist
6. Third episode (age 27): Triggered by minor stress (work stress)
7. Chronic depression (age 30+): Persistent low-grade depression, shortened well periods

Critical insight: Each episode changes the brain, making subsequent episodes more likely and easier to trigger. This is called "kindling" - like kindling a fire, less "fuel" (stress) is needed each time. Early intervention and achieving full remission (not just symptom reduction) after each episode is crucial to prevent progression to chronic depression.""",
        baseline_age=16,
        baseline_gender="female",
        baseline_background="Sofia grew up with a critical, perfectionistic mother. She learned to be hard on herself and felt she could never meet expectations. She was anxious and self-critical but not yet depressed.",
        baseline_personality={
            'openness': 0.65,
            'conscientiousness': 0.70,
            'extraversion': 0.55,
            'agreeableness': 0.75,
            'neuroticism': 0.70
        },
        baseline_attachment_style="anxious",
        predefined_experiences=[
            {
                'age': 16,
                'category': 'family_dynamics',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Early Vulnerability',
                'description': 'Sofia grew up with a critical, perfectionistic mother. She learned to be hard on herself and felt she could never meet expectations. She was anxious and self-critical but not yet depressed.',
                'impact': 'Developed cognitive vulnerability to depression - negative self-schema, perfectionism, rumination. These cognitive patterns would later interact with stress to trigger depression.',
                'clinical_note': 'Cognitive vulnerability (negative self-schema) creates diathesis for depression',
                'symptoms_developed': [
                    {'name': 'Anxiety', 'severity': 6},
                    {'name': 'Perfectionism', 'severity': 8},
                    {'name': 'Self-criticism', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Emotional Sensitivity', 'before': 60, 'after': 70},
                    {'trait': 'Agreeableness', 'before': 75, 'after': 70}
                ]
            },
            {
                'age': 19,
                'category': 'bereavement',
                'valence': 'negative',
                'intensity': 'severe',
                'title': "First Episode - Father's Death",
                'description': "Sofia's father died suddenly in a car accident. She was devastated. Within weeks, she couldn't get out of bed. She stopped eating, stopped seeing friends, stopped caring about school. Everything felt pointless.",
                'impact': 'First major depressive episode triggered by significant life stress (bereavement). Met full criteria for MDD. Required major stressor to trigger this initial episode.',
                'clinical_note': 'First episode typically requires major life stress - meets diathesis-stress model',
                'symptoms_developed': [
                    {'name': 'Depressed mood', 'severity': 10},
                    {'name': 'Anhedonia', 'severity': 9},
                    {'name': 'Fatigue', 'severity': 9},
                    {'name': 'Worthlessness', 'severity': 8},
                    {'name': 'Concentration problems', 'severity': 8},
                    {'name': 'Sleep disturbance', 'severity': 8},
                    {'name': 'Appetite loss', 'severity': 7},
                    {'name': 'Suicidal ideation', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 70, 'after': 50},
                    {'trait': 'Extraversion', 'before': 55, 'after': 40},
                    {'trait': 'Emotional Sensitivity', 'before': 70, 'after': 80}
                ]
            },
            {
                'age': 23,
                'category': 'relationship_loss',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Second Episode - Relationship Breakup',
                'description': "Sofia's long-term relationship ended. She was sad but not devastated. Yet within weeks, she spiraled into severe depression again. She was shocked - the breakup didn't seem bad enough to trigger this.",
                'impact': "Second episode triggered by moderate stress (less severe than first episode). Illustrates 'kindling' - brain becomes sensitized, requiring less stress to trigger episodes.",
                'clinical_note': 'Kindling effect evident - less stress required for second episode than first',
                'symptoms_developed': [
                    {'name': 'Depressed mood', 'severity': 9},
                    {'name': 'Anhedonia', 'severity': 9},
                    {'name': 'Fatigue', 'severity': 8},
                    {'name': 'Worthlessness', 'severity': 9},
                    {'name': 'Concentration problems', 'severity': 7},
                    {'name': 'Suicidal ideation', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 60, 'after': 45},
                    {'trait': 'Extraversion', 'before': 50, 'after': 35},
                    {'trait': 'Emotional Sensitivity', 'before': 80, 'after': 85}
                ]
            },
            {
                'age': 27,
                'category': 'work_stress',
                'valence': 'negative',
                'intensity': 'mild',
                'title': 'Third Episode - Minimal Trigger',
                'description': 'Sofia had a stressful week at work - nothing major. But it was enough. The depression returned with full force. She realized her brain had become hypersensitive to stress.',
                'impact': 'Third episode triggered by minor stress. Clear evidence of kindling/sensitization. Brain changes from previous episodes made her increasingly vulnerable.',
                'clinical_note': 'Advanced kindling - minimal stress sufficient to trigger full episode',
                'symptoms_developed': [
                    {'name': 'Depressed mood', 'severity': 8},
                    {'name': 'Anhedonia', 'severity': 8},
                    {'name': 'Fatigue', 'severity': 9},
                    {'name': 'Worthlessness', 'severity': 8},
                    {'name': 'Hopelessness', 'severity': 9},
                    {'name': 'Suicidal ideation', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 50, 'after': 40}
                ]
            },
            {
                'age': 30,
                'category': 'chronic_depression',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Chronic Depression',
                'description': 'Sofia has had three more episodes since age 27. The periods between episodes have shortened. She now has persistent low-grade depression even between major episodes. Depression has become chronic.',
                'impact': 'Progression to chronic/recurrent depression. Shorter well periods. Persistent residual symptoms. Significant functional impairment. Increased risk of treatment resistance.',
                'clinical_note': 'Chronic depression with persistent residual symptoms between episodes',
                'symptoms_developed': [
                    {'name': 'Depressed mood', 'severity': 6},
                    {'name': 'Anhedonia', 'severity': 7},
                    {'name': 'Fatigue', 'severity': 8},
                    {'name': 'Worthlessness', 'severity': 7},
                    {'name': 'Concentration problems', 'severity': 7},
                    {'name': 'Social withdrawal', 'severity': 7}
                ]
            }
        ],
        predefined_interventions=[
            {
                'age': 20,
                'therapy_type': 'Cognitive Behavioral Therapy (CBT)',
                'duration': '20_sessions',
                'intensity': 'weekly',
                'rationale': 'Recovery from first episode with treatment. Symptoms remitted. However, neurobiological changes from first episode increased vulnerability to recurrence.',
                'description': "After 8 months, Sofia's depression lifted. She started therapy and antidepressants. She felt like herself again and believed the depression was behind her. She returned to school and rebuilt her life.",
                'outcomes': [
                    {'metric': 'Depressive symptoms', 'improvement': 80},
                    {'metric': 'Functioning', 'improvement': 75},
                    {'metric': 'Quality of life', 'improvement': 70}
                ]
            },
            {
                'age': 24,
                'therapy_type': 'CBT + medication adjustment',
                'duration': '15_sessions',
                'intensity': 'weekly',
                'rationale': 'Partial remission. Residual symptoms persisted. This incomplete recovery increased risk of rapid relapse.',
                'description': "Sofia increased her medication and returned to therapy. The depression improved but didn't fully lift. She had lingering fatigue, anhedonia, and negative thoughts. She functioned but didn't feel like herself.",
                'outcomes': [
                    {'metric': 'Depressive symptoms', 'improvement': 60},
                    {'metric': 'Functioning', 'improvement': 55}
                ]
            },
            {
                'age': 32,
                'therapy_type': 'Maintenance CBT + medication',
                'duration': '100_sessions',
                'intensity': 'monthly_maintenance',
                'rationale': 'Shift to maintenance/management approach. Acceptance of chronic condition. Focus on quality of life and relapse prevention rather than complete remission.',
                'description': "Sofia continues medication and therapy. She's learning to accept that depression may always be part of her life. She focuses on managing symptoms and preventing full relapses rather than expecting to be 'cured.'",
                'outcomes': [
                    {'metric': 'Episode frequency', 'improvement': 40},
                    {'metric': 'Episode severity', 'improvement': 35},
                    {'metric': 'Coping skills', 'improvement': 60},
                    {'metric': 'Acceptance', 'improvement': 50}
                ]
            }
        ],
        expected_outcomes={
            'personality_changes': {
                'openness': 0.65,
                'conscientiousness': 0.40,
                'extraversion': 0.35,
                'agreeableness': 0.70,
                'neuroticism': 0.85
            },
            'symptoms_developed': [
                'Chronic depressed mood',
                'Anhedonia',
                'Fatigue',
                'Worthlessness',
                'Concentration problems',
                'Social withdrawal'
            ],
            'attachment_changes': 'anxious',
            'trauma_markers': [
                'Recurrent depressive episodes',
                'Stress sensitization',
                'Chronic residual symptoms',
                'Treatment resistance'
            ]
        },
        citations=[
            "Post, R. (1992). Transduction of psychosocial stress into the neurobiology of recurrent affective disorder",
            "Monroe, S. & Harkness, K. (2005). Life stress, the 'kindling' hypothesis, and the recurrence of depression",
            "Kendler, K. et al. (2000). Stressful life events and previous episodes in the etiology of major depression",
            "Judd, L. et al. (1998). A prospective 12-year study of subsyndromal and syndromal depressive symptoms"
        ],
        remix_suggestions=[
            {
                'title': 'Maintenance Treatment After First Episode',
                'changes': ['Continue medication and therapy for 2 years after age 20 remission'],
                'hypothesis': 'Maintenance treatment after first episode could prevent kindling and reduce recurrence by 50%'
            },
            {
                'title': 'Full Remission Focus',
                'changes': ['Extend age 24 treatment until complete symptom remission, not just improvement'],
                'hypothesis': 'Achieving full remission (not partial) reduces rapid relapse risk significantly'
            }
        ]
    )


def create_anorexia_template():
    """Create Anorexia Nervosa template."""
    return ClinicalTemplate(
        name="Lily - Anorexia Nervosa",
        disorder_type="Anorexia",
        description="Lily's journey demonstrates the perfectionism-control pathway to anorexia nervosa. From 'perfect child' to life-threatening eating disorder, her story shows how the need for control during puberty combined with perfectionism creates this devastating illness. Multiple relapses highlight that psychological recovery is harder than physical recovery.",
        clinical_rationale="""This template demonstrates the classic perfectionism-control pathway to anorexia nervosa.

Key developmental factors:
1. Perfectionist personality (age 10): High achievement, people-pleasing, anxiety-prone
2. Puberty as loss of control (age 13): Body changes feel uncontrollable, multiple stressors
3. Dieting as solution (age 14): Restriction provides sense of control and accomplishment
4. Escalation (age 15): Food rules become rigid, eating disorder crystallizes
5. Medical crisis (age 16): Severe malnutrition requires hospitalization
6. Physical vs psychological recovery gap (age 16-17): Weight restored but beliefs unchanged
7. Relapse (age 17): Body image distortion persists despite treatment
8. Long-term recovery (age 18-19): Years of treatment needed for psychological change

Critical insights:
- Anorexia served a function: provided control when life felt chaotic
- Physical recovery (weight restoration) is achievable but psychological recovery (body image, fear of weight gain, perfectionism) is profoundly difficult
- Treatment addressing only weight without addressing underlying perfectionism, anxiety, and need for control typically fails
- Eating disorder becomes ego-syntonic (part of identity), making recovery feel like losing oneself""",
        baseline_age=10,
        baseline_gender="female",
        baseline_background="Lily was a model student and daughter - straight A's, followed all rules, never caused problems. Teachers praised her, parents were proud. But beneath the surface, she was anxious and afraid of disappointing anyone.",
        baseline_personality={
            'openness': 0.60,
            'conscientiousness': 0.75,
            'extraversion': 0.50,
            'agreeableness': 0.70,
            'neuroticism': 0.70
        },
        baseline_attachment_style="anxious",
        predefined_experiences=[
            {
                'age': 10,
                'category': 'personality_development',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'The Perfect Child',
                'description': "Lily was a model student and daughter. She got straight A's, followed all rules, and never caused problems. Teachers praised her. Parents were proud. But beneath the surface, she was anxious and afraid of disappointing anyone.",
                'impact': 'Developed perfectionistic personality style. Self-worth became tied to achievement and approval. High need for control. Anxiety-prone. These traits created vulnerability to eating disorder.',
                'clinical_note': 'Perfectionism, need for control, and anxiety create vulnerability for eating disorders',
                'symptoms_developed': [
                    {'name': 'Perfectionism', 'severity': 8},
                    {'name': 'Anxiety', 'severity': 6},
                    {'name': 'Need for control', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 75, 'after': 85},
                    {'trait': 'Agreeableness', 'before': 70, 'after': 75},
                    {'trait': 'Emotional Sensitivity', 'before': 70, 'after': 75}
                ]
            },
            {
                'age': 13,
                'category': 'puberty_stress',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Puberty and Loss of Control',
                'description': "Lily's body began changing rapidly. She developed curves, gained weight, got her period. She felt her body was betraying her. Everything felt out of control. Her parents were divorcing. School became more competitive.",
                'impact': 'Multiple stressors converged: puberty, family conflict, academic pressure. Body changes felt uncontrollable. Anxiety intensified. Began seeking ways to regain sense of control.',
                'clinical_note': 'Puberty as loss of control plus family stress creates critical vulnerability period',
                'symptoms_developed': [
                    {'name': 'Anxiety', 'severity': 8},
                    {'name': 'Body dissatisfaction', 'severity': 6},
                    {'name': 'Need for control', 'severity': 8},
                    {'name': 'Perfectionism', 'severity': 9}
                ],
                'personality_changes': [
                    {'trait': 'Emotional Sensitivity', 'before': 75, 'after': 80},
                    {'trait': 'Extraversion', 'before': 50, 'after': 45}
                ]
            },
            {
                'age': 14,
                'category': 'diet_initiation',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'The Diet Begins',
                'description': "Lily started 'eating healthy' and exercising. She cut out junk food, counted calories, and felt proud of her discipline. Friends complimented her on losing weight. She felt in control for the first time in months.",
                'impact': 'Initial dieting phase. Positive reinforcement for weight loss. Sense of accomplishment and control. Perfectionism channeled into food/exercise. Eating disorder behaviors began.',
                'clinical_note': 'Positive reinforcement for dieting and control feeling initiates eating disorder',
                'symptoms_developed': [
                    {'name': 'Calorie restriction', 'severity': 5},
                    {'name': 'Excessive exercise', 'severity': 5},
                    {'name': 'Body checking', 'severity': 6},
                    {'name': 'Fear of weight gain', 'severity': 6}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 85, 'after': 90}
                ]
            },
            {
                'age': 15,
                'category': 'eating_disorder_escalation',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Escalation',
                'description': "Lily's food rules became more rigid. She cut out entire food groups. She exercised even when exhausted. She weighed herself multiple times daily. She couldn't eat without calculating every calorie. Food consumed her thoughts.",
                'impact': 'Progression to full eating disorder. Rigid food rules. Compulsive behaviors. Preoccupation with food/weight. Social withdrawal. Academic performance still high (perfectionism intact).',
                'clinical_note': 'Full eating disorder criteria met - rigid rules, preoccupation, compulsions',
                'symptoms_developed': [
                    {'name': 'Severe restriction', 'severity': 8},
                    {'name': 'Fear of weight gain', 'severity': 9},
                    {'name': 'Body image distortion', 'severity': 8},
                    {'name': 'Excessive exercise', 'severity': 8},
                    {'name': 'Food rituals', 'severity': 7},
                    {'name': 'Social withdrawal', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 90, 'after': 95},
                    {'trait': 'Extraversion', 'before': 45, 'after': 35},
                    {'trait': 'Emotional Sensitivity', 'before': 80, 'after': 85}
                ]
            },
            {
                'age': 16,
                'category': 'medical_crisis',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Medical Crisis',
                'description': "Lily's weight dropped to 85 pounds (BMI 14.5). Her heart rate was dangerously low. She fainted at school. She was hospitalized involuntarily. She was terrified of being forced to gain weight.",
                'impact': 'Medical complications required hospitalization. Involuntary treatment felt like loss of control. Resistance to weight restoration. Eating disorder became ego-syntonic (felt like part of identity).',
                'clinical_note': 'Medical complications requiring hospitalization - life-threatening severity',
                'symptoms_developed': [
                    {'name': 'Severe malnutrition', 'severity': 10},
                    {'name': 'Fear of weight gain', 'severity': 10},
                    {'name': 'Body image distortion', 'severity': 10},
                    {'name': 'Bradycardia', 'severity': 9},
                    {'name': 'Amenorrhea', 'severity': 10},
                    {'name': 'Resistance to treatment', 'severity': 9}
                ]
            },
            {
                'age': 17,
                'category': 'relapse',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Relapse',
                'description': "Six months after discharge, Lily started restricting again. The weight she'd gained felt unbearable. She couldn't tolerate seeing her body in the mirror. She felt like she'd lost herself.",
                'impact': 'Relapse after initial recovery. Body image distortion and fear of weight gain persisted despite weight restoration. Illustrates why psychological recovery is harder than physical recovery.',
                'clinical_note': 'Relapse illustrates gap between physical and psychological recovery',
                'symptoms_developed': [
                    {'name': 'Restrictive eating', 'severity': 7},
                    {'name': 'Fear of weight gain', 'severity': 10},
                    {'name': 'Body image distortion', 'severity': 9},
                    {'name': 'Excessive exercise', 'severity': 6},
                    {'name': 'Depression', 'severity': 8}
                ]
            }
        ],
        predefined_interventions=[
            {
                'age': 16,
                'therapy_type': 'Family-Based Treatment (FBT)',
                'duration': '90_sessions',
                'intensity': 'daily_inpatient',
                'rationale': 'Weight restoration achieved through structured refeeding. Medical stabilization. However, psychological recovery lagged behind physical recovery. Body image distortion persisted.',
                'description': "Lily spent 3 months in an eating disorder unit. She was forced to gain weight through meal plans and supervision. She learned about the medical dangers. She was miserable and felt like a failure.",
                'outcomes': [
                    {'metric': 'Weight restoration', 'improvement': 100},
                    {'metric': 'Medical stabilization', 'improvement': 90},
                    {'metric': 'Body image', 'improvement': 20},
                    {'metric': 'Fear of weight gain', 'improvement': 30}
                ]
            },
            {
                'age': 18,
                'therapy_type': 'CBT for eating disorders',
                'duration': '60_sessions',
                'intensity': 'weekly_intensive',
                'rationale': "More intensive psychological treatment. Learning to identify and challenge eating disorder thoughts. Developing alternative coping mechanisms. Addressing perfectionism and need for control.",
                'description': "Lily entered an intensive outpatient program focusing on cognitive-behavioral therapy for eating disorders. She's working on challenging distorted thoughts about food, weight, and control.",
                'outcomes': [
                    {'metric': 'Eating disorder thoughts', 'improvement': 40},
                    {'metric': 'Coping skills', 'improvement': 50},
                    {'metric': 'Weight maintenance', 'improvement': 60},
                    {'metric': 'Body image', 'improvement': 35}
                ]
            },
            {
                'age': 19,
                'therapy_type': 'Ongoing CBT + support group',
                'duration': '40_sessions',
                'intensity': 'weekly',
                'rationale': 'Partial recovery. Weight restored but psychological symptoms persist. Learning to tolerate discomfort without restricting. Building life outside eating disorder. Recovery is long-term process.',
                'description': "Lily is maintaining a healthy weight but still struggles daily with eating disorder thoughts. She's learning that recovery isn't linear. Some days are harder than others. She's working on building an identity beyond the eating disorder.",
                'outcomes': [
                    {'metric': 'Quality of life', 'improvement': 50},
                    {'metric': 'Social functioning', 'improvement': 45},
                    {'metric': 'Eating disorder behaviors', 'improvement': 60},
                    {'metric': 'Body acceptance', 'improvement': 40}
                ]
            }
        ],
        expected_outcomes={
            'personality_changes': {
                'openness': 0.60,
                'conscientiousness': 0.95,
                'extraversion': 0.30,
                'agreeableness': 0.75,
                'neuroticism': 0.85
            },
            'symptoms_developed': [
                'Eating disorder thoughts',
                'Fear of weight gain',
                'Body image concerns',
                'Anxiety',
                'Perfectionism'
            ],
            'attachment_changes': 'anxious',
            'trauma_markers': [
                'Body image distortion',
                'Fear of weight gain',
                'Control-seeking behavior',
                'Perfectionism',
                'Recovery fragility'
            ]
        },
        citations=[
            "Fairburn, C. & Harrison, P. (2003). Eating disorders",
            "Lock, J. & Le Grange, D. (2012). Treatment Manual for Anorexia Nervosa: A Family-Based Approach",
            "Kaye, W. et al. (2004). Neurobiology of anorexia and bulimia nervosa",
            "Schmidt, U. & Treasure, J. (2006). Anorexia nervosa: Valued and visible"
        ],
        remix_suggestions=[
            {
                'title': 'Early Anxiety Treatment',
                'changes': ['Add anxiety-focused therapy at age 10-13', 'Teach emotion regulation before puberty'],
                'hypothesis': 'Early anxiety treatment could prevent need for control manifesting as eating disorder'
            },
            {
                'title': 'Psychological Recovery Focus',
                'changes': ['Extend age 16 treatment to include cognitive work before discharge', 'Continue therapy throughout maintenance phase'],
                'hypothesis': 'Addressing psychological factors during weight restoration could prevent relapse'
            }
        ]
    )


def create_ocd_template():
    """Create Obsessive-Compulsive Disorder template."""
    return ClinicalTemplate(
        name="Ryan - Obsessive-Compulsive Disorder",
        disorder_type="OCD",
        description="Ryan's OCD journey shows the typical childhood-onset trajectory with contamination and symmetry obsessions. From normal childhood rituals to time-consuming compulsions, his story demonstrates the OCD cycle, role of family accommodation, importance of specialized ERP treatment, and chronic relapsing nature of the disorder.",
        clinical_rationale="""This template demonstrates the classic developmental trajectory of OCD.

Key developmental features:
1. Normal childhood rituals (age 7): Part of typical development
2. Onset after illness trigger (age 9): Contamination fears emerge after stomach flu
3. OCD cycle established: Obsession → Anxiety → Compulsion → Temporary relief
4. Family accommodation (age 11): Well-intentioned but reinforces OCD
5. Symptom expansion (age 12): New themes (symmetry) emerge
6. Insight with shame (age 14): Knows thoughts are irrational but can't stop
7. Failed treatment (age 16): Cognitive therapy alone insufficient
8. Evidence-based treatment (age 21): ERP (Exposure Response Prevention) works
9. Relapse during stress (age 23): Chronic waxing-waning pattern
10. Ongoing management (age 24+): Chronic condition requiring maintenance

Critical insights:
- OCD maintained by negative reinforcement - compulsions temporarily reduce anxiety
- Family accommodation is one of strongest predictors of severity
- Cognitive therapy alone insufficient - need exposure-based treatment (ERP)
- Insight doesn't equal control - knowing thoughts are irrational doesn't stop them
- Chronic condition requiring ongoing management, not one-time cure""",
        baseline_age=7,
        baseline_gender="male",
        baseline_background="Ryan had normal childhood rituals - stuffed animals arranged in specific order, bedtime routine said in certain way. His parents thought it was cute. Most kids have some compulsive-like behaviors at this age.",
        baseline_personality={
            'openness': 0.55,
            'conscientiousness': 0.60,
            'extraversion': 0.60,
            'agreeableness': 0.65,
            'neuroticism': 0.60
        },
        baseline_attachment_style="secure",
        predefined_experiences=[
            {
                'age': 7,
                'category': 'normal_development',
                'valence': 'neutral',
                'intensity': 'mild',
                'title': 'Normal Childhood Rituals',
                'description': 'Ryan had bedtime rituals - stuffed animals had to be arranged in a specific order, goodnight had to be said in a certain way. His parents thought it was cute. Most kids have some compulsive-like behaviors at this age.',
                'impact': 'Normal developmental compulsive-like behaviors. Part of typical childhood. Not yet pathological. Genetic vulnerability present but not yet manifest.',
                'clinical_note': 'Normal childhood rituals - not yet pathological OCD',
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 60, 'after': 65}
                ]
            },
            {
                'age': 9,
                'category': 'ocd_onset',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Contamination Fears Emerge',
                'description': 'After a stomach flu, Ryan became terrified of germs. He started washing his hands repeatedly. He avoided touching doorknobs. He made his mom wash his clothes multiple times. The fears felt overwhelming and real.',
                'impact': 'Onset of true OCD symptoms. Contamination obsessions and washing compulsions emerged. Triggered by illness (common trigger). OCD cycle began: obsession → anxiety → compulsion → temporary relief.',
                'clinical_note': 'OCD onset triggered by illness - contamination theme begins',
                'symptoms_developed': [
                    {'name': 'Contamination obsessions', 'severity': 7},
                    {'name': 'Washing compulsions', 'severity': 7},
                    {'name': 'Avoidance behaviors', 'severity': 6},
                    {'name': 'Anxiety', 'severity': 8}
                ],
                'personality_changes': [
                    {'trait': 'Emotional Sensitivity', 'before': 60, 'after': 70},
                    {'trait': 'Conscientiousness', 'before': 65, 'after': 75},
                    {'trait': 'Extraversion', 'before': 60, 'after': 55}
                ]
            },
            {
                'age': 11,
                'category': 'family_accommodation',
                'valence': 'negative',
                'intensity': 'moderate',
                'title': 'Family Accommodation',
                'description': "Ryan's parents started accommodating his OCD. His mom washed his clothes multiple times. His dad opened doors for him. They reassured him constantly that things were clean. This made the OCD worse.",
                'impact': 'Family accommodation reinforced OCD behaviors. Reassurance-seeking became a compulsion. OCD symptoms expanded. Time consumed by rituals increased. Academic performance began to decline.',
                'clinical_note': 'Family accommodation reinforces OCD - strong predictor of severity',
                'symptoms_developed': [
                    {'name': 'Contamination obsessions', 'severity': 8},
                    {'name': 'Washing compulsions', 'severity': 8},
                    {'name': 'Reassurance-seeking', 'severity': 7},
                    {'name': 'Avoidance behaviors', 'severity': 7},
                    {'name': 'Time consumed by rituals', 'severity': 7}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 75, 'after': 80},
                    {'trait': 'Extraversion', 'before': 55, 'after': 50}
                ]
            },
            {
                'age': 12,
                'category': 'symptom_expansion',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Symmetry Obsessions Emerge',
                'description': "Ryan developed new obsessions about symmetry and order. Objects had to be arranged 'just right.' He touched things in patterns. He repeated actions until they felt right. If interrupted, he had to start over.",
                'impact': 'Symptom expansion - new obsession theme emerged. Symmetry/ordering compulsions added to contamination fears. OCD became more time-consuming and impairing. Social withdrawal increased.',
                'clinical_note': 'Symptom expansion typical in OCD - new themes emerge over time',
                'symptoms_developed': [
                    {'name': 'Contamination obsessions', 'severity': 8},
                    {'name': 'Washing compulsions', 'severity': 8},
                    {'name': 'Symmetry obsessions', 'severity': 7},
                    {'name': 'Ordering compulsions', 'severity': 7},
                    {'name': 'Repeating behaviors', 'severity': 6},
                    {'name': 'Time consumed by rituals', 'severity': 8}
                ],
                'personality_changes': [
                    {'trait': 'Conscientiousness', 'before': 80, 'after': 85},
                    {'trait': 'Extraversion', 'before': 50, 'after': 45},
                    {'trait': 'Emotional Sensitivity', 'before': 70, 'after': 75}
                ]
            },
            {
                'age': 14,
                'category': 'insight_development',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Insight and Shame',
                'description': "Ryan realized his obsessions were irrational. He knew washing his hands 50 times wouldn't really prevent illness. But he couldn't stop. The anxiety was too overwhelming. He felt ashamed and hid his rituals from friends.",
                'impact': "Developed insight (knew thoughts were irrational) but couldn't stop compulsions. Shame and secrecy increased. Social isolation worsened. Depression emerged secondary to OCD.",
                'clinical_note': 'Insight without control - hallmark of OCD. Shame leads to hiding symptoms',
                'symptoms_developed': [
                    {'name': 'Contamination obsessions', 'severity': 8},
                    {'name': 'Washing compulsions', 'severity': 9},
                    {'name': 'Symmetry obsessions', 'severity': 7},
                    {'name': 'Ordering compulsions', 'severity': 7},
                    {'name': 'Shame', 'severity': 8},
                    {'name': 'Depression', 'severity': 6},
                    {'name': 'Time consumed by rituals', 'severity': 9}
                ],
                'personality_changes': [
                    {'trait': 'Extraversion', 'before': 45, 'after': 40},
                    {'trait': 'Emotional Sensitivity', 'before': 75, 'after': 80}
                ]
            },
            {
                'age': 19,
                'category': 'functional_impairment',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'College Struggles',
                'description': "Ryan started college but struggled. His rituals took hours each day. He was late to class because of checking rituals. His roommate complained about his constant washing. He felt his life was consumed by OCD.",
                'impact': 'Functional impairment increased in college. OCD interfered with academic performance, social relationships, and daily functioning. Checking compulsions emerged. Depression worsened.',
                'clinical_note': 'Significant functional impairment - OCD consuming multiple hours daily',
                'symptoms_developed': [
                    {'name': 'Contamination obsessions', 'severity': 8},
                    {'name': 'Washing compulsions', 'severity': 9},
                    {'name': 'Symmetry obsessions', 'severity': 7},
                    {'name': 'Ordering compulsions', 'severity': 7},
                    {'name': 'Checking compulsions', 'severity': 6},
                    {'name': 'Time consumed by rituals', 'severity': 9},
                    {'name': 'Depression', 'severity': 7}
                ]
            },
            {
                'age': 23,
                'category': 'relapse',
                'valence': 'negative',
                'intensity': 'severe',
                'title': 'Relapse During Stress',
                'description': 'Ryan graduated and started a stressful job. The OCD symptoms returned with full force. He started washing excessively again. The symmetry obsessions intensified. He realized OCD was a chronic condition requiring ongoing management.',
                'impact': 'Relapse triggered by stress. OCD symptoms waxing and waning over time. Recognized need for ongoing treatment and relapse prevention strategies.',
                'clinical_note': 'Stress-triggered relapse - OCD is chronic with waxing-waning pattern',
                'symptoms_developed': [
                    {'name': 'Contamination obsessions', 'severity': 7},
                    {'name': 'Washing compulsions', 'severity': 7},
                    {'name': 'Symmetry obsessions', 'severity': 6},
                    {'name': 'Ordering compulsions', 'severity': 6},
                    {'name': 'Time consumed by rituals', 'severity': 7}
                ]
            }
        ],
        predefined_interventions=[
            {
                'age': 16,
                'therapy_type': 'Cognitive therapy (not ERP)',
                'duration': '6_sessions',
                'intensity': 'weekly',
                'rationale': 'First treatment attempt with non-specialized therapy. Cognitive therapy alone insufficient for OCD. Needed exposure and response prevention (ERP). Minimal improvement. Dropout common in OCD.',
                'description': "Ryan started therapy. His therapist taught him about the OCD cycle and tried cognitive restructuring. Ryan understood intellectually but couldn't stop the compulsions. He dropped out after 6 sessions.",
                'outcomes': [
                    {'metric': 'Understanding of OCD', 'improvement': 60},
                    {'metric': 'Symptom reduction', 'improvement': 10}
                ]
            },
            {
                'age': 21,
                'therapy_type': 'Exposure and Response Prevention (ERP)',
                'duration': '30_sessions',
                'intensity': 'weekly_intensive',
                'rationale': 'Evidence-based treatment with ERP. Learned to tolerate anxiety without compulsions. Habituation occurred. Significant symptom reduction. However, treatment was difficult and dropout risk high.',
                'description': "Ryan found a therapist specializing in OCD who used Exposure and Response Prevention (ERP). He gradually exposed himself to feared situations without doing rituals. It was terrifying but it worked.",
                'outcomes': [
                    {'metric': 'Contamination obsessions', 'improvement': 50},
                    {'metric': 'Washing compulsions', 'improvement': 60},
                    {'metric': 'Time consumed by rituals', 'improvement': 55},
                    {'metric': 'Functional impairment', 'improvement': 50}
                ]
            },
            {
                'age': 24,
                'therapy_type': 'ERP + SSRI medication',
                'duration': '50_sessions',
                'intensity': 'monthly_maintenance',
                'rationale': 'Maintenance treatment with ERP + medication. Learning to manage chronic condition. Focus on functioning despite symptoms rather than complete elimination. Acceptance of OCD as part of life.',
                'description': "Ryan returned to ERP therapy and started medication (SSRI). He's learning to manage OCD as a chronic condition. He has good days and bad days. He uses ERP skills when symptoms flare. He's building a life despite OCD.",
                'outcomes': [
                    {'metric': 'Symptom management', 'improvement': 60},
                    {'metric': 'Quality of life', 'improvement': 55},
                    {'metric': 'Functional impairment', 'improvement': 65},
                    {'metric': 'Acceptance', 'improvement': 50}
                ]
            }
        ],
        expected_outcomes={
            'personality_changes': {
                'openness': 0.55,
                'conscientiousness': 0.85,
                'extraversion': 0.40,
                'agreeableness': 0.65,
                'neuroticism': 0.80
            },
            'symptoms_developed': [
                'Contamination obsessions',
                'Washing compulsions',
                'Symmetry obsessions',
                'Ordering compulsions',
                'Time consumed by rituals'
            ],
            'attachment_changes': 'secure',
            'trauma_markers': [
                'Chronic OCD pattern',
                'Stress sensitivity',
                'Need for ongoing management',
                'Insight without control'
            ]
        },
        citations=[
            "Abramowitz, J. et al. (2009). Exposure and response prevention for OCD",
            "Foa, E. et al. (2012). Randomized trial of prolonged exposure for OCD",
            "Piacentini, J. & Langley, A. (2004). Cognitive-behavioral therapy for children who have OCD",
            "Calvocoressi, L. et al. (1995). Family accommodation in OCD"
        ],
        remix_suggestions=[
            {
                'title': 'Early ERP Intervention',
                'changes': ['Replace age 16 cognitive therapy with specialized ERP', 'Reduce family accommodation at age 11'],
                'hypothesis': 'Early evidence-based treatment could prevent chronic severe course'
            },
            {
                'title': 'Family Intervention',
                'changes': ['Add family psychoeducation at age 9-11 to prevent accommodation'],
                'hypothesis': 'Preventing family accommodation could reduce symptom severity by 40%'
            }
        ]
    )


def seed_database(force_reseed=False):
    """Main function to seed the database with all clinical templates.

    Args:
        force_reseed: If True, delete existing templates without prompting
    """
    print("Starting database seed process...")

    # Create tables
    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    try:
        # Check if templates already exist
        existing_count = db.query(ClinicalTemplate).count()
        if existing_count > 0:
            print(f"\nWarning: {existing_count} templates already exist in database.")
            if force_reseed:
                print("Force reseed enabled - deleting existing templates...")
                db.query(ClinicalTemplate).delete()
                db.commit()
                print("Existing templates deleted.")
            else:
                print("To reseed, run: python scripts/seed_psych_templates.py --force")
                print("Seed process cancelled.")
                return

        # Create all templates
        print("\nCreating templates...")
        templates = [
            create_npd_template(),
            create_schizophrenia_template(),
            create_sud_template(),
            create_mdd_template(),
            create_anorexia_template(),
            create_ocd_template()
        ]

        # Add to database
        for template in templates:
            print(f"  Adding: {template.name}")
            db.add(template)

        # Commit transaction
        db.commit()
        print(f"\n[SUCCESS] Successfully seeded {len(templates)} clinical templates!")

        # Display summary
        print("\nSeeded templates:")
        for template in templates:
            print(f"  - {template.disorder_type}: {template.name}")

    except Exception as e:
        print(f"\n[ERROR] Error during seed process: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Seed clinical templates database')
    parser.add_argument('--force', action='store_true',
                        help='Force reseed, deleting existing templates')
    args = parser.parse_args()

    seed_database(force_reseed=args.force)
