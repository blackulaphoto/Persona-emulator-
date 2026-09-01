import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Persona, PersonaNarrative, User
from app.services import narrative_service


NARRATIVE_TEXT = """## EXECUTIVE SUMMARY
Summary.
## DEVELOPMENTAL FORMULATION
Development.
## CURRENT FORMULATION
Current.
## TREATMENT RESPONSE
Response.
## PROGNOSIS & RECOMMENDATIONS
Prognosis.
"""


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        user = User(id="user-1", email="narrative@example.com", hashed_password="unused")
        persona = Persona(
            id="persona-1",
            user_id=user.id,
            name="Elena",
            baseline_age=8,
            current_age=18,
            baseline_gender="female",
            baseline_background="A meaningful developmental history.",
            current_personality={
                "openness": 0.6,
                "conscientiousness": 0.7,
                "extraversion": 0.5,
                "agreeableness": 0.6,
                "neuroticism": 0.6,
            },
            current_attachment_style="anxious",
            current_trauma_markers=[],
        )
        session.add_all([user, persona])
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def _response():
    return SimpleNamespace(
        output_text=NARRATIVE_TEXT,
        model="gpt-5.6-luna",
        usage=SimpleNamespace(
            input_tokens=1234,
            output_tokens=567,
            output_tokens_details=SimpleNamespace(reasoning_tokens=89),
        ),
    )


def test_luna_responses_request_parses_and_persists(monkeypatch, db_session, caplog):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _response()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setattr(narrative_service.openai, "OpenAI", FakeOpenAI)

    with caplog.at_level("INFO", logger=narrative_service.__name__):
        result = asyncio.run(
            narrative_service.generate_persona_narrative(
                db_session, persona_id="persona-1", user_id="user-1"
            )
        )

    assert captured["model"] == "gpt-5.6-luna"
    assert captured["max_output_tokens"] == 8000
    assert captured["reasoning"] == {"effort": "low"}
    assert "temperature" not in captured
    assert captured["instructions"] == narrative_service.NARRATIVE_SYSTEM_INSTRUCTIONS
    assert "Elena" in captured["input"]

    assert result.executive_summary == "Summary."
    assert result.developmental_timeline == "Development."
    assert result.current_presentation == "Current."
    assert result.treatment_response == "Response."
    assert result.prognosis == "Prognosis."
    assert result.full_narrative == NARRATIVE_TEXT
    assert db_session.query(PersonaNarrative).filter_by(id=result.id).one().full_narrative == NARRATIVE_TEXT
    assert "model=gpt-5.6-luna" in caplog.text
    assert "input_tokens=1234" in caplog.text
    assert "output_tokens=567" in caplog.text
    assert "reasoning_tokens=89" in caplog.text


def test_luna_failure_uses_existing_visible_error_path(monkeypatch, db_session):
    class FailingResponses:
        def create(self, **kwargs):
            raise RuntimeError("unsupported model configuration")

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FailingResponses()

    monkeypatch.setattr(narrative_service.openai, "OpenAI", FakeOpenAI)

    with pytest.raises(Exception, match="Failed to generate narrative with gpt-5.6-luna"):
        asyncio.run(
            narrative_service.generate_persona_narrative(
                db_session, persona_id="persona-1", user_id="user-1"
            )
        )

    assert db_session.query(PersonaNarrative).count() == 0
