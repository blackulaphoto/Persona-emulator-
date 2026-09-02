"""
WholeLifeFormulationRequest assembler - PHASE 0 PROTOTYPE.

Builds the exact input contract locked in decision #1: background, caregiver
history, temperament/self-description, all experiences in chronological
order, interventions, current age, and previously persisted FACTUAL source
data only - never prior derived psychology (no exposures, patterns,
hypotheses, or personality numbers from any earlier run are fed back in).

Works from a plain LifeSourceData object so it can run against fixtures
without touching the database - this prototype never reads or writes
Postgres.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExperienceSource:
    id: str
    age_at_event: int
    sequence_index: int
    user_description: str


@dataclass
class InterventionSource:
    id: str
    age_at_intervention: int
    description: str


@dataclass
class LifeSourceData:
    """Previously persisted FACTUAL source data only - decision #1."""
    persona_name: str
    current_age: int
    background: str
    caregiver_history: str
    temperament_self_description: str
    experiences: List[ExperienceSource]
    interventions: List[InterventionSource] = field(default_factory=list)

    def all_valid_experience_ids(self) -> set:
        return {e.id for e in self.experiences}

    def all_valid_intervention_ids(self) -> set:
        return {i.id for i in self.interventions}

    def experience_age_by_id(self) -> dict:
        return {e.id: e.age_at_event for e in self.experiences}


@dataclass
class WholeLifeFormulationRequest:
    life: LifeSourceData
    prompt_input: str  # the fully-assembled text block sent as the model's `input`


def assemble_request(life: LifeSourceData) -> WholeLifeFormulationRequest:
    ordered = sorted(life.experiences, key=lambda e: (e.age_at_event, e.sequence_index))

    experience_block = "\n".join(
        f'- id="{e.id}" age={e.age_at_event}: {e.user_description}'
        for e in ordered
    )
    intervention_block = (
        "\n".join(
            f'- id="{i.id}" age={i.age_at_intervention}: {i.description}'
            for i in life.interventions
        )
        or "(none recorded)"
    )

    prompt_input = f"""SUBJECT: {life.persona_name}
CURRENT AGE: {life.current_age}

BACKGROUND (general developmental context):
{life.background}

CAREGIVER HISTORY (who raised them, and what those caregivers were like):
{life.caregiver_history}

TEMPERAMENT / SELF-DESCRIPTION (how the subject describes their own disposition):
{life.temperament_self_description}

EXPERIENCES (chronological, each with a stable id and the age it occurred at):
{experience_block}

INTERVENTIONS (chronological):
{intervention_block}
"""
    return WholeLifeFormulationRequest(life=life, prompt_input=prompt_input)
