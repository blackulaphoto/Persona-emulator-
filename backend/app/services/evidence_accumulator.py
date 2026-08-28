"""
Evidence Accumulator.

The single writer for clinical-pattern state (see docs/MIGRATION_MAP.md,
"Canonical pipeline"). Consumes DevelopmentalExposure, ProtectiveFactor, and
NarrationRecord rows accumulated across a persona's timeline and produces
ClinicalPatternHypothesis state - patterns worth investigating, with
evidence that is earned and revisable, never seeded.

Hard rule (Revision 3, docs/MIGRATION_MAP.md): EXPOSURE_HYPOTHESIS_PRIORS
below decides which hypotheses are worth OPENING. It never sets how
strongly to believe them - every hypothesis opens with evidence_strength =
None. Strength only comes from accumulated evidence: persistence across the
timeline, corroborating narrative signals, and protective factors that
contradict it. (Symptom/functional-impact evidence is a real evidence type
per the product spec but isn't wired in yet - it depends on the
Pattern/Adaptation engine, step 5, which hasn't been built. Its slot exists
in the evidence-entry shape below and will be populated once that lands.)

This module is pure - it takes plain dicts describing a persona's current
timeline state and returns computed hypothesis state. It does not read from
or write to the database; callers are responsible for loading input rows and
persisting the result (see build_clinical_pattern_hypothesis_rows).
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Hypothesis-opening priors
# ============================================================
# exposure_type (from app/services/developmental_exposure_engine.py) ->
# pattern_keys (from app/utils/symptom_taxonomy.py) worth opening as
# hypotheses when this exposure is present. This is the direct replacement
# for app/utils/symptom_assessment_engine.py's EXPERIENCE_TO_DISORDER_MAPPING
# - same idea (certain exposures make certain patterns worth watching for),
# but re-keyed to the new exposure taxonomy and stripped of the old
# per-category severity floats (e.g. the old "abuse -> ptsd: 0.8"). Opening a
# hypothesis here never implies a starting strength.
EXPOSURE_HYPOTHESIS_PRIORS: Dict[str, List[str]] = {
    "caregiver_substance_use": ["reactive_attachment_disorder", "complex_ptsd", "generalized_anxiety"],
    "caregiver_absence": ["reactive_attachment_disorder", "avoidant_personality", "generalized_anxiety"],
    "caregiver_emotional_unavailability": ["reactive_attachment_disorder", "avoidant_personality", "depression"],
    "caregiver_mental_illness": ["reactive_attachment_disorder", "generalized_anxiety", "complex_ptsd"],
    "household_unpredictability": ["generalized_anxiety", "complex_ptsd"],
    "physical_discipline_or_violence": ["ptsd", "complex_ptsd", "depression"],
    "domestic_violence_witnessed": ["ptsd", "complex_ptsd", "generalized_anxiety"],
    "sexual_boundary_violation": ["ptsd", "complex_ptsd", "borderline_personality"],
    "emotional_abuse_or_humiliation": ["complex_ptsd", "depression", "avoidant_personality"],
    "neglect_of_basic_needs": ["reactive_attachment_disorder", "depression", "complex_ptsd"],
    "caregiver_incarceration": ["reactive_attachment_disorder", "generalized_anxiety"],
    "separation_or_divorce": ["adjustment_disorder", "generalized_anxiety"],
    "death_of_caregiver_or_family": ["prolonged_grief_disorder", "depression", "adjustment_disorder"],
    "frequent_relocation": ["adjustment_disorder", "social_anxiety"],
    "financial_instability": ["generalized_anxiety", "adjustment_disorder"],
    "peer_rejection_or_bullying": ["social_anxiety", "depression", "avoidant_personality"],
    "high_achievement_pressure": ["obsessive_compulsive_personality", "generalized_anxiety"],
    "chronic_illness_self": ["illness_anxiety_disorder", "adjustment_disorder"],
    "chronic_illness_family_member": ["adjustment_disorder", "generalized_anxiety"],
}

# ============================================================
# Adaptation-strategy hypothesis links (docs/MIGRATION_MAP.md, Step 12)
# ============================================================
# adaptation_strategy (app/services/pattern_engine.py ADAPTATION_STRATEGIES)
# -> pattern_keys worth opening/supporting.
#
# This is the fix for the architectural disconnect the Emma audit found:
# EXPOSURE_HYPOTHESIS_PRIORS above keys hypotheses off literal exposure_type
# recurrence, which does not model a real life. Emma's six events are six
# DIFFERENT exposure types (friend rejection, parental conflict, humiliation,
# unstable romance, family loss, sexual assault), so nothing ever recurred by
# that key and every hypothesis stayed pinned near 0.0 - even though the
# interpretation layer had correctly recognized all six as reinforcing ONE
# adaptation (self_reliance, which climbed 0.0 -> 1.0 across the same
# timeline). A varied history must be able to converge on the same
# psychological hypothesis; identical event types are not required.
#
# Deliberately non-exhaustive, same principle as SIGNAL_HYPOTHESIS_SUPPORT
# and intervention_engine.PATTERN_KEY_THERAPY_ALIASES: a strategy with no
# defensible single-pattern link is left unmapped rather than forced into a
# clinically wrong one. "humor" is mapped to nothing on purpose - deflecting
# with humor is not, by itself, evidence of any disorder.
ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT: Dict[str, List[str]] = {
    "hypervigilance": ["ptsd", "complex_ptsd", "generalized_anxiety", "paranoid_personality"],
    "emotional_distancing": ["avoidant_personality", "schizoid_personality", "complex_ptsd"],
    "people_pleasing": ["dependent_personality", "depression"],
    "control_seeking": ["obsessive_compulsive_personality", "generalized_anxiety"],
    "aggression": ["intermittent_explosive_disorder", "borderline_personality"],
    "avoidance": ["avoidant_personality", "social_anxiety", "ptsd"],
    "self_reliance": ["avoidant_personality", "schizoid_personality"],
    "perfectionism": ["obsessive_compulsive_personality", "social_anxiety"],
    "humor": [],
    "caretaking": ["dependent_personality"],
    "substance_use": ["substance_use_disorder", "alcohol_use_disorder"],
    "intellectualization": ["obsessive_compulsive_personality"],
}

# Conservative, non-exhaustive: only signal_types with a defensible clinical
# link are mapped. Most of SIGNAL_TYPES (see self_narration_engine.py) is
# left unmapped deliberately rather than forcing a pattern link that isn't
# well justified.
SIGNAL_HYPOTHESIS_SUPPORT: Dict[str, List[str]] = {
    "normalization": ["complex_ptsd"],
    "self_blame": ["depression", "complex_ptsd"],
    "caregiver_framing": ["reactive_attachment_disorder", "complex_ptsd"],
    "detached_description_of_severe_content": ["complex_ptsd"],
    "emotional_vocabulary_absence": ["complex_ptsd", "avoidant_personality"],
    "affect_content_mismatch": ["complex_ptsd"],
}

# Evidence-strength mechanics. Intentionally simple and transparent rather
# than a weighted formula dressed up as precision - the point isn't the
# specific constants, it's that strength (a) starts at None, (b) is built
# from an auditable, typed list of evidence entries, and (c) moves down as
# well as up. This is a first pass; the Pattern/Adaptation engine (step 5)
# is expected to add richer evidence types (functional impact, reinforcement
# across interventions) that will make this more than an increment counter.
SUPPORT_INCREMENT = 0.15
CONTRADICT_DECREMENT = 0.15
MAX_NARRATIVE_ENTRIES_PER_PATTERN = 3  # caps repeated identical signals from inflating strength
PERSISTENCE_MIN_OCCURRENCES = 2
RESEMBLANCE_THRESHOLD = 0.6  # tier: developmental_pattern -> clinical_pattern_resemblance


def evidence_strength_label(strength: Optional[float]) -> str:
    """Secondary framing per the product spec: confidence supports the
    conclusion, it doesn't apologize for making one."""
    if strength is None:
        return "no_evidence_yet"
    if strength >= 0.7:
        return "high"
    if strength >= 0.4:
        return "moderate"
    return "low"


