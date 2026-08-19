"""
Tests for Step 11c of docs/MIGRATION_MAP.md: state_trait_engine.py actually
wired into developmental_pipeline.py, updating Persona.current_state
(always) and Persona.current_personality (gated on AdaptationPattern.status
== "established") in a real end-to-end pipeline run.

Uses "bullied/picked on/made fun of/excluded" text across four calls -
these four phrases all map to the SAME exposure_type (peer_rejection_or_
bullying, see developmental_exposure_engine.EXPOSURE_TAXONOMY) and
therefore the SAME adaptation_strategy ("avoidance", see pattern_engine.
EXPOSURE_INTERPRETATION_DEFAULTS) under the heuristic fallback path -
chosen deliberately so the reinforcement math is fully predictable, unlike
this repo's other multi-exposure test texts (e.g. "drank...disappeared",
which maps to two different exposure_types with an extraction-order-
dependent adaptation_strategy).

With REINFORCE_INCREMENT=0.2 and ESTABLISHED_THRESHOLD=0.5 (pattern_engine.py),
the 4th interpretation sharing a strategy is the first to cross the
threshold (0.2 + 0.2 + 0.2 = 0.6 >= 0.5) - so the trait gate should open on
exactly the 4th call, not before.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, Interpretation, AdaptationPattern
from app.services.developmental_pipeline import process_developmental_text

TEST_DB_URL = "sqlite:///./test_developmental_pipeline_state_trait.db"
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
def _fail_all_ai_calls():
    patches = [
        patch("app.services.developmental_exposure_engine.openai_service.analyze", new_callable=AsyncMock),
        patch("app.services.self_narration_engine.openai_service.analyze", new_callable=AsyncMock),
        patch("app.services.pattern_engine.openai_service.analyze", new_callable=AsyncMock),
        patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock),
    ]
    mocks = [p.start() for p in patches]
    for m in mocks:
        m.side_effect = Exception("simulated API failure - forces fallback path")
    yield
    for p in patches:
        p.stop()


def _make_persona(db, **overrides):
    defaults = dict(
        name="Michael", baseline_age=8, current_age=8, baseline_gender="male",
        baseline_background="He was bullied by classmates at school.",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], current_state={}, user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


BULLYING_TEXTS = [
    "He was bullied by classmates at school.",
    "He was picked on by classmates again.",
    "He was made fun of by classmates once more.",
    "He was excluded by classmates yet again.",
]


class TestStateTierAppliesOnSingleCall:
    @pytest.mark.asyncio
    async def test_single_backstory_moves_current_state(self, db):
        persona = _make_persona(db, baseline_background=BULLYING_TEXTS[0])
        result = await process_developmental_text(
            db, persona, persona.baseline_background, source="backstory", age=8,
        )
        db.commit()
        db.refresh(persona)

        assert result["state_changes"]  # avoidance's heuristic default proposes state movement
        assert persona.current_state != {}
        assert "avoidance" in persona.current_state  # ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS["avoidance"]

    @pytest.mark.asyncio
    async def test_single_call_does_not_move_trait(self, db):
        # Status is "emerging" after one interpretation - gate must stay closed.
        persona = _make_persona(db, baseline_background=BULLYING_TEXTS[0])
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=8)
        db.commit()
        db.refresh(persona)

        pattern = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).first()
        assert pattern.status == "emerging"
        assert persona.current_personality["extraversion"] == 0.5  # untouched

    @pytest.mark.asyncio
    async def test_interpretation_row_persists_state_and_trait_implications(self, db):
        persona = _make_persona(db, baseline_background=BULLYING_TEXTS[0])
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=8)
        db.commit()

        interp = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).first()
        assert interp.state_implications  # populated
        assert interp.trait_implications is None  # gate was closed - nothing to persist


class TestTraitTierGatedAcrossReinforcement:
    @pytest.mark.asyncio
    async def test_trait_stays_closed_until_pattern_established_then_opens_on_the_crossing_call(self, db):
        persona = _make_persona(db, baseline_background=BULLYING_TEXTS[0])

        # Call 1: originates the pattern. emerging, strength None.
        await process_developmental_text(db, persona, BULLYING_TEXTS[0], source="backstory", age=8)
        db.commit()
        db.refresh(persona)
        assert persona.current_personality["extraversion"] == 0.5

        # Call 2: 1st reinforcement -> strength 0.2, still emerging.
        await process_developmental_text(db, persona, BULLYING_TEXTS[1], source="experience", age=9, source_event_id="e2")
        db.commit()
        db.refresh(persona)
        pattern = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).first()
        assert pattern.status == "emerging"
        assert persona.current_personality["extraversion"] == 0.5

        # Call 3: 2nd reinforcement -> strength 0.4, still emerging (< 0.5 threshold).
        await process_developmental_text(db, persona, BULLYING_TEXTS[2], source="experience", age=10, source_event_id="e3")
        db.commit()
        db.refresh(persona)
        pattern = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).first()
        assert pattern.status == "emerging"
        assert persona.current_personality["extraversion"] == 0.5

        # Call 4: 3rd reinforcement -> strength 0.6, crosses ESTABLISHED_THRESHOLD.
        # The gate opens on THIS call - extraversion should move down (avoidance's
        # heuristic trait default) by exactly TRAIT_STEP["mild"] from the 0.5 baseline.
        await process_developmental_text(db, persona, BULLYING_TEXTS[3], source="experience", age=11, source_event_id="e4")
        db.commit()
        db.refresh(persona)
        pattern = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).first()
        assert pattern.status == "established"
        assert persona.current_personality["extraversion"] < 0.5
        assert persona.current_personality["extraversion"] == pytest.approx(0.48, abs=1e-6)

        # Only the 4th Interpretation row should carry trait_implications - the
        # first three all had the gate closed.
        interps = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).order_by(Interpretation.age_at_event).all()
        assert [i.trait_implications for i in interps[:3]] == [None, None, None]
        assert interps[3].trait_implications is not None

    @pytest.mark.asyncio
    async def test_a_single_unrelated_event_never_moves_trait(self, db):
        # Direct regression test for the user's literal "boss yells at Michael,
        # neuroticism 57->59" complaint - one event, unrelated adaptation
        # strategy, must never move Trait regardless of magnitude.
        persona = _make_persona(db, baseline_background="They lived in a house and went to school.")
        await process_developmental_text(
            db, persona, "His boss yelled at him during a meeting.",
            source="experience", age=24, source_event_id="e1",
        )
        db.commit()
        db.refresh(persona)
        assert persona.current_personality == {
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5,
        }


class TestOtherTraitsAndPersonaFieldsUnaffected:
    @pytest.mark.asyncio
    async def test_untouched_traits_and_current_trauma_markers_still_correct(self, db):
        persona = _make_persona(db, baseline_background=BULLYING_TEXTS[0])
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=8)
        db.commit()
        db.refresh(persona)

        # avoidance's heuristic trait default only ever touches extraversion.
        assert persona.current_personality["openness"] == 0.5
        assert persona.current_personality["neuroticism"] == 0.5
        # Existing step-4 behavior (trauma marker projection) unaffected by Step 11.
        assert result["trauma_markers"] == []
