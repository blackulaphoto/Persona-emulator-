"""
Tests for step 8 of docs/MIGRATION_MAP.md: narrative_service.py's
verdict/pattern/evidence-strength structure and the "three realities"
model (event reality / persona's belief / engine formulation).

_build_narrative_prompt is a pure function (no DB, no network) so these
tests exercise it directly with plain constructed ORM instances (unsaved,
matching the pattern used elsewhere in this rebuild's tests).
"""
from app.services.narrative_service import _build_narrative_prompt
from app.models.persona import Persona
from app.models.adaptation_pattern import AdaptationPattern
from app.models.clinical_pattern_hypothesis import ClinicalPatternHypothesis
from app.models.narration import PersonaBelief


def _persona():
    return Persona(
        name="Michael",
        baseline_age=6,
        current_age=32,
        baseline_gender="male",
        baseline_background="Parents divorced when he was 6; unstable caregiving before that.",
        current_personality={
            "openness": 0.5, "conscientiousness": 0.4, "extraversion": 0.4,
            "agreeableness": 0.5, "neuroticism": 0.7,
        },
        current_attachment_style="insecure-anxious",
        current_trauma_markers=[],
    )


class TestGracefulDegradationWithNoPatternData:
    """Live system today: these tables are always empty until steps 2-5 are wired into a route."""

    def test_no_pattern_or_belief_data_still_produces_valid_prompt(self):
        # Step 11f split the old combined "developmental patterns" section
        # into emerging/established, each with its own explicit fallback text.
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert "None yet - no adaptation strategy has reached the established evidence bar." in prompt
        assert "None currently emerging." in prompt
        assert "No clinical pattern hypothesis has accumulated enough evidence" in prompt
        assert "has not stated an explicit belief" in prompt

    def test_anti_hedging_instruction_present(self):
        # The phrase legitimately appears once, inside the instruction that
        # prohibits it ("Never write '...' as a substitute for reasoning").
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert 'Never write "there isn\'t enough information to say"' in prompt
        assert "reason confidently from the objective experience timeline" in prompt


class TestAdaptationPatternsInPrompt:
    def test_pattern_name_and_evidence_label_included(self):
        patterns = [AdaptationPattern(
            persona_id="p1", pattern_name="Leave Before You're Left",
            adaptation_strategy="avoidance", status="established",
            evidence_strength=0.75, description="Avoids commitment ahead of anticipated abandonment.",
        )]
        prompt = _build_narrative_prompt(_persona(), [], [], adaptation_patterns=patterns)
        assert "Leave Before You're Left" in prompt
        assert "established" in prompt
        assert "high" in prompt  # evidence_strength_label(0.75) == "high"

    def test_null_evidence_strength_labeled_no_evidence_yet(self):
        patterns = [AdaptationPattern(
            persona_id="p1", pattern_name="Emerging Pattern",
            adaptation_strategy="hypervigilance", status="emerging",
            evidence_strength=None,
        )]
        prompt = _build_narrative_prompt(_persona(), [], [], adaptation_patterns=patterns)
        assert "no_evidence_yet" in prompt

    def test_verdict_instruction_present_when_patterns_exist(self):
        patterns = [AdaptationPattern(persona_id="p1", pattern_name="X", adaptation_strategy="avoidance", status="established", evidence_strength=0.6)]
        prompt = _build_narrative_prompt(_persona(), [], [], adaptation_patterns=patterns)
        assert "THE VERDICT" in prompt or "name it explicitly" in prompt
        assert "SECONDARY framing" in prompt


class TestClinicalPatternHypothesesInPrompt:
    def test_pattern_key_and_tier_included(self):
        hypotheses = [ClinicalPatternHypothesis(
            persona_id="p1", pattern_key="complex_ptsd", tier="clinical_pattern_resemblance", evidence_strength=0.65,
        )]
        prompt = _build_narrative_prompt(_persona(), [], [], clinical_pattern_hypotheses=hypotheses)
        assert "complex_ptsd" in prompt
        assert "clinical_pattern_resemblance" in prompt

    def test_never_called_a_diagnosis(self):
        hypotheses = [ClinicalPatternHypothesis(persona_id="p1", pattern_key="ptsd", tier="developmental_pattern", evidence_strength=0.3)]
        prompt = _build_narrative_prompt(_persona(), [], [], clinical_pattern_hypotheses=hypotheses)
        assert "never a diagnosis" in prompt