def _candidate_patterns_for_exposures(exposures: List[Dict]) -> Dict[str, List[Dict]]:
    """pattern_key -> list of exposures that make it worth investigating."""
    candidates: Dict[str, List[Dict]] = {}
    for exposure in exposures:
        for pattern_key in EXPOSURE_HYPOTHESIS_PRIORS.get(exposure.get("exposure_type"), []):
            candidates.setdefault(pattern_key, []).append(exposure)
    return candidates


def _candidate_patterns_for_adaptations(adaptation_patterns: List[Dict]) -> Dict[str, List[Dict]]:
    """
    pattern_key -> the AdaptationPatterns that make it worth investigating
    (Step 12). A hypothesis opened this way still opens with no earned
    strength, exactly like an exposure-opened one - see the module docstring's
    hard rule. Only patterns that have actually earned some evidence_strength
    of their own count: an "emerging" adaptation with strength None is a
    single interpretation, and one interpretation should not open a clinical
    hypothesis on its own any more than one exposure does.
    """
    candidates: Dict[str, List[Dict]] = {}
    for pattern in adaptation_patterns:
        if (pattern.get("evidence_strength") or 0) <= 0:
            continue
        strategy = pattern.get("adaptation_strategy")
        for pattern_key in ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT.get(strategy, []):
            candidates.setdefault(pattern_key, []).append(pattern)
    return candidates


