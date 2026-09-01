"""Current-age applicability policy for canonical clinical hypotheses."""
from typing import Dict


# These rules affect presentation as a *current* hypothesis only. Persisted
# developmental evidence remains available for historical formulation.
#
# Two directions, both real:
#   - max_current_age: the pattern is a childhood-only clinical presentation
#     (RAD) - an adult persona's accumulated evidence for it is real
#     developmental history, not a live current condition.
#   - min_current_age: the pattern is a personality-disorder diagnosis, which
#     by clinical convention (DSM-5: a pattern that must be "stable and of
#     long duration," with onset traceable to adolescence/early adulthood)
#     is not given to a still-developing child - a child persona's evidence
#     for one of these is a real emerging pattern, just not yet a
#     diagnosable personality disorder. Deliberately conservative and
#     non-exhaustive, same principle as EXPOSURE_HYPOTHESIS_PRIORS/
#     ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT in evidence_accumulator.py: a
#     pattern_key with no clearly defensible age boundary (the mood/anxiety/
#     trauma/adjustment/substance-use keys - all of which have real
#     documented presentations across childhood, adolescence, and adulthood)
#     is deliberately left unscoped here rather than guessed at.
HYPOTHESIS_APPLICABILITY: Dict[str, Dict] = {
    "reactive_attachment_disorder": {
        "max_current_age": 17,
        "historical_label": "childhood attachment-disturbance resemblance",
        "reason": "childhood-only current applicability",
    },
    **{
        pattern_key: {
            "min_current_age": 18,
            "historical_label": f"emerging {pattern_key.replace('_personality', '')} relational/temperament pattern",
            "reason": "personality-disorder diagnoses require a stable, long-duration pattern typically not "
                      "assessed before adulthood - personality is still consolidating in a child/adolescent persona",
        }
        for pattern_key in (
            "avoidant_personality", "borderline_personality", "obsessive_compulsive_personality",
            "schizoid_personality", "dependent_personality", "paranoid_personality",
        )
    },
}


def is_currently_applicable(pattern_key: str, current_age: int) -> bool:
    rule = HYPOTHESIS_APPLICABILITY.get(pattern_key)
    if not rule:
        return True
    minimum = rule.get("min_current_age")
    maximum = rule.get("max_current_age")
    return not (
        (minimum is not None and current_age < minimum)
        or (maximum is not None and current_age > maximum)
    )


def applicability_for(pattern_key: str, current_age: int) -> Dict:
    rule = HYPOTHESIS_APPLICABILITY.get(pattern_key, {})
    current = is_currently_applicable(pattern_key, current_age)
    return {
        "currently_applicable": current,
        "historical_developmental_only": not current,
        "historical_label": rule.get("historical_label"),
        "reason": rule.get("reason"),
    }