class TestThreeRealitiesModel:
    """The persona's stated belief vs. the engine's own formulation - the gap is real material."""

    def test_belief_text_included(self):
        beliefs = [PersonaBelief(
            subject_id="p1", belief_text="My parents' divorce caused everything.",
            narrative_theme="single-event causal explanation",
            timeline_evaluation="partially_supported",
            engine_interpretation="Instability predates the divorce; the divorce likely reinforced an existing pattern.",
        )]
        prompt = _build_narrative_prompt(_persona(), [], [], persona_beliefs=beliefs)
        assert "My parents' divorce caused everything." in prompt
        assert "partially_supported" in prompt
        assert "Instability predates the divorce" in prompt

    def test_gap_naming_instruction_present(self):
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert "diverge" in prompt.lower()
        assert "do not silently pick one account over the other" in prompt

    def test_no_belief_stated_does_not_invent_one(self):
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert "do not invent one" in prompt
        assert "has not stated an explicit belief" in prompt


class TestBackwardCompatibility:
    def test_legacy_three_positional_args_still_works(self):
        # The exact call shape used before step 8 existed.
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert "Michael" in prompt
        assert "## EXECUTIVE SUMMARY" in prompt
        assert "## PROGNOSIS & RECOMMENDATIONS" in prompt


class TestStatePatternTraitArc:
    """Step 11f: the immediate-state -> emerging-adaptation -> established-pattern -> trait-shift arc."""

    def test_no_state_data_degrades_gracefully(self):
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert "No State-tier movement recorded yet." in prompt

    def test_current_state_values_included(self):
        persona = _persona()
        persona.current_state = {"threat_sensitivity": 0.62, "trust": 0.3}
        prompt = _build_narrative_prompt(persona, [], [])
        assert "Threat Sensitivity: 0.62" in prompt
        assert "Trust: 0.30" in prompt

    def test_emerging_and_established_patterns_are_split_into_separate_sections(self):
        patterns = [
            AdaptationPattern(persona_id="p1", pattern_name="Early Warning Signs", adaptation_strategy="hypervigilance", status="emerging", evidence_strength=0.2),
            AdaptationPattern(persona_id="p1", pattern_name="Leave Before You're Left", adaptation_strategy="avoidance", status="established", evidence_strength=0.75),
        ]
        prompt = _build_narrative_prompt(_persona(), [], [], adaptation_patterns=patterns)

        emerging_section = prompt.split("**EMERGING DEVELOPMENTAL PATTERNS")[1].split("**ENGINE'S OWN FORMULATION")[0]
        established_section = prompt.split("ESTABLISHED DEVELOPMENTAL PATTERNS**")[1].split("**ENGINE'S OWN FORMULATION - CLINICAL")[0]

        assert "Early Warning Signs" in emerging_section
        assert "Leave Before You're Left" not in emerging_section
        assert "Leave Before You're Left" in established_section
        assert "Early Warning Signs" not in established_section

    def test_no_established_patterns_says_so_explicitly(self):
        patterns = [AdaptationPattern(persona_id="p1", pattern_name="Early Warning Signs", adaptation_strategy="hypervigilance", status="emerging", evidence_strength=0.2)]
        prompt = _build_narrative_prompt(_persona(), [], [], adaptation_patterns=patterns)
        assert "None yet - no adaptation strategy has reached the established evidence bar." in prompt

    def test_arc_guidance_and_instruction_present(self):
        prompt = _build_narrative_prompt(_persona(), [], [])
        assert "STATE -> PATTERN -> TRAIT arc" in prompt
        assert "do not collapse the stages together" in prompt
        assert "just {persona.name}'s starting temperament" not in prompt  # template must be interpolated, not left literal
        assert "Michael's starting temperament" in prompt
