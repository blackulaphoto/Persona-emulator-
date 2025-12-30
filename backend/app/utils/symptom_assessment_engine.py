"""
Symptom Assessment Engine

Maps experiences to appropriate disorders and calculates symptom severity.

This replaces the simple "depression/anxiety" tracking with comprehensive
DSM-5 aligned disorder assessment.
"""

from typing import Dict, List, Tuple
from .symptom_taxonomy import SYMPTOM_TAXONOMY


class SymptomAssessmentEngine:
    """
    Assesses which disorders a persona may develop based on their experiences.
    """
    
    # Experience category → Disorder risk mapping
    EXPERIENCE_TO_DISORDER_MAPPING = {
        "trauma": {
            "ptsd": 0.7,
            "complex_ptsd": 0.5,
            "depression": 0.6,
            "generalized_anxiety": 0.5,
            "substance_use_disorder": 0.4
        },
        "neglect": {
            "reactive_attachment_disorder": 0.8,
            "depression": 0.6,
            "avoidant_personality": 0.4,
            "dependent_personality": 0.3,
            "complex_ptsd": 0.6
        },
        "abuse": {
            "ptsd": 0.8,
            "complex_ptsd": 0.7,
            "borderline_personality": 0.6,
            "depression": 0.7,
            "substance_use_disorder": 0.5
        },
        "loss": {
            "depression": 0.7,
            "prolonged_grief_disorder": 0.6,
            "generalized_anxiety": 0.4,
            "substance_use_disorder": 0.3
        },
        "achievement": {
            "narcissistic_personality": 0.2,  # Can develop if excessive praise
            "obsessive_compulsive_personality": 0.3,
            "generalized_anxiety": 0.2  # Performance anxiety
        },
        "social_isolation": {
            "social_anxiety": 0.6,
            "depression": 0.5,
            "avoidant_personality": 0.4,
            "schizoid_personality": 0.3
        },
        "bullying": {
            "social_anxiety": 0.7,
            "depression": 0.6,
            "ptsd": 0.5,
            "avoidant_personality": 0.4
        },
        "parental_substance_use": {
            "substance_use_disorder": 0.6,  # Modeling
            "generalized_anxiety": 0.5,
            "reactive_attachment_disorder": 0.6,
            "dependent_personality": 0.4
        },
        "domestic_violence": {
            "ptsd": 0.8,
            "complex_ptsd": 0.7,
            "depression": 0.6,
            "generalized_anxiety": 0.7
        },
        "sexual_abuse": {
            "ptsd": 0.9,
            "complex_ptsd": 0.8,
            "hypersexuality": 0.4,  # Maladaptive coping
            "sexual_dysfunction": 0.6,
            "borderline_personality": 0.5
        },
        "financial_instability": {
            "generalized_anxiety": 0.6,
            "depression": 0.4,
            "hoarding_disorder": 0.3,  # Scarcity mindset
            "kleptomania": 0.1
        },
        "chronic_illness": {
            "depression": 0.6,
            "generalized_anxiety": 0.5,
            "illness_anxiety_disorder": 0.4,
            "somatic_symptom_disorder": 0.3
        },
        "peer_rejection": {
            "social_anxiety": 0.7,
            "depression": 0.5,
            "avoidant_personality": 0.5
        }
    }
    
    # Age multipliers (younger = more impact for certain disorders)
    AGE_VULNERABILITY = {
        "reactive_attachment_disorder": {"max_age": 5, "multiplier": 2.0},
        "complex_ptsd": {"max_age": 12, "multiplier": 1.5},
        "borderline_personality": {"max_age": 18, "multiplier": 1.3},
        "avoidant_personality": {"max_age": 18, "multiplier": 1.3},
        "dependent_personality": {"max_age": 18, "multiplier": 1.3},
        "obsessive_compulsive_personality": {"max_age": 18, "multiplier": 1.3},
        "substance_use_disorder": {"min_age": 13, "max_age": 25, "multiplier": 1.4}
    }
    
    # Severity multipliers
    SEVERITY_MULTIPLIERS = {
        "mild": 0.3,
        "moderate": 0.6,
        "severe": 0.9,
        "extreme": 1.0
    }
    
    def assess_symptoms(
        self,
        experiences: List[Dict],
        current_age: int,
        baseline_age: int
    ) -> Dict[str, Dict]:
        """
        Assess which symptoms/disorders a persona has based on experiences.
        
        Args:
            experiences: List of experience dicts with category, severity, age
            current_age: Persona's current age
            baseline_age: Age when persona was created
            
        Returns:
            Dict of {disorder_name: {severity, symptoms, onset_age}}
        """
        disorder_scores = {}
        
        for exp in experiences:
            category = exp.get("category", "").lower()
            severity = exp.get("severity", "moderate")
            age_at_exp = exp.get("age_at_experience", baseline_age)
            
            if category not in self.EXPERIENCE_TO_DISORDER_MAPPING:
                continue
            
            # Get disorders this experience can cause
            affected_disorders = self.EXPERIENCE_TO_DISORDER_MAPPING[category]
            
            for disorder, base_risk in affected_disorders.items():
                # Calculate severity
                severity_mult = self.SEVERITY_MULTIPLIERS.get(severity, 0.6)
                age_mult = self._calculate_age_multiplier(disorder, age_at_exp)
                
                final_score = base_risk * severity_mult * age_mult
                
                # Track disorder
                if disorder not in disorder_scores:
                    disorder_scores[disorder] = {
                        "severity": 0.0,
                        "contributing_experiences": [],
                        "onset_age": age_at_exp
                    }
                
                # Accumulate severity (cap at 1.0)
                disorder_scores[disorder]["severity"] = min(
                    1.0,
                    disorder_scores[disorder]["severity"] + final_score
                )
                disorder_scores[disorder]["contributing_experiences"].append(exp["id"])
                
                # Update onset age if earlier
                if age_at_exp < disorder_scores[disorder]["onset_age"]:
                    disorder_scores[disorder]["onset_age"] = age_at_exp
        
        # Add symptom details for each disorder
        for disorder_name in disorder_scores.keys():
            disorder_scores[disorder_name]["symptoms"] = self._get_symptom_breakdown(
                disorder_name,
                disorder_scores[disorder_name]["severity"]
            )
            disorder_scores[disorder_name]["category"] = SYMPTOM_TAXONOMY.get(
                disorder_name, {}
            ).get("category", "Unknown")
        
        return disorder_scores
    
    def _calculate_age_multiplier(self, disorder: str, age: int) -> float:
        """Calculate age-based vulnerability multiplier"""
        if disorder not in self.AGE_VULNERABILITY:
            return 1.0
        
        vuln = self.AGE_VULNERABILITY[disorder]
        
        if "max_age" in vuln and age <= vuln["max_age"]:
            return vuln["multiplier"]
        
        if "min_age" in vuln and "max_age" in vuln:
            if vuln["min_age"] <= age <= vuln["max_age"]:
                return vuln["multiplier"]
        
        return 1.0
    
    def _get_symptom_breakdown(self, disorder_name: str, overall_severity: float) -> Dict[str, float]:
        """
        Get individual symptom severities for a disorder.
        
        Returns dict of {symptom_name: severity}
        """
        if disorder_name not in SYMPTOM_TAXONOMY:
            return {}
        
        symptoms = SYMPTOM_TAXONOMY[disorder_name].get("symptoms", [])
        
        # Generate symptom severities (vary slightly around overall severity)
        import random
        symptom_breakdown = {}
        
        for symptom in symptoms:
            # Add some variance (±20%)
            variance = random.uniform(-0.2, 0.2)
            symptom_severity = max(0.0, min(1.0, overall_severity + variance))
            symptom_breakdown[symptom] = round(symptom_severity, 2)
        
        return symptom_breakdown
    
    def calculate_intervention_effect(
        self,
        disorder: str,
        intervention_type: str,
        duration_weeks: int,
        adherence: float = 0.8
    ) -> float:
        """
        Calculate how much an intervention reduces symptom severity.
        
        Returns: Reduction amount (0-1 scale)
        """
        # Intervention effectiveness by disorder type
        INTERVENTION_EFFECTIVENESS = {
            "depression": {
                "CBT": 0.5,
                "medication": 0.6,
                "combination": 0.7
            },
            "anxiety": {
                "CBT": 0.6,
                "exposure_therapy": 0.7,
                "medication": 0.5
            },
            "ptsd": {
                "EMDR": 0.6,
                "CPT": 0.6,
                "PE": 0.7,
                "medication": 0.4
            },
            "ocd": {
                "ERP": 0.7,
                "medication": 0.5,
                "combination": 0.75
            },
            "borderline_personality": {
                "DBT": 0.6,
                "schema_therapy": 0.5,
                "MBT": 0.5
            },
            "substance_use": {
                "MAT": 0.7,  # Medication-assisted treatment
                "12_step": 0.4,
                "CBT": 0.5,
                "residential": 0.6
            },
            "eating_disorders": {
                "FBT": 0.7,  # Family-based therapy
                "CBT_E": 0.6,
                "medication": 0.3
            }
        }
        
        base_effectiveness = INTERVENTION_EFFECTIVENESS.get(disorder, {}).get(
            intervention_type,
            0.4  # Default moderate effectiveness
        )
        
        # Adjust for duration (more weeks = more effect, up to a point)
        duration_factor = min(1.0, duration_weeks / 24)  # Plateaus at 24 weeks
        
        # Adjust for adherence
        adherence_factor = adherence
        
        # Calculate final reduction
        reduction = base_effectiveness * duration_factor * adherence_factor
        
        return round(reduction, 2)


# Example usage
if __name__ == "__main__":
    engine = SymptomAssessmentEngine()
    
    # Example experiences
    experiences = [
        {
            "id": "exp1",
            "category": "abuse",
            "severity": "severe",
            "age_at_experience": 8
        },
        {
            "id": "exp2",
            "category": "neglect",
            "severity": "moderate",
            "age_at_experience": 5
        }
    ]
    
    # Assess symptoms
    symptoms = engine.assess_symptoms(experiences, current_age=28, baseline_age=28)
    
    print("Assessed Disorders:")
    for disorder, details in symptoms.items():
        print(f"\n{disorder}:")
        print(f"  Severity: {details['severity']:.2f}")
        print(f"  Onset Age: {details['onset_age']}")
        print(f"  Category: {details['category']}")
        print(f"  Top Symptoms:")
        for symptom, severity in list(details['symptoms'].items())[:3]:
            print(f"    - {symptom}: {severity:.2f}")