MAX_PERSISTENCE_ENTRIES = 4  # caps persistence's contribution at 4 * SUPPORT_INCREMENT (0.6) on its own


def _persistence_evidence(pattern_key: str, supporting_exposures: List[Dict]) -> List[Dict]:
    """
    A pattern-relevant exposure recurring ACROSS SEPARATE ENTRIES is real
    evidence, distinct from the exposure that opened the hypothesis in the
    first place. Distinctness is keyed on (source, source_event_id), not raw
    row count - a single backstory sentence like "my father drank constantly
    and disappeared for days" produces two exposure_types (caregiver_
    substance_use, caregiver_absence) that both implicate the same pattern,
    but that's one situation described two ways, not two separate
    occurrences over time. Two exposures sharing source_event_id=None (both
    extracted from the same backstory call) count as ONE entry; an exposure
    from the backstory plus one from a later, distinct experience count as
    two. Callers must set source/source_event_id on every exposure dict (the
    real pipeline always does).

    Returns ONE entry per distinct occurrence beyond the first (capped at
    MAX_PERSISTENCE_ENTRIES), not a single fixed-weight signal - a pattern
    that recurred 4 separate times is meaningfully stronger evidence than one
    that recurred twice, and strength should be able to reflect that.
    Originally returned at most one entry regardless of recurrence count,
    which silently capped every purely-exposure-driven hypothesis at
    SUPPORT_INCREMENT (0.15) forever - since exposures are the only evidence
    source currently wired into a live route (narration and functional
    observations aren't yet), that meant current_trauma_markers could never
    populate in practice. Found via tests/test_developmental_pipeline.py's
    end-to-end run.
    """
    entries = {(e.get("source"), e.get("source_event_id")) for e in supporting_exposures}
    if len(entries) < PERSISTENCE_MIN_OCCURRENCES:
        return []
    ages = sorted({e.get("age_at_exposure") for e in supporting_exposures if e.get("age_at_exposure") is not None})
    types = sorted({e.get("exposure_type") for e in supporting_exposures})
    extra_occurrences = min(len(entries) - 1, MAX_PERSISTENCE_ENTRIES)
    return [
        {
            "type": "persistence",
            "description": f"{', '.join(types)} recurred across {len(entries)} separate entries"
                            + (f" (ages {', '.join(str(a) for a in ages)})" if ages else ""),
            "source_id": None,
            "age": ages[-1] if ages else None,
        }
        for _ in range(extra_occurrences)
    ]


