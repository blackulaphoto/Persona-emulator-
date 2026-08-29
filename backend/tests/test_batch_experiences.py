from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.routes.experiences import add_experiences_batch
from app.schemas import BatchExperienceCreate, ExperienceResponse


def _response(age, sequence):
    return ExperienceResponse(
        id=f"event-{sequence}", persona_id="persona", sequence_number=sequence, sequence_index=sequence,
        age_at_event=age, user_description=f"event at {age}", created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_batch_processes_chronologically_and_preserves_same_age_order():
    batch = BatchExperienceCreate(experiences=[
        {"age_at_event": 14, "description": "third"},
        {"age_at_event": 10, "description": "first"},
        {"age_at_event": 10, "description": "second"},
    ])
    calls = []

    async def fake_add(persona_id, data, user_id, db):
        calls.append((data.age_at_event, data.user_description))
        return _response(data.age_at_event, len(calls))

    with patch("app.api.routes.experiences.add_experience", new=AsyncMock(side_effect=fake_add)):
        result = await add_experiences_batch("persona", batch, "owner", object())

    assert calls == [(10, "first"), (10, "second"), (14, "third")]
    assert [item.input_index for item in result.results] == [1, 2, 0]
    assert result.processed_count == 3
    assert result.failed_count == 0


@pytest.mark.asyncio
async def test_batch_uses_explicit_same_age_sequence_before_input_order():
    batch = BatchExperienceCreate(experiences=[
        {"age_at_event": 16, "sequence_index": 2, "description": "betrayal"},
        {"age_at_event": 16, "sequence_index": 1, "description": "reliable relationship"},
        {"age_at_event": 17, "sequence_index": 1, "description": "later event"},
    ])
    calls = []

    async def fake_add(persona_id, data, user_id, db):
        calls.append((data.age_at_event, data.sequence_index, data.user_description))
        return _response(data.age_at_event, len(calls))

    with patch("app.api.routes.experiences.add_experience", new=AsyncMock(side_effect=fake_add)):
        await add_experiences_batch("persona", batch, "owner", object())

    assert calls == [
        (16, 1, "reliable relationship"),
        (16, 2, "betrayal"),
        (17, 1, "later event"),
    ]


@pytest.mark.asyncio
async def test_batch_reports_failure_and_stops_without_hiding_prior_results():
    batch = BatchExperienceCreate(experiences=[
        {"age_at_event": 8, "description": "works"},
        {"age_at_event": 9, "description": "fails"},
        {"age_at_event": 10, "description": "not attempted"},
    ])
    mocked = AsyncMock(side_effect=[_response(8, 1), HTTPException(status_code=500, detail="pipeline unavailable")])

    with patch("app.api.routes.experiences.add_experience", new=mocked):
        result = await add_experiences_batch("persona", batch, "owner", object())

    assert [item.status for item in result.results] == ["processed", "failed"]
    assert result.results[1].error == "pipeline unavailable"
    assert result.processed_count == 1
    assert result.failed_count == 1
    assert mocked.await_count == 2
