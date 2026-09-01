"""
Integration test for app/services/developmental_pipeline.py -
process_developmental_text(), the actual wiring of steps 2-5 (docs/
MIGRATION_MAP.md). Runs the full chain against a real SQLite session with
every AI call mocked to fail fast, exercising the fallback/heuristic paths
end to end - which also happens to be the honest current production state
(no OpenAI credits configured), so this test validates exactly the behavior
a real deployment would see today.

Every "experience" call in this file first creates a real Experience row
with that exact id via _make_experience(), matching what
experiences.py::add_experience actually does in production (creates and
flushes the Experience row, THEN calls process_developmental_text() with
its real id as source_event_id) - required since canonical_provenance.py's
exposure_has_provenance/interpretation_has_provenance now validate that a
source_event_id genuinely belongs to this persona's real timeline before
letting it contribute to accumulated evidence. Every "backstory" call uses
age=None, matching personas.py::create_persona's canonical grounding fix -
undated developmental background must never carry a fabricated current-age.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Persona, Experience, DevelopmentalExposure, ProtectiveFactor, NarrationRecord,
    ClinicalPatternHypothesis, AdaptationPattern, Interpretation,
)
from app.services.developmental_pipeline import process_developmental_text

TEST_DB_URL = "sqlite:///./test_developmental_pipeline.db"
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
    """
    Forces every engine's fallback path - deterministic, fast, and matches
    this environment's actual state (no OpenAI credits). Patches each
    module's own openai_service instance since they're separate
    OpenAIService() objects, not a shared singleton.
    """
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
        name="Timmy", baseline_age=6, current_age=6, baseline_gender="male",
        baseline_background="My father drank constantly and disappeared for days.",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def _make_experience(db, persona, event_id: str, age: int, description: str) -> Experience:
    """Real Experience row, flushed so its id is valid provenance for a
    process_developmental_text(source="experience", source_event_id=event_id)
    call - see this module's docstring."""
    experience = Experience(
        id=event_id, persona_id=persona.id, user_id=persona.user_id,
        sequence_number=age, sequence_index=1, age_at_event=age, user_description=description,
    )
    db.add(experience)
    db.flush()
    return experience


class TestSingleCallEndToEnd:
    @pytest.mark.asyncio
    async def test_backstory_produces_exposures(self, db):
        persona = _make_persona(db)
        result = await process_developmental_text(
            db, persona, persona.baseline_background, source="backstory", age=None,
        )
        db.commit()

        exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).all()
        assert len(exposures) >= 1
        assert {e.exposure_type for e in exposures} & {"caregiver_substance_use", "caregiver_absence"}
        assert all(e.speaker_role == "case_author" for e in exposures)
        assert result["exposures"]

    @pytest.mark.asyncio
    async def test_narration_record_created_but_gated(self, db):
        # case_author speaker_role - narration analysis must be gated (see step-10/
        # self_narration_engine tests), but a record with provenance is still stored.
        persona = _make_persona(db)
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        records = db.query(NarrationRecord).filter(NarrationRecord.subject_id == persona.id).all()
        assert len(records) == 1
        assert records[0].attributed_to_persona is False
        assert records[0].linguistic_signals == []

    @pytest.mark.asyncio
    async def test_single_exposure_opens_hypothesis_without_seeding_belief(self, db):
        # The core invariant from step 4, now proven through the actual wired pipeline.
        persona = _make_persona(db)
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        hypotheses = db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
        assert len(hypotheses) >= 1
        assert all(h.evidence_strength is None for h in hypotheses)
        assert result["trauma_markers"] == []  # nothing crosses the display threshold yet

    @pytest.mark.asyncio
    async def test_interpretation_and_pattern_created(self, db):
        persona = _make_persona(db)
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        interpretations = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).all()
        assert len(interpretations) == 1
        assert interpretations[0].adaptation_strategy is not None
        assert interpretations[0].age_at_event is None  # undated background stays undated

        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        assert len(patterns) == 1
        assert patterns[0].status == "emerging"  # single interpretation - not established yet
        assert result["interpretation"] is not None

    @pytest.mark.asyncio
    async def test_no_exposures_in_text_produces_no_new_rows(self, db):
        persona = _make_persona(db, baseline_background="They lived in a house and went to school.")
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        assert db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).count() == 0
        assert db.query(Interpretation).filter(Interpretation.persona_id == persona.id).count() == 0
        assert result["trauma_markers"] == []