MAX_ADAPTATION_ENTRIES_PER_PATTERN = 3


def _adaptation_evidence(pattern_key: str, supporting_adaptations: List[Dict]) -> List[Dict]:
    """
    An AdaptationPattern that has itself accumulated real reinforcement across
    the timeline is supporting evidence for the clinical patterns that
    adaptation is associated with (Step 12).

    Scaled to the adaptation's own earned evidence_strength rather than a flat
    per-pattern signal: pattern_engine adds REINFORCE_INCREMENT (0.2) per
    reinforcement, so one entry per 0.2 of strength means "reinforced four
    separate times" contributes more than "reinforced once" - the same
    recurrence-matters principle _persistence_evidence uses for exposures.
    Capped at MAX_ADAPTATION_ENTRIES_PER_PATTERN so a single maxed-out
    adaptation cannot single-handedly drive a hypothesis to certainty.
    """
    entries: List[Dict] = []
    for adaptation in supporting_adaptations:
        strength = adaptation.get("evidence_strength") or 0
        count = min(int(strength / 0.2), MAX_ADAPTATION_ENTRIES_PER_PATTERN)
        name = adaptation.get("pattern_name") or adaptation.get("adaptation_strategy")
        for _ in range(count):
            entries.append({
                "type": "adaptation_pattern",
                "description": f"adaptation \"{name}\" ({adaptation.get('adaptation_strategy')}) "
                               f"reinforced across the timeline, status {adaptation.get('status')}",
                "source_id": adaptation.get("id"),
                "age": adaptation.get("first_emerged_age"),
            })
    return entries[:MAX_ADAPTATION_ENTRIES_PER_PATTERN]


def _narrative_evidence(pattern_key: str, narration_records: List[Dict]) -> List[Dict]:
    """
    Only persona_voice narration counts as evidence about the persona's own
    psychology - third-party/case-author narration is about the persona but
    isn't evidence of their internal schema (see docs/MIGRATION_MAP.md,
    "Operator vs. subject vs. source").
    """
    entries: List[Dict] = []
    for record in narration_records:
        if not record.get("attributed_to_persona"):
            continue
        for signal in record.get("linguistic_signals", []):
            signal_type = signal.get("signal_type")
            if pattern_key in SIGNAL_HYPOTHESIS_SUPPORT.get(signal_type, []):
                entries.append({
                    "type": "narrative",
                    "description": f"{signal_type}: {signal.get('evidence_text', '')}",
                    "source_id": record.get("id"),
                    "age": record.get("age"),
                })
            if len(entries) >= MAX_NARRATIVE_ENTRIES_PER_PATTERN:
                break
        if len(entries) >= MAX_NARRATIVE_ENTRIES_PER_PATTERN:
            break
    return entries[:MAX_NARRATIVE_ENTRIES_PER_PATTERN]


def _protective_contradiction(pattern_key: str, supporting_exposures: List[Dict], protective_factors: List[Dict]) -> List[Dict]:
    """
    A protective factor whose buffered domains overlap with the domains this
    pattern's exposures implicate is contradicting evidence, not a silent
    severity discount (see docs/MIGRATION_MAP.md, "Protective factors are
    first-class").

    Excludes protective factors extracted FROM one of this hypothesis's own
    supporting events - the same self-buffering bug already fixed in
    pattern_engine.accumulate_patterns(), which turned out to exist
    independently here too (Step 12). The AI extracts something protective
    from most events, adverse ones included ("she still had one close friend"
    is a real detail even in the event where that friend betrays her), and
    developmental domains are a small reused vocabulary - so without this
    exclusion a hypothesis is perpetually contradicted by the very events
    that opened it, and can never accumulate. Confirmed against a real
    GPT-4-interpreted persona: complex_ptsd sat at 0.0 across six escalating
    events including a sexual assault.
    """
    implicated_domains = set()
    for exposure in supporting_exposures:
        implicated_domains.update(exposure.get("developmental_domains", []))

    own_event_ids = {
        e.get("source_event_id") for e in supporting_exposures if e.get("source_event_id") is not None
    }

    entries = []
    for factor in protective_factors:
        if factor.get("source_event_id") is not None and factor.get("source_event_id") in own_event_ids:
            continue
        buffered = set(factor.get("domains_buffered", []))
        if buffered & implicated_domains:
            entries.append({
                "type": "protective_factor",
                "description": f"{factor.get('factor_type')} buffers {', '.join(sorted(buffered & implicated_domains))}",
                "source_id": factor.get("id"),
                "age": factor.get("active_from_age"),
            })
    return entries


