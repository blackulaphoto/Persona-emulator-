"""Run isolated same-input repeatability trials against the live analysis pipeline.

This is an audit utility, not an application entrypoint. Each trial gets a fresh
SQLite database and user id, then uses the same persona/experience route
functions the product uses. Results contain canonical state only; prose is not
compared.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.experiences import add_experience
from app.api.routes.personas import create_persona
from app.core.database import Base
from app.models import (
    AdaptationPattern, ClinicalPatternHypothesis, DevelopmentalExposure,
    Persona, ProtectiveFactor,
)
from app.schemas import ExperienceCreate, PersonaCreate


FIXTURES = {
    "complex": {
    "persona": {
        "name": "Repeatability Case",
        "baseline_age": 3,
        "baseline_gender": "female",
        "baseline_background": (
            "A curious, sociable child in a working-class home. Both parents are affectionate, "
            "but her father's drinking makes evenings unpredictable and her mother increasingly "
            "relies on her to stay calm and help with her younger brother."
        ),
        "baseline_attachment_style": "anxious",
    },
    "experiences": [
        (4, 1, "She hears intense arguments after her father drinks and hides with her younger brother until the house is quiet."),
        (5, 1, "Her mother calls her the responsible one and asks her to watch her brother when the adults are overwhelmed."),
        (7, 1, "Her father loses his job; money becomes scarce and his drinking and absences increase."),
        (8, 1, "A teacher notices her anxiety, gives her predictable routines, and consistently praises her writing."),
        (10, 1, "Classmates mock her worn clothes. She stops inviting friends home and works hard to appear self-sufficient."),
        (12, 1, "She earns an academic award, but dismisses it as luck and worries that any mistake will expose her."),
        (14, 1, "Her closest friend shares private information during an argument; she withdraws rather than discuss feeling hurt."),
        (16, 1, "Her father enters recovery and apologizes. She appreciates the effort but remains watchful for relapse."),
        (17, 1, "A counselor helps her name parentification and practice asking trusted people for help."),
        (18, 1, "She receives a scholarship and chooses a nearby college, balancing ambition with fear of abandoning her family."),
    ],
    },
    "mixed": {
        "persona": {
            "name": "Mixed Support Case", "baseline_age": 5,
            "baseline_gender": "female",
            "baseline_background": "Her father was alcoholic and often absent, but her grandmother raised her in an adaptable close-knit neighborhood.",
            "baseline_attachment_style": None,
        },
        "experiences": [
            (7, 1, "Her parents fighting made home unpredictable."),
            (8, 1, "A mentor and close friends consistently offered support."),
            (11, 1, "She was bullied and excluded at a new school."),
            (13, 1, "She started counseling and repaired conflicts with a reliable partner."),
        ],
    },
    "low_adversity": {
        "persona": {
            "name": "Stable Support Case", "baseline_age": 5,
            "baseline_gender": "male",
            "baseline_background": "He was easygoing, financially stable, and grew up in a close-knit neighborhood with close friends.",
            "baseline_attachment_style": None,
        },
        "experiences": [
            (8, 1, "A coach believed in him and became a mentor."),
            (12, 1, "He had close friends and a secure relationship with family support."),
            (16, 1, "He started therapy after a stressful transition and repaired conflicts openly."),
        ],
    },
    "brandon_grounding": {
        "persona": {
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
        },
        "experiences": [
            (4, 1, "Brandon is placed for adoption in St. Louis and adopted into Audrey’s foster family in San Diego."),
            (6, 1, "Audrey takes Brandon to live in England, where he attends primary school, travels extensively with her, and spends time with her British relatives."),
            (12, 1, "Brandon moves to Benson, Arizona, where he forms close friendships and begins getting into trouble."),
            (14, 1, "He becomes deeply involved in a church in Benson. A pastor trains him as a youth minister, and the youth group becomes a major part of his life."),
            (15, 1, "Audrey dies. Brandon gives up his involvement with the church and begins moving heavily into crime and drugs"),
            (16, 1, "Brandon enters a serious relationship with Heather. She later becomes pregnant with his son while Brandon is becoming heavily involved with drugs"),
            (19, 1, "While incarcerated, Brandon meets a man who teaches him event promotion. After release, Karen allows him to handle entertainment at her bar, leading to years of promoting bands, art shows, fashion shows, fundraisers, and nightclub events."),
            (23, 1, "A model named Soma buys Brandon his first camera. He moves to Los Angeles and begins a freelance photography career that lasts roughly 20 years, including magazine publication and travel across the country"),
            (37, 1, "Brandon meets Hillary, whom he describes as the most significant romantic relationship of his life. Their relationship lasts roughly two years before she relapses and dies from alcohol use."),
            (40, 1, "After another prolonged period of drug use, Brandon enters rehab, earns his RADT, becomes a case manager in substance-use treatment, and begins developing AI applications."),
        ],
    },
}


def _snapshot(db, persona_id: str) -> dict:
    persona = db.query(Persona).filter_by(id=persona_id).one()
    patterns = db.query(AdaptationPattern).filter_by(persona_id=persona_id).order_by(
        AdaptationPattern.adaptation_strategy
    ).all()
    hypotheses = db.query(ClinicalPatternHypothesis).filter_by(persona_id=persona_id).order_by(
        ClinicalPatternHypothesis.pattern_key
    ).all()
    exposures = db.query(DevelopmentalExposure).filter_by(persona_id=persona_id).order_by(
        DevelopmentalExposure.age_at_exposure, DevelopmentalExposure.exposure_type
    ).all()
    protections = db.query(ProtectiveFactor).filter_by(persona_id=persona_id).order_by(
        ProtectiveFactor.active_from_age, ProtectiveFactor.factor_type
    ).all()
    return {
        "baseline_attachment_style": persona.baseline_attachment_style,
        "baseline_attachment_dimensions": persona.baseline_attachment_dimensions,
        "baseline_personality": persona.baseline_personality,
        "current_attachment_style": persona.current_attachment_style,
        "current_attachment_dimensions": persona.current_attachment_dimensions,
        "current_personality": persona.current_personality,
        "current_state": persona.current_state,
        "exposures": [
            {
                "key": row.exposure_type, "domains": row.developmental_domains,
                "age": row.age_at_exposure, "source": row.source,
                "has_source_event": row.source_event_id is not None, "raw_text": row.raw_text,
            }
            for row in exposures
        ],
        "protective_factors": [
            {
                "key": row.factor_type, "domains": row.domains_buffered,
                "age": row.active_from_age,
                "source": "backstory" if row.source_event_id is None else "experience",
                "has_source_event": row.source_event_id is not None,
            }
            for row in protections
        ],
        "patterns": [
            {
                "adaptation_strategy": row.adaptation_strategy,
                "pattern_name": row.pattern_name,
                "status": row.status,
                "evidence_strength": row.evidence_strength,
                "first_emerged_age": row.first_emerged_age,
            }
            for row in patterns
        ],
        "hypotheses": [
            {
                "pattern_key": row.pattern_key,
                "tier": row.tier,
                "evidence_strength": row.evidence_strength,
                # Database UUIDs intentionally differ in fresh isolated runs;
                # compare semantic evidence identity rather than row identity.
                "supporting_evidence": [
                    {k: v for k, v in item.items() if k != "source_id"}
                    for item in (row.supporting_evidence or [])
                ],
                "contradicting_evidence": [
                    {k: v for k, v in item.items() if k != "source_id"}
                    for item in (row.contradicting_evidence or [])
                ],
            }
            for row in hypotheses
        ],
    }


async def _run_trial(fixture_name: str, fixture: dict, index: int, root: Path) -> dict:
    db_path = root / f"{fixture_name}-trial-{index}.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    user_id = f"repeatability-audit-{index}"
    try:
        persona_response = await create_persona(PersonaCreate(**fixture["persona"]), user_id, session)
        for age, sequence_index, description in fixture["experiences"]:
            await add_experience(
                persona_response.id,
                ExperienceCreate(
                    user_description=description,
                    age_at_event=age,
                    sequence_index=sequence_index,
                ),
                user_id,
                session,
            )
        return {"trial": index, **_snapshot(session, persona_response.id)}
    finally:
        session.close()
        engine.dispose()


async def main(trials: int, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="rubicks-repeatability-") as temp_dir:
        results = {}
        for fixture_name, fixture in FIXTURES.items():
            runs = await asyncio.gather(*[
                _run_trial(fixture_name, fixture, index, Path(temp_dir))
                for index in range(1, trials + 1)
            ])
            canonical = [{k: v for k, v in run.items() if k != "trial"} for run in runs]
            results[fixture_name] = {
                "fixture": fixture,
                "runs": runs,
                "identical": all(run == canonical[0] for run in canonical[1:]),
            }
    output.write_text(json.dumps({"trials": trials, "fixtures": results}, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.trials, args.output))
