import pytest
from pydantic import ValidationError

from app.schemas import PersonaCreate, PersonaUpdate


def test_create_accepts_2000_character_background():
    payload = PersonaCreate(
        name="Boundary",
        baseline_age=18,
        baseline_gender="unspecified",
        baseline_background="x" * 2000,
    )
    assert len(payload.baseline_background) == 2000


def test_create_rejects_2001_character_background():
    with pytest.raises(ValidationError):
        PersonaCreate(
            name="Boundary",
            baseline_age=18,
            baseline_gender="unspecified",
            baseline_background="x" * 2001,
        )


def test_update_uses_the_same_2000_character_boundary():
    assert len(PersonaUpdate(baseline_background="x" * 2000).baseline_background) == 2000
    with pytest.raises(ValidationError):
        PersonaUpdate(baseline_background="x" * 2001)