def _functional_supporting_evidence(pattern_key: str, functional_observations: List[Dict]) -> List[Dict]:
    """
    A "concerning" functional observation (app/services/
    functional_observation_engine.py) whose candidate_pattern_keys names
    this pattern is real evidence per the product spec's own list ("actual
    symptoms, persistence, functional effects, narrative material..."). Not
    gated by speaker_role - see functional_observation_engine.py's module
    docstring for why a behavioral observation isn't source-gated the way
    self-narration is.
    """
    entries = []
    for obs in functional_observations:
        if obs.get("valence") != "concerning":
            continue
        if pattern_key in obs.get("candidate_pattern_keys", []):
            entries.append({
                "type": "functional_impact",
                "description": f"{obs.get('observation_type')}: {obs.get('description', '')}",
                "source_id": obs.get("id"),
                "age": obs.get("age_observed"),
            })
    return entries


def _functional_contradiction(pattern_key: str, supporting_exposures: List[Dict], functional_observations: List[Dict]) -> List[Dict]:
    """
    A "protective" valence functional observation contradicts by domain
    overlap, the same mechanism as _protective_contradiction - "Timmy
    maintains close, trusting relationships" doesn't name a pattern to
    refute, it counts against whatever attachment-domain hypothesis is open,
    same as a ProtectiveFactor would.
    """
    implicated_domains = set()
    for exposure in supporting_exposures:
        implicated_domains.update(exposure.get("developmental_domains", []))

    entries = []
    for obs in functional_observations:
        if obs.get("valence") != "protective":
            continue
        domains = set(obs.get("developmental_domains", []))
        if domains & implicated_domains:
            entries.append({
                "type": "functional_impact",
                "description": f"{obs.get('observation_type')}: {obs.get('description', '')}",
                "source_id": obs.get("id"),
                "age": obs.get("age_observed"),
            })
    return entries


def _current_manifestations_from_observations(pattern_key: str, functional_observations: List[Dict]) -> List[str]:
    """Descriptive, not evidentiary - answers 'how does this show up now', not 'is this pattern real'."""
    return [
        obs["description"]
        for obs in functional_observations
        if obs.get("valence") == "concerning" and pattern_key in obs.get("candidate_pattern_keys", [])
    ]


def _compute_strength(supporting: List[Dict], contradicting: List[Dict]) -> Optional[float]:
    if not supporting and not contradicting:
        return None
    net = len(supporting) * SUPPORT_INCREMENT - len(contradicting) * CONTRADICT_DECREMENT
    return round(max(0.0, min(1.0, net)), 2)