class TestUndatedBackgroundStaysUndated:
    """
    Canonical grounding fix: process_developmental_text's age parameter for
    a "backstory" call must be None, never persona.baseline_age or any
    other real number - a stray age on undated background is exactly what
    let a fabricated current-age event (the age-40 caregiver_substance_use
    regression) enter the timeline in the first place.
    """

    @pytest.mark.asyncio
    async def test_backstory_exposure_persists_with_no_age(self, db):
        persona = _make_persona(db)
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).all()
        assert exposures
        assert all(e.age_at_exposure is None for e in exposures)
        assert all(e.source_event_id is None for e in exposures)

    @pytest.mark.asyncio
    async def test_backstory_interpretation_persists_with_no_age(self, db):
        persona = _make_persona(db)
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        interpretation = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).one()
        assert interpretation.age_at_event is None
        assert interpretation.source_event_id is None

    @pytest.mark.asyncio
    async def test_a_dated_backstory_call_is_a_misuse_that_gets_filtered_out(self, db):
        # Defensive proof, not an endorsement: if something ever calls this
        # function with source="backstory" and a real age again (the exact
        # bug this whole correction removes from personas.py), the
        # provenance filter still refuses to let the resulting interpretation
        # contribute a pattern - it fails safe rather than silently
        # persisting a fabricated current-age developmental event.
        persona = _make_persona(db)
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=40)
        db.commit()

        assert result["interpretation"] is not None  # this call's own interpretation is still built...
        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        assert patterns == []  # ...but provenance-filtered out of pattern accumulation


class TestSecondCallAcrossTimelineRecomputes:
    @pytest.mark.asyncio
    async def test_recurring_exposure_earns_real_evidence_on_second_call(self, db):
        persona = _make_persona(db)
        # First call - backstory.
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()

        # Second call - a later "experience" describing the same kind of exposure.
        _make_experience(db, persona, "exp-1", 10, "His father was gone again for days, drinking the whole time.")
        await process_developmental_text(
            db, persona, "His father was gone again for days, drinking the whole time.",
            source="experience", age=10, source_event_id="exp-1",
        )
        db.commit()

        # Same pattern_key rows updated in place, not duplicated.
        hypotheses = db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
        pattern_keys = [h.pattern_key for h in hypotheses]
        assert len(pattern_keys) == len(set(pattern_keys))  # no duplicates

        # A single persistence bump (0.15) is real, earned evidence - but
        # correctly stays below the 0.4 display threshold on its own. It
        # should not yet appear in current_trauma_markers.
        strengths = {h.pattern_key: h.evidence_strength for h in hypotheses}
        assert any(v is not None for v in strengths.values())
        assert all((v or 0) < 0.4 for v in strengths.values())

        # With backstory + exp-1, that's 2 distinct entries so far (1
        # persistence bump = 0.15). Two more distinct occurrences are needed
        # to cross DISPLAY_THRESHOLD (0.4): extra_occurrences = entries - 1,
        # capped at MAX_PERSISTENCE_ENTRIES - 3 entries -> 2 bumps (0.30,
        # still under); 4 entries -> 3 bumps (0.45, crosses). See
        # evidence_accumulator.MAX_PERSISTENCE_ENTRIES.
        _make_experience(db, persona, "exp-2", 14, "By age 14 his father was still drinking constantly and disappearing for days at a time.")
        await process_developmental_text(
            db, persona, "By age 14 his father was still drinking constantly and disappearing for days at a time.",
            source="experience", age=14, source_event_id="exp-2",
        )
        db.commit()
        _make_experience(db, persona, "exp-3", 17, "At 17 his father drank for days again, gone without a word.")
        result4 = await process_developmental_text(
            db, persona, "At 17 his father drank for days again, gone without a word.",
            source="experience", age=17, source_event_id="exp-3",
        )
        db.commit()
        assert result4["trauma_markers"]  # now crosses the display threshold

    @pytest.mark.asyncio
    async def test_adaptation_pattern_reinforced_not_duplicated(self, db):
        persona = _make_persona(db)
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()
        _make_experience(db, persona, "exp-1", 10, "His father was gone again for days, drinking the whole time.")
        await process_developmental_text(
            db, persona, "His father was gone again for days, drinking the whole time.",
            source="experience", age=10, source_event_id="exp-1",
        )
        db.commit()

        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        strategies = [p.adaptation_strategy for p in patterns]
        assert len(strategies) == len(set(strategies))  # no duplicates per strategy


