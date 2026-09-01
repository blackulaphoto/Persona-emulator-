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
            {"key": row.exposure_type, "domains": row.developmental_domains, "age": row.age_at_exposure}
            for row in exposures
        ],
        "protective_factors": [
            {"key": row.factor_type, "domains": row.domains_buffered, "age": row.active_from_age}
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