def accumulate_evidence(
    exposures: List[Dict],
    protective_factors: Optional[List[Dict]] = None,
    narration_records: Optional[List[Dict]] = None,
    functional_observations: Optional[List[Dict]] = None,
    existing_status: Optional[Dict[str, str]] = None,
    adaptation_patterns: Optional[List[Dict]] = None,
) -> Dict[str, Dict]:
    """
    Recomputes hypothesis state from a persona's full current timeline.
    Deliberately recomputes from scratch each call rather than incrementally
    mutating stored state - this is what makes "later evidence can revise
    earlier hypotheses" (and can un-revise it, if a hypothesis's supporting
    exposure turns out to be isolated once more history is added) safe to
    reason about, instead of accumulating drift through repeated partial
    updates.

    Args:
        exposures: [{id, exposure_type, developmental_domains, age_at_exposure}, ...]
        protective_factors: [{id, factor_type, domains_buffered, active_from_age}, ...]
        narration_records: [{id, attributed_to_persona, linguistic_signals, age}, ...]
        functional_observations: [{id, valence, observation_type, description,
            developmental_domains, candidate_pattern_keys, age_observed}, ...]
            - see app/services/functional_observation_engine.py
        existing_status: optional {pattern_key: status} to preserve manual
            status overrides (e.g. "dismissed") across recomputation
        adaptation_patterns: [{id, adaptation_strategy, pattern_name, status,
            evidence_strength, first_emerged_age}, ...] from
            pattern_engine.accumulate_patterns() (Step 12). Lets a varied life
            history converge on one hypothesis through the adaptation it
            reinforced, instead of requiring the same literal exposure_type to
            recur - see ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT.

    Returns:
        {pattern_key: {tier, supporting_evidence, contradicting_evidence,
                        developmental_precursors, current_manifestations,
                        evidence_strength, status}}
    """
    protective_factors = protective_factors or []
    narration_records = narration_records or []
    functional_observations = functional_observations or []
    existing_status = existing_status or {}
    adaptation_patterns = adaptation_patterns or []

    exposure_candidates = _candidate_patterns_for_exposures(exposures)
    adaptation_candidates = _candidate_patterns_for_adaptations(adaptation_patterns)

    result: Dict[str, Dict] = {}

    for pattern_key in set(exposure_candidates) | set(adaptation_candidates):
        supporting_exposures = exposure_candidates.get(pattern_key, [])
        supporting_adaptations = adaptation_candidates.get(pattern_key, [])
        supporting_evidence: List[Dict] = []

        supporting_evidence.extend(_persistence_evidence(pattern_key, supporting_exposures))
        supporting_evidence.extend(_adaptation_evidence(pattern_key, supporting_adaptations))

        supporting_evidence.extend(_narrative_evidence(pattern_key, narration_records))
        supporting_evidence.extend(_functional_supporting_evidence(pattern_key, functional_observations))

        contradicting_evidence = _protective_contradiction(pattern_key, supporting_exposures, protective_factors)
        contradicting_evidence.extend(_functional_contradiction(pattern_key, supporting_exposures, functional_observations))

        strength = _compute_strength(supporting_evidence, contradicting_evidence)
        tier = "clinical_pattern_resemblance" if (strength or 0) >= RESEMBLANCE_THRESHOLD else "developmental_pattern"

        status = existing_status.get(pattern_key, "open")
        if status not in ("dismissed",):
            status = "revised" if pattern_key in existing_status else "open"

        result[pattern_key] = {
            "tier": tier,
            "supporting_evidence": supporting_evidence,
            "contradicting_evidence": contradicting_evidence,
            "developmental_precursors": sorted(
                {e.get("exposure_type") for e in supporting_exposures if e.get("exposure_type")}
                | {a.get("adaptation_strategy") for a in supporting_adaptations if a.get("adaptation_strategy")}
            ),
            "current_manifestations": _current_manifestations_from_observations(pattern_key, functional_observations),
            "evidence_strength": strength,
            "status": status,
            # Falls back to the adaptation's own first_emerged_age for a
            # hypothesis opened purely through adaptation continuity (Step 12).
            "opened_at_age": min(
                [e["age_at_exposure"] for e in supporting_exposures if e.get("age_at_exposure") is not None]
                + [a["first_emerged_age"] for a in supporting_adaptations if a.get("first_emerged_age") is not None],
                default=None,
            ),
        }

    return result


# ============================================================
# Display projection
# ============================================================
# The direct replacement for every module that used to write
# Persona.current_trauma_markers independently (personas.py's backstory
# call, psychology_engine's freeform symptom list, experiences.py's direct
# append). Nothing should write current_trauma_markers except this
# projection, computed from ClinicalPatternHypothesis state.

DISPLAY_THRESHOLD = 0.4  # matches evidence_strength_label's "moderate" floor


