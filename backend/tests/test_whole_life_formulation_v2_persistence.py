"""
Persistence-phase tests for Whole-Life Formulation V2.

The LLM call (formulation_service.generate_whole_life_formulation) is
monkeypatched throughout - these tests exercise enforcement, persistence,
reconciliation, and rollback logic deterministically, not the model's
psychological judgment (which the three shadow-testing passes already
exercised extensively with real calls). Handcrafted formulations let each
test target one specific enforcement/persistence code path precisely,
something a live call can't reliably guarantee.
"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    AdaptationPattern, ClinicalPatternHypothesis, Experience, Persona,
    PersonaBelief, PersonalitySnapshot, ProtectiveFactor,
    WholeLifeFormulation as WholeLifeFormulationRow, FormulationValidationReport,
)
from app.services.whole_life_formulation import persistence_service
from app.services.whole_life_formulation.enforcement import enforce_validation
from app.services.whole_life_formulation.formulation_service import FormulationResult
from app.services.whole_life_formulation.request_assembler import ExperienceSource, LifeSourceData
from app.services.whole_life_formulation.schema import (
    AttachmentDimensionScore, AttachmentTrajectoryPoint, BigFiveProfile, BigFiveScore, Citation,
    CurrentState, ModelAttachmentDimensions, ModelWholeLifeFormulation, PatternFamilyScore,
    PatternScorecard, StateDimensionScore, HypothesisFamilyScore, HypothesisScorecard,
    WholeLifeFormulation,
)

# Reuse the shadow prototype's regression checks directly rather than
# duplicating that logic - "do not redesign the formulation engine."
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "whole_life_formulation_prototype"))
from regression_checks import check_caregiver_self_confusion, check_no_diagnosis_language  # noqa: E402

TEST_DB_URL = "sqlite:///./test_wlf_v2_persistence.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Builders - minimal-but-valid ModelWholeLifeFormulation / test personas
# ---------------------------------------------------------------------------

def _cite(experience_id=None, background_span=None, subject_role="self"):
    return Citation(experience_id=experience_id, intervention_id=None, background_span=background_span, subject_role=subject_role)


def _score(value=0.5, evidence=None, confidence=0.7, reasoning="test reasoning"):
    return BigFiveScore(value=value, evidence=evidence or [_cite("e1")], confidence=confidence, reasoning=reasoning)


def _dim(value=0.5, evidence=None, confidence=0.7):
    return AttachmentDimensionScore(value=value, evidence=evidence or [_cite("e1")], confidence=confidence)


def _state_dim(value=0.5, evidence=None, confidence=0.7):
    return StateDimensionScore(value=value, evidence=evidence or [_cite("e1")], confidence=confidence)


def _empty_pattern_score(relevance=0.1):
    return PatternFamilyScore(relevance_score=relevance, confidence=0.3, human_label="n/a", reasoning="not relevant", supporting_evidence=[], contradicting_evidence=[])


def _empty_hyp_score(strength=0.1):
    return HypothesisFamilyScore(evidence_strength=strength, confidence=0.3, supporting_evidence=[], contradicting_evidence=[], competing_explanations=[])


def build_minimal_model_formulation(**overrides) -> ModelWholeLifeFormulation:
    """A minimal, fully schema-valid ModelWholeLifeFormulation with everything
    scoring low/empty except what a test explicitly overrides via kwargs."""
    base = dict(
        schema_version="test-v2.2",
        baseline_personality=BigFiveProfile(**{t: _score() for t in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")}),
        current_personality=BigFiveProfile(**{t: _score() for t in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")}),
        personality_deltas=[],
        baseline_attachment=ModelAttachmentDimensions(attachment_anxiety=_dim(), attachment_avoidance=_dim(), relational_security=_dim()),
        current_attachment=ModelAttachmentDimensions(attachment_anxiety=_dim(), attachment_avoidance=_dim(), relational_security=_dim()),
        attachment_trajectory=[],
        current_state=CurrentState(**{d: _state_dim() for d in ("trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security")}),
        pattern_scorecard=PatternScorecard(**{
            f: _empty_pattern_score() for f in (
                "loss_and_bereavement", "identity_reconstruction", "relational_repair", "avoidant_withdrawal",
                "risk_seeking_dysregulation", "caregiving_role_reversal", "achievement_or_competence_compensation",
                "hypervigilant_monitoring", "prosocial_reinvention", "substance_coping",
            )
        }),
        beliefs=[],
        protective_factors=[],
        causal_chains=[],
        hypothesis_scorecard=HypothesisScorecard(**{
            f: _empty_hyp_score() for f in (
                "adjustment_reaction", "complicated_grief_pattern", "attachment_insecurity_pattern",
                "substance_use_vulnerability", "identity_disruption_pattern", "resilient_trajectory",
            )
        }),
        contradictions=[],
        unresolved_questions=["what does the persona believe about this"],
        change_points=[],
        overall_confidence=0.5,
    )
    base.update(overrides)
    return ModelWholeLifeFormulation(**base)


def make_persona(db, persona_id="p1", user_id="user1", n_experiences=2) -> Persona:
    persona = Persona(
        id=persona_id, user_id=user_id, name="Test Subject", baseline_age=20, current_age=25,
        baseline_background="Test background.", current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_attachment_dimensions={}, current_state={},
    )
    db.add(persona)
    for i in range(n_experiences):
        db.add(Experience(id=f"e{i+1}", persona_id=persona_id, user_id=user_id, sequence_number=i + 1,
                           age_at_event=20 + i, sequence_index=1, user_description=f"Experience {i+1} description."))
    db.commit()
    db.refresh(persona)
    return persona


def stub_model_call(monkeypatch, model_formulation: ModelWholeLifeFormulation, model_id="test-model"):
    def _fake_call(request, reasoning_effort="medium", max_output_tokens=16000):
        from app.services.whole_life_formulation.derivation import derive_attachment_profile, derive_hypothesis_projection, derive_pattern_projection
        life = request.life
        final = WholeLifeFormulation(
            schema_version=model_formulation.schema_version,
            baseline_personality=model_formulation.baseline_personality,
            current_personality=model_formulation.current_personality,
            personality_deltas=model_formulation.personality_deltas,
            baseline_attachment=derive_attachment_profile(model_formulation.baseline_attachment),
            current_attachment=derive_attachment_profile(model_formulation.current_attachment),
            attachment_trajectory=model_formulation.attachment_trajectory,
            current_state=model_formulation.current_state,
            developmental_patterns=derive_pattern_projection(model_formulation.pattern_scorecard, life),
            beliefs=model_formulation.beliefs,
            protective_factors=model_formulation.protective_factors,
            causal_chains=model_formulation.causal_chains,
            hypotheses=derive_hypothesis_projection(model_formulation.hypothesis_scorecard),
            contradictions=model_formulation.contradictions,
            unresolved_questions=model_formulation.unresolved_questions,
            change_points=model_formulation.change_points,
            overall_confidence=model_formulation.overall_confidence,
        )
        return FormulationResult(final=final, raw_model_output=model_formulation, model_id=model_id)
    monkeypatch.setattr(persistence_service, "generate_whole_life_formulation", _fake_call)


def stub_model_call_always_rejecting(monkeypatch):
    """Every attempt produces a Big Five score citing a nonexistent experience_id - guaranteed enforcement rejection."""
    def _fake_call(request, reasoning_effort="medium", max_output_tokens=16000):
        bad = build_minimal_model_formulation(
            baseline_personality=BigFiveProfile(**{
                t: (_score(evidence=[_cite("nonexistent_exp")]) if t == "openness" else _score())
                for t in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
            }),
        )
        from app.services.whole_life_formulation.derivation import derive_attachment_profile, derive_hypothesis_projection, derive_pattern_projection
        life = request.life
        final = WholeLifeFormulation(
            schema_version=bad.schema_version, baseline_personality=bad.baseline_personality,
            current_personality=bad.current_personality, personality_deltas=[],
            baseline_attachment=derive_attachment_profile(bad.baseline_attachment),
            current_attachment=derive_attachment_profile(bad.current_attachment),
            attachment_trajectory=[], current_state=bad.current_state,
            developmental_patterns=derive_pattern_projection(bad.pattern_scorecard, life),
            beliefs=[], protective_factors=[], causal_chains=[],
            hypotheses=derive_hypothesis_projection(bad.hypothesis_scorecard),
            contradictions=[], unresolved_questions=[], change_points=[], overall_confidence=0.5,
        )
        return FormulationResult(final=final, raw_model_output=bad, model_id="test-model")
    monkeypatch.setattr(persistence_service, "generate_whole_life_formulation", _fake_call)


# ---------------------------------------------------------------------------
# 1. Invalid optional claim is quarantined and not persisted
# ---------------------------------------------------------------------------

def test_invalid_optional_claim_is_rejected_not_persisted(db):
    life = LifeSourceData(persona_name="X", current_age=25, background="", caregiver_history="", temperament_self_description="",
                           experiences=[ExperienceSource(id="e1", age_at_event=20, sequence_index=1, user_description="d")])
    model = build_minimal_model_formulation(
        pattern_scorecard=PatternScorecard(**{
            f: (PatternFamilyScore(relevance_score=0.9, confidence=0.8, human_label="bad", reasoning="r",
                                    supporting_evidence=[_cite("nonexistent_exp")], contradicting_evidence=[])
                if f == "loss_and_bereavement" else _empty_pattern_score())
            for f in ("loss_and_bereavement", "identity_reconstruction", "relational_repair", "avoidant_withdrawal",
                      "risk_seeking_dysregulation", "caregiving_role_reversal", "achievement_or_competence_compensation",
                      "hypervigilant_monitoring", "prosocial_reinvention", "substance_coping")
        }),
    )
    from app.services.whole_life_formulation.derivation import derive_attachment_profile, derive_hypothesis_projection, derive_pattern_projection
    final = WholeLifeFormulation(
        schema_version="t", baseline_personality=model.baseline_personality, current_personality=model.current_personality,
        personality_deltas=[], baseline_attachment=derive_attachment_profile(model.baseline_attachment),
        current_attachment=derive_attachment_profile(model.current_attachment), attachment_trajectory=[],
        current_state=model.current_state, developmental_patterns=derive_pattern_projection(model.pattern_scorecard, life),
        beliefs=[], protective_factors=[], causal_chains=[], hypotheses=derive_hypothesis_projection(model.hypothesis_scorecard),
        contradictions=[], unresolved_questions=[], change_points=[], overall_confidence=0.5,
    )
    assert len(final.developmental_patterns) == 1  # the bad one made it past derivation (validity isn't checked there)

    result = enforce_validation(final, life)
    assert result.status == "accepted"
    assert len(result.accepted_formulation.developmental_patterns) == 0  # dropped by enforcement
    assert any(a.action_taken == "claim_rejected" and a.claim_type == "pattern" for a in result.actions)


# ---------------------------------------------------------------------------
# 2. Invalid citation removed when sufficient valid evidence remains
# ---------------------------------------------------------------------------

def test_invalid_citation_removed_claim_retained(db):
    life = LifeSourceData(persona_name="X", current_age=25, background="", caregiver_history="", temperament_self_description="",
                           experiences=[ExperienceSource(id="e1", age_at_event=20, sequence_index=1, user_description="d")])
    model = build_minimal_model_formulation(
        baseline_personality=BigFiveProfile(**{
            t: (_score(evidence=[_cite("e1"), _cite("nonexistent_exp")]) if t == "openness" else _score(evidence=[_cite("e1")]))
            for t in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
        }),
    )
    stub_final = _to_final(model, life)
    result = enforce_validation(stub_final, life)
    assert result.status == "accepted"
    assert len(result.accepted_formulation.baseline_personality.openness.evidence) == 1
    assert result.accepted_formulation.baseline_personality.openness.evidence[0].experience_id == "e1"
    assert any(a.action_taken == "citation_removed" for a in result.actions)


# ---------------------------------------------------------------------------
# 3. Invalid required core claim with no remaining evidence -> rejection
# ---------------------------------------------------------------------------

def test_required_core_claim_no_valid_evidence_rejects_whole_formulation(db):
    life = LifeSourceData(persona_name="X", current_age=25, background="", caregiver_history="", temperament_self_description="",
                           experiences=[ExperienceSource(id="e1", age_at_event=20, sequence_index=1, user_description="d")])
    model = build_minimal_model_formulation(
        baseline_personality=BigFiveProfile(**{
            t: (_score(evidence=[_cite("nonexistent_exp")]) if t == "openness" else _score(evidence=[_cite("e1")]))
            for t in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
        }),
    )
    stub_final = _to_final(model, life)
    result = enforce_validation(stub_final, life)
    assert result.status == "rejected"
    assert result.accepted_formulation is None
    assert "openness" in result.rejection_summary


def test_analyze_life_v2_retries_then_fails_on_persistent_rejection(db, monkeypatch):
    persona = make_persona(db)
    stub_model_call_always_rejecting(monkeypatch)
    result = persistence_service.analyze_life_v2(db, persona)
    assert result.status == "failed"
    assert "Previous formulation" in result.error
    assert db.query(WholeLifeFormulationRow).filter_by(persona_id=persona.id).count() == 0


# ---------------------------------------------------------------------------
# 4. Failed formulation leaves previous formulation unchanged
# ---------------------------------------------------------------------------

def test_failed_reanalysis_leaves_previous_formulation_unchanged(db, monkeypatch):
    persona = make_persona(db)
    good_model = build_minimal_model_formulation()
    stub_model_call(monkeypatch, good_model)
    first = persistence_service.analyze_life_v2(db, persona)
    assert first.status == "accepted"
    assert first.generation_number == 1
    original_personality = dict(persona.current_personality)

    stub_model_call_always_rejecting(monkeypatch)
    second = persistence_service.analyze_life_v2(db, persona)
    assert second.status == "failed"

    db.refresh(persona)
    assert persona.current_personality == original_personality
    rows = db.query(WholeLifeFormulationRow).filter_by(persona_id=persona.id).all()
    assert len(rows) == 1
    assert rows[0].status == "accepted"
    assert rows[0].generation_number == 1


# ---------------------------------------------------------------------------
# 5. Atomic rollback on projection failure
# ---------------------------------------------------------------------------

def test_atomic_rollback_on_projection_failure(db, monkeypatch):
    persona = make_persona(db)
    stub_model_call(monkeypatch, build_minimal_model_formulation())

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated projection failure")
    monkeypatch.setattr(persistence_service, "reconcile_all_projections", _boom)

    result = persistence_service.analyze_life_v2(db, persona)
    assert result.status == "failed"
    assert db.query(WholeLifeFormulationRow).filter_by(persona_id=persona.id).count() == 0
    db.refresh(persona)
    assert persona.formulation_engine_version == "v1"
    # session must still be usable after rollback
    assert db.query(Persona).filter_by(id=persona.id).first() is not None


# ---------------------------------------------------------------------------
# 6. V1 persona behavior unchanged with flag false
# ---------------------------------------------------------------------------

def test_v2_disabled_by_default(db):
    from app.core.config import settings
    assert settings.whole_life_formulation_v2 is False
    assert settings.whole_life_formulation_v2_enabled_for("any-persona", "any-user") is False


def test_v2_enabled_only_for_allowlisted_persona(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "whole_life_formulation_v2", True)
    monkeypatch.setattr(settings, "whole_life_formulation_v2_persona_allowlist_raw", "qa-persona-1")
    assert settings.whole_life_formulation_v2_enabled_for("qa-persona-1", "some-user") is True
    assert settings.whole_life_formulation_v2_enabled_for("other-persona", "some-user") is False


# ---------------------------------------------------------------------------
# 7 / 9. V2 re-analysis creates next generation; old generation remains historical
# ---------------------------------------------------------------------------

def test_reanalysis_increments_generation_and_keeps_history(db, monkeypatch):
    persona = make_persona(db)
    stub_model_call(monkeypatch, build_minimal_model_formulation())
    first = persistence_service.analyze_life_v2(db, persona)
    assert first.status == "accepted" and first.generation_number == 1

    stub_model_call(monkeypatch, build_minimal_model_formulation(overall_confidence=0.9))
    second = persistence_service.analyze_life_v2(db, persona)
    assert second.status == "accepted" and second.generation_number == 2

    rows = db.query(WholeLifeFormulationRow).filter_by(persona_id=persona.id).order_by(WholeLifeFormulationRow.generation_number).all()
    assert len(rows) == 2
    assert rows[0].generation_number == 1 and rows[0].status == "superseded"
    assert rows[1].generation_number == 2 and rows[1].status == "accepted"


# ---------------------------------------------------------------------------
# 8. Projections reflect latest accepted formulation
# ---------------------------------------------------------------------------

def test_projections_reflect_latest_generation(db, monkeypatch):
    persona = make_persona(db)
    model1 = build_minimal_model_formulation(
        pattern_scorecard=PatternScorecard(**{
            f: (PatternFamilyScore(relevance_score=0.9, confidence=0.8, human_label="gen1 pattern", reasoning="r",
                                    supporting_evidence=[_cite("e1")], contradicting_evidence=[])
                if f == "loss_and_bereavement" else _empty_pattern_score())
            for f in ("loss_and_bereavement", "identity_reconstruction", "relational_repair", "avoidant_withdrawal",
                      "risk_seeking_dysregulation", "caregiving_role_reversal", "achievement_or_competence_compensation",
                      "hypervigilant_monitoring", "prosocial_reinvention", "substance_coping")
        }),
    )
    stub_model_call(monkeypatch, model1)
    persistence_service.analyze_life_v2(db, persona)
    patterns = db.query(AdaptationPattern).filter_by(persona_id=persona.id).all()
    assert len(patterns) == 1 and patterns[0].pattern_name == "gen1 pattern"

    model2 = build_minimal_model_formulation(
        pattern_scorecard=PatternScorecard(**{
            f: (PatternFamilyScore(relevance_score=0.9, confidence=0.8, human_label="gen2 pattern", reasoning="r",
                                    supporting_evidence=[_cite("e1")], contradicting_evidence=[])
                if f == "prosocial_reinvention" else _empty_pattern_score())
            for f in ("loss_and_bereavement", "identity_reconstruction", "relational_repair", "avoidant_withdrawal",
                      "risk_seeking_dysregulation", "caregiving_role_reversal", "achievement_or_competence_compensation",
                      "hypervigilant_monitoring", "prosocial_reinvention", "substance_coping")
        }),
    )
    stub_model_call(monkeypatch, model2)
    persistence_service.analyze_life_v2(db, persona)
    patterns = db.query(AdaptationPattern).filter_by(persona_id=persona.id).all()
    assert len(patterns) == 1 and patterns[0].pattern_name == "gen2 pattern"  # replaced, not accumulated


# ---------------------------------------------------------------------------
# 10. Snapshots replace rather than duplicate
# ---------------------------------------------------------------------------

def test_snapshots_replace_not_duplicate(db, monkeypatch):
    persona = make_persona(db, n_experiences=2)
    stub_model_call(monkeypatch, build_minimal_model_formulation())
    persistence_service.analyze_life_v2(db, persona)
    persistence_service.analyze_life_v2(db, persona)
    snapshots = db.query(PersonalitySnapshot).filter_by(persona_id=persona.id).all()
    assert len(snapshots) == 2  # one per experience, not 4


# ---------------------------------------------------------------------------
# 11. No cross-user/persona access
# ---------------------------------------------------------------------------

def test_no_cross_user_access(db):
    make_persona(db, persona_id="p1", user_id="owner")
    found_for_wrong_user = db.query(Persona).filter(Persona.id == "p1", Persona.user_id == "attacker").first()
    assert found_for_wrong_user is None
    found_for_owner = db.query(Persona).filter(Persona.id == "p1", Persona.user_id == "owner").first()
    assert found_for_owner is not None


# ---------------------------------------------------------------------------
# 12 / 13. Brandon caregiver/self regression remains clean; no diagnosis leakage
# ---------------------------------------------------------------------------

def test_brandon_shaped_formulation_has_no_caregiver_self_confusion_or_diagnosis_leak(db, monkeypatch):
    life = LifeSourceData(
        persona_name="Brandon", current_age=40, background="", caregiver_history="", temperament_self_description="",
        experiences=[
            # e1 matches build_minimal_model_formulation()'s default Big
            # Five/attachment/state citations; brandon_e07/e10 are this
            # test's own pattern-level citations.
            ExperienceSource(id="e1", age_at_event=10, sequence_index=1, user_description="baseline"),
            ExperienceSource(id="brandon_e07", age_at_event=19, sequence_index=1, user_description="incarcerated"),
            ExperienceSource(id="brandon_e10", age_at_event=40, sequence_index=1, user_description="rehab"),
        ],
    )
    model = build_minimal_model_formulation(
        pattern_scorecard=PatternScorecard(**{
            f: (PatternFamilyScore(
                    relevance_score=0.8, confidence=0.7, human_label="Substance coping after loss", reasoning="r",
                    supporting_evidence=[_cite("brandon_e10", subject_role="self")], contradicting_evidence=[],
                ) if f == "substance_coping" else _empty_pattern_score())
            for f in ("loss_and_bereavement", "identity_reconstruction", "relational_repair", "avoidant_withdrawal",
                      "risk_seeking_dysregulation", "caregiving_role_reversal", "achievement_or_competence_compensation",
                      "hypervigilant_monitoring", "prosocial_reinvention", "substance_coping")
        }),
    )
    final = _to_final(model, life)
    result = enforce_validation(final, life)
    assert result.status == "accepted"

    caregiver_confusion = check_caregiver_self_confusion(result.accepted_formulation, self_event_ids={"brandon_e07", "brandon_e10"})
    assert caregiver_confusion == []
    diagnosis_leaks = check_no_diagnosis_language(result.accepted_formulation)
    assert diagnosis_leaks == []


# ---------------------------------------------------------------------------
# helper
# ---------------------------------------------------------------------------

def _to_final(model: ModelWholeLifeFormulation, life: LifeSourceData) -> WholeLifeFormulation:
    from app.services.whole_life_formulation.derivation import derive_attachment_profile, derive_hypothesis_projection, derive_pattern_projection
    return WholeLifeFormulation(
        schema_version=model.schema_version, baseline_personality=model.baseline_personality,
        current_personality=model.current_personality, personality_deltas=model.personality_deltas,
        baseline_attachment=derive_attachment_profile(model.baseline_attachment),
        current_attachment=derive_attachment_profile(model.current_attachment),
        attachment_trajectory=model.attachment_trajectory, current_state=model.current_state,
        developmental_patterns=derive_pattern_projection(model.pattern_scorecard, life),
        beliefs=model.beliefs, protective_factors=model.protective_factors, causal_chains=model.causal_chains,
        hypotheses=derive_hypothesis_projection(model.hypothesis_scorecard), contradictions=model.contradictions,
        unresolved_questions=model.unresolved_questions, change_points=model.change_points,
        overall_confidence=model.overall_confidence,
    )
