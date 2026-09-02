"""
DB-backed WholeLifeFormulationRequest assembly - PERSISTENCE PHASE.

The shadow-testing fixtures (scripts/whole_life_formulation_prototype/fixtures.py)
had background/caregiver_history/temperament as three separately-authored
strings. Real personas don't - the production create flow concatenates all
three UI fields into one Persona.baseline_background column (see
app/models/persona.py; there is no separate caregiver_history/temperament
column). Rather than changing the request contract (out of scope - "do not
redesign the formulation engine"), the whole combined text goes into
`background` and the other two fields are left empty; no information is
lost, it's just not pre-split into three sections the way the fixtures were.
"""
from typing import List

from sqlalchemy.orm import Session

from app.models import Experience, Intervention, Persona
from app.services.whole_life_formulation.request_assembler import (
    ExperienceSource,
    InterventionSource,
    LifeSourceData,
    WholeLifeFormulationRequest,
    assemble_request,
)


def build_life_source_data(db: Session, persona: Persona) -> LifeSourceData:
    experiences: List[Experience] = (
        db.query(Experience)
        .filter(Experience.persona_id == persona.id)
        .order_by(Experience.age_at_event, Experience.sequence_index, Experience.created_at)
        .all()
    )
    interventions: List[Intervention] = (
        db.query(Intervention)
        .filter(Intervention.persona_id == persona.id)
        .order_by(Intervention.age_at_intervention, Intervention.created_at)
        .all()
    )
    return LifeSourceData(
        persona_name=persona.name,
        current_age=persona.current_age,
        background=persona.baseline_background or "",
        caregiver_history="",
        temperament_self_description="",
        experiences=[
            ExperienceSource(
                id=e.id, age_at_event=e.age_at_event,
                sequence_index=e.sequence_index or 0, user_description=e.user_description,
            )
            for e in experiences
        ],
        interventions=[
            InterventionSource(
                id=i.id, age_at_intervention=i.age_at_intervention,
                description=i.user_notes or i.therapy_type or "",
            )
            for i in interventions
        ],
    )


def assemble_request_for_persona(db: Session, persona: Persona) -> WholeLifeFormulationRequest:
    return assemble_request(build_life_source_data(db, persona))