def project_current_trauma_markers(accumulated: Dict[str, Dict]) -> List[str]:
    """
    Read-only projection: pattern_keys whose evidence has actually
    accumulated past a display floor. A freshly opened hypothesis
    (evidence_strength is None) never appears here - "worth investigating"
    is not the same as "worth showing."
    """
    return sorted(
        pattern_key
        for pattern_key, state in accumulated.items()
        if (state.get("evidence_strength") or 0) >= DISPLAY_THRESHOLD
    )


# ============================================================
# Persistence helpers
# ============================================================

def build_clinical_pattern_hypothesis_rows(persona_id: str, accumulated: Dict[str, Dict]):
    """
    Converts accumulate_evidence()'s output into unsaved
    ClinicalPatternHypothesis ORM instances. Caller is responsible for
    db.add()/commit() - and, for an existing persona, for reconciling
    against already-persisted rows rather than blindly re-inserting
    (upsert-by-pattern_key is the caller's job, not this function's - see
    upsert_clinical_pattern_hypothesis_rows for that).
    """
    from app.models.clinical_pattern_hypothesis import ClinicalPatternHypothesis

    return [
        ClinicalPatternHypothesis(
            persona_id=persona_id,
            pattern_key=pattern_key,
            tier=state["tier"],
            supporting_evidence=state["supporting_evidence"],
            contradicting_evidence=state["contradicting_evidence"],
            developmental_precursors=state["developmental_precursors"],
            current_manifestations=state["current_manifestations"],
            evidence_strength=state["evidence_strength"],
            opened_at_age=state["opened_at_age"],
            status=state["status"],
        )
        for pattern_key, state in accumulated.items()
    ]


def upsert_clinical_pattern_hypothesis_rows(db, persona_id: str, accumulated: Dict[str, Dict]):
    """
    The actual wiring entry point (docs/MIGRATION_MAP.md, "wiring steps 2-5
    into routes"). Since accumulate_evidence() recomputes from the persona's
    complete timeline on every call, this updates existing rows in place by
    pattern_key rather than inserting duplicates - a persona's third
    experience must revise its first hypothesis, not create a second row for
    the same pattern. Patterns no longer present in `accumulated` (e.g. the
    exposures that opened them turn out isolated) are left as-is rather than
    deleted - a hypothesis quietly disappearing is a stronger claim than this
    function should make unilaterally.

    Does not commit - caller controls the transaction.
    """
    from app.models.clinical_pattern_hypothesis import ClinicalPatternHypothesis

    existing = {
        row.pattern_key: row
        for row in db.query(ClinicalPatternHypothesis).filter(
            ClinicalPatternHypothesis.persona_id == persona_id
        ).all()
    }

    for pattern_key, state in accumulated.items():
        if pattern_key in existing:
            row = existing[pattern_key]
            # Step 12: remember where this hypothesis was before this
            # recomputation so the board can show direction of travel.
            # Only updated when the value actually changed - otherwise a run
            # of no-op recomputations would erase the last real movement.
            if row.evidence_strength != state["evidence_strength"]:
                row.previous_evidence_strength = row.evidence_strength
            row.tier = state["tier"]
            row.supporting_evidence = state["supporting_evidence"]
            row.contradicting_evidence = state["contradicting_evidence"]
            row.developmental_precursors = state["developmental_precursors"]
            row.current_manifestations = state["current_manifestations"]
            row.evidence_strength = state["evidence_strength"]
            row.status = state["status"]
        else:
            db.add(ClinicalPatternHypothesis(
                persona_id=persona_id,
                pattern_key=pattern_key,
                tier=state["tier"],
                supporting_evidence=state["supporting_evidence"],
                contradicting_evidence=state["contradicting_evidence"],
                developmental_precursors=state["developmental_precursors"],
                current_manifestations=state["current_manifestations"],
                evidence_strength=state["evidence_strength"],
                opened_at_age=state["opened_at_age"],
                status=state["status"],
            ))

    return {row.pattern_key: row.status for row in existing.values()}
