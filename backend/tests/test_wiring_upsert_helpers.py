"""
Tests for the upsert helpers that make wiring steps 2-5 into live routes
possible without duplicating rows on every new experience:
evidence_accumulator.upsert_clinical_pattern_hypothesis_rows and
pattern_engine.upsert_adaptation_pattern_rows.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, ClinicalPatternHypothesis, AdaptationPattern
from app.services.evidence_accumulator import upsert_clinical_pattern_hypothesis_rows, accumulate_evidence
from app.services.pattern_engine import upsert_adaptation_pattern_rows, accumulate_patterns

TEST_DB_URL = "sqlite:///./test_wiring_upsert.db"
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
def _mock_pattern_naming():
    # upsert_adaptation_pattern_rows names new patterns via pattern_engine's
    # AI call; mock it fast-fail so tests exercise the (also-tested)
    # heuristic fallback instead of hitting the live API and sitting
    # through real retry backoff.
    with patch("app.services.pattern_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.side_effect = Exception("simulated API failure - tests use the heuristic fallback")
        yield mock_analyze


def _make_persona(db):
    persona = Persona(
        name="Michael", baseline_age=6, current_age=32, baseline_gender="male",
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.4, "extraversion": 0.4, "agreeableness": 0.5, "neuroticism": 0.7},
        current_attachment_style="insecure-anxious", current_trauma_markers=[], user_id="user-1",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def _exp(id_, exposure_type, domains, age):
    # source/source_event_id are required for evidence_accumulator's
    # persistence distinctness check (see its docstring) - id_ doubles as a
    # unique source_event_id here so each call is treated as a separate entry.
    return {"id": id_, "exposure_type": exposure_type, "developmental_domains": domains, "age_at_exposure": age, "source": "experience", "source_event_id": id_}


class TestClinicalPatternHypothesisUpsert:
    def test_first_call_inserts(self, db):
        persona = _make_persona(db)
        exposures = [_exp("e1", "physical_discipline_or_violence", ["emotional_safety"], 7)]
        accumulated = accumulate_evidence(exposures)
        upsert_clinical_pattern_hypothesis_rows(db, persona.id, accumulated)
        db.commit()

        rows = db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
        assert len(rows) == len(accumulated)
        assert rows[0].evidence_strength is None  # single exposure, no persistence yet

    def test_second_call_updates_not_duplicates(self, db):
        persona = _make_persona(db)
        exposures_1 = [_exp("e1", "physical_discipline_or_violence", ["emotional_safety"], 7)]
        upsert_clinical_pattern_hypothesis_rows(db, persona.id, accumulate_evidence(exposures_1))
        db.commit()

        # Second experience of the same exposure_type - now there's real persistence evidence.
        exposures_2 = exposures_1 + [_exp("e2", "physical_discipline_or_violence", ["emotional_safety"], 11)]
        upsert_clinical_pattern_hypothesis_rows(db, persona.id, accumulate_evidence(exposures_2))
        db.commit()

        rows = db.query(ClinicalPatternHypothesis).filter(
            ClinicalPatternHypothesis.persona_id == persona.id, ClinicalPatternHypothesis.pattern_key == "ptsd"
        ).all()
        assert len(rows) == 1  # not duplicated
        assert rows[0].evidence_strength is not None  # revised upward with real evidence

    def test_pattern_no_longer_candidate_is_left_alone_not_deleted(self, db):
        persona = _make_persona(db)
        exposures = [_exp("e1", "physical_discipline_or_violence", ["emotional_safety"], 7)]
        upsert_clinical_pattern_hypothesis_rows(db, persona.id, accumulate_evidence(exposures))
        db.commit()

        # A totally unrelated second call (e.g. different exposure type) must not delete the first hypothesis.
        other_exposures = [_exp("e2", "separation_or_divorce", ["stability"], 9)]
        upsert_clinical_pattern_hypothesis_rows(db, persona.id, accumulate_evidence(other_exposures))
        db.commit()

        rows = db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
        pattern_keys = {r.pattern_key for r in rows}
        assert "ptsd" in pattern_keys  # from the first call, still present
        assert "adjustment_disorder" in pattern_keys  # from the second call


class TestAdaptationPatternUpsert:
    def _interp(self, id_, age, strategy, belief="People leave."):
        return {"id": id_, "source_event_id": f"exp-{id_}", "age_at_event": age, "adaptation_strategy": strategy, "belief_statement": belief, "developmental_domains": ["attachment_security"]}

    @pytest.mark.asyncio
    async def test_first_call_inserts_with_real_name(self, db):
        persona = _make_persona(db)
        accumulated = accumulate_patterns([self._interp("i1", 6, "self_reliance")])
        await upsert_adaptation_pattern_rows(db, persona.id, accumulated, persona_name="Michael")
        db.commit()

        rows = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        assert len(rows) == 1
        assert rows[0].adaptation_strategy == "self_reliance"
        assert rows[0].pattern_name  # named, not empty

    @pytest.mark.asyncio
    async def test_second_call_updates_not_duplicates(self, db):
        persona = _make_persona(db)
        await upsert_adaptation_pattern_rows(db, persona.id, accumulate_patterns([self._interp("i1", 6, "self_reliance")]), persona_name="Michael")
        db.commit()

        await upsert_adaptation_pattern_rows(
            db, persona.id,
            accumulate_patterns([self._interp("i1", 6, "self_reliance"), self._interp("i2", 10, "self_reliance")]),
            persona_name="Michael",
        )
        db.commit()

        rows = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id, AdaptationPattern.adaptation_strategy == "self_reliance").all()
        assert len(rows) == 1
        assert len(rows[0].reinforcement_history) == 2

    @pytest.mark.asyncio
    async def test_established_pattern_name_stays_stable_across_updates(self, db):
        persona = _make_persona(db)
        # Build up to "established" (4 reinforcements needed at 0.2 increment to cross 0.5).
        interps = [self._interp(f"i{n}", 5 + n * 3, "hypervigilance") for n in range(4)]
        await upsert_adaptation_pattern_rows(db, persona.id, accumulate_patterns(interps), persona_name="Michael")
        db.commit()

        row = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).first()
        assert row.status == "established"
        original_name = row.pattern_name

        # One more reinforcement - name must not silently change now that it's established.
        interps.append(self._interp("i5", 20, "hypervigilance"))
        await upsert_adaptation_pattern_rows(db, persona.id, accumulate_patterns(interps), persona_name="Michael")
        db.commit()

        row = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).first()
        assert row.pattern_name == original_name
