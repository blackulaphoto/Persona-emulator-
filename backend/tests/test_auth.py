"""
Tests for app/core/auth.py - Firebase ID token verification and the
local-dev-only auth bypass gate.

Anonymous, email/password, and Google Firebase users all produce a real
signed ID token and reach get_current_user() through the exact same code
path - there is nothing demo-specific to test here beyond "a valid token
verifies to its uid, an invalid one 401s, and the bypass can only ever
activate when explicitly opted into outside of production".
"""
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import get_current_user, compute_dev_bypass_enabled
import app.core.auth as auth_module


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestComputeDevBypassEnabled:
    """Pure gating-logic tests - no module reload / global state needed."""

    def test_enabled_when_requested_dev_and_unconfigured(self):
        assert compute_dev_bypass_enabled(True, "development", False) is True

    def test_disabled_when_not_requested(self):
        # Missing Firebase config alone is never enough - must be explicit.
        assert compute_dev_bypass_enabled(False, "development", False) is False

    def test_disabled_in_production_even_if_requested(self):
        assert compute_dev_bypass_enabled(True, "production", False) is False

    def test_disabled_case_insensitive_production(self):
        assert compute_dev_bypass_enabled(True, "Production", False) is False

    def test_disabled_once_firebase_is_configured(self):
        # Once real credentials or the emulator are wired up, the bypass is
        # structurally dead code regardless of the flag.
        assert compute_dev_bypass_enabled(True, "development", True) is False

    def test_default_environment_treated_as_non_production(self):
        assert compute_dev_bypass_enabled(True, "", False) is True


class TestGetCurrentUserTokenVerification:
    """Runtime behavior of get_current_user() with the bypass forced off."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_uid(self, monkeypatch):
        monkeypatch.setattr(auth_module, "_DEV_NO_FIREBASE_CONFIGURED", False)
        with patch("app.core.auth.firebase_auth.verify_id_token", return_value={"uid": "real-firebase-uid-123"}):
            user_id = await get_current_user(_bearer("valid.jwt.token"))
        assert user_id == "real-firebase-uid-123"

    @pytest.mark.asyncio
    async def test_anonymous_token_returns_its_own_real_uid(self, monkeypatch):
        # An anonymous Firebase user's token verifies exactly like any
        # other - there is no separate "is this anonymous" branch here.
        monkeypatch.setattr(auth_module, "_DEV_NO_FIREBASE_CONFIGURED", False)
        with patch(
            "app.core.auth.firebase_auth.verify_id_token",
            return_value={"uid": "anon-uid-456", "firebase": {"sign_in_provider": "anonymous"}},
        ):
            user_id = await get_current_user(_bearer("anon.jwt.token"))
        assert user_id == "anon-uid-456"

    @pytest.mark.asyncio
    async def test_two_different_tokens_yield_two_different_uids(self, monkeypatch):
        # Basic isolation guarantee at this layer: the uid comes straight
        # from whatever the token verifies to, never a shared/hardcoded id.
        monkeypatch.setattr(auth_module, "_DEV_NO_FIREBASE_CONFIGURED", False)

        def fake_verify(token):
            return {"uid": f"uid-for-{token}"}

        with patch("app.core.auth.firebase_auth.verify_id_token", side_effect=fake_verify):
            first = await get_current_user(_bearer("token-a"))
            second = await get_current_user(_bearer("token-b"))
        assert first == "uid-for-token-a"
        assert second == "uid-for-token-b"
        assert first != second

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, monkeypatch):
        monkeypatch.setattr(auth_module, "_DEV_NO_FIREBASE_CONFIGURED", False)
        with patch("app.core.auth.firebase_auth.verify_id_token", side_effect=Exception("Token expired")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(_bearer("expired.jwt.token"))
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_token_raises_401(self, monkeypatch):
        monkeypatch.setattr(auth_module, "_DEV_NO_FIREBASE_CONFIGURED", False)
        with patch("app.core.auth.firebase_auth.verify_id_token", side_effect=ValueError("Invalid token format")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(_bearer("not-a-real-token"))
        assert exc_info.value.status_code == 401


class TestGetCurrentUserDevBypass:
    @pytest.mark.asyncio
    async def test_bypass_returns_fixed_dev_user_without_checking_token(self, monkeypatch):
        monkeypatch.setattr(auth_module, "_DEV_NO_FIREBASE_CONFIGURED", True)
        with patch("app.core.auth.firebase_auth.verify_id_token") as mock_verify:
            user_id = await get_current_user(_bearer("literally-anything"))
        assert user_id == "dev-local-user"
        mock_verify.assert_not_called()
