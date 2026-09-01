"""
Direct regression test for the production Brandon factual-grounding bug.

Fixture text is verbatim the real production persona's baseline_background
and all 10 Experience entries (persona id fc37e6e6-eff8-4449-8827-191f4272169f
in production) - same text as scripts/audit_repeatability.py's
"brandon_grounding" fixture, kept as an independent literal copy here rather
than importing that script, so this regression stays pinned even if the
audit script's fixture set changes shape later.

The bug: the dashboard showed "Hypervigilance Response - first seen around
age 40" and a "Reactive Attachment Disorder 15%" hypothesis, both grounded
in a phantom caregiver-substance-use event at age 40. Root cause (see
app/services/developmental_exposure_engine.py's requires_caregiver_context):
"rehab" was a bare-substring keyword for caregiver_substance_use with no
check that a caregiver was the subject of the sentence, so Brandon's own
"Brandon enters rehab..." (age 40, about himself, not a caregiver) matched
it - compounded by a provenance bug that stamped the resulting exposure with
persona.baseline_age (also 40) instead of leaving it genuinely undated
background or the real event's age. The same false-positive pattern also
existed for caregiver_incarceration matching Brandon's own incarceration
at age 19.

This test drives the exact same real route functions production calls
(create_persona, add_experience) against the exact real text, and asserts
the specific wrong outputs are gone - not merely that *something* changed.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.experiences import add_experience
from app.api.routes.personas import create_persona
from app.core.database import Base
from app.models import AdaptationPattern, ClinicalPatternHypothesis, DevelopmentalExposure
from app.schemas import ExperienceCreate, PersonaCreate

TEST_DB_URL = "sqlite:///./test_brandon_grounding_regression.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BRANDON_PERSONA = {
    "name": "brandon", "baseline_age": 40,
    "baseline_gender": "male",
    "baseline_background": (
        "Brandon was born in St. Louis in 1980 and placed for adoption as an infant. He was adopted into a large "
        "foster/adoptive family in San Diego and was the youngest of eight adopted children. He spent parts of childhood "
        "in San Diego, England, and Benson, Arizona, moving several times before returning to San Diego at 15. His childhood "
        "included travel, books, science, music, art, church, large groups of friends, and later significant involvement with "
        "drugs, nightlife, photography, treatment work, and AI development. His biological mother was a young woman in St. "
        "Louis who placed him for adoption; he does not remember her. He was raised by Audrey, an older British woman who had "
        "operated a foster home and later adopted eight children. He describes her as loving, generous, cultured, and largely "
        "without discipline. Audrey died when Brandon was 15. He was then adopted by Karen, who tried to provide structure, "
        "counseling, and treatment during his teenage years and is the woman he calls his mother today. As a child, Brandon "
        "describes himself as angry, rebellious, and sometimes emotionally shut off. He also describes himself as outgoing, "
        "extroverted, socially confident, fearless, creative, and able to make friends easily. He was drawn to literature, "
        "science, music, art, leadership, and protecting people he felt could not protect themselves."
    ),
    "baseline_attachment_style": "secure",
}

BRANDON_EXPERIENCES = [
    (4, 1, "Brandon is placed for adoption in St. Louis and adopted into Audrey's foster family in San Diego."),
    (6, 1, "Audrey takes Brandon to live in England, where he attends primary school, travels extensively with her, and spends time with her British relatives."),
    (12, 1, "Brandon moves to Benson, Arizona, where he forms close friendships and begins getting into trouble."),
    (14, 1, "He becomes deeply involved in a church in Benson. A pastor trains him as a youth minister, and the youth group becomes a major part of his life."),
    (15, 1, "Audrey dies. Brandon gives up his involvement with the church and begins moving heavily into crime and drugs"),
    (16, 1, "Brandon enters a serious relationship with Heather. She later becomes pregnant with his son while Brandon is becoming heavily involved with drugs"),
    (19, 1, "While incarcerated, Brandon meets a man who teaches him event promotion. After release, Karen allows him to handle entertainment at her bar, leading to years of promoting bands, art shows, fashion shows, fundraisers, and nightclub events."),
    (23, 1, "A model named Soma buys Brandon his first camera. He moves to Los Angeles and begins a freelance photography career that lasts roughly 20 years, including magazine publication and travel across the country"),
    (37, 1, "Brandon meets Hillary, whom he describes as the most significant romantic relationship of his life. Their relationship lasts roughly two years before she relapses and dies from alcohol use."),
    (40, 1, "After another prolonged period of drug use, Brandon enters rehab, earns his RADT, becomes a case manager in substance-use treatment, and begins developing AI applications."),
]


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


async def _build_brandon(db) -> str:
    persona = await create_persona(PersonaCreate(**BRANDON_PERSONA), "user-1", db)
    for age, sequence_index, description in BRANDON_EXPERIENCES:
        await add_experience(
            persona.id,
            ExperienceCreate(user_description=description, age_at_event=age, sequence_index=sequence_index),
            "user-1", db,
        )
    return persona.id


class TestBrandonAgeFortyGroundingRegression:
    @pytest.mark.asyncio
    async def test_no_caregiver_substance_use_exposure_at_age_forty(self, db):
        # The exact production defect: "rehab" in Brandon's own age-40
        # experience (about himself) must never be attributed to a
        # caregiver.
        persona_id = await _build_brandon(db)
        exposures = db.query(DevelopmentalExposure).filter(
            DevelopmentalExposure.persona_id == persona_id
        ).all()
        assert not any(
            e.exposure_type == "caregiver_substance_use" and e.age_at_exposure == 40
            for e in exposures
        )
        # Stronger: no caregiver_substance_use exposure exists at all - none
        # of Brandon's real text describes a caregiver's substance use in
        # taxonomy-matching language, so none should be fabricated.
        assert not any(e.exposure_type == "caregiver_substance_use" for e in exposures)

    @pytest.mark.asyncio
    async def test_no_caregiver_incarceration_exposure_from_brandons_own_incarceration(self, db):
        # Second real false positive found on the same fixture: Brandon's
        # own incarceration at 19 ("While incarcerated, Brandon meets...")
        # must never be attributed to a caregiver either.
        persona_id = await _build_brandon(db)
        exposures = db.query(DevelopmentalExposure).filter(
            DevelopmentalExposure.persona_id == persona_id
        ).all()
        assert not any(e.exposure_type == "caregiver_incarceration" for e in exposures)

    @pytest.mark.asyncio
    async def test_no_reactive_attachment_disorder_hypothesis_grounded_in_the_phantom_event(self, db):
        persona_id = await _build_brandon(db)
        hypotheses = db.query(ClinicalPatternHypothesis).filter(
            ClinicalPatternHypothesis.persona_id == persona_id
        ).all()
        assert not any(h.pattern_key == "reactive_attachment_disorder" for h in hypotheses)

    @pytest.mark.asyncio
    async def test_no_hypervigilance_pattern_first_emerging_at_age_forty(self, db):
        persona_id = await _build_brandon(db)
        patterns = db.query(AdaptationPattern).filter(
            AdaptationPattern.persona_id == persona_id
        ).all()
        assert not any(
            p.adaptation_strategy == "hypervigilance" and p.first_emerged_age == 40
            for p in patterns
        )

    @pytest.mark.asyncio
    async def test_every_persisted_exposure_and_pattern_traces_to_real_grounding(self, db):
        # General provenance sweep, not just the two known false positives:
        # every exposure on this real persona must be either genuinely
        # undated background (age None) or tied to one of the 10 real,
        # persisted experiences at that experience's own real age - never a
        # fabricated age with no backing event.
        persona_id = await _build_brandon(db)
        real_ages = {age for age, _, _ in BRANDON_EXPERIENCES}
        exposures = db.query(DevelopmentalExposure).filter(
            DevelopmentalExposure.persona_id == persona_id
        ).all()
        for e in exposures:
            if e.source == "backstory":
                assert e.age_at_exposure is None, f"{e.exposure_type} backstory row carries a fabricated age"
            else:
                assert e.age_at_exposure in real_ages, (
                    f"{e.exposure_type} at age {e.age_at_exposure} does not match any real Brandon experience age"
                )

    @pytest.mark.asyncio
    async def test_repeated_runs_produce_identical_canonical_state(self, db):
        # Lightweight in-process determinism check for this exact fixture,
        # complementing (not replacing) scripts/audit_repeatability.py's
        # full 5-trial, fresh-database harness.
        persona_id = await _build_brandon(db)
        first = sorted(
            (e.exposure_type, e.age_at_exposure, e.source)
            for e in db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona_id).all()
        )

        Base.metadata.create_all(bind=engine)
        second_session = TestingSessionLocal()
        try:
            second_persona_id = await _build_brandon(second_session)
            second = sorted(
                (e.exposure_type, e.age_at_exposure, e.source)
                for e in second_session.query(DevelopmentalExposure).filter(
                    DevelopmentalExposure.persona_id == second_persona_id
                ).all()
            )
        finally:
            second_session.close()

        assert first == second
