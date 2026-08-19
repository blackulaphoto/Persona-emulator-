"""
Integration tests for Step 11e (docs/MIGRATION_MAP.md): the State/Trait
mechanism wired into app/api/routes/interventions.py::add_intervention.

Covers: the old ungated write (persona.current_personality[trait] = analysis
value, straight from the AI's own "personality_changes") is gone; State
always moves from a proposal; Trait only moves once select_targeted_pattern
finds a real established AdaptationPattern AND intervention_trait_gate_open
sees documented efficacy_match improvement (>= INTERVENTION_IMPROVEMENT_
THRESHOLD) on >= INTERVENTION_SUSTAINED_COUNT interventions targeting that
same pattern, this one included.

app/services/intervention_engine.py's own AI call (analyze_intervention) is
mocked per-test to control efficacy_match directly - unlike the other
_route_wiring test files, it is NOT forced to fail, since these tests need
specific efficacy_match values to cross (or stay under) the sustained-
improvement threshold. state_trait_engine's own AI call IS forced to fail
(the honest current production state - no OpenAI credits configured),
exercising the deterministic heuristic fallback (see state_trait_engine.
propose_intervention_state_trait_implications_heuristic) for State/Trait
movement itself.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, Intervention, AdaptationPattern, PersonalitySnapshot
from app.api.routes.interventions import add_intervention
from app.schemas import InterventionCreate

TEST_DB_URL = "sqlite:///./test_interventions_route_wiring.db"
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


@pytest.fixture(autouse=True)
def _fail_state_trait_ai_calls():
    # Forces state_trait_engine's own AI call to fail every time, so State/
    # Trait movement always comes from the deterministic heuristic fallback -
    # intervention_engine's AI call (efficacy_match etc.) is mocked
    # separately, per test, via _mock_analysis below.
    p = patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock)
    mock = p.start()
    mock.side_effect = Exception("simulated API failure - forces heuristic fallback")
    yield
    p.stop()


def _make_persona(db, **overrides):
    defaults = dict(
        name="Michael", baseline_age=25, current_age=25, baseline_gender="male",
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], current_state={}, user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def _make_established_pattern(db, persona_id, adaptation_strategy="avoidance", evidence_strength=0.6, pattern_name="Leave Before You're Left"):
    pattern = AdaptationPattern(
        persona_id=persona_id,
        pattern_name=pattern_name,
        adaptation_strategy=adaptation_strategy,
        status="established",
        evidence_strength=evidence_strength,
        supporting_experience_ids=[],
        current_manifestations=[],
    )
    db.add(pattern)
    db.commit()
    return pattern


def _mock_analysis(efficacy_match=0.9):
    return {
        "efficacy_match": efficacy_match,
        "symptom_changes": {"before": {"avoidance": 7}, "after": {"avoidance": 5}, "percentage_improvement": {"avoidance": 29}},
        "personality_changes": {"neuroticism": 0.9},  # deliberately extreme - must NOT be applied directly (see below)
        "coping_skills_gained": ["values-based action"],
        "sustained_effects": ["Some gains maintained with practice"],
        "limitations": ["Root attachment wounds persist"],
        "reasoning": "test reasoning",
    }


async def _add_intervention(db, persona, therapy_type="DBT", efficacy_match=0.9, age=30):
    with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = _mock_analysis(efficacy_match)
        return await add_intervention(
            persona_id=persona.id,
            intervention_data=InterventionCreate(therapy_type=therapy_type, duration="6_months", intensity="weekly", age_at_intervention=age),
            user_id="user-1", db=db,
        )


class TestOldUngatedWriteIsGone:
    @pytest.mark.asyncio
    async def test_ai_personality_changes_value_is_never_applied_directly(self, db):
        # _mock_analysis proposes neuroticism=0.9 directly - Step 11e retires
        # the old code path that would have written that straight onto
        # persona.current_personality. With no established pattern yet, the
        # gate is closed and current_personality must stay untouched.
        persona = _make_persona(db)
        await _add_intervention(db, persona, efficacy_match=0.9)
        db.refresh(persona)
        assert persona.current_personality["neuroticism"] == 0.5


class TestNoEstablishedPattern:
    @pytest.mark.asyncio
    async def test_state_and_trait_both_stay_empty_without_an_established_pattern(self, db):
        persona = _make_persona(db)
        response = await _add_intervention(db, persona, efficacy_match=0.9)
        db.refresh(persona)
        assert persona.current_state == {}
        assert persona.current_personality == {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
        assert response.personality_changes == persona.current_personality

    @pytest.mark.asyncio
    async def test_targeted_adaptation_strategy_recorded_as_none(self, db):
        persona = _make_persona(db)
        response = await _add_intervention(db, persona, efficacy_match=0.9)
        row = db.query(Intervention).filter(Intervention.id == response.id).first()
        assert row.targeted_adaptation_strategy is None
        assert row.state_implications is None
        assert row.trait_implications is None


class TestStateMovesUnconditionally:
    @pytest.mark.asyncio
    async def test_state_moves_on_first_intervention_even_though_trait_gate_is_closed(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")
        await _add_intervention(db, persona, efficacy_match=0.9)
        db.refresh(persona)

        # avoidance's own default INCREASES "avoidance" state - therapy
        # heuristically proposes the inverse (decrease).
        assert persona.current_state["avoidance"] < 0.5
        # Trait gate is closed (only 1 documented improvement so far).
        assert persona.current_personality["extraversion"] == 0.5

    @pytest.mark.asyncio
    async def test_snapshot_carries_state_profile(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")
        response = await _add_intervention(db, persona, efficacy_match=0.9)
        db.refresh(persona)

        snapshot = db.query(PersonalitySnapshot).filter(PersonalitySnapshot.intervention_id == response.id).first()
        assert snapshot is not None
        assert snapshot.state_profile == persona.current_state
        assert snapshot.state_profile != {}


class TestSustainedImprovementGate:
    @pytest.mark.asyncio
    async def test_trait_gate_opens_on_second_documented_improvement_targeting_same_pattern(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")

        await _add_intervention(db, persona, therapy_type="DBT", efficacy_match=0.8)
        db.refresh(persona)
        assert persona.current_personality["extraversion"] == 0.5  # still closed after #1

        await _add_intervention(db, persona, therapy_type="DBT", efficacy_match=0.9)
        db.refresh(persona)
        # avoidance's own default DECREASES extraversion - therapy proposes
        # the inverse (increase) once the gate opens.
        assert persona.current_personality["extraversion"] > 0.5

    @pytest.mark.asyncio
    async def test_low_efficacy_never_opens_the_gate_no_matter_how_many_interventions(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")

        for _ in range(4):
            await _add_intervention(db, persona, efficacy_match=0.2)
            db.refresh(persona)

        assert persona.current_personality["extraversion"] == 0.5

    @pytest.mark.asyncio
    async def test_targeted_adaptation_strategy_persisted_per_intervention(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")
        response = await _add_intervention(db, persona, efficacy_match=0.9)
        row = db.query(Intervention).filter(Intervention.id == response.id).first()
        assert row.targeted_adaptation_strategy == "avoidance"
        assert row.state_implications  # non-empty dict
        # {} or None -> None, same "empty means null" convention as
        # Interpretation.trait_implications (Step 11a/11c) - gate was closed.
        assert row.trait_implications is None

    @pytest.mark.asyncio
    async def test_prior_intervention_targeting_a_different_pattern_does_not_count_toward_sustained(self, db):
        persona = _make_persona(db)
        # A prior, already-persisted intervention that targeted a DIFFERENT
        # established pattern (hypervigilance) with high documented
        # improvement - must not count toward avoidance's sustained-gate.
        db.add(Intervention(
            user_id="user-1", persona_id=persona.id, sequence_number=1, age_at_intervention=25,
            therapy_type="Somatic_Experiencing", duration="6_months", intensity="weekly",
            efficacy_match=0.95, targeted_adaptation_strategy="hypervigilance",
        ))
        db.commit()

        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance", evidence_strength=0.9)
        await _add_intervention(db, persona, efficacy_match=0.9)
        db.refresh(persona)

        # Only 1 real documented improvement for avoidance (this call) - gate stays closed.
        assert persona.current_personality["extraversion"] == 0.5

    @pytest.mark.asyncio
    async def test_personality_changes_response_field_reflects_real_current_personality_after_gate_opens(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")
        await _add_intervention(db, persona, efficacy_match=0.9)
        response = await _add_intervention(db, persona, efficacy_match=0.9)
        db.refresh(persona)

        # Not the AI's fabricated neuroticism=0.9 from _mock_analysis - the
        # real, gated current_personality dict.
        assert response.personality_changes == persona.current_personality
        assert response.personality_changes["neuroticism"] == 0.5
        assert response.personality_changes["extraversion"] > 0.5


class TestInterventionEngineStillGetsAdaptationPatterns:
    @pytest.mark.asyncio
    async def test_adaptation_patterns_passed_to_analyze_intervention(self, db):
        # Step 11e also wires the persona's real AdaptationPattern rows into
        # analyze_intervention's optional adaptation_patterns param (dormant
        # since Step 7 - see intervention_engine.py's own docstring).
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")

        with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = _mock_analysis(0.9)
            await add_intervention(
                persona_id=persona.id,
                intervention_data=InterventionCreate(therapy_type="DBT", duration="6_months", intensity="weekly", age_at_intervention=30),
                user_id="user-1", db=db,
            )
            prompt_arg = mock_analyze.call_args.kwargs.get("prompt") or mock_analyze.call_args.args[0]
            assert "ESTABLISHED DEVELOPMENTAL PATTERNS" in prompt_arg
            assert "Leave Before You're Left" in prompt_arg


class TestStateTraitProposalFailureDoesNotBlockIntervention:
    @pytest.mark.asyncio
    async def test_intervention_still_created_if_proposal_raises(self, db):
        persona = _make_persona(db)
        _make_established_pattern(db, persona.id, adaptation_strategy="avoidance")

        with patch(
            "app.api.routes.interventions.propose_intervention_state_trait_implications_async",
            new_callable=AsyncMock, side_effect=RuntimeError("simulated crash"),
        ):
            response = await _add_intervention(db, persona, efficacy_match=0.9)

        assert response is not None
        persisted = db.query(Intervention).filter(Intervention.id == response.id).first()
        assert persisted is not None
        db.refresh(persona)
        assert persona.current_state == {}  # apply_state_update({}, {}) -> {}
        assert persona.current_personality["extraversion"] == 0.5
