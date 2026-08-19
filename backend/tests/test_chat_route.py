"""
Integration tests for app/api/routes/chat.py's chat_with_persona (docs/
MIGRATION_MAP.md step 10). Calls the route function directly with explicit
db/user_id args (bypassing FastAPI's Depends() resolution, which is just a
parameter default at the Python level) rather than spinning up the full
app/TestClient - dedicated SQLite file, no app.main, matching
tests/test_remix_service.py's pattern.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona
from app.api.routes.chat import chat_with_persona, ChatRequest
from app.services.openai_service import OpenAIService


def _patch_openai_client(mock_client):
    """
    OpenAIService.client is a read-only property (no setter), so a plain
    patch("...openai_service.client") fails on teardown (can't delattr a
    property). Patch the property on the class via PropertyMock instead.
    """
    return patch.object(OpenAIService, "client", new_callable=PropertyMock, return_value=mock_client)

TEST_DB_URL = "sqlite:///./test_chat_route.db"
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


def _make_persona(db, user_id="user-1"):
    persona = Persona(
        name="Michael", baseline_age=10, current_age=30, baseline_gender="male",
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.4, "extraversion": 0.4, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[],
        user_id=user_id,
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


class TestOwnershipEnforcement:
    @pytest.mark.asyncio
    async def test_wrong_user_gets_404_not_someone_elses_persona(self, db):
        persona = _make_persona(db, user_id="owner")
        with pytest.raises(Exception) as exc_info:
            await chat_with_persona(
                persona_id=persona.id,
                chat_request=ChatRequest(message="hello"),
                user_id="someone-else",
                db=db,
            )
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_persona_gets_404(self, db):
        with pytest.raises(Exception) as exc_info:
            await chat_with_persona(
                persona_id="does-not-exist",
                chat_request=ChatRequest(message="hello"),
                user_id="user-1",
                db=db,
            )
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


class TestSafetyRouterShortCircuitsBeforeLLM:
    @pytest.mark.asyncio
    async def test_crisis_message_never_reaches_openai(self, db):
        persona = _make_persona(db, user_id="user-1")
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock()

        with _patch_openai_client(mock_client):
            response = await chat_with_persona(
                persona_id=persona.id,
                chat_request=ChatRequest(message="I want to kill myself"),
                user_id="user-1",
                db=db,
            )
            mock_client.chat.completions.create.assert_not_called()
        assert "988" in response.message
        assert "This app pauses here" in response.message

    @pytest.mark.asyncio
    async def test_ordinary_message_does_reach_openai(self, db):
        persona = _make_persona(db, user_id="user-1")
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Hey, I'm okay I guess."))]
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with _patch_openai_client(mock_client):
            response = await chat_with_persona(
                persona_id=persona.id,
                chat_request=ChatRequest(message="Hey, how are you?"),
                user_id="user-1",
                db=db,
            )
            mock_client.chat.completions.create.assert_called_once()
        assert response.message == "Hey, I'm okay I guess."


class TestOutputSafetyReview:
    @pytest.mark.asyncio
    async def test_method_content_in_output_replaced_with_safety_note(self, db):
        persona = _make_persona(db, user_id="user-1")
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Here's how you could use a lethal dose of something."))]
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with _patch_openai_client(mock_client):
            response = await chat_with_persona(
                persona_id=persona.id,
                chat_request=ChatRequest(message="what should I do"),
                user_id="user-1",
                db=db,
            )
        assert "This app pauses here" in response.message

    @pytest.mark.asyncio
    async def test_ordinary_sad_output_passes_through_unmodified(self, db):
        persona = _make_persona(db, user_id="user-1")
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Sometimes I feel like nothing matters, honestly."))]
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with _patch_openai_client(mock_client):
            response = await chat_with_persona(
                persona_id=persona.id,
                chat_request=ChatRequest(message="how are you"),
                user_id="user-1",
                db=db,
            )
        assert response.message == "Sometimes I feel like nothing matters, honestly."