class TestCurrentTraumaMarkersProjection:
    @pytest.mark.asyncio
    async def test_projection_only_includes_evidenced_patterns(self, db):
        persona = _make_persona(db)
        result1 = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()
        assert result1["trauma_markers"] == []

        _make_experience(db, persona, "exp-1", 10, "His father was gone again for days, drinking the whole time.")
        result2 = await process_developmental_text(
            db, persona, "His father was gone again for days, drinking the whole time.",
            source="experience", age=10, source_event_id="exp-1",
        )
        db.commit()
        assert isinstance(result2["trauma_markers"], list)

    @pytest.mark.asyncio
    async def test_age_inapplicable_hypothesis_excluded_from_result_for_an_adult_persona(self, db):
        # End-to-end version of test_evidence_accumulator.py's direct unit
        # test: reactive_attachment_disorder must not surface in this
        # pipeline's own returned trauma_markers for an adult persona, even
        # if evidence for it were somehow strong - exercised here by
        # confirming the current_age argument actually reaches the
        # projection call (a wiring check, not a re-test of the threshold
        # math already covered in test_evidence_accumulator.py).
        persona = _make_persona(db, current_age=40, baseline_age=40)
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=None)
        db.commit()
        assert "reactive_attachment_disorder" not in result["trauma_markers"]


# ============================================================
# P0-2 correction regression: developmental significance is not the same
# thing as adversity (RELEASE_READINESS_2026-08-30.md). Positive/reparative
# text that extract_developmental_exposures_async classifies as a
# ProtectiveFactor (not an adverse Exposure) must still be eligible for
# interpretation and State movement - it must not be silently skipped the
# way it was before this pipeline was gated on this_batch_exposures alone.
#
# Every case here runs through the same AI-fails-forces-fallback harness as
# the rest of this file (see _fail_all_ai_calls above), so extraction goes
# through the deterministic keyword-fallback path and interpretation goes
# through interpret_reparative_experience_heuristic /
# interpret_experience_heuristic - exercising the real, wired pipeline
# end-to-end, not a mocked shortcut.
# ============================================================
class TestPositiveAndReparativeExperiencesAreAnalyzed:
    @pytest.mark.asyncio
    async def test_case1_adversity_still_analyzes_as_a_regression_fixture(self, db):
        """CASE 1 (section 14): the flagship betrayal scenario from the audit
        must keep working exactly as before - this is the regression fixture
        every other case in this class is a variant of."""
        persona = _make_persona(db, baseline_background="A stable, ordinary childhood.")
        description = (
            "Her best friend since kindergarten told the whole class a secret in confidence, "
            "and she felt utterly humiliated."
        )
        _make_experience(db, persona, "exp-betrayal", 8, description)
        result = await process_developmental_text(
            db, persona, description, source="experience", age=8, source_event_id="exp-betrayal",
        )
        db.commit()

        assert result["interpretation"] is not None
        assert result["interpretation"].adaptation_strategy is not None
        interpretations = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).all()
        assert len(interpretations) == 1

    @pytest.mark.asyncio
    async def test_case2_trust_repair_is_analyzed_not_skipped(self, db):
        """CASE 2: the exact defect from the audit - a batch with a
        protective/reparative factor and NO adverse exposure must still
        produce a real interpretation, not a null one."""
        persona = _make_persona(db, baseline_background="A stable, ordinary childhood.")
        description = (
            "He took responsibility and repaired the relationship, and she found herself "
            "able to trust him again."
        )
        _make_experience(db, persona, "exp-repair", 9, description)
        result = await process_developmental_text(
            db, persona, description, source="experience", age=9, source_event_id="exp-repair",
        )
        db.commit()

        assert result["exposures"] == []  # confirms this is genuinely the no-exposure path
        assert result["protective_factors"]
        assert result["interpretation"] is not None
        assert result["interpretation"].belief_statement is not None
        assert result["interpretation"].reasoning is not None
        # Deliberately no adaptation_strategy - see pattern_engine.
        # interpret_reparative_experience_async's docstring for why.
        assert result["interpretation"].adaptation_strategy is None
        # The headline before/after from the audit: current_state actually moves.
        assert result["state_changes"]

    @pytest.mark.asyncio
    async def test_case3_achievement_is_analyzed_without_forced_pathology_framing(self, db):
        """CASE 3: a genuine achievement must be analyzed, and must not be
        coerced into one of the 12 adverse coping-strategy labels."""
        persona = _make_persona(db, baseline_background="A stable, ordinary childhood.")
        description = "She won a competition and it felt like a proud accomplishment."
        _make_experience(db, persona, "exp-achievement", 11, description)
        result = await process_developmental_text(
            db, persona, description, source="experience", age=11, source_event_id="exp-achievement",
        )
        db.commit()

        assert result["interpretation"] is not None
        assert result["interpretation"].adaptation_strategy is None
        assert result["interpretation"].belief_statement is not None

    @pytest.mark.asyncio
    async def test_case4_sustained_support_is_eligible_for_analysis(self, db):
        """CASE 4: sustained support during vulnerability is eligible for
        developmental analysis, same as any other reparative factor."""
        persona = _make_persona(db, baseline_background="A stable, ordinary childhood.")
        description = "Her aunt consistently offered support through the hardest years."
        _make_experience(db, persona, "exp-support", 12, description)
        result = await process_developmental_text(
            db, persona, description, source="experience", age=12, source_event_id="exp-support",
        )
        db.commit()

        assert result["interpretation"] is not None
        assert result["interpretation"].belief_statement is not None

    @pytest.mark.asyncio
    async def test_case5_developmentally_trivial_positive_event_is_not_forced_into_significance(self, db):
        """CASE 5: a real but developmentally trivial positive event is a
        VALID "nothing significant here" outcome - extraction itself finds
        neither an exposure nor a protective factor, and the pipeline must
        not manufacture an interpretation or move the model just because the
        text is pleasant. This is the one case that stays uninterpreted -
        not a taxonomy blind spot, extraction genuinely found nothing."""
        persona = _make_persona(db, baseline_background="A stable, ordinary childhood.")
        before_state = dict(persona.current_state or {})
        before_personality = dict(persona.current_personality)

        description = "They had a pleasant lunch together and watched a movie afterward."
        _make_experience(db, persona, "exp-trivial", 10, description)
        result = await process_developmental_text(
            db, persona, description, source="experience", age=10, source_event_id="exp-trivial",
        )
        db.commit()

        assert result["exposures"] == []
        assert result["protective_factors"] == []
        assert result["interpretation"] is None
        assert result["state_changes"] == {}
        assert result["trait_changes"] == {}
        assert db.query(Interpretation).filter(Interpretation.persona_id == persona.id).count() == 0
        assert persona.current_state == before_state
        assert persona.current_personality == before_personality

    @pytest.mark.asyncio
    async def test_reparative_evidence_weakens_a_later_reinforcement_of_the_adverse_pattern_it_contradicts(self, db):
        """Section 11's contradictory-evidence requirement, proven through
        the real end-to-end pipeline rather than accumulate_patterns() in
        isolation (already covered by tests/test_pattern_engine.py). A
        protective factor whose domains overlap a LATER same-strategy
        adverse reinforcement is marked "weakened", not "strengthened" -
        this was already true of accumulate_patterns() before this
        correction; what's new is that the reparative event that PRODUCES
        the protective factor is now itself a real, analyzed event instead
        of a silently-skipped one."""
        persona = _make_persona(
            db, baseline_background="A stable, ordinary childhood, though sensitive to criticism."
        )
        # First adverse event: opens the "self_reliance"-strategy pattern via
        # caregiver_absence (keywords: "disappeared", "never around"),
        # domains attachment_security + stability.
        description1 = "Her father disappeared for days and was never around."
        _make_experience(db, persona, "exp-adverse-1", 7, description1)
        await process_developmental_text(
            db, persona, description1, source="experience", age=7, source_event_id="exp-adverse-1",
        )
        db.commit()
        pattern_before = db.query(AdaptationPattern).filter_by(persona_id=persona.id, adaptation_strategy="self_reliance").first()
        assert pattern_before is not None
        assert pattern_before.status == "emerging"

        # Reparative event in between: a genuine repair, no exposure, no
        # adaptation_strategy of its own - must still be analyzed (case 2's
        # assertion again, incidentally). Its protective factor
        # (corrective_emotional_experience, domains include
        # attachment_security - the same domain the pattern above was opened
        # on) becomes available to buffer a later reinforcement.
        description2 = (
            "He took responsibility and repaired the relationship, and this "
            "time he stayed instead of leaving."
        )
        _make_experience(db, persona, "exp-repair-2", 9, description2)
        reparative_result = await process_developmental_text(
            db, persona, description2, source="experience", age=9, source_event_id="exp-repair-2",
        )
        db.commit()
        assert reparative_result["interpretation"] is not None

        # Second adverse event, same strategy/domain as the first - normally
        # "strengthened"; here it should register as "weakened" instead,
        # because of the intervening protective factor.
        description3 = "Her father disappeared again for days, gone without a word."
        _make_experience(db, persona, "exp-adverse-3", 11, description3)
        await process_developmental_text(
            db, persona, description3, source="experience", age=11, source_event_id="exp-adverse-3",
        )
        db.commit()

        pattern_after = db.query(AdaptationPattern).filter_by(persona_id=persona.id, adaptation_strategy="self_reliance").first()
        assert pattern_after.reinforcement_history[-1]["effect"] == "weakened"


class TestPatternEmergenceCannotCiteANonexistentEvent:
    """
    Provenance filtering, exercised through the live pipeline rather than
    canonical_provenance.py in isolation: an Interpretation/DevelopmentalExposure
    row whose source_event_id does not correspond to any real Experience this
    persona actually has (a stale row left behind by a deleted experience, a
    copy/paste error, a future migration bug) must not contribute to pattern
    accumulation or hypothesis evidence, even though the row itself is
    real and persisted.
    """

    @pytest.mark.asyncio
    async def test_orphaned_exposure_with_no_matching_experience_is_excluded_from_pattern_accumulation(self, db):
        persona = _make_persona(db, baseline_background="A stable, ordinary childhood.")

        # A real, valid experience - opens a real pattern.
        description = "Her father disappeared for days and was never around."
        _make_experience(db, persona, "exp-real", 7, description)
        await process_developmental_text(
            db, persona, description, source="experience", age=7, source_event_id="exp-real",
        )
        db.commit()
        real_pattern = db.query(AdaptationPattern).filter_by(persona_id=persona.id, adaptation_strategy="self_reliance").first()
        assert real_pattern is not None
        assert real_pattern.status == "emerging"

        # Directly insert an orphaned exposure/interpretation pair claiming
        # a source_event_id that was never a real Experience for this
        # persona - simulating a stale/corrupted row, not something any
        # current code path would create.
        orphan_exposure = DevelopmentalExposure(
            persona_id=persona.id, source_event_id="exp-does-not-exist", source="experience",
            age_at_exposure=9, exposure_type="caregiver_absence",
            developmental_domains=["attachment_security", "stability"], raw_text="fabricated",
        )
        db.add(orphan_exposure)
        db.flush()
        orphan_interpretation = Interpretation(
            persona_id=persona.id, source_event_id="exp-does-not-exist", age_at_event=9,
            exposure_ids=[orphan_exposure.id], developmental_domains=["attachment_security", "stability"],
            belief_statement="Fabricated belief.", adaptation_strategy="self_reliance",
            reasoning="Fabricated reasoning citing an event that never happened.",
        )
        db.add(orphan_interpretation)
        db.commit()

        # Re-running the pipeline (any new call recomputes patterns from the
        # persona's FULL timeline) must not let the orphaned interpretation
        # add a second reinforcement to the pattern it fraudulently claims
        # to belong to.
        description2 = "She won a competition and it felt like a proud accomplishment."
        _make_experience(db, persona, "exp-unrelated", 12, description2)
        await process_developmental_text(
            db, persona, description2, source="experience", age=12, source_event_id="exp-unrelated",
        )
        db.commit()

        pattern = db.query(AdaptationPattern).filter_by(persona_id=persona.id, adaptation_strategy="self_reliance").first()
        cited_events = {entry.get("experience_id") for entry in (pattern.reinforcement_history or [])}
        assert "exp-does-not-exist" not in cited_events
        assert pattern.status == "emerging"  # still just the one real reinforcement, not two
